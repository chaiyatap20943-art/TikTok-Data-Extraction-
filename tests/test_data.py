import csv
import io
from datetime import date

import pytest
from openpyxl import Workbook

from collector.data import (FIELDS, INPUT_FIELDS, channel_handle, coverage,
                            export_csv, filename, import_csv, metric,
                            normalize_rows, read_table, reconcile,
                            suggest_mapping)

CHANNEL = 'https://www.tiktok.com/@masterart_th'
START, END = date(2026, 10, 1), date(2026, 10, 31)


def row(**changes):
    return {'publication_datetime': '2026-10-01T00:00:00+07:00',
            'caption': 'สีสวย 🎨, "ไทย"\n#ศิลปะ', 'video_url': CHANNEL + '/video/1234567890123456789',
            'video_url_quality': 'verified', 'caption_quality': 'full',
            'views': '104K', 'likes': '0', 'comments': '12', 'shares': '', 'saves': 'N/A', **changes}


def normalize(rows):
    return normalize_rows(rows, dict(zip(INPUT_FIELDS, INPUT_FIELDS)), CHANNEL, START, END, 'fixture', 'synthetic')


@pytest.mark.parametrize('text,expected', [('104K', (None, '104K', 'rounded')), ('1.2M', (None, '1.2M', 'rounded')), ('0', (0, '0', 'exact')), ('', (None, '', 'missing')), ('1,234', (1234, '1,234', 'exact')), ('-3', (None, '-3', 'invalid'))])
def test_precision(text, expected):
    assert metric(text) == expected


def test_boundaries_and_nulls():
    records, issues = normalize([row(), row(publication_datetime='2026-09-30T16:59:59Z'),
                                row(publication_datetime='2026-10-31T16:59:59.999999Z'),
                                row(publication_datetime='2026-10-31T17:00:00Z')])
    assert len(records) == 2
    assert len(issues) == 2
    assert records[0]['likes'] == 0
    assert records[0]['views'] is None
    assert records[0]['shares'] is None
    assert records[0]['posted_at_utc'] == '2026-09-30T17:00:00+00:00'


def test_csv_roundtrip_and_injection():
    records, _ = normalize([row(caption='=HYPERLINK("x")\nไทย 🎨')])
    blob = export_csv(records)
    assert blob.startswith(b'\xef\xbb\xbf')
    parsed = list(csv.DictReader(io.StringIO(blob.decode('utf-8-sig'))))
    assert tuple(parsed[0]) == FIELDS
    assert parsed[0]['caption'] == "'=HYPERLINK(\"x\")\nไทย 🎨"
    assert parsed[0]['video_id'] == '1234567890123456789'
    assert parsed[0]['views'] == ''
    assert not export_csv(records, False).startswith(b'\xef\xbb\xbf')


def test_thai_headers_and_date_only():
    data = 'วันที่,คำบรรยาย,ยอดดู,ถูกใจ\n2026-10-20,ศิลปะ 🎨,11K,0\n'.encode()
    records, issues = import_csv(data, CHANNEL, START, END, 'fixture')
    assert not issues
    assert records[0]['caption'] == 'ศิลปะ 🎨'
    assert records[0]['posted_time_bangkok'] == ''
    assert records[0]['publication_time_quality'] == 'date_only'
    assert records[0]['video_url_quality'] == 'missing'


def test_errors_and_provisional_urls():
    records, issues = normalize([row(video_url=CHANNEL + '/video/1', video_url_quality='provisional'),
                                row(publication_datetime='bad'), row(video_url='http://127.0.0.1'),
                                row(video_url='https://www.tiktok.com/@other/video/2')])
    assert len(records) == 1 and len(issues) == 3
    assert records[0]['video_url'] == ''
    assert 'Provisional' in records[0]['notes']


def test_dedup_retains_exact_and_conflicts():
    records, _ = normalize([row(views='100', likes='2'), row(views='1K', likes='0')])
    merged = reconcile(records)
    assert len(merged) == 1
    assert merged[0]['views'] == 100
    assert merged[0]['record_status'] == 'needs_review'
    records, _ = normalize([row(video_url_quality='provisional'), row(video_url_quality='provisional')])
    assert len(reconcile(records)) == 2


def test_upload_limits_and_headers():
    with pytest.raises(ValueError):
        read_table(b'x' * (5 * 1024 * 1024 + 1), 'test.csv')
    with pytest.raises(ValueError):
        read_table(b'x,x\n1,2', 'test.csv')
    with pytest.raises(ValueError):
        channel_handle('https://www.tiktok.com.evil/@owner')
    with pytest.raises(ValueError):
        channel_handle('https://www.tiktok.com/@owner?redirect=http://localhost')


def test_xlsx_and_formula_rejection():
    workbook = Workbook()
    workbook.active.append(['วันที่', 'คำบรรยาย', 'views'])
    workbook.active.append(['2026-10-01', 'ทดสอบ', '12'])
    data = io.BytesIO()
    workbook.save(data)
    headers, rows = read_table(data.getvalue(), 'owner.xlsx')
    assert suggest_mapping(headers)['publication_datetime'] == 'วันที่'
    assert rows[0]['คำบรรยาย'] == 'ทดสอบ'
    workbook.active.append(['2026-10-02', '=1+1', '0'])
    data = io.BytesIO()
    workbook.save(data)
    with pytest.raises(ValueError, match='formulas'):
        read_table(data.getvalue(), 'owner.xlsx')


def test_coverage_and_name():
    records, issues = normalize([row(), row(publication_datetime='2026-11-01')])
    report = coverage(records, issues, 2)
    assert report['outside_range'] == 1
    assert report['missing_fields']['shares'] == 1
    assert filename(CHANNEL, START, END, date(2026, 11, 10)) == 'tiktok_masterart_th_2026-10-01_2026-10-31_2026-11-10.csv'


def test_numeric_zero_and_observation_order():
    records, issues = normalize([row(likes=0, collected_at_utc='2026-11-02T00:00:00Z'),
                                row(likes=0, collected_at_utc='2026-11-01T00:00:00Z')])
    assert not issues
    assert records[0]['likes'] == 0
    assert reconcile(records)[0]['collected_at_utc'] == '2026-11-02T00:00:00+00:00'


def test_fixture_labels_survive_import():
    records, _ = import_csv(open('tests/fixtures/synthetic.csv', 'rb').read(), CHANNEL, START, END)
    assert len(records) == 2
    assert all(record['source_type'] == 'fixture' for record in records)


def test_explicitly_unmapped_column_stays_blank():
    mapping = dict(zip(INPUT_FIELDS, INPUT_FIELDS))
    mapping['likes'] = ''
    records, issues = normalize_rows([row(likes='123')], mapping, CHANNEL, START, END, 'fixture')
    assert not issues
    assert records[0]['likes'] is None
