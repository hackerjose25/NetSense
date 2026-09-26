import time
import unittest

from scapy.all import ARP, IP, IPv6, TCP, UDP

from live_capture import LiveCapture, packet_record


class TestLiveCapture(unittest.TestCase):
    def setUp(self):
        self.now = 100.25
        self.capture = LiveCapture(history_limit=2, clock=lambda: self.now)
        self.capture._ready()

    def test_observed_packet_fields_and_ipv6(self):
        packet = IPv6(src="::1", dst="::1") / UDP(sport=1234, dport=5678)
        packet.time = 123456.75
        record = packet_record(packet)
        self.assertEqual(record["Timestamp"], 123456.75)
        self.assertEqual(record["Length"], len(packet))
        self.assertEqual(record["Protocol"], "UDP")
        self.assertEqual(record["Destination port"], 5678)
        self.assertIsNone(packet_record(ARP()))

    def test_counters_survive_history_eviction(self):
        packets = [IP() / TCP(), IP() / UDP(), IPv6() / TCP()]
        for packet in packets:
            self.capture._record(packet)
        result = self.capture.snapshot()
        self.assertEqual(result["packet_count"], 3)
        self.assertEqual(result["byte_count"], sum(map(len, packets)))
        self.assertEqual(len(result["packets"]), 2)
        self.assertEqual(result["protocols"], {"TCP": 2, "UDP": 1})

    def test_rates_use_elapsed_seconds_and_include_idle_intervals(self):
        self.now = 101.2
        self.capture._record(IP() / UDP())
        self.capture._record(IP() / UDP())
        self.now = 103.2
        result = self.capture.snapshot()
        self.assertEqual(result["packet_rate"], 1)  # 2 packets / 2 complete seconds
        self.assertEqual(result["byte_rate"], len(IP() / UDP()))
        self.now = 109.2
        result = self.capture.snapshot()
        self.assertEqual(result["packet_rate"], 0)
        self.assertGreater(result["last_packet_age"], 5)
        self.assertEqual(result["packet_count"], 2)

    def test_no_rate_before_observation_or_after_stop(self):
        self.assertIsNone(self.capture.snapshot()["packet_rate"])
        self.capture.state = "stopped"
        self.now += 10
        self.assertIsNone(self.capture.snapshot()["packet_rate"])

    def test_capture_failure_is_not_data(self):
        def failure(**kwargs):
            raise PermissionError("capture denied")
        capture = LiveCapture(sniff_fn=failure)
        capture.start("test")
        capture._thread.join(timeout=1)
        result = capture.snapshot()
        self.assertEqual(result["state"], "error")
        self.assertIn("capture denied", result["error"])
        self.assertEqual(result["packet_count"], 0)
        self.assertEqual(result["packets"], [])
        self.assertIsNone(result["packet_rate"])

    def test_idle_capture_can_stop_and_restart_cleanly(self):
        def idle(**kwargs):
            kwargs["started_callback"]()
            time.sleep(0.02)
        capture = LiveCapture(sniff_fn=idle)
        capture.start("test")
        time.sleep(0.03)
        capture._record(IP() / TCP())
        capture.stop()
        self.assertEqual(capture.snapshot()["state"], "stopped")
        self.assertFalse(capture._thread.is_alive())
        capture.start("test")
        time.sleep(0.03)
        self.assertEqual(capture.snapshot()["packet_count"], 0)
        capture.stop()

    def test_sessions_do_not_share_packets(self):
        other = LiveCapture()
        self.capture._record(IP() / TCP())
        self.assertEqual(other.snapshot()["packet_count"], 0)


if __name__ == "__main__":
    unittest.main()
