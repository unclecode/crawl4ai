# Workflow Quick Reference

## Quick Commands

### Standard Release
```bash
# 1. Update version
vim crawl4ai/__version__.py  # Set to "1.2.3"

# 2. Commit and tag
git add crawl4ai/__version__.py
git commit -m "chore: bump version to 1.2.3"
git tag v1.2.3
git push origin main
git push origin v1.2.3

# 3. Monitor
# - PyPI: ~2-3 minutes
# - Docker: ~1-15 minutes
```

### Docker Rebuild Only
```bash
git tag docker-rebuild-v1.2.3
git push origin docker-rebuild-v1.2.3
```

### Delete Tag (Undo Release)
```bash
# Local
git tag -d v1.2.3

# Remote
git push --delete origin v1.2.3

# GitHub Release
gh release delete v1.2.3
```

---

## Workflow Triggers

### release.yml
| Event | Pattern | Example |
|-------|---------|---------|
| Tag push | `v*` | `v1.2.3` |
| Excludes | `test-v*` | `test-v1.2.3` |

### docker-release.yml
| Event | Pattern | Example |
|-------|---------|---------|
| Release published | `release.published` | Automatic |
| Tag push | `docker-rebuild-v*` | `docker-rebuild-v1.2.3` |

---

## Environment Variables

### release.yml
| Variable | Source | Example |
|----------|--------|---------|
| `VERSION` | Git tag | `1.2.3` |
| `TWINE_USERNAME` | Static | `__token__` |
| `TWINE_PASSWORD` | Secret | `pypi-Ag...` |
| `GITHUB_TOKEN` | Auto | `ghp_...` |

### docker-release.yml
| Variable | Source | Example |
|----------|--------|---------|
| `VERSION` | Release/Tag | `1.2.3` |
| `MAJOR` | Computed | `1` |
| `MINOR` | Computed | `1.2` |
| `DOCKER_USERNAME` | Secret | `unclecode` |
| `DOCKER_TOKEN` | Secret | `dckr_pat_...` |

---

## Docker Tags Generated

| Version | Tags Created |
|---------|-------------|
| v1.0.0 | `1.0.0`, `1.0`, `1`, `latest` |
| v1.1.0 | `1.1.0`, `1.1`, `1`, `latest` |
| v1.2.3 | `1.2.3`, `1.2`, `1`, `latest` |
| v2.0.0 | `2.0.0`, `2.0`, `2`, `latest` |

---

## Workflow Outputs

### release.yml
| Output | Location | Time |
|--------|----------|------|
| PyPI Package | https://pypi.org/project/crawl4ai/ | ~2-3 min |
| GitHub Release | Repository → Releases | ~2-3 min |
| Workflow Summary | Actions → Run → Summary | Immediate |

### docker-release.yml
| Output | Location | Time |
|--------|----------|------|
| Docker Images | https://hub.docker.com/r/unclecode/crawl4ai | ~1-15 min |
| Workflow Summary | Actions → Run → Summary | Immediate |

---

## Common Issues

| Issue | Solution |
|-------|----------|
| Version mismatch | Update `crawl4ai/__version__.py` to match tag |
| PyPI 403 Forbidden | Check `PYPI_TOKEN` secret |
| PyPI 400 File exists | Version already published, increment version |
| Docker auth failed | Regenerate `DOCKER_TOKEN` |
| Docker build timeout | Check Dockerfile, review build logs |
| Cache not working | First build on branch always cold |

---

## Secrets Checklist

- [ ] `PYPI_TOKEN` - PyPI API token (project or account scope)
- [ ] `DOCKER_USERNAME` - Docker Hub username
- [ ] `DOCKER_TOKEN` - Docker Hub access token (read/write)
- [ ] `GITHUB_TOKEN` - Auto-provided (no action needed)

---

## Workflow Dependencies

