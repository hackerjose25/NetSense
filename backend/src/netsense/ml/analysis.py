"""Artifact readiness checks and bounded, capture-wide model analysis."""

from datetime import datetime, timezone
from functools import lru_cache
import hashlib
import json
from pathlib import Path


BUNDLE_NAME = 'packet-size-v1'


@lru_cache(maxsize=4)
def verified_metadata(folder, signature):
    folder = Path(folder)
    metadata = json.loads((folder / 'metadata.json').read_text(encoding='utf-8'))
    if metadata['version'] != BUNDLE_NAME or metadata['timesteps'] != 10:
        raise ValueError('Unsupported model bundle version.')
    for name, key in [('tcp_udp_lstm_pytorch.pt', 'weights_sha256'), ('scaler.pkl', 'scaler_sha256')]:
        if hashlib.sha256((folder / name).read_bytes()).hexdigest() != metadata[key]:
            raise ValueError('Model weights and scaler do not match the saved training manifest.')
    return metadata


def model_status(models_dir):
    folder = Path(models_dir) / BUNDLE_NAME
    files = [folder / name for name in ['tcp_udp_lstm_pytorch.pt', 'scaler.pkl', 'metadata.json']]
    missing = [path.name for path in files if not path.is_file()]
    if missing:
        return {'available': False, 'detail': 'Model setup is incomplete: missing ' + ', '.join(missing),
                'setup_command': 'python -m netsense.ml.train', 'metadata': None}
    try:
        signature = tuple((p.stat().st_mtime_ns, p.stat().st_size) for p in files)
        metadata = verified_metadata(str(folder), signature)
        return {'available': True, 'detail': 'Matched model and scaler ready. Analyze live traffic or a saved capture.',
                'metadata': metadata, 'setup_command': 'python -m netsense.ml.train'}
    except (ValueError, KeyError, OSError) as exc:
        return {'available': False, 'detail': str(exc), 'metadata': None,
                'setup_command': 'python -m netsense.ml.train'}


def analyze(snapshot, models_dir):
    import numpy as np
    import pandas as pd
    from netsense.ml.inference import LABEL_NAMES, load_model, load_scaler, make_sequences, predict, preprocess

    status = model_status(models_dir)
    if not status['available']:
        raise RuntimeError(status['detail'])
    packets = snapshot['packets']
    if len(packets) < 10:
        raise ValueError('Capture at least 10 IP packets or open a saved session with 10 packets.')
    frame = preprocess(pd.DataFrame(packets).sort_values('Timestamp', kind='stable'))
    sequences, _ = make_sequences(frame)
    # At most 100 evenly spaced windows; keep requests responsive for full buffers.
    indices = np.unique(np.linspace(0, len(sequences) - 1, min(100, len(sequences))).astype(int))
    folder = Path(models_dir) / BUNDLE_NAME
    # Cache keys include file times, allowing a retrained bundle to be loaded.
    model, scaler = load_bundle(str(folder), tuple((p.stat().st_mtime_ns, p.stat().st_size) for p in [folder / 'tcp_udp_lstm_pytorch.pt', folder / 'scaler.pkl']))
    predictions, probabilities = predict(model, sequences[indices], scaler)
    average = probabilities.mean(axis=0)
    counts = np.bincount(predictions, minlength=3)
    windows = [{
        'start': float(frame.iloc[int(index)]['Timestamp']),
        'end': float(frame.iloc[int(index) + 9]['Timestamp']),
        'label': LABEL_NAMES[int(predictions[i])],
        'probability': float(probabilities[i].max()),
    } for i, index in enumerate(indices)]
    elapsed = float(frame['Timestamp'].max() - frame['Timestamp'].min())
    total_bytes = int(frame['Length'].sum())
    return {
        'label': LABEL_NAMES[int(counts.argmax())],
        'probabilities': {LABEL_NAMES[i]: float(value) for i, value in enumerate(average)},
        'distribution': {LABEL_NAMES[i]: int(value) for i, value in enumerate(counts)},
        'packet_count': snapshot['packet_count'], 'retained_packets': len(frame),
        'windows_analyzed': len(indices), 'total_windows': len(sequences), 'windows': windows,
        'model_version': status['metadata']['version'], 'analyzed_at': datetime.now(timezone.utc).isoformat(),
        'source': snapshot.get('session_name', 'Current capture'),
        'observed': {'bytes': total_bytes, 'duration_seconds': elapsed,
                     'packets_per_second': len(frame) / elapsed if elapsed > 0 else None},
        'warning': 'These classes describe packet-size patterns relative to the training dataset. Model probabilities are uncalibrated. They do not measure congestion, packet loss, or attacks.',
    }


@lru_cache(maxsize=2)
def load_bundle(folder, signature):
    import joblib
    import torch
    from netsense.ml.inference import load_model
    torch.set_num_threads(min(4, torch.get_num_threads()))
    path = Path(folder)
    # Bypass the older path-only cache when files change.
    return load_model.__wrapped__(str(path / 'tcp_udp_lstm_pytorch.pt')), joblib.load(path / 'scaler.pkl')
