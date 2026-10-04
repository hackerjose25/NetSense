"""Train a matched NetSense model bundle from the local dataset."""
import argparse
from pathlib import Path
from netsense.config import MODELS_DIR, TRAINING_DATA


def main():
    parser = argparse.ArgumentParser(description="Train and evaluate a matched model/scaler bundle.")
    parser.add_argument("--data", type=Path, default=TRAINING_DATA)
    parser.add_argument("--output-dir", type=Path, default=MODELS_DIR / "packet-size-v1")
    parser.add_argument("--epochs", type=int, default=12)
    parser.add_argument("--max-samples", type=int, default=24000)
    args = parser.parse_args()
    if args.epochs < 1 or args.max_samples < 100:
        parser.error("Use at least 1 epoch and 100 samples.")
    from netsense.ml.training import train
    train(args.data, args.output_dir, args.epochs, args.max_samples)


if __name__ == "__main__":
    main()
