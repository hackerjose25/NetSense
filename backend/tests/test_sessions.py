import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

from scapy.all import IP, IPv6, TCP, UDP

from netsense.services.capture import LiveCapture
from netsense.services.sessions import SessionStore


def capture_fixture():
    capture = LiveCapture(history_limit=3, clock=lambda: 100.0)
    capture._ready()
    packets = [
        IP(src="10.0.0.1", dst="10.0.0.2") / TCP(sport=5000, dport=443),
        IP(src="10.0.0.2", dst="10.0.0.1") / TCP(sport=443, dport=5000),
        IPv6(src="::1", dst="::2") / UDP(sport=53, dport=6000),
    ]
    for timestamp, packet in zip([10, 20, 40], packets):
        packet.time = timestamp
        capture._record(packet)
    capture.stop()
    capture.state = "stopped"
    return capture


class TestSessionStore(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "sessions.sqlite3"
        self.store = SessionStore(self.path)
        self.snapshot = capture_fixture().snapshot()

    def test_saved_snapshot_survives_restart_and_is_not_live(self):
        self.snapshot.update(state="running", packet_rate=10, byte_rate=100, last_packet_age=0)
        session_id = self.store.save("Example", self.snapshot)
        saved = SessionStore(self.path).load(session_id)
        self.assertEqual(saved["packets"], self.snapshot["packets"])
        self.assertEqual(saved["byte_count"], self.snapshot["byte_count"])
        self.assertEqual(saved["state"], "stopped")
        self.assertEqual(saved["source_state"], "running")
        self.assertIsNone(saved["packet_rate"])
        self.assertEqual(self.snapshot["state"], "running")
        self.snapshot["packets"].clear()
        self.assertEqual(len(self.store.load(session_id)["packets"]), 3)

    def test_save_preserves_full_totals_after_packet_eviction(self):
        self.snapshot["packet_count"] = 5000
        self.snapshot["byte_count"] = 100000
        saved = self.store.load(self.store.save("Window", self.snapshot))
        self.assertEqual(saved["packet_count"], 5000)
        self.assertEqual(len(saved["packets"]), 3)

    def test_limits_and_delete_are_explicit(self):
        with self.assertRaises(ValueError):
            self.store.save(" ", self.snapshot)
        with self.assertRaises(ValueError):
            self.store.save("Empty", dict(self.snapshot, packets=[]))
        with patch("netsense.services.sessions.MAX_SNAPSHOT_BYTES", 1), self.assertRaises(ValueError):
            self.store.save("Large", self.snapshot)
        session_id = self.store.save("One", self.snapshot)
        with patch("netsense.services.sessions.MAX_SESSIONS", 1), self.assertRaises(ValueError):
            self.store.save("Two", self.snapshot)
        self.assertEqual(len(self.store.list_sessions()), 1)
        self.store.delete(session_id)
        self.assertEqual(self.store.list_sessions(), [])
        with self.assertRaises(ValueError):
            self.store.load(session_id)

    def test_names_are_data_and_duplicate_names_have_unique_ids(self):
        name = "Capture '); DROP TABLE sessions; --"
        first = self.store.save(name, self.snapshot)
        second = self.store.save(name, self.snapshot)
        self.assertNotEqual(first, second)
        self.assertEqual(len(self.store.list_sessions()), 2)
        self.assertEqual(self.store.load(first)["session_name"], name)


if __name__ == "__main__":
    unittest.main()
