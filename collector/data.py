"""Schema v1: source-preserving, precision-aware private analytics processing."""
import csv
import io
import json
import re
import zipfile
from datetime import date, datetime, timezone
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

BANGKOK = ZoneInfo('Asia/Bangkok')
METRICS = ('views', 'likes', 'comments', 'shares', 'saves')
INPUT_FIELDS = ('publication_datetime', 'caption', 'video_url', *METRICS)
FIELDS = ('account_handle', 'video_id', 'video_url', 'posted_at_utc',
          'posted_at_bangkok', 'posted_date_bangkok', 'posted_time_bangkok',
          'caption', *METRICS, 'collected_at_utc', 'source_type', 'source_reference',
          'publication_time_quality', 'metrics_precision', 'caption_quality',
          'video_url_quality', 'record_status', 'notes',
          *(name for metric in METRICS for name in (f'{metric}_displayed', f'{metric}_quality')))
MAX_BYTES = 5 * 1024 * 1024
SOURCE_TYPES = {'owner_export', 'owner_screenshot', 'authorized_browser', 'approved_provider', 'manual', 'fixture'}
ALIASES = {
    'publication_datetime': ('posted_at_bangkok', 'posted_at_utc', 'posted_date_bangkok', 'date', 'publish time', 'วันที่เผยแพร่', 'วันที่'),
    'caption': ('description', 'title', 'คำบรรยาย', 'ชื่อวิดีโอ'),
    'video_url': ('url', 'link', 'ลิงก์วิดีโอ'),
    'views': ('video views', 'ยอดดู', 'ยอดเข้าชม'),
    'likes': ('like', 'ถูกใจ', 'ยอดถูกใจ'),
    'comments': ('comment', 'ความคิดเห็น'),
    'shares': ('share', 'แชร์'),
    'saves': ('favorites', 'บันทึก'),
}


def channel_handle(url):
    parts = urlsplit(url.strip())
    if (parts.scheme != 'https' or parts.netloc not in ('www.tiktok.com', 'tiktok.com')
            or parts.query or parts.fragment):
        raise ValueError('Use a canonical HTTPS TikTok channel URL without query parameters.')
    match = re.fullmatch(r'/@([A-Za-z0-9_.]{1,24})/?', parts.path)
    if not match:
        raise ValueError('Expected https://www.tiktok.com/@channel')
    return match[1].lower()


def video_identity(url):
    parts = urlsplit(url.strip())
    if parts.scheme != 'https' or parts.netloc not in ('www.tiktok.com', 'tiktok.com'):
        raise ValueError('Video URL must use the canonical TikTok HTTPS host.')
    match = re.fullmatch(r'/@([A-Za-z0-9_.]{1,24})/video/([0-9]{1,24})/?', parts.path)
    if not match or parts.query or parts.fragment:
        raise ValueError('Expected a canonical /@channel/video/numeric-id URL.')
    return match[1].lower(), match[2]


def parse_timestamp(value):
    value = value.strip()
    if not value:
        return None, 'unknown', ''
    if re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
        return None, 'date_only', date.fromisoformat(value).isoformat()
    result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if result.tzinfo is None:
        result = result.replace(tzinfo=BANGKOK)
    result = result.astimezone(BANGKOK)
    return result, 'exact', result.date().isoformat()


def metric(value):
    displayed = str(value if value is not None else '').strip()
    if displayed.lower() in ('', 'n/a', 'na', 'unknown', 'null', '-'):
        return None, displayed, 'missing'
    if re.fullmatch(r'\d+(?:\.\d+)?\s*[KMkm]', displayed):
        return None, displayed, 'rounded'
    if not re.fullmatch(r'(?:[0-9]+|[0-9]{1,3}(?:,[0-9]{3})+)', displayed):
        return None, displayed, 'invalid'
    result = int(displayed.replace(',', ''))
    return (result, displayed, 'exact') if result <= 2**63 - 1 else (None, displayed, 'invalid')


