#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: "2025-02-15 01:56:49 (ywatanabe)"
# File: /home/ywatanabe/proj/example-scitex-project/scripts/mnist/plot_digits.py

__file__ = "./scripts/mnist/plot_digits.py"

"""
Functionality:
    - Visualizes MNIST dataset samples
Input:
    - MNIST dataset
Output:
    - Sample image plots
Prerequisites:
    - scitex package
    - PyTorch
"""

"""Imports"""
import argparse
from typing import Optional

import matplotlib.pyplot as plt
import scitex
from torch.utils.data import DataLoader

"""Parameters"""

"""Functions & Classes"""


def plot_samples(loader: DataLoader, n_samples: int = 25) -> None:
    images, labels = next(iter(loader))
    fig, axes = scitex.plt.subplots(5, 5, figsize=(10, 10))

    for idx, ax in enumerate(axes.flat):
        if idx < n_samples:
            ax.imshow(images[idx].squeeze(), cmap="gray")
            ax.set_title(f"Label: {labels[idx]}")
            # ax.axis("off")

    plt.tight_layout()
    scitex.io.save(fig, CONFIG.PATH.MNIST.FIGURES + "mnist_samples.jpg", symlink_from_cwd=True)


def plot_label_examples(loader: DataLoader) -> None:
    images, labels = next(iter(loader))
    fig, axes = scitex.plt.subplots(2, 5, figsize=(15, 6))

    label_examples = {}
    for img, label in zip(images, labels):
        if label.item() not in label_examples and len(label_examples) < 10:
            label_examples[label.item()] = img

    for idx, (label, img) in enumerate(sorted(label_examples.items())):
        row, col = idx // 5, idx % 5
        axes[row, col].imshow(img.squeeze(), cmap="gray")
        axes[row, col].set_title(f"Digit: {label}")
        # axes[row, col].axis("off")

    plt.tight_layout()
    scitex.io.save(fig, CONFIG.PATH.MNIST.FIGURES + "mnist_digits.jpg", symlink_from_cwd=True)


def main(args: argparse.Namespace) -> Optional[int]:
    train_loader = scitex.io.load(CONFIG.PATH.MNIST.LOADER.TRAIN)
    plot_samples(train_loader)
    plot_label_examples(train_loader)
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Visualize MNIST samples")
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