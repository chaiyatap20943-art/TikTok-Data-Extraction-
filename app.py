"""Private single-owner pilot; source data lives only in the current session."""
import hashlib
import hmac
import json
import os
import time
from datetime import date, datetime

import pandas as pd
import streamlit as st

from collector.data import (BANGKOK, INPUT_FIELDS, channel_handle, coverage,
                            export_csv, filename, normalize_rows, read_table,
                            reconcile, suggest_mapping)
from collector.screenshots import extract_text

st.set_page_config(page_title='TikTok Content Collector', layout='wide')
st.title('TikTok Content Collector')
password = os.environ.get('PILOT_PASSWORD', '')
if not password:
    try:
        password = st.secrets.get('PILOT_PASSWORD', '')
    except (FileNotFoundError, st.errors.StreamlitSecretNotFoundError):
        password = ''
if not isinstance(password, str) or len(password) < 16:
    st.error('Private pilot unavailable: configure PILOT_PASSWORD with at least 16 characters.')
    st.stop()
if not st.session_state.get('authenticated'):
    with st.form('login', clear_on_submit=True):
        entered = st.text_input('Pilot password', type='password')
        submitted = st.form_submit_button('Sign in')
    if submitted:
        now = time.monotonic()
        if now < st.session_state.get('retry_after', 0):
            st.error('Wait before trying again.')
        elif hmac.compare_digest(hashlib.sha256(entered.encode()).digest(), hashlib.sha256(password.encode()).digest()):
            st.session_state['authenticated'] = True
            st.rerun()
        else:
            st.session_state['retry_after'] = now + 5
            st.error('Incorrect password.')
    st.stop()
if st.sidebar.button('Delete session data and sign out'):
    st.session_state.clear()
    st.rerun()
st.caption('Private owner pilot • session-only retention • Live TikTok collection: NOT VERIFIED / NOT TESTED')
st.caption('Process permitted sources only. No authentication bypass or CAPTCHA solving.')
channel = st.text_input('TikTok channel URL', 'https://www.tiktok.com/@masterart_th')
left, right = st.columns(2)
start = left.date_input('Published from (Asia/Bangkok)', date(2026, 10, 1))
end = right.date_input('Published until (inclusive, Asia/Bangkok)', date(2026, 10, 31))
try:
    channel_handle(channel)
    if start > end:
        raise ValueError('Start date must be on or before end date.')
except ValueError as exc:
    st.error(str(exc))
    st.stop()
st.info('Missing counts stay blank. Rounded K/M displays are retained separately. Naive timestamps use Asia/Bangkok; date-only records have no invented time.')
authorized = st.checkbox('I am authorized to process these uploaded sources.')
mode = st.radio('Method', ['My Account / authorized import', 'Screenshot / manual upload', 'Authorized browser collection'])
context = (channel, start, end, mode)
if st.session_state.get('context') != context:
    for key in ('result', 'raw_observations', 'ocr_text'):
        st.session_state.pop(key, None)
    st.session_state['context'] = context

batches = []
if mode == 'My Account / authorized import':
    st.download_button('Download CSV template', (','.join(INPUT_FIELDS) + '\n').encode('utf-8-sig'), 'template.csv', 'text/csv')
    uploads = st.file_uploader('Authorized CSV/XLSX files (5 MB each, maximum 10 files)', type=['csv', 'xlsx'], accept_multiple_files=True)
    if len(uploads) > 10:
        st.error('Maximum 10 files per batch.')
        st.stop()
    for index, upload in enumerate(uploads):
        try:
            headers, rows = read_table(upload.getvalue(), upload.name)
            with st.expander(f'Preview and map: {upload.name}', expanded=True):
                st.dataframe(pd.DataFrame(rows[:5]), hide_index=True)
                suggestions = suggest_mapping(headers)
                mapping = {}
                for field in INPUT_FIELDS:
                    options = ['', *headers]
                    mapping[field] = st.selectbox(field, options, index=options.index(suggestions[field]), key=f'map-{index}-{field}')
                st.caption('Missing mappings stay blank. For verified links add video_url_quality=verified only after checking the actual source. Full captions require caption_quality=full.')
            batches.append((rows, mapping, 'owner_export', upload.name))
        except Exception as exc:
            st.error(f'Cannot read file: {type(exc).__name__}. Check encoding, format, limits and literal XLSX values.')
