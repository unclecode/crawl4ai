#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: "2025-02-15 01:59:49 (ywatanabe)"
# File: /home/ywatanabe/proj/example-scitex-project/scripts/mnist/clf_svm_plot_conf_mat.py

__file__ = "./scripts/mnist/clf_svm_plot_conf_mat.py"

"""
Functionality:
- Plots confusion matrix from saved predictions and labels
Input:
- Predictions and labels from SVM classifier
Output:
- Confusion matrix plot
Prerequisites:
- scitex package
- seaborn
"""

"""Imports"""
import argparse
from typing import Optional
import scitex
import numpy as np
import seaborn as sns
from sklearn.metrics import confusion_matrix

"""Parameters"""

"""Functions & Classes"""


def plot_confusion_matrix(labels: np.ndarray, predictions: np.ndarray) -> None:
    cm = confusion_matrix(labels, predictions)
    fig, ax = scitex.plt.subplots(figsize=(10, 8))
    ax.imshow2d(cm)
    ax.set_xyt("Predicted", "True", "Confusion Matrix")
    # sns.heatmap(cm, annot=True, fmt="d", ax=ax)
    # ax.set_xlabel()
    # ax.set_ylabel("True")
    # ax.set_title("Confusion Matrix")
    scitex.io.save(
        fig,
        CONFIG.PATH.MNIST.FIGURES + "confusion_matrix.jpg",
        symlink_from_cwd=True,
    )


def main(args: argparse.Namespace) -> Optional[int]:
    predictions = scitex.io.load("./scripts/mnist/clf_svm_out/predictions.npy")
    labels = scitex.io.load("./scripts/mnist/clf_svm_out/labels.npy")
    plot_confusion_matrix(labels, predictions)
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plot confusion matrix")
    args = parser.parse_args()
    scitex.str.printc(args, c="yellow")
    return args


def run_main() -> None:
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