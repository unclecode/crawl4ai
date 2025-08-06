<!-- ---
!-- Timestamp: 2025-06-04 05:02:02
!-- Author: ywatanabe
!-- File: /ssh:ywatanabe@sp:/home/ywatanabe/proj/.claude-worktree/gPAC/docs/slurm/README.md
!-- --- -->

# SLURM Utilities

Simple SLURM workflow for persistent GPU nodes.

## Quick Start

1. Request persistent node:
```bash
sbatch request.sh
```

2. Run commands on allocated node:
```bash
./run.sh python train.py
./run.sh script.py
./run.sh nvidia-smi
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