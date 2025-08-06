<!-- ---
!-- Timestamp: 2025-06-14 06:50:01
!-- Author: ywatanabe
!-- File: /home/ywatanabe/.dotfiles/.claude/to_claude/guidelines/programming_common/IMPORTANT-slurm.md
!-- --- -->

# SLURM Utilities

Simple SLURM workflow for persistent GPU nodes.

## `module load`
In spartan HPC, module load may be required.

``` bash
module load \
    GCCcore/11.3.0 \
    Python/3.10.4 \
    Tkinter/3.10.4 \
    OpenSSL/1.1 \
    Apptainer/1.3.3 \
    bzip2 \
    slurm/latest \
    GLib/2.72.1 \
    GTK3/3.24.33 \
    Gdk-Pixbuf/2.42.8 \
    nodejs/18.17.1
    # texlive/20230313
```

## Quick Start

1. Request persistent node:
```bash
sbatch request.sh
```

2. Run commands on allocated node:
```bash
srun.sh python train.py
srun.sh script.py
srun.sh nvidia-smi
```

3. Login to node directly:
```bash
./login.sh
```

## Files

- `request.sh` - Requests 4-GPU node for 7 days, saves node info to slurm-persistent.txt
- `run.sh` - Runs commands on allocated node via srun
- `login.sh` - SSH login to allocated node

## Python Command Processing

- `python script.py` → `python -u script.py`  
- `script.py` → `python -u script.py`
- `python -u script.py` → unchanged

## GPU Control

- Default: Uses all 4 GPUs (0,1,2,3)
- Custom: `CUDA_VISIBLE_DEVICES=0,1 ./run.sh python script.py`

## Resource Allocation

- 4 GPUs (A100)
- 32 CPU cores (8 per GPU)
- 256GB RAM
- 7 days runtime with auto-resubmission

<!-- EOF -->