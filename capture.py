import time
import requests
import pandas as pd
from scapy.all import sniff
from collections import deque

# Render API endpoint
API_URL = "https://your-render-app.onrender.com/predict"

# Buffer for packets
packet_buffer = deque(maxlen=20)

# Store processed features
data_rows = []


def extract_features(pkt):
    try:
        length = len(pkt)
        proto = 0

        if pkt.haslayer("TCP"):
            proto = "TCP"
        elif pkt.haslayer("UDP"):
            proto = "UDP"

        timestamp = time.time()

        return {
            "Timestamp": timestamp,
            "Length": length,
            "Protocol": proto
        }
    except:
        return None


# PROCESS PACKETS
def process_packet(pkt):
    features = extract_features(pkt)

    if features:
        packet_buffer.append(features)

        # Only process when buffer is filled
        if len(packet_buffer) == 10:
            df = pd.DataFrame(packet_buffer)

            # SAME preprocessing logic as your model
            df['packet_count'] = 1
            df['avg_size'] = df['Length']
            df['size_variation'] = df['Length'].diff().fillna(0)
            df['packet_rate'] = df['Length'].rolling(2).sum().fillna(0)
            df['rate_change'] = df['packet_rate'].diff().fillna(0)

            # Take last 10 rows (sequence)
            seq = [df[['packet_count','avg_size','size_variation','packet_rate','rate_change']].values.tolist()]
            send_to_server(seq)


# ─────────────────────────────────────────
last_sent = 0   # 👈 put this ABOVE the function (global)

def send_to_server(sequence):
    global last_sent

    try:
        # ⏱️ Rate limit (optional but recommended)
        if time.time() - last_sent < 1:
            return
        last_sent = time.time()

        payload = {
            "sequence": sequence
        }

        # ✅ ADD timeout HERE
        response = requests.post(API_URL, json=payload, timeout=5)

        if response.status_code == 200:
            result = response.json()
            print("✅ Prediction:", result)
        else:
            # ✅ ADD response.text HERE
            print("❌ Server error:", response.status_code, response.text)

    except Exception as e:
        print("🚨 Error sending data:", e)


# ─────────────────────────────────────────
# START CAPTURE
# ─────────────────────────────────────────
def start_capture():
    print("Starting packet capture... (Press Ctrl+C to stop)")
    sniff(prn=process_packet, store=False, filter="ip")


# ─────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────
if __name__ == "__main__":
    start_capture()