from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from scapy.all import IP, TCP

from netsense.api import CaptureService, create_app
from netsense.services.capture import LiveCapture
from netsense.services.sessions import SessionStore


class TestAPI(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.capture = LiveCapture(sniff_fn=self.sniff)
        self.service = CaptureService(self.capture)
        self.store = SessionStore(Path(self.temp.name) / 'sessions.sqlite3')
        self.client = TestClient(create_app(self.service, self.store))
        self.client.__enter__()
        self.addCleanup(self.client.__exit__, None, None, None)

    @staticmethod
    def sniff(**kwargs):
        kwargs['started_callback']()
        time.sleep(0.01)

    def seed(self):
        self.capture._ready()
        self.capture._record(IP(src='10.0.0.1', dst='10.0.0.2') / TCP(sport=5000, dport=443))
        self.capture.state = 'stopped'

    def test_start_stop_conflict_validation_and_capture_identity(self):
        before = self.client.get('/api/capture').json()['capture_id']
        with patch('netsense.api.interfaces', return_value={'interfaces': [{'id': 'test', 'name': 'Test'}], 'default': 'test'}):
            self.assertEqual(self.client.post('/api/capture/start', json={'interface': 'unknown'}).status_code, 400)
            response = self.client.post('/api/capture/start', json={'interface': 'test'})
            self.assertEqual(response.status_code, 200)
            self.assertNotEqual(response.json()['capture_id'], before)
            self.assertEqual(self.client.post('/api/capture/start', json={'interface': 'test'}).status_code, 409)
            self.capture._record(IP() / TCP())
            self.assertEqual(self.client.post('/api/capture/stop').json()['state'], 'stopped')
            self.assertEqual(self.client.get('/api/capture').json()['packet_count'], 1)

    def test_saved_session_roundtrip_and_deletion(self):
        self.assertEqual(self.client.post('/api/sessions', json={'name': 'Empty'}).status_code, 400)
        self.seed()
        response = self.client.post('/api/sessions', json={'name': 'API capture'})
        self.assertEqual(response.status_code, 201)
        session_id = response.json()['id']
        self.assertEqual(len(self.client.get('/api/sessions').json()), 1)
        snapshot = self.client.get(f'/api/sessions/{session_id}').json()
        self.assertEqual(snapshot['packet_count'], 1)
        self.assertIsNone(snapshot['packet_rate'])
        self.assertEqual(self.client.delete(f'/api/sessions/{session_id}').status_code, 204)
        self.assertEqual(self.client.get(f'/api/sessions/{session_id}').status_code, 404)
        self.assertEqual(self.client.get('/api/sessions').json(), [])

    def test_socket_sends_changed_packets_and_omits_unchanged_window(self):
        self.seed()
        with self.client.websocket_connect('/api/live', headers={'origin': 'http://127.0.0.1:8000'}) as ws:
            first = ws.receive_json()
            self.assertEqual(len(first['packets']), 1)
            ws.send_text('ack')
            second = ws.receive_json()
            self.assertNotIn('packets', second)
            self.capture._record(IP() / TCP())
            ws.send_text('ack')
            self.assertEqual(len(ws.receive_json()['packets']), 2)

    def test_socket_reconnect_gets_complete_snapshot(self):
        self.seed()
        for _ in range(2):
            with self.client.websocket_connect('/api/live', headers={'origin': 'http://localhost:5173'}) as ws:
                self.assertEqual(len(ws.receive_json()['packets']), 1)

    def test_unresponsive_socket_is_closed_so_browser_can_reconnect(self):
        from starlette.websockets import WebSocketDisconnect
        with patch('netsense.api.ACK_TIMEOUT', 0.01):
            with self.client.websocket_connect('/api/live', headers={'origin': 'http://127.0.0.1:8000'}) as ws:
                ws.receive_json()
                with self.assertRaises(WebSocketDisconnect) as disconnected:
                    ws.receive_json()
                self.assertEqual(disconnected.exception.code, 1001)

    def test_remote_origins_and_hosts_are_rejected(self):
        self.assertEqual(self.client.post('/api/capture/stop', headers={'origin': 'https://unrelated.example'}).status_code, 403)
        self.assertEqual(self.client.get('/api/capture', headers={'host': 'unrelated.example'}).status_code, 400)
        from starlette.websockets import WebSocketDisconnect
        with self.assertRaises(WebSocketDisconnect):
            with self.client.websocket_connect('/api/live', headers={'origin': 'https://unrelated.example'}):
                pass

    def test_no_interfaces_does_not_block_saved_sessions(self):
        self.seed()
        self.store.save('Offline capture', self.service.snapshot())
        with patch('netsense.api.interfaces', side_effect=RuntimeError('no driver')):
            self.assertEqual(self.client.get('/api/interfaces').status_code, 503)
            self.assertEqual(len(self.client.get('/api/sessions').json()), 1)

    def test_missing_model_is_explicit_and_names_are_validated(self):
        with patch('netsense.api.MODELS_DIR', Path(self.temp.name)):
            self.assertFalse(self.client.get('/api/model').json()['available'])
            self.assertEqual(self.client.post('/api/model/predict', json={}).status_code, 503)
        self.seed()
        self.assertEqual(self.client.post('/api/sessions', json={'name': ' '}).status_code, 400)
        self.assertEqual(self.client.post('/api/sessions', json={'name': 'x' * 81}).status_code, 422)
        self.assertEqual(self.client.get('/api/capture').headers['cache-control'], 'no-store')


if __name__ == '__main__':
    unittest.main()
