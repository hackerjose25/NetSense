import os
import unittest
import torch
import numpy as np
import pandas as pd

from netsense.ml.inference import (
    LSTMClassifier,
    load_model,
    preprocess,
    make_sequences,
    predict,
    LABEL_NAMES,
)

from netsense.config import MODELS_DIR

class TestInference(unittest.TestCase):

    def setUp(self):
        self.model_path = MODELS_DIR / "packet-size-v1" / "tcp_udp_lstm_pytorch.pt"

    def test_01_model_loading(self):
        """Test loading PyTorch model weights."""
        self.assertTrue(os.path.exists(self.model_path), "Model file not found")
        model = load_model(self.model_path)
        self.assertIsInstance(model, LSTMClassifier)
        self.assertFalse(model.training, "Model should be in eval mode")

    def test_02_preprocessing(self):
        """Test dataframe feature extraction and cleaning."""
        raw_df = pd.DataFrame({
            "Timestamp": [1000.0, 1001.0, 1002.0, 1003.0, 1004.0, 1005.0, 1006.0, 1007.0, 1008.0, 1009.0, 1010.0],
            "Length": [64, 128, 512, 1024, 1500, 64, 128, 256, 512, 1024, 1500],
            "Protocol": ["TCP", "TCP", "UDP", "TCP", "TCP", "UDP", "TCP", "TCP", "UDP", "TCP", "TCP"]
        })
        proc_df = preprocess(raw_df)
        expected_cols = ["packet_count", "avg_size", "size_variation", "packet_rate", "rate_change"]
        for col in expected_cols:
            self.assertIn(col, proc_df.columns, f"Missing feature {col}")
        self.assertEqual(len(proc_df), len(raw_df))

    def test_03_sequence_generation(self):
        """Test creating 10-timestep rolling sequences."""
        raw_df = pd.DataFrame({
            "Timestamp": list(range(25)),
            "Length": [64] * 25,
            "Protocol": ["TCP"] * 25
        })
        proc_df = preprocess(raw_df)
        X_seq, features = make_sequences(proc_df, timesteps=10)
        self.assertEqual(X_seq.shape, (16, 10, 5))
        self.assertEqual(len(features), 5)

    def test_04_model_inference(self):
        """Test end-to-end prediction and probability distribution."""
        model = load_model(self.model_path)
        if not (MODELS_DIR / "packet-size-v1" / "scaler.pkl").is_file():
            with self.assertRaises(FileNotFoundError):
                predict(model, np.ones((5, 10, 5)))
            return
        # Test inputs only: never used as dashboard data.
        # Create synthetic sequence of shape (5, 10, 5)
        synthetic_seq = np.random.uniform(0, 1500, (5, 10, 5))
        preds, probs = predict(model, synthetic_seq)
        
        self.assertEqual(len(preds), 5)
        self.assertEqual(probs.shape, (5, 3))
        # Validate that predicted labels are 0, 1, or 2
        for p in preds:
            self.assertIn(p, [0, 1, 2])
            self.assertIn(p, LABEL_NAMES)
        # Validate probabilities sum to ~1.0
        prob_sums = np.sum(probs, axis=1)
        np.testing.assert_allclose(prob_sums, np.ones(5), atol=1e-4)


if __name__ == "__main__":
    unittest.main()
