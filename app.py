import streamlit as st
import pandas as pd
import numpy as np
import torch
import torch.nn as nn

st.set_page_config(
    page_title="NetSense | Live Network Intelligence",
    page_icon="N",
    layout="wide",
    initial_sidebar_state="collapsed",
)

class LSTMClassifier(nn.Module):
    def __init__(self, input_dim, hidden_dim=64, num_classes=3):
        super(LSTMClassifier, self).__init__()
        self.lstm1 = nn.LSTM(input_dim, hidden_dim, batch_first=True)
        self.dropout1 = nn.Dropout(0.3)
        self.lstm2 = nn.LSTM(hidden_dim, hidden_dim // 2, batch_first=True)
        self.dropout2 = nn.Dropout(0.2)
        self.fc1 = nn.Linear(hidden_dim // 2, 32)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(32, num_classes)

    def forward(self, x):
        out, _ = self.lstm1(x)
        out = self.dropout1(out)
        out, _ = self.lstm2(out)
        out = self.dropout2(out[:, -1, :])
        out = self.fc1(out)
        out = self.relu(out)
        out = self.fc2(out)
        return out


# ─────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────
LABEL_NAMES = {0: "Low Traffic", 1: "Medium Traffic", 2: "High Traffic"}
LABEL_COLORS = {0: "#60a5fa", 1: "#34d399", 2: "#f87171"}

@st.cache_resource
def load_model(model_path):
    model = LSTMClassifier(input_dim=5)
    model.load_state_dict(torch.load(model_path, map_location=torch.device('cpu')))
    model.eval()
    return model


def preprocess(df):
    df = df.copy()
    df['Protocol'] = df['Protocol'].fillna(0)
    df['Length'] = df['Length'].fillna(0)
    df['Timestamp'] = pd.to_numeric(df['Timestamp'], errors='coerce')
    df = df.dropna(subset=['Timestamp'])

    df['packet_count'] = 1
    df['avg_size'] = df['Length']
    df['size_variation'] = df['Length'].diff().fillna(0)
    df['packet_rate'] = df['Length'].rolling(2).sum().fillna(0)
    df['rate_change'] = df['packet_rate'].diff().fillna(0)
    return df


def make_sequences(df, timesteps=10):
    features = ['packet_count', 'avg_size', 'size_variation', 'packet_rate', 'rate_change']
    data = df[features].values
    X = []
    for i in range(len(data) - timesteps):
        X.append(data[i:i + timesteps])
    return np.array(X), features


@st.cache_resource
def load_scaler():
    import joblib
    import os
    if not os.path.exists("scaler.pkl"):
        raise FileNotFoundError("Matching training scaler.pkl is missing; AI estimates are unavailable.")
    return joblib.load("scaler.pkl")

def predict(model, X_seq):
    scaler = load_scaler()
    nsamples, ntimesteps, nfeatures = X_seq.shape
    
    X_scaled = scaler.transform(X_seq.reshape(-1, nfeatures)).reshape(nsamples, ntimesteps, nfeatures)
        
    tensor = torch.tensor(X_scaled, dtype=torch.float32)
    with torch.no_grad():
        outputs = model(tensor)
        preds = torch.argmax(outputs, dim=1).numpy()
        probs = torch.softmax(outputs, dim=1).numpy()
    return preds, probs


def parse_pcap(file):
    from scapy.all import rdpcap
    import tempfile
    import os
    
    if hasattr(file, 'getbuffer'):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pcap") as tmp:
            tmp.write(file.getbuffer())
            tmp_path = tmp.name
        try:
            packets = rdpcap(tmp_path)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
    else:
        packets = rdpcap(file)

    data = []

    for pkt in packets:
        try:
            if pkt.haslayer("IP"):
                length = len(pkt)

                if pkt.haslayer("TCP"):
                    proto = "TCP"
                elif pkt.haslayer("UDP"):
                    proto = "UDP"
                else:
                    proto = "OTHER"

                data.append({
                    "Timestamp": pkt.time,
                    "Length": length,
                    "Protocol": proto
                })
        except:
            continue

    return pd.DataFrame(data)


from ui import render_shell, render_footer
from live_dashboard import render_dashboard

render_shell()
render_dashboard(load_model, predict, preprocess, make_sequences)
render_footer()