### release.yml Dependencies
```yaml
Python: 3.12
Actions:
  - actions/checkout@v4
  - actions/setup-python@v5
  - softprops/action-gh-release@v2
PyPI Packages:
  - build
  - twine
```

### docker-release.yml Dependencies
```yaml
Actions:
  - actions/checkout@v4
  - docker/setup-buildx-action@v3
  - docker/login-action@v3
  - docker/build-push-action@v5
Docker:
  - Buildx
  - QEMU (for multi-arch)
```

---

## Cache Information

### Type
- GitHub Actions Cache (`type=gha`)

### Storage
- **Limit**: 10GB per repository
- **Retention**: 7 days for unused entries
- **Cleanup**: Automatic LRU eviction

### Performance
| Scenario | Cache Hit | Build Time |
|----------|-----------|------------|
| First build | 0% | 10-15 min |
| Code change only | 85% | 1-2 min |
| Dependency update | 60% | 3-5 min |
| No changes | 100% | 30-60 sec |

---

## Build Platforms

| Platform | Architecture | Devices |
|----------|--------------|---------|
| linux/amd64 | x86_64 | Intel/AMD servers, AWS EC2, GCP |
| linux/arm64 | aarch64 | Apple Silicon, AWS Graviton, Raspberry Pi |

---

## Version Validation

### Pre-Tag Checklist
```bash
# Check current version
python -c "from crawl4ai.__version__ import __version__; print(__version__)"

# Verify it matches intended tag
# If tag is v1.2.3, version should be "1.2.3"
```

### Post-Release Verification
```bash
# PyPI
pip install crawl4ai==1.2.3
python -c "import crawl4ai; print(crawl4ai.__version__)"

# Docker
docker pull unclecode/crawl4ai:1.2.3
docker run unclecode/crawl4ai:1.2.3 python -c "import crawl4ai; print(crawl4ai.__version__)"
```

---

## Monitoring URLs

| Service | URL |
|---------|-----|
| GitHub Actions | `https://github.com/{owner}/{repo}/actions` |
| PyPI Project | `https://pypi.org/project/crawl4ai/` |
| Docker Hub | `https://hub.docker.com/r/unclecode/crawl4ai` |
| GitHub Releases | `https://github.com/{owner}/{repo}/releases` |

---

## Rollback Strategy

### PyPI (Cannot Delete)
```bash
# Increment patch version
git tag v1.2.4
git push origin v1.2.4
```

### Docker (Can Overwrite)
```bash
# Rebuild with fix
git tag docker-rebuild-v1.2.3
git push origin docker-rebuild-v1.2.3
```

### GitHub Release
```bash
# Delete release
gh release delete v1.2.3

# Delete tag
git push --delete origin v1.2.3
```

---

## Status Badge Markdown

```markdown
[![Release Pipeline](https://github.com/{owner}/{repo}/actions/workflows/release.yml/badge.svg)](https://github.com/{owner}/{repo}/actions/workflows/release.yml)

[![Docker Release](https://github.com/{owner}/{repo}/actions/workflows/docker-release.yml/badge.svg)](https://github.com/{owner}/{repo}/actions/workflows/docker-release.yml)
```

---

## Timeline Example

```
0:00 - Push tag v1.2.3
0:01 - release.yml starts
0:02 - Version validation passes
0:03 - Package built
0:04 - PyPI upload starts
0:06 - PyPI upload complete ✓
0:07 - GitHub release created ✓
0:08 - release.yml complete
0:08 - docker-release.yml triggered
0:10 - Docker build starts
0:12 - amd64 image built (cache hit)
0:14 - arm64 image built (cache hit)
0:15 - Images pushed to Docker Hub ✓
0:16 - docker-release.yml complete

Total: ~16 minutes
Critical path (PyPI + GitHub): ~8 minutes
```

---

## Contact

For workflow issues:
1. Check Actions tab for logs
2. Review this reference
3. See [README.md](./README.md) for detailed docs
