"""Live packet measurements. No generated traffic or simulated network metrics."""

from collections import Counter, deque
import threading
import time


def packet_record(packet):
    from scapy.all import IP, IPv6, TCP, UDP

    if IP in packet:
        network = packet[IP]
    elif IPv6 in packet:
        network = packet[IPv6]
    else:
        return None
    transport = packet[TCP] if TCP in packet else packet[UDP] if UDP in packet else None
    return {
        "Timestamp": float(packet.time),
        "Length": len(packet),
        "Protocol": "TCP" if TCP in packet else "UDP" if UDP in packet else "OTHER",
        "Source": network.src,
        "Destination": network.dst,
        "Source port": int(transport.sport) if transport is not None else None,
        "Destination port": int(transport.dport) if transport is not None else None,
    }


class LiveCapture:
    """One capture per UI session; synchronized counters and bounded history."""

    def __init__(self, history_limit=2000, sniff_fn=None, clock=time.monotonic):
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread = None
        self._sniff_fn = sniff_fn
        self._clock = clock
        self._packets = deque(maxlen=history_limit)
        self._buckets = {}
        self._protocols = Counter()
        self._count = self._bytes = 0
        self._started = self._ended = self._last_packet = None
        self._heartbeat = clock()
        self.state = "idle"
        self.error = None
        self.interface = None

    def start(self, interface):
        if self._thread is not None and self._thread.is_alive():
            return
        with self._lock:
            self._packets.clear()
            self._buckets.clear()
            self._protocols.clear()
            self._count = self._bytes = 0
            self._started = self._ended = self._last_packet = None
            self._heartbeat = self._clock()
            self.interface = interface
            self.state = "starting"
            self.error = None
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _ready(self):
        with self._lock:
            if self._started is None:
                self._started = self._clock()
            self.state = "running"

    def _record(self, packet):
        record = packet_record(packet)
        if record is None or self._stop.is_set():
            return
        now = self._clock()
        with self._lock:
            self._packets.append(record)
            self._count += 1
            self._bytes += record["Length"]
            self._protocols[record["Protocol"]] += 1
            self._last_packet = now
            bucket = self._buckets.setdefault(int(now), [0, 0])
            bucket[0] += 1
            bucket[1] += record["Length"]
            self._buckets = {k: v for k, v in self._buckets.items() if k >= int(now) - 60}

    def _run(self):
        try:
            if self._sniff_fn is None:
                from scapy.all import sniff
            else:
                sniff = self._sniff_fn
            while not self._stop.is_set():
                # Timeout also stops an idle capture; no next packet is required.
                sniff(iface=self.interface, prn=self._record, store=False,
                      timeout=1, started_callback=self._ready)
                with self._lock:
                    if self._clock() - self._heartbeat > 60:
                        self._stop.set()  # Release captures abandoned by a browser session.
        except Exception as exc:
            with self._lock:
                self.error = str(exc)
                self.state = "error"
        finally:
            with self._lock:
                self._ended = self._clock()
                if self.state != "error":
                    self.state = "stopped"

    def stop(self):
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=3)
            if self._thread.is_alive():
                with self._lock:
                    self.state = "stopping"

    def snapshot(self):
        with self._lock:
            now = self._clock()
            self._heartbeat = now
            end = self._ended if self._ended is not None else now
            elapsed = max(0, end - self._started) if self._started is not None else 0
            # Only fully observed one-second intervals: no partial bucket bias.
            first = int(self._started) + 1 if self._started is not None else int(end)
            last = int(end)
            seconds = range(max(first, last - 60), last)
            history = [{"Second since start": second - int(self._started),
                        "Packets/s": self._buckets.get(second, [0, 0])[0],
                        "Bytes/s": self._buckets.get(second, [0, 0])[1]}
                       for second in seconds]
            recent = history[-5:]
            live_rate = self.state == "running" and bool(recent)
            return {
                "state": self.state, "error": self.error, "interface": self.interface,
                "packets": list(self._packets), "packet_count": self._count,
                "byte_count": self._bytes, "protocols": dict(self._protocols),
                "elapsed": elapsed, "history": history,
                "packet_rate": sum(p["Packets/s"] for p in recent) / len(recent) if live_rate else None,
                "byte_rate": sum(p["Bytes/s"] for p in recent) / len(recent) if live_rate else None,
                "rate_seconds": len(recent),
                "last_packet_age": now - self._last_packet if self._last_packet is not None else None,
            }