def read_table(payload, filename):
    if len(payload) > MAX_BYTES:
        raise ValueError('Upload exceeds the 5 MB limit.')
    if filename.lower().endswith('.xlsx'):
        from openpyxl import load_workbook
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            if sum(item.file_size for item in archive.infolist()) > 30 * 1024 * 1024:
                raise ValueError('Expanded XLSX exceeds 30 MB.')
        workbook = load_workbook(io.BytesIO(payload), read_only=True, data_only=False, keep_links=False)
        try:
            rows = workbook.active.iter_rows()
            headers = [str(cell.value or '').strip() for cell in next(rows)]
            values = []
            for index, cells in enumerate(rows):
                if index >= 10000:
                    raise ValueError('Maximum 10,000 rows per file.')
                row = {}
                for header, cell in zip(headers, cells):
                    if cell.data_type == 'f':
                        raise ValueError('XLSX formulas are not accepted. Export literal values instead.')
                    if header in ('video_id', 'Video ID') and isinstance(cell.value, (int, float)):
                        raise ValueError('Store video IDs as text in XLSX to prevent precision loss.')
                    row[header] = str(cell.value if cell.value is not None else '')
                values.append(row)
        finally:
            workbook.close()
    elif filename.lower().endswith('.csv'):
        reader = csv.DictReader(io.StringIO(payload.decode('utf-8-sig'), newline=''))
        headers = reader.fieldnames or []
        values = []
        for index, row in enumerate(reader):
            if index >= 10000:
                raise ValueError('Maximum 10,000 rows per file.')
            values.append(row)
    else:
        raise ValueError('Use a CSV or XLSX file.')
    if not headers or len(set(headers)) != len(headers):
        raise ValueError('Upload requires unique column headers.')
    return headers, values


def suggest_mapping(headers):
    lowered = {key.strip().lower(): key for key in headers}
    return {field: next((lowered[name.lower()] for name in (field, *ALIASES.get(field, ()))
                         if name.lower() in lowered), '') for field in INPUT_FIELDS}


def normalize_rows(rows, mapping, channel, start, end, source='owner_export', reference='upload', observed=None):
    if source not in SOURCE_TYPES:
        raise ValueError('Unknown source type.')
    if start > end:
        raise ValueError('Start date must be on or before end date.')
    handle = channel_handle(channel)
    observed = observed or datetime.now(timezone.utc).isoformat()
    records, issues = [], []
    for line, raw in enumerate(rows, 2):
        try:
            if None in raw or any(value is None for value in raw.values()):
                raise ValueError('Row has too many columns.')
            def get(field):
                column = mapping.get(field, field)
                value = raw.get(column, '') if column else ''
                return '' if value is None else str(value)
            published, time_quality, day = parse_timestamp(get('publication_datetime'))
            if not day:
                raise ValueError('Missing publication date; retained in review issues, excluded from dated export.')
            if not start <= date.fromisoformat(day) <= end:
                issues.append({'row': line, 'kind': 'outside_range', 'reason': 'Outside Bangkok date range'})
                continue
            identifier, url = '', get('video_url').strip()
            url_quality = 'missing'
            if url:
                owner, identifier = video_identity(url)
                if owner != handle:
                    raise ValueError('Video belongs to a different channel.')
                url_quality = 'verified' if raw.get('video_url_quality') == 'verified' else 'provisional'
                url = f'https://www.tiktok.com/@{owner}/video/{identifier}'
            supplied_id = str(raw.get('video_id', '') or '')
            if supplied_id:
                if not re.fullmatch(r'[0-9]{1,24}', supplied_id) or (identifier and supplied_id != identifier):
                    raise ValueError('Video ID is invalid or conflicts with URL.')
                identifier = supplied_id
            if raw.get('publication_time_quality') in ('estimated_video_id', 'unknown'):
                time_quality = raw['publication_time_quality']
            observation = observed
            if raw.get('collected_at_utc'):
                instant = datetime.fromisoformat(str(raw['collected_at_utc']).replace('Z', '+00:00'))
                if instant.tzinfo is None:
                    raise ValueError('Observation timestamp must include a timezone.')
                observation = instant.astimezone(timezone.utc).isoformat()
            record = dict.fromkeys(FIELDS, '')
            record.update(account_handle='@' + handle, video_id=identifier,
                          video_url=url if url_quality == 'verified' else '',
                          posted_at_utc=published.astimezone(timezone.utc).isoformat() if published else '',
                          posted_at_bangkok=published.isoformat() if published else '',
                          posted_date_bangkok=day,
                          posted_time_bangkok=published.strftime('%H:%M:%S') if published else '',
                          caption=get('caption'), collected_at_utc=observation,
                          source_type='fixture' if raw.get('source_type') == 'fixture' else source, source_reference=reference,
                          publication_time_quality=time_quality,
                          caption_quality=raw.get('caption_quality') if raw.get('caption_quality') in ('full', 'truncated') else 'unknown',
                          video_url_quality=url_quality)
            notes, precision = [], {}
            if url_quality == 'provisional':
                notes.append('Provisional URL supplied: ' + url)
            for key in METRICS:
                value, displayed, quality = metric(get(key))
                # Preserve already known precision on reimport, never upgrade a rounded observation.
                if raw.get(key + '_quality') in ('rounded', 'estimated', 'missing'):
                    quality = raw[key + '_quality']
                    displayed = raw.get(key + '_displayed', displayed)
                    value = None
                record[key] = value
                record[key + '_displayed'] = displayed
                record[key + '_quality'] = quality
                precision[key] = quality
            record['metrics_precision'] = json.dumps(precision, ensure_ascii=False, sort_keys=True)
            if any(value == 'invalid' for value in precision.values()):
                notes.append('Invalid metric values require review')
            record['record_status'] = 'needs_review' if (url_quality != 'verified' or time_quality != 'exact' or 'invalid' in precision.values()) else 'partial'
            if (record['record_status'] == 'partial' and record['caption_quality'] == 'full'
                    and all(value == 'exact' for value in precision.values())):
                record['record_status'] = 'verified'
            record['notes'] = '; '.join(notes)
            records.append(record)
        except (ValueError, TypeError, OverflowError) as exc:
            issues.append({'row': line, 'kind': 'invalid', 'reason': str(exc)})
    return records, issues


