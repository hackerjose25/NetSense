# NetSense — AI-Powered Network Traffic Classifier & Live Telemetry

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.40+-FF4B4B.svg?style=flat&logo=Streamlit&logoColor=white)](https://streamlit.io/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-EE4C2C.svg?style=flat&logo=PyTorch&logoColor=white)](https://pytorch.org/)
[![Scapy](https://img.shields.io/badge/Scapy-Packet_Capture-008080.svg)](https://scapy.net/)

> **NetSense** is an enterprise-grade, real-time packet intelligence dashboard and neural network traffic analyzer built with Python, Streamlit, Scapy, and PyTorch. 
> 
> Maintained & owned by **Jose Regish J** ([@hackerjose25](https://github.com/hackerjose25)) and the NetSense engineering team.

---

## ⚡ Key Features

- **Real-Time Packet Ingestion**: Live IPv4 and IPv6 packet capture directly at the network adapter using Scapy with raw-socket / Npcap integration.
- **Strictly Genuine Telemetry**: Zero mock data, simulated TCP windows, or synthetic fallback. Every displayed rate, protocol slice, and byte count comes directly from your physical or virtual network interface.
- **Deep Learning Classification**: Built-in PyTorch LSTM classifier (`tcp_udp_lstm_pytorch.pt`) for sequence-level packet categorization and pattern inference.
- **Glassmorphic Control Console**: Premium dark-mode interface inspired by advanced network telemetry consoles, featuring responsive typography, smooth state animations, and an interactive live dashboard.
- **Packet Explorer & CSV Export**: Real-time packet table with timestamped packet sizes, source/destination IPs, ports, and instant CSV snapshot download (up to 2,000 packets).
- **Session-Guarded Architecture**: Thread-safe background sniffer with automatic heartbeat timeouts, graceful adapter release, and isolated per-session states.

---

## 🏗️ Architecture & Data Pipeline

```text
[ Network Interface ] (Wi-Fi / Ethernet / Loopback)
        │
        ▼
[ Scapy Sniffer Thread ] (live_capture.py)
   ├── Raw Packet Capture (Npcap / libpcap)
   ├── Thread-safe Ring Buffer
   └── Synchronized 1-second Rate Interval Aggregators
        │
        ├──► [ Live Telemetry Dashboard ] (live_dashboard.py / ui.py)
        │       ├── Instant Throughput (packets/s & Mbit/s)
        │       ├── Protocol Breakdown (TCP / UDP / ICMP / ARP)
        │       └── Packet Detail Table & CSV Export
        │
        └──► [ Feature Extraction & ML Engine ] (app.py)
                ├── Rolling 10-Timestep Sequences
                ├── Scaler Normalization
                └── PyTorch LSTM Inference (`tcp_udp_lstm_pytorch.pt`)
```

---

## 🚀 Quick Start

### 1. Prerequisites

- **Python 3.10+**
- **Windows**: Install [Npcap](https://npcap.com/) with **"Install Npcap in WinPcap API-compatible Mode"** enabled. (Run Streamlit from an Administrator terminal if your user group requires raw-socket privileges).
- **Linux / macOS**: Ensure `libpcap` is installed (`sudo apt-get install libpcap-dev` on Debian/Ubuntu).

### 2. Installation

Clone the repository and install the dependencies:

```powershell
git clone https://github.com/hackerjose25/NetSense.git
cd NetSense
pip install -r requirements.txt
```

### 3. Launch the Application

```powershell
streamlit run app.py
```

Open your browser at **`http://localhost:8501`**.

---

## 🖥️ Using the Console

1. Click **Open console ↗** in the navigation bar to jump directly to the live monitoring center.
2. Select your active network adapter (e.g., Wi-Fi, Ethernet, or Virtual Adapter) from the dropdown.
3. Click **Start Live Capture** to initiate a clean, synchronized sniffing session.
4. Monitor live bandwidth, packets per second, and protocol distributions in real time.
5. Inspect individual packet headers under the **Packet explorer** tab or click **Export CSV snapshot** to download session data.
6. Click **Stop Capture** to safely release the adapter and preserve your capture snapshot.

---

## 🧪 Verification & Testing

NetSense includes a full suite of automated unit tests covering packet preprocessing, sequence construction, model inference, and UI state integrity:

```powershell
python -m unittest test_live_capture test_netsense -q
```

---

## 📁 Repository Structure

```text
NetSense/
├── app.py                # Main application entry point & ML model inference
├── ui.py                 # Bequant-inspired hero, navigation, and team components
├── live_capture.py       # Thread-safe packet capture engine & interval metrics
├── live_dashboard.py     # Live telemetry visualization, charts & packet table
├── train.py              # PyTorch model training pipeline for LSTM classifier
├── test_netsense.py      # Core unit tests for model, preprocessing & UI guards
├── test_live_capture.py  # Synchronized packet capture unit tests
├── requirements.txt      # Python dependencies
├── LICENSE               # MIT License
├── static/
│   ├── netsense.css      # Custom styling, glassmorphic effects & design tokens
│   └── hero-network.mp4  # Local high-definition telemetry hero video
└── images/
    ├── jose.jpg          # Jose Regish J profile avatar
    └── gayathri.jpg      # Gayathri M profile avatar
```

---

## 👥 Built By

The NetSense platform was conceptualized and built by:

| Builder | Role | Contribution | Profile |
| :--- | :--- | :--- | :--- |
| **Jose Regish J** | **Full Stack Developer** | Designed the frontend architecture and user interface, and contributed to core backend packet processing. | [![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=flat&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/hackerjose25/) |
| **Gayathri M** | **Backend & ML Developer** | Developed, trained, and fine-tuned the machine learning models used for network traffic analysis and packet classification. | [![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=flat&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/gayathri-m-140279394/) |
| **Dharshini M** | **Frontend Developer** | Researched the project concept and problem space, and contributed to frontend interface development and styling. | *Profile Space Reserved* |

---

## 📄 License

This project is open-source and available under the **[MIT License](LICENSE)**.

```text
Copyright (c) 2025 Jose Regish J (hackerjose25)
```