elif mode == 'Screenshot / manual upload':
    st.warning('OCR is unverified text. Confirm every value against the screenshot. There is no automatic row or metric inference.')
    upload = st.file_uploader('Owner screenshot (PNG/JPEG, 10 MB, 20 MP maximum)', type=['png', 'jpg', 'jpeg'])
    if upload and authorized and st.button('Extract visible text (OCR)'):
        try:
            st.session_state['ocr_text'] = extract_text(upload.getvalue())
        except Exception:
            st.error('OCR unavailable or invalid image. Use manual transcription below. English and Thai Tesseract data are required for OCR.')
    st.text_area('Unverified visible text', st.session_state.get('ocr_text', ''), height=160)
    st.caption('Transcribe only visible values. Blank time is allowed with a date-only publication value. No-key manual fallback is always available.')
    seed = pd.DataFrame([{**dict.fromkeys(INPUT_FIELDS, ''), 'video_url_quality': 'provisional', 'caption_quality': 'unknown'}])
    edited = st.data_editor(seed, num_rows='dynamic', key='manual-table', hide_index=True)
    confirmed = st.checkbox('I reviewed each transcribed field against its source; exact numbers and verified URLs are evidence-based.')
    if confirmed:
        batches.append((edited.fillna('').to_dict('records'), dict(zip(INPUT_FIELDS, INPUT_FIELDS)), 'owner_screenshot' if upload else 'manual', upload.name if upload else 'manual transcription'))
else:
    st.error('Blocked: no documentary authorization for automated TikTok extraction has been established. Ownership alone is insufficient. Use imports or manual evidence.')
    st.button('Start browser collection', disabled=True)
    st.caption('A separate local fixture worker is tested; it does not establish live TikTok access.')

if batches and st.button('Import & process', disabled=not authorized):
    records, issues, count = [], [], 0
    progress = st.progress(0, text='Running: validating sources')
    for index, (rows, mapping, source, reference) in enumerate(batches):
        count += len(rows)
        accepted, rejected = normalize_rows(rows, mapping, channel, start, end, source, reference)
        records.extend(accepted)
        issues.extend({**issue, 'source_reference': reference} for issue in rejected)
        progress.progress((index + 1) / len(batches), text=f'Running: {count} rows processed')
    st.session_state['raw_observations'] = records
    merged = reconcile(records)
    st.session_state['result'] = (merged, issues, count)
    progress.empty()

result = st.session_state.get('result')
if result and authorized:
    records, issues, count = result
    st.subheader('Results: ' + ('Partial' if issues or any(r['record_status'] != 'verified' for r in records) else 'Completed'))
    st.write(f'{count} source rows processed; {len(records)} included; {len(issues)} excluded or invalid.')
    if not records:
        st.warning('No valid matching imported rows. This does not mean the channel published zero videos.')
    if records:
        status = st.selectbox('Filter review table', ['All', 'needs_review', 'partial', 'verified'])
        visible = [r for r in records if status == 'All' or r['record_status'] == status]
        st.dataframe(pd.DataFrame(visible).astype(str), hide_index=True)
        with st.expander('Review or correct records, then revalidate'):
            editable = []
            for record in records:
                editable.append({'publication_datetime': record['posted_at_bangkok'] or record['posted_date_bangkok'],
                                 'caption': record['caption'], 'video_url': record['video_url'] or (channel.rstrip('/') + '/video/' + record['video_id'] if record['video_id'] else ''),
                                 'source_type': record['source_type'],
                                 'publication_time_quality': record['publication_time_quality'],
                                 **{key: record[key + '_displayed'] for key in ('views', 'likes', 'comments', 'shares', 'saves')},
                                 'video_url_quality': record['video_url_quality'], 'caption_quality': record['caption_quality']})
            corrections = st.data_editor(pd.DataFrame(editable), key='corrections', hide_index=True, disabled=['source_type'])
            checked = st.checkbox('I checked corrections against the source evidence.')
            if st.button('Apply verified corrections', disabled=not checked):
                accepted, rejected = normalize_rows(corrections.fillna('').to_dict('records'), dict(zip(INPUT_FIELDS, INPUT_FIELDS)), channel, start, end, 'manual', 'human correction of imported evidence')
                st.session_state['result'] = (reconcile(accepted), rejected, len(corrections))
                st.rerun()
        bom = st.checkbox('Excel-compatible UTF-8 BOM', value=True)
        snapshot = datetime.now(BANGKOK).date()
        st.download_button('Download CSV', export_csv(records, bom), filename(channel, start, end, snapshot), 'text/csv')
    report = coverage(records, issues, count)
    st.json(report, expanded=False)
    st.download_button('Download Coverage Report', json.dumps(report, ensure_ascii=False, indent=2).encode('utf-8'), 'coverage.json', 'application/json')
    if issues:
        st.dataframe(issues, hide_index=True)
    with st.expander('Original normalized observations (before deduplication)'):
        st.dataframe(pd.DataFrame(st.session_state.get('raw_observations', [])).astype(str), hide_index=True)
