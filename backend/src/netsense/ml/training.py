"""Reproducible training of a matched packet-size model/scaler bundle."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import torch
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.preprocessing import MinMaxScaler
from torch.utils.data import DataLoader, TensorDataset

from netsense.ml.inference import FEATURES, LABEL_NAMES, make_sequences, preprocess
from netsense.ml.model import LSTMClassifier


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def train(dataset, output_dir, epochs=12, max_samples=24000):
    torch.manual_seed(42)
    torch.set_num_threads(min(4, torch.get_num_threads()))
    rng = np.random.default_rng(42)
    raw = pd.read_csv(dataset)
    raw['Timestamp'] = pd.to_numeric(raw['Timestamp'], errors='coerce')
    raw['Length'] = pd.to_numeric(raw['Length'], errors='coerce')
    raw = raw.dropna(subset=['Timestamp', 'Length']).sort_values('Timestamp', kind='stable')
    if len(raw) < 100:
        raise ValueError('Training needs at least 100 valid packet records.')
    # Split packet rows first, so overlapping sequences never cross partitions.
    a, b = int(len(raw) * .7), int(len(raw) * .85)
    partitions = [preprocess(part.copy()) for part in (raw.iloc[:a], raw.iloc[a:b], raw.iloc[b:])]
    thresholds = partitions[0]['packet_rate'].quantile([.33, .66]).to_numpy()
    scaler = MinMaxScaler().fit(partitions[0][FEATURES].to_numpy())
    sets = []
    for index, part in enumerate(partitions):
        sequences, _ = make_sequences(part)
        labels = np.searchsorted(thresholds, part['packet_rate'].to_numpy()[9:], side='left')
        limit = max_samples if index == 0 else min(6000, max_samples)
        selected = np.sort(rng.choice(len(sequences), min(limit, len(sequences)), replace=False))
        sequences = sequences[selected]
        scaled = scaler.transform(sequences.reshape(-1, 5)).reshape(-1, 10, 5).astype(np.float32)
        sets.append((torch.from_numpy(scaled), torch.from_numpy(labels[selected]).long()))
    x_train, y_train = sets[0]
    counts = np.bincount(y_train.numpy(), minlength=3)
    if np.any(counts == 0):
        raise ValueError('The training dataset must contain all three packet-size classes.')
    weights = torch.tensor(counts.sum() / (3 * counts), dtype=torch.float32)
    model = LSTMClassifier(5)
    optimizer = torch.optim.Adam(model.parameters(), lr=.002)
    criterion = torch.nn.CrossEntropyLoss(weight=weights)
    loader = DataLoader(TensorDataset(x_train, y_train), batch_size=256, shuffle=True)
    best_score, best_weights, patience = -1.0, None, 0

    def evaluate(inputs):
        model.eval()
        with torch.inference_mode():
            return np.concatenate([model(batch).argmax(1).numpy() for batch in inputs.split(512)])

    for epoch in range(epochs):
        model.train()
        loss_sum = 0.0
        for inputs, targets in loader:
            optimizer.zero_grad()
            loss = criterion(model(inputs), targets)
            loss.backward()
            optimizer.step()
            loss_sum += loss.item() * len(inputs)
        validation = evaluate(sets[1][0])
        score = f1_score(sets[1][1].numpy(), validation, labels=[0, 1, 2], average='macro', zero_division=0)
        print(f'Epoch {epoch + 1}/{epochs}: loss={loss_sum / len(x_train):.4f}, validation macro-F1={score:.4f}', flush=True)
        if score > best_score:
            best_score = score
            best_weights = {key: value.detach().clone() for key, value in model.state_dict().items()}
            patience = 0
        else:
            patience += 1
            if patience >= 3:
                break
    model.load_state_dict(best_weights)
    actual = sets[2][1].numpy()
    predicted = evaluate(sets[2][0])
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    weights_path, scaler_path = output_dir / 'tcp_udp_lstm_pytorch.pt', output_dir / 'scaler.pkl'
    torch.save(model.state_dict(), weights_path)
    joblib.dump(scaler, scaler_path)
    metadata = {
        'version': 'packet-size-v1', 'trained_at': datetime.now(timezone.utc).isoformat(),
        'features': FEATURES, 'timesteps': 10, 'labels': list(LABEL_NAMES.values()),
        'label_definition': 'Low/Medium/High classes derived from training-only quantiles of the sum of two consecutive packet lengths. Not a congestion or threat label.',
        'thresholds': thresholds.tolist(), 'dataset_sha256': digest(dataset),
        'weights_sha256': digest(weights_path), 'scaler_sha256': digest(scaler_path),
        'dataset_rows': len(raw), 'training_windows': len(x_train),
        'validation_windows': len(sets[1][0]), 'test_windows': len(actual),
        'split': 'Chronological 70/15/15, disjoint packet rows; scaler and label thresholds fitted on training only.',
        'accuracy': float(accuracy_score(actual, predicted)),
        'macro_f1': float(f1_score(actual, predicted, labels=[0, 1, 2], average='macro', zero_division=0)),
        'classification_report': classification_report(actual, predicted, labels=[0, 1, 2], target_names=list(LABEL_NAMES.values()), output_dict=True, zero_division=0),
        'limitation': 'Evaluation uses derived labels from one capture dataset. Results have not been validated across independent networks.',
    }
    (output_dir / 'metadata.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    print(f'Saved matched bundle. Test accuracy={metadata["accuracy"]:.4f}, macro-F1={metadata["macro_f1"]:.4f}', flush=True)
    return metadata
