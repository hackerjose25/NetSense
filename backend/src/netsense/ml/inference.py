"""Shared model inference; independent of either frontend."""

from functools import lru_cache
import pandas as pd
import numpy as np
import torch

from netsense.config import MODELS_DIR
from netsense.ml.model import LSTMClassifier

FEATURES = ['packet_count', 'avg_size', 'size_variation', 'packet_rate', 'rate_change']
BUNDLE_NAME = "packet-size-v1"

# ─────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────
LABEL_NAMES = {0: "Low Traffic", 1: "Medium Traffic", 2: "High Traffic"}

@lru_cache(maxsize=4)
def load_model(model_path):
    model = LSTMClassifier(input_dim=5)
    model.load_state_dict(torch.load(model_path, map_location=torch.device('cpu'), weights_only=True))
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
    features = FEATURES
    data = df[features].values
    X = []
    for i in range(len(data) - timesteps + 1):
        X.append(data[i:i + timesteps])
    return np.asarray(X, dtype=np.float32).reshape(-1, timesteps, len(features)), features


@lru_cache(maxsize=4)
def load_scaler(path=None):
    import joblib
    path = path or MODELS_DIR / BUNDLE_NAME / "scaler.pkl"
    if not path.is_file():
        raise FileNotFoundError("Matching training scaler.pkl is missing; AI estimates are unavailable.")
    return joblib.load(path)

def predict(model, X_seq, scaler=None):
    scaler = scaler if scaler is not None else load_scaler()
    nsamples, ntimesteps, nfeatures = X_seq.shape
    
    X_scaled = scaler.transform(X_seq.reshape(-1, nfeatures)).reshape(nsamples, ntimesteps, nfeatures)
        
    tensor = torch.tensor(X_scaled, dtype=torch.float32)
    with torch.no_grad():
        outputs = model(tensor)
        preds = torch.argmax(outputs, dim=1).numpy()
        probs = torch.softmax(outputs, dim=1).numpy()
    return preds, probs
