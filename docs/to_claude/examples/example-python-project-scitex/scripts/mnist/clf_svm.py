#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: "2025-02-15 01:20:16 (ywatanabe)"
# File: /home/ywatanabe/proj/example-scitex-project/scripts/mnist/clf_svm.py

__file__ = "./scripts/mnist/clf_svm.py"

"""
Functionality:
    - Trains and evaluates SVM classifier on MNIST dataset
Input:
    - MNIST dataset
Output:
    - Trained SVM model
    - Classification metrics
Prerequisites:
    - scitex package
    - scikit-learn
"""

"""Imports"""
import argparse
from typing import Dict, Optional

import scitex
import numpy as np
from sklearn.metrics import classification_report
from sklearn.svm import SVC

"""Parameters"""

"""Functions & Classes"""


def train_svm(features: np.ndarray, labels: np.ndarray) -> SVC:
    model = SVC(kernel="rbf", random_state=CONFIG.MNIST.RANDOM_STATE)
    model.fit(features, labels)
    return model


def evaluate(
    model: SVC,
    features: np.ndarray,
    labels: np.ndarray,
) -> Dict[str, float]:
    predictions = model.predict(features)
    report = classification_report(labels, predictions, output_dict=True)

    scitex.io.save(report, "./classification_report.csv")
    scitex.io.save(predictions, "./predictions.npy")
    scitex.io.save(labels, "./labels.npy")

    return {
        "accuracy": report["accuracy"],
        "macro_f1": report["macro avg"]["f1-score"],
    }


def main(args: argparse.Namespace) -> Optional[int]:
    train_data = scitex.io.load(CONFIG.PATH.MNIST.FLATTENED.TRAIN)
    train_labels = scitex.io.load(CONFIG.PATH.MNIST.LABELS.TRAIN)
    test_data = scitex.io.load(CONFIG.PATH.MNIST.FLATTENED.TEST)
    test_labels = scitex.io.load(CONFIG.PATH.MNIST.LABELS.TEST)

    model = train_svm(train_data, train_labels)
    metrics = evaluate(model, test_data, test_labels)

    scitex.str.printc(
        f"Test Accuracy: {metrics['accuracy']:.4f}, Macro F1: {metrics['macro_f1']:.4f}",
        c="green",
    )

    scitex.io.save(model, eval(CONFIG.PATH.MNIST.MODEL_SVM))
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train SVM classifier on MNIST"
    )
    args = parser.parse_args()
    scitex.str.printc(args, c="yellow")
    return args


def run_main() -> None:
    """Initialize scitex framework, run main function, and cleanup.

    scitex framework manages:
      - Parameters defined in yaml files under `./config dir`
      - Setting saving directory (/path/to/file.py -> /path/to/file.py_out/)
      - Symlink for `./data` directory
      - Logging timestamp, stdout, stderr, and parameters
      - Matplotlib configurations (also, `scitex.plt` will track plotting data)
      - Random seeds

    THUS, DO NOT MODIFY THIS RUN_MAIN FUNCTION
    """
    import sys

    import matplotlib.pyplot as plt

    global CONFIG, CC, sys, plt
    args = parse_args()
    CONFIG, sys.stdout, sys.stderr, plt, CC = scitex.gen.start(
        sys,
        plt,
        args=args,
        file=__file__,
        agg=True,
    )

    exit_status = main(args)

    scitex.gen.close(
        CONFIG,
        exit_status=exit_status,
    )


if __name__ == "__main__":
    run_main()

# EOF