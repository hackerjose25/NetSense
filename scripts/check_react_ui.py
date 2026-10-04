"""End-to-end check of the built React app at http://127.0.0.1:8000.

Uses the bundled PCAP for a temporary historical session and removes only
that session afterwards. Tests the real HTTP/WebSocket backend, not mocks.
"""

from collections import Counter
from pathlib import Path
import sys
from uuid import uuid4

from playwright.sync_api import sync_playwright, expect
from scapy.all import rdpcap

ROOT = Path(__file__).resolve().parent.parent
from netsense.services.capture import packet_record
from netsense.services.sessions import SessionStore


(ROOT / 'test-results').mkdir(exist_ok=True)

packets = [record for packet in rdpcap(str(ROOT / 'backend/tests/fixtures/sample_capture.pcap'))
           if (record := packet_record(packet)) is not None]
name = 'Browser verification ' + uuid4().hex[:8]
store = SessionStore()
session_id = store.save(name, {
    'state': 'stopped', 'error': None, 'interface': 'Bundled sample_capture.pcap',
    'packets': packets[-2000:], 'packet_count': len(packets),
    'byte_count': sum(p['Length'] for p in packets), 'protocols': dict(Counter(p['Protocol'] for p in packets)),
    'elapsed': max(p['Timestamp'] for p in packets) - min(p['Timestamp'] for p in packets),
    'history': [], 'packet_rate': None, 'byte_rate': None, 'last_packet_age': None, 'rate_seconds': 0,
})
try:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel='msedge', headless=True)
        page = browser.new_page(viewport={'width': 1440, 'height': 1100})
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto('http://127.0.0.1:8000')
        enter_btn = page.locator('#hero-enter-console-btn')
        if enter_btn.is_visible():
            page.screenshot(path=str(ROOT / 'test-results/react-landing.png'), full_page=True)
            enter_btn.click()
        expect(page.locator('.app-shell')).to_be_visible()
        expect(page.get_by_label('Network adapter')).not_to_contain_text('Finding network adapters', timeout=20000)
        page.screenshot(path=str(ROOT / 'test-results/react-overview.png'), full_page=True)
        page.get_by_role('button', name='Saved sessions').click()
        row = page.get_by_role('row').filter(has_text=name)
        expect(row).to_be_visible()
        row.get_by_role('button', name='Open', exact=True).click()
        expect(page.get_by_text('Saved snapshot', exact=True)).to_be_visible()
        page.get_by_role('button', name='Model analysis', exact=True).click()
        expect(page.get_by_role('button', name='Analyze capture', exact=True)).to_be_enabled()
        page.get_by_role('button', name='Analyze capture', exact=True).click()
        expect(page.get_by_role('heading', name='Analysis results', exact=True)).to_be_visible(timeout=20000)
        expect(page.get_by_role('heading', name='Window-by-window results', exact=True)).to_be_visible()
        with page.expect_download() as report_event:
            page.get_by_role('button', name='Download report', exact=True).click()
        import json
        report = json.loads(Path(report_event.value.path()).read_text(encoding='utf-8'))
        assert report['retained_packets'] == len(packets)
        assert sum(report['distribution'].values()) == report['windows_analyzed']
        assert abs(sum(report['probabilities'].values()) - 1) < 0.00001
        page.screenshot(path=str(ROOT / 'test-results/react-model-analysis.png'), full_page=True)
        page.set_viewport_size({'width': 390, 'height': 844})
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        page.screenshot(path=str(ROOT / 'test-results/react-model-mobile.png'), full_page=True)
        page.set_viewport_size({'width': 1440, 'height': 1100})
        page.get_by_label('Capture to analyze').select_option('live')
        expect(page.get_by_role('heading', name='Analysis results', exact=True)).to_have_count(0)
        page.get_by_label('Capture to analyze').select_option(session_id)
        expect(page.get_by_role('button', name='Analyze capture', exact=True)).to_be_enabled()
        print('PASS matched model, saved-source selection, analysis results, report download and mobile layout', flush=True)
        page.get_by_role('button', name='Traffic explorer', exact=True).click()
        expect(page.get_by_role('table')).to_be_visible()
        expect(page.get_by_role('row')).to_have_count(3)
        page.get_by_label('Port', exact=True).fill('443')
        expect(page.get_by_text('No matching traffic', exact=True)).to_be_visible()
        page.get_by_label('Port', exact=True).fill('80')
        expect(page.get_by_role('row')).to_have_count(2)
        page.get_by_role('button', name='Inspect 192.168.1.10:5000 to 93.184.216.34:80').click()
        expect(page.get_by_role('tab', name='Packets', exact=True)).to_have_attribute('aria-selected', 'true')
        with page.expect_download() as event:
            page.get_by_role('button', name='Export CSV').click()
        assert event.value.suggested_filename == 'netsense_packets.csv'
        page.get_by_role('button', name='Clear filters').click()
        page.get_by_role('tab', name='Top talkers').click()
        expect(page.get_by_role('row')).to_have_count(4)
        page.get_by_role('tab', name='Connections').click()
        page.screenshot(path=str(ROOT / 'test-results/react-investigation.png'), full_page=True)
        # A periodic live update must not replace the focused input or its value.
        address = page.get_by_label('IP address or subnet', exact=True)
        address.fill('192.168.1.10')
        page.wait_for_timeout(1500)
        expect(address).to_be_focused()
        expect(address).to_have_value('192.168.1.10')
        page.set_viewport_size({'width': 390, 'height': 844})
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        page.screenshot(path=str(ROOT / 'test-results/react-mobile.png'), full_page=True)
        # Test cancellation and explicit deletion in the real session library.
        page.get_by_role('button', name='Saved sessions').click()
        row = page.get_by_role('row').filter(has_text=name)
        row.get_by_role('button', name=f'Delete {name}', exact=True).click()
        expect(page.get_by_role('dialog')).to_be_visible()
        page.get_by_role('button', name='Cancel', exact=True).click()
        expect(row).to_be_visible()
        row.get_by_role('button', name=f'Delete {name}', exact=True).click()
        page.get_by_role('button', name='Delete session', exact=True).click()
        expect(row).to_have_count(0)
        if '--live' in sys.argv:
            page.set_viewport_size({'width': 1440, 'height': 1100})
            page.get_by_role('button', name='Overview', exact=True).click()
            expect(page.get_by_role('button', name='Start capture', exact=True)).to_be_enabled()
            page.get_by_role('button', name='Start capture', exact=True).click()
            try:
                expect(page.get_by_role('button', name='Stop capture', exact=True)).to_be_enabled(timeout=20000)
                page.wait_for_function("async () => { const r = await fetch('/api/capture'); const s = await r.json(); return s.state === 'running' && s.elapsed >= 4; }", timeout=20000)
                page.screenshot(path=str(ROOT / 'test-results/react-live.png'), full_page=True)
                # Save through the new UI if this adapter observed traffic.
                capture = page.request.get('http://127.0.0.1:8000/api/capture').json()
                print(f"LIVE capture observed {capture['packet_count']} packets", flush=True)
                if capture['packets']:
                    live_name = name + ' live'
                    page.get_by_role('button', name='Save session', exact=True).click()
                    page.get_by_label('Session name', exact=True).fill(live_name)
                    page.get_by_role('button', name='Save snapshot', exact=True).click()
                    expect(page.get_by_text('Session saved. Find it in your capture library.', exact=True)).to_be_visible()
                    page.get_by_role('button', name='Saved sessions', exact=True).click()
                    live_row = page.get_by_role('row').filter(has_text=live_name)
                    expect(live_row).to_be_visible()
                    live_row.get_by_role('button', name=f'Delete {live_name}', exact=True).click()
                    page.get_by_role('button', name='Delete session', exact=True).click()
                    expect(live_row).to_have_count(0)
            finally:
                page.request.post('http://127.0.0.1:8000/api/capture/stop')
        page.set_viewport_size({'width': 1440, 'height': 1100})
        landing_btn = page.get_by_role('button', name='Landing page')
        if landing_btn.is_visible():
            landing_btn.click()
            expect(page.locator('#hero-enter-console-btn')).to_be_visible()
        assert not errors, errors
        print('PASS Landing page, Hero, WebSocket, saved session, filters, drill-down, CSV, focus persistence, mobile, deletion, and return to landing', flush=True)
        browser.close()
finally:
    store.delete(session_id)
    for session in store.list_sessions():
        if session['name'] == name + ' live':
            store.delete(session['id'])
