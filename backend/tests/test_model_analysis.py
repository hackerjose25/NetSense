"""Integration checks use the shipped trained bundle and the real test PCAP."""

from pathlib import Path
import shutil
import tempfile
import unittest

from fastapi.testclient import TestClient
from scapy.all import rdpcap

from netsense.api import CaptureService, create_app
from netsense.config import MODELS_DIR
from netsense.ml.analysis import analyze, model_status
from netsense.services.capture import LiveCapture, packet_record
from netsense.services.sessions import SessionStore


class TestModelAnalysis(unittest.TestCase):
    def setUp(self):
        fixture = Path(__file__).parent / 'fixtures' / 'sample_capture.pcap'
        self.packets = [record for packet in rdpcap(str(fixture)) if (record := packet_record(packet))]
        self.snapshot = {'packets': self.packets, 'packet_count': len(self.packets)}

    def test_trained_bundle_and_capture_wide_results(self):
        status = model_status(MODELS_DIR)
        self.assertTrue(status['available'], status['detail'])
        self.assertEqual(status['metadata']['version'], 'packet-size-v1')
        result = analyze(self.snapshot, MODELS_DIR)
        self.assertEqual(result['total_windows'], len(self.packets) - 9)
        self.assertEqual(sum(result['distribution'].values()), result['windows_analyzed'])
        self.assertAlmostEqual(sum(result['probabilities'].values()), 1, places=5)
        self.assertEqual(result['retained_packets'], len(self.packets))
        self.assertEqual(result['observed']['bytes'], sum(p['Length'] for p in self.packets))
        self.assertGreaterEqual(result['windows'][-1]['end'], result['windows'][0]['start'])
        for window in result['windows']:
            self.assertTrue(0 <= window['probability'] <= 1)

    def test_ten_packets_form_one_complete_window(self):
        result = analyze({'packets': self.packets[:10], 'packet_count': 10}, MODELS_DIR)
        self.assertEqual(result['windows_analyzed'], 1)
        with self.assertRaises(ValueError):
            analyze({'packets': self.packets[:9], 'packet_count': 9}, MODELS_DIR)

    def test_mismatched_scaler_disables_bundle(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'packet-size-v1'
            shutil.copytree(MODELS_DIR / 'packet-size-v1', target)
            with (target / 'scaler.pkl').open('ab') as file:
                file.write(b'changed')
            status = model_status(Path(directory))
            self.assertFalse(status['available'])
            self.assertIn('do not match', status['detail'])

    def test_api_analyzes_live_and_saved_sources(self):
        capture = LiveCapture()
        capture._ready()
        fixture = Path(__file__).parent / 'fixtures' / 'sample_capture.pcap'
        for packet in rdpcap(str(fixture)):
            capture._record(packet)
        capture.state = 'stopped'
        service = CaptureService(capture)
        with tempfile.TemporaryDirectory() as directory:
            store = SessionStore(Path(directory) / 'sessions.sqlite3')
            session_id = store.save('Historical model test', service.snapshot())
            with TestClient(create_app(service, store)) as client:
                self.assertEqual(client.get('/api/model').status_code, 200)
                live = client.post('/api/model/predict', json={})
                saved = client.post('/api/model/predict', json={'session_id': session_id})
                self.assertEqual(live.status_code, 200, live.text)
                self.assertEqual(saved.status_code, 200, saved.text)
                self.assertEqual(saved.json()['source'], 'Historical model test')
                self.assertEqual(live.json()['distribution'], saved.json()['distribution'])
                self.assertEqual(client.post('/api/model/predict', json={'session_id': 'missing'}).status_code, 404)
                capture._packets.clear()
                self.assertEqual(client.post('/api/model/predict', json={}).status_code, 400)


if __name__ == '__main__':
    unittest.main()
