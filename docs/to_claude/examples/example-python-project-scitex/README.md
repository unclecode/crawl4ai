<!-- ---
!-- Timestamp: 2025-02-15 02:05:17
!-- Author: ywatanabe
!-- File: /home/ywatanabe/proj/example-scitex-project/README.md
!-- --- -->

# example-scitex-project

This repository demonstrates a project format using [scitex](https://github.com/ywatanabe1989/scitex), a Python utility package that standardizes analyses and applications in scientific projects.

## SCITEX Framework
scitex project features predefined directory structure - [`./config`](./config), [`./data`](./data), [`./scripts`](./scripts)

Config:
    - Centralized YAML configuration files (e.g., [`./config/PATH.yaml`](./config/PATH.yaml))
Data:
    - Centralized data files (e.g., [`./data/mnist`](./data/mnist))

Scripts:
    - Script files
    - Directly linked outputs (artifacts and logs)
    - Symlink to the ./data directory

For example, 
- [`./scripts/mnist/plot_images.py`](./scripts/mnist/plot_images.py) produces [`./scripts/mnist/plot_images_out/`](./scripts/mnist/plot_images_out/).
- [`./scripts/mnist/plot_images_out/data/figures/mnist_digits.jpg`](./scripts/mnist/plot_images_out/data/figures/mnist_digits.jpg) is symlinked to [`./data/figures/mnist_digits.jpg`](./data/figures/mnist_digits.jpg)
- [`./scripts/mnist/plot_images_out/RUNNING`](./scripts/mnist/plot_images_out/RUNNING): Logs for running scripts
- [`./scripts/mnist/plot_images_out/FINISHED_SUCCESS`](./scripts/mnist/plot_images_out/FINISHED_SUCCESS): Logs for successfully completed scripts
- [`./scripts/mnist/plot_images_out/FINISHED_FAILED`](./scripts/mnist/plot_images_out/FINISHED_FAILED): Logs for failed scripts

## Directory Structure

``` plaintext
.
├── config
│   ├── MNIST.yaml
│   └── PATH.yaml
├── data
│   └── mnist
│       ├── figures
│       │   ├── confusion_matrix.jpg -> ../../../scripts/mnist/plot_conf_mat_out/data/mnist/figures/confusion_matrix.jpg
│       │   ├── mnist_digits.jpg -> ../../../scripts/mnist/plot_digits_out/data/mnist/figures/mnist_digits.jpg
│       │   ├── mnist_samples.jpg -> ../../../scripts/mnist/plot_digits_out/data/mnist/figures/mnist_samples.jpg
│       │   └── umap.jpg -> ../../../scripts/mnist/plot_umap_space_out/data/mnist/figures/umap.jpg
│       ├── raw
│       │   └── MNIST
│       │       └── raw
│       │           ├── t10k-images-idx3-ubyte
│       │           ├── t10k-images-idx3-ubyte.gz
│       │           ├── t10k-labels-idx1-ubyte
│       │           ├── t10k-labels-idx1-ubyte.gz
│       │           ├── train-images-idx3-ubyte
│       │           ├── train-images-idx3-ubyte.gz
│       │           ├── train-labels-idx1-ubyte
│       │           └── train-labels-idx1-ubyte.gz
│       ├── test_flattened.npy -> ../../scripts/mnist/download_out/data/mnist/test_flattened.npy
│       ├── test_labels.npy -> ../../scripts/mnist/download_out/data/mnist/test_labels.npy
│       ├── test_loader.pkl -> ../../scripts/mnist/download_out/data/mnist/test_loader.pkl
│       ├── train_flattened.npy -> ../../scripts/mnist/download_out/data/mnist/train_flattened.npy
│       ├── train_labels.npy -> ../../scripts/mnist/download_out/data/mnist/train_labels.npy
│       └── train_loader.pkl -> ../../scripts/mnist/download_out/data/mnist/train_loader.pkl
├── README.md
├── requirements.txt
└── scripts
    └── mnist
        ├── clf_svm_out
        │   ├── classification_report.csv
        │   ├── data
        │   │   └── mnist
        │   │       └── models
        │   │           └── mnist_svm.pkl
        │   ├── FINISHED_SUCCESS
        │   │   ├── 2025Y-02M-15D-01h10m16s_hOkM
        │   │   │   └── logs
        │   │   │       ├── stderr.log
        │   │   │       └── stdout.log
        │   │   └── 2025Y-02M-15D-01h41m27s_8im5
        │   │       └── logs
        │   │           ├── stderr.log
        │   │           └── stdout.log
        │   ├── labels.npy
        │   ├── predictions.npy
        │   └── RUNNING
        ├── clf_svm.py
        ├── download_out
        │   ├── data
        │   │   └── mnist
        │   │       ├── test_flattened.npy
        │   │       ├── test_labels.npy
        │   │       ├── test_loader.pkl
        │   │       ├── train_flattened.npy
        │   │       ├── train_labels.npy
        │   │       └── train_loader.pkl
        │   ├── FINISHED_SUCCESS
        │   │   └── 2025Y-02M-15D-01h07m18s_qSoK
        │   │       └── logs
        │   │           ├── stderr.log
        │   │           └── stdout.log
        │   └── RUNNING
        ├── download.py
        ├── main.sh
        ├── main.sh.log
        ├── plot_conf_mat_out
        │   ├── data
        │   │   └── mnist
        │   │       └── figures
        │   │           ├── confusion_matrix.csv
        │   │           └── confusion_matrix.jpg
        │   ├── FINISHED_SUCCESS
        │   │   ├── 2025Y-02M-15D-01h57m44s_V8Lm
        │   │   │   └── logs
        │   │   │       ├── stderr.log
        │   │   │       └── stdout.log
        │   │   └── 2025Y-02M-15D-02h00m11s_hQQp
        │   │       └── logs
        │   │           ├── stderr.log
        │   │           └── stdout.log
        │   └── RUNNING
        ├── plot_conf_mat.py
        ├── plot_digits_out
        │   ├── data
        │   │   └── mnist
        │   │       └── figures
        │   │           ├── mnist_digits.csv
        │   │           ├── mnist_digits.jpg
        │   │           ├── mnist_samples.csv
        │   │           └── mnist_samples.jpg
        │   ├── FINISHED_SUCCESS
        │   │   └── 2025Y-02M-15D-01h08m12s_bmQm
        │   │       └── logs
        │   │           ├── stderr.log
        │   │           └── stdout.log
        │   └── RUNNING
        ├── plot_digits.py
        ├── plot_umap_space_out
        │   ├── data
        │   │   └── mnist
        │   │       └── figures
        │   │           ├── umap.csv
        │   │           └── umap.jpg
        │   ├── FINISHED_SUCCESS
        │   │   └── 2025Y-02M-15D-01h08m36s_FntU
        │   │       └── logs
        │   │           ├── stderr.log
        │   │           └── stdout.log
        │   └── RUNNING
        └── plot_umap_space.py

53 directories, 61 files
```

## Contact
Yusuke Watanabe (ywatanabe@alumni.u-tokyo.ac.jp)

<!-- EOF -->