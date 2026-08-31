# Contributing to Crawl4AI

Welcome to the Crawl4AI project! As an open-source library for web crawling and AI integration, we value contributions from the community. This guide explains our branching strategy, how to contribute effectively, and the overall release process. Our goal is to maintain a stable, collaborative environment where bug fixes, features, and improvements can be integrated smoothly while allowing for experimental development.

We follow a GitFlow-inspired workflow to ensure predictability and quality. Releases occur approximately every two weeks, with a focus on semantic versioning, comprehensive documentation, and user-friendly updates.

## Core Branches

- **main**: The stable branch containing production-ready code. It's always identical to the latest released version and is tagged for releases. Do not submit PRs directly here.
- **develop**: The primary integration branch for ongoing development. This is where all contributions (bug fixes, minor features, documentation updates) are merged. Submit your pull requests targeting this branch.
- **next**: Reserved for the lead maintainer (Unclecode) to experiment with major features, refactors, or cutting-edge changes. These are merged into `develop` when ready.
- **release/vX.Y.Z**: Temporary branches created from `develop` for final release preparations (e.g., version bumps, demos, release notes). These are short-lived and deleted after the release.

## Contributor Workflow

We encourage contributions of all kinds: bug fixes, new features, documentation improvements, tests, or even Docker enhancements. Follow these steps to contribute:

1. **Fork the Repository**: Create your own fork on GitHub.
2. **Create a Branch**: Base your work on the `develop` branch.
    
    ```
    git checkout develop
    git checkout -b feature/your-feature-name  # Or bugfix/your-bugfix-name
    
    ```
    
3. **Make Changes**:
    - Implement your feature or fix.
    - If updating documentation (e.g., README.md, mkdocs.yml, or docs/blog/), ensure version references are consistent (e.g., update site_name in mkdocs.yml to reflect the upcoming version if relevant).
    - For Docker-related changes (e.g., Dockerfile, docker-compose.yml, or docs/md_v2/core/docker-deployment.md), test locally and include build instructions in your PR description.
    - Add tests if applicable (run `pytest` to verify).
    - Follow code style guidelines (use black for formatting).
4. **Commit and Push**:
    - Use descriptive commit messages (e.g., "Fix: Resolve issue with async crawling").
    - Push to your fork: `git push origin feature/your-feature-name`.
5. **Submit a Pull Request**:
    - Target the `develop` branch.
    - Provide a clear description: What does it do? Link to any issues. Include screenshots or code examples if helpful.
    - If your change affects documentation or Docker, mention how it aligns with the version (e.g., "Updates Docker docs for v0.7.0 compatibility").
    - We'll review and merge approved PRs into `develop`.
6. **Discuss Large Changes**: For major features or experimental ideas, open an issue first to align with the project's direction.

If your PR involves breaking changes, include a migration guide in the description.

## Lead Maintainer's Workflow (For Reference)

- The lead maintainer (Unclecode) uses the `next` branch for isolated experimental work.
- Features from `next` are periodically merged into `develop` (via rebase and merge) to keep everything in sync.
- This isolation ensures your contributions aren't disrupted by ongoing major changes.

## Release Process (High-Level Overview)

Releases happen bi-weekly to ship improvements regularly. As a contributor, your merged changes in `develop` will be included in the next release unless specified otherwise. Here's a summary of what happens:

- **Preparation**: A temporary `release/vX.Y.Z` branch is created from `develop`. Any ready features from `next` are merged here.
- **Final Updates**:
    - Version bump in code (e.g., `__version__.py`).
    - Creation of a demo script in `examples/` to showcase new features.
    - Writing release notes in `docs/blog/` (personal "I" voice from Unclecode, with code examples, impacts, and migration guides if needed).
    - Documentation updates: README.md (highlights, version refs), mkdocs.yml (site_name with version), docs/blog/index.md (add new release), and copying notes to `docs/md_v2/blog/releases/`.
    - Docker updates: Dockerfile (version arg), docker-compose.yml, deploy/docker/README.md, and docs/md_v2/core/docker-deployment.md. A release candidate image (e.g., `X.Y.Z-r1`) is built and tested.
- **Testing and Merge**: Full tests run; changes committed and merged to `main` with a tag.
- **Publication**: Tagged release on GitHub (with notes), publish to PyPI, and push Docker images (stable and `latest` after testing).
- **Sync**: Back-merge to `develop` and reset `next` for the next cycle.

Semantic versioning is used: MAJOR for breaking changes, MINOR for features, PATCH for fixes. Pre-releases (e.g., `-rc1`) may be used for testing.

If your contribution requires Docker testing or affects docs, it may be part of this step—feel free to suggest updates in your PR.

## Benefits of This Approach

- **Stability**: `main` is always reliable for users.
- **Collaboration**: Fixed PR target (`develop`) makes contributing straightforward.
- **Isolation**: Experimental work in `next` doesn't block team progress.
- **User-Focused**: Releases include demos, detailed notes, and updated docs/Docker for easy adoption.
- **Predictability**: Bi-weekly cadence keeps the project active.

## Checklist for Contributors

Before submitting a PR:

- [ ]  Based on and targeting `develop`.
- [ ]  Tests pass (`pytest`).
- [ ]  Docs updated if needed (e.g., version refs in mkdocs.yml, Docker files).
- [ ]  No breaking changes without a migration guide.
- [ ]  Descriptive title and description.

## Common Issues

- **Merge Conflicts**: Rebase your branch on latest `develop` before PR.
- **Docker Builds**: Test multi-arch (amd64/arm64) locally if changing Dockerfile.
- **Version Consistency**: Ensure any version mentions match semantic rules.

## Communication

- Open issues for discussions or bugs.
- Join our Discord (link in README) for real-time help.
- After releases, announcements go to GitHub, Discord, and social media.

Thanks for contributing to Crawl4AI — we appreciate your help in making it better!

*Last Updated: Feb 3, 2026*
