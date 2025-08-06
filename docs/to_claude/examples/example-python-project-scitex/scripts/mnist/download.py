#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: "2025-02-15 01:06:56 (ywatanabe)"
# File: /home/ywatanabe/proj/example-scitex-project/scripts/mnist/download.py

__file__ = "./scripts/mnist/download.py"

"""
Functionality:
    - Downloads MNIST dataset and saves preprocessed versions
Input:
    - None
Output:
    - Raw MNIST data
    - Preprocessed data for different models
Prerequisites:
    - scitex package
    - PyTorch
"""

"""Imports"""
import argparse
from typing import Dict, Optional

import scitex
import numpy as np
import torch
from torch.utils.data import DataLoader
from torchvision import datasets, transforms

"""Parameters"""

"""Functions & Classes"""


def download_mnist() -> Dict[str, torch.utils.data.Dataset]:
    transform = transforms.Compose(
        [
            transforms.ToTensor(),
            transforms.Normalize(
                eval(CONFIG.MNIST.NORMALIZE.MEAN),
                eval(CONFIG.MNIST.NORMALIZE.STD),
            ),
        ]
    )
    train_dataset = datasets.MNIST(
        CONFIG.PATH.MNIST.RAW, train=True, download=True, transform=transform
    )
    test_dataset = datasets.MNIST(
        CONFIG.PATH.MNIST.RAW, train=False, transform=transform
    )
    return {"train": train_dataset, "test": test_dataset}


def create_loaders(
    datasets: Dict[str, torch.utils.data.Dataset]
) -> Dict[str, DataLoader]:
    train_loader = DataLoader(
        datasets["train"],
        batch_size=CONFIG.MNIST.BATCH_SIZE.TRAIN,
        shuffle=True,
    )
    test_loader = DataLoader(
        datasets["test"], batch_size=CONFIG.MNIST.BATCH_SIZE.TEST
    )

    return {"train": train_loader, "test": test_loader}


def prepare_flattened_data(
    datasets: Dict[str, torch.utils.data.Dataset]
) -> Dict[str, np.ndarray]:
    flattened_data = {}
    labels = {}

    for split, dataset in datasets.items():
        data = dataset.data.numpy()
        flattened_data[split] = data.reshape(len(data), -1) / 255.0
        labels[split] = dataset.targets.numpy()

    return {"data": flattened_data, "labels": labels}


def main(args: argparse.Namespace) -> Optional[int]:
    datasets = download_mnist()
    loaders = create_loaders(datasets)
    flat_data = prepare_flattened_data(datasets)

    scitex.io.save(
        loaders["train"], CONFIG.PATH.MNIST.LOADER.TRAIN, symlink_from_cwd=True
    )
    scitex.io.save(
        loaders["test"], CONFIG.PATH.MNIST.LOADER.TEST, symlink_from_cwd=True
    )
    scitex.io.save(
        flat_data["data"]["train"],
        CONFIG.PATH.MNIST.FLATTENED.TRAIN,
        symlink_from_cwd=True,
    )
    scitex.io.save(
        flat_data["data"]["test"],
        CONFIG.PATH.MNIST.FLATTENED.TEST,
        symlink_from_cwd=True,
    )
    scitex.io.save(
        flat_data["labels"]["train"],
        CONFIG.PATH.MNIST.LABELS.TRAIN,
        symlink_from_cwd=True,
    )
    scitex.io.save(
        flat_data["labels"]["test"],
        CONFIG.PATH.MNIST.LABELS.TEST,
        symlink_from_cwd=True,
    )
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download and preprocess MNIST dataset"
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