def reconcile(records):
    """Select complete observation by verified ID. Never silently mix metric snapshots."""
    result, positions = [], {}
    for record in records:
        key = record['video_id'] if record['video_url_quality'] == 'verified' else ''
        if not key or key not in positions:
            if key:
                positions[key] = len(result)
            result.append(dict(record))
            continue
        index = positions[key]
        prior = result[index]
        def rank(row):
            return (sum(row[key + '_quality'] == 'exact' for key in METRICS), row['collected_at_utc'])
        winner = dict(max((prior, record), key=rank))
        winner['notes'] += '; Duplicate observations reconciled by exact-field count then collection time; snapshots not mixed'
        if any(prior[key] != record[key] for key in (*METRICS, 'caption', 'posted_at_bangkok')):
            winner['record_status'] = 'needs_review'
            winner['notes'] += '; Conflicting source observations retained in session review'
        result[index] = winner
    return sorted(result, key=lambda row: (row['posted_date_bangkok'], row['posted_time_bangkok'], row['video_id']))


def import_csv(payload, channel, start, end, source='owner_export'):
    headers, rows = read_table(payload, 'upload.csv')
    records, issues = normalize_rows(rows, suggest_mapping(headers), channel, start, end, source)
    return reconcile(records), issues


def spreadsheet_safe(value):
    if isinstance(value, str) and value.lstrip().startswith(('=', '+', '-', '@')):
        return "'" + value
    return '' if value is None else value


def export_csv(records, bom=True):
    output = io.StringIO(newline='')
    writer = csv.DictWriter(output, fieldnames=FIELDS)
    writer.writeheader()
    for record in sorted(records, key=lambda row: (row['posted_date_bangkok'], row['posted_time_bangkok'], row['video_id'])):
        writer.writerow({key: spreadsheet_safe(record.get(key)) for key in FIELDS})
    return output.getvalue().encode('utf-8-sig' if bom else 'utf-8')


def filename(channel, start, end, snapshot):
    return f'tiktok_{channel_handle(channel)}_{start}_{end}_{snapshot}.csv'


def coverage(records, issues, found):
    return {'found': found, 'included': len(records),
            'outside_range': sum(row['kind'] == 'outside_range' for row in issues),
            'missing_fields': {key: sum(row[key] is None for row in records) for key in METRICS},
            'blocked': 0, 'unverified': sum(row['record_status'] != 'verified' for row in records),
            'invalid_rows': sum(row['kind'] == 'invalid' for row in issues),
            'warning': 'Imported evidence only. Discovered count may be incomplete; no channel completeness guarantee.'}
