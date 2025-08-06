#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: "2025-02-15 01:06:57 (ywatanabe)"
# File: /home/ywatanabe/proj/example-scitex-project/scripts/mnist/plot_umap_space.py

__file__ = "./scripts/mnist/plot_umap_space.py"

"""
Functionality:
    - Creates UMAP visualization of MNIST dataset
Input:
    - MNIST dataset
Output:
    - UMAP visualization plots
Prerequisites:
    - scitex package
    - umap-learn
"""

"""Imports"""
import argparse
from typing import Optional

import matplotlib.pyplot as plt
import scitex
import numpy as np
import umap

"""Parameters"""


"""Functions & Classes"""


def create_umap_embedding(data: np.ndarray) -> np.ndarray:
    reducer = umap.UMAP(random_state=CONFIG.MNIST.UMAP_RANDOM_STATE, n_jobs=-1)
    embedding = reducer.fit_transform(data)
    return embedding


def plot_umap(embedding: np.ndarray, labels: np.ndarray) -> None:
    fig, ax = scitex.plt.subplots(figsize=(12, 8))
    scatter = ax.scatter(
        embedding[:, 0], embedding[:, 1], c=labels, cmap="tab10", alpha=0.5
    )

    plt.colorbar(scatter)
    ax.set_title("UMAP Projection of MNIST Digits")
    ax.set_xlabel("UMAP 1")
    ax.set_ylabel("UMAP 2")

    scitex.io.save(fig, CONFIG.PATH.MNIST.FIGURES + "umap.jpg", symlink_from_cwd=True)


def main(args: argparse.Namespace) -> Optional[int]:
    train_data = scitex.io.load(CONFIG.PATH.MNIST.FLATTENED.TRAIN)
    train_labels = scitex.io.load(CONFIG.PATH.MNIST.LABELS.TRAIN)
    embedding = create_umap_embedding(train_data)
    plot_umap(embedding, train_labels)
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create UMAP visualization of MNIST"
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