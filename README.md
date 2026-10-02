# NetSense — Network Traffic Intelligence

NetSense is a local network monitoring and investigation application with a **React + TypeScript frontend** and a **Python FastAPI backend**. Scapy captures IPv4/IPv6 packet headers; the dashboard shows live measurements, connections, endpoint rankings, and saved sessions.

## Start the React app

Prerequisites: Python 3.10+, Node.js 20.18+ with npm, and a packet capture driver. On Windows, install [Npcap](https://npcap.com/) with WinPcap compatibility. On Linux/macOS, install libpcap and use the capture permissions required by your system.

Run from the repository root:

```powershell
pip install -r requirements.txt
npm --prefix frontend ci
npm --prefix frontend run build
python run.py
```

Open **http://127.0.0.1:8000**. FastAPI serves the built frontend and API together; Node is only needed to install/build or develop the frontend. The lockfile pins frontend dependencies, and Vite 6 supports the project's existing Node 20.18 environment.

After changing frontend code, rebuild it and refresh the browser. Stop the server with Ctrl+C. If Npcap restricts capture to administrators, run the backend from an Administrator terminal.

## What changed from Streamlit

- Filters, tabs, pagination, and connection drill-down execute in the browser without Python page reruns.
- A WebSocket delivers capture snapshots once per second. Unchanged packet windows are omitted, and React reuses their existing data instead of reaggregating them.
- Tables render 50 rows per page. All matching retained rows are included in CSV exports.
- Packet capture runs independently of the UI. Optional PyTorch inference loads only when requested and executes outside the API event loop.
- Disconnects are visible, current rates become unavailable, and the frontend reconnects automatically. Inputs remain mounted during live updates.
- Saved sessions use the existing `data/sessions.sqlite3` database; no migration is needed.

This is a local, single-user application. Browser tabs share one capture and library. Run **one backend worker**. The default server binds only to loopback; this application is not configured for public hosting or multiple users. The Python backend observes traffic visible to the adapter of the computer running it, not the computer visiting a remotely hosted page.

## Using the dashboard

1. Select a network adapter and click **Start capture**. Starting a new capture clears the previous in-memory capture.
2. **Overview** shows full-session counters, the last 60 observed seconds, protocol distribution, and the top retained endpoints.
3. **Traffic explorer** combines protocol, IP/CIDR, port, and time-window filters. Use **Connections**, **Top talkers**, or **Packets**. Arrow buttons open a connection's packets or filter to an IP. Clear filters to return to the full retained window.
4. **Export CSV** downloads all matching rows for the current investigation tab, including rows beyond the current page.
5. **Save session** records the current capture. **Saved sessions** opens historical snapshots and offers explicit deletion. Stop capture separately if you do not want it to continue while reviewing history.
6. **Model analysis** runs an optional, one-time estimate when matching trained weights and `scaler.pkl` are present.

## Measurement and storage boundaries

- Session counters include all observed IP packets. Investigation and packet exports cover the latest **2,000 retained headers**.
- Connections group protocol and bidirectional endpoint pairs. Duration spans matching retained packets; it is not a measured TCP connection lifetime. Reused endpoint pairs are grouped together.
- IP and port filters match either endpoint. Time windows end at the latest retained packet. Packet timestamps and saved-session times are displayed in UTC.
- Top-talker sent/received bytes are relative to each IP. Adding endpoint totals counts each packet twice.
- Rates average up to five complete observed one-second intervals, including idle intervals. Throughput is visible traffic, not internet plan speed. Loss, congestion window, and timeouts are not measured.
- Saved snapshots include session totals, up to 2,000 headers, and up to 60 seconds of chart history. They do not contain packet payloads or a complete PCAP. Historical snapshots do not show current rates.
- The local SQLite library allows **50 sessions**, at most **5 MB** each, and never automatically deletes an older session. It is excluded from Git. Anyone with access to this local app instance can access that library.
- Abandoned capture stops after roughly 60 seconds without an active consumer. Closing the backend also stops capture.
- AI labels remain estimates derived from packet-size features. They do not establish congestion, application identity, packet loss, or malicious activity. The existing training methodology has not been changed by this frontend migration.

## Frontend development

Use two terminals in the repository root:

```powershell
# Terminal 1: backend
python -m uvicorn api:app --host 127.0.0.1 --port 8000

# Terminal 2: frontend with hot reload
npm --prefix frontend run dev
```

Open http://127.0.0.1:5173. Vite proxies `/api` and WebSocket traffic to the backend. Default local origins on ports 8000 and 5173 are accepted; unrelated browser origins are rejected. API documentation is available at http://127.0.0.1:8000/docs.

## Verification

```powershell
python -m unittest discover -s backend/tests -p "test_*.py" -v
npm --prefix frontend test
npm --prefix frontend run build
```

Browser checks require Playwright, Microsoft Edge, and the built app running on port 8000:

```powershell
python scripts/check_react_ui.py
# Optional: also exercise real adapter capture and save via the UI
python scripts/check_react_ui.py --live
```

The browser check uses the bundled PCAP as a clearly identified temporary saved session and deletes only its own test sessions afterwards. It checks the real API/WebSocket connection, filtering, connection drill-down, CSV download, input focus during updates, mobile layout, and deletion.

## Project structure

```text
├── backend/
│   ├── src/netsense/
│   │   ├── api.py            FastAPI routes, WebSocket streaming, and React hosting
│   │   ├── config.py         Centralized paths and runtime configuration
│   │   ├── services/
│   │   │   ├── capture.py    Thread-safe Scapy packet capture & rate measurement
│   │   │   └── sessions.py   Bounded SQLite persistence for saved session snapshots
│   │   └── ml/
│   │       ├── inference.py  PyTorch model inference and feature preprocessing
│   │       ├── model.py      PyTorch LSTM neural network architecture
│   │       └── train.py      LSTM training pipeline with evaluation metrics
│   ├── tests/
│   │   ├── fixtures/         Test packet captures (sample_capture.pcap)
│   │   ├── test_api.py       FastAPI route and WebSocket endpoint tests
│   │   ├── test_capture.py   Live packet capture and metric calculation tests
│   │   ├── test_inference.py ML inference and sequence preprocessing tests
│   │   └── test_sessions.py  SQLite session store persistence tests
│   └── pyproject.toml        Backend package definition and dependency metadata
├── frontend/
│   ├── src/
│   │   ├── App.tsx           Main dashboard, capture telemetry, and session drawer
│   │   ├── components/
│   │   │   ├── Investigation.tsx Traffic explorer, IP/port filtering, and CSV export
│   │   │   └── TrafficChart.tsx  Real-time SVG packet/throughput rate chart
│   │   ├── hooks/
│   │   │   └── useLiveCapture.ts WebSocket connection hook with auto-reconnect
│   │   ├── lib/
│   │   │   ├── api.ts        REST client and WebSocket stream manager
│   │   │   └── analysis.ts   Client-side flow grouping and top talker rankings
│   │   ├── styles/
│   │   │   └── dashboard.css Responsive dark-mode dashboard styling
│   │   └── types.ts          Shared TypeScript data interfaces
│   ├── package.json          Frontend dependencies and build scripts
│   └── vite.config.ts        Vite build configuration with local API proxy
├── data/
│   ├── samples/              Sample packet captures & CSV traffic data
│   ├── training/             Dataset for model training (output1.csv)
│   └── sessions.sqlite3      Local capture session database (git-ignored)
├── models/
│   └── tcp_udp_lstm_pytorch.pt Pre-trained PyTorch LSTM weights
├── docs/
│   └── screenshots/          Application UI screenshots (overview, live, explorer, mobile)
├── images/                   Project contributor profile pictures
├── scripts/
│   └── check_react_ui.py     End-to-end browser verification script
├── run.py                    Unified launcher for backend & React UI
└── requirements.txt          Python project dependencies (-e ./backend)
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
