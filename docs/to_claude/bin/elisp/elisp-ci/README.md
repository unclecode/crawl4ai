# Elisp-CI: Universal CI/CD for Emacs Lisp Projects

A powerful, reusable testing framework that brings modern CI/CD practices to the Emacs Lisp ecosystem.

## 🚀 Features

- **Cross-Version Testing**: Test across Emacs 27.1 through snapshot automatically
- **Docker Integration**: Reproducible testing environments 
- **GitHub Actions**: Ready-to-use CI/CD templates
- **Zero Configuration**: Works out-of-box for standard project structures
- **Local Development**: Fast feedback loops with watch mode
- **Coverage Reports**: Track test coverage across versions
- **Dependency Analysis**: Automatically detect package dependencies

## 📦 Quick Start

### Installation

```bash
# Add to PATH
export PATH="$HOME/.claude/to_claude/bin/elisp-ci:$PATH"

# Or create symlink
ln -s ~/.claude/to_claude/bin/elisp-ci/elisp-ci /usr/local/bin/elisp-ci
```

### Initialize Project

```bash
cd your-elisp-project/
elisp-ci init
```

This creates:
- `.elisp-ci.yml` - Configuration file
- `tests/` directory with sample test
- `Makefile` with common targets
- `.github/workflows/elisp-ci.yml` - GitHub Actions workflow

### Run Tests

```bash
# Test current Emacs version
elisp-ci test

# Test all supported versions
elisp-ci test --all-versions

# Test specific version
elisp-ci test --version 29.1

# Test in Docker (reproducible)
elisp-ci docker-test --all-versions
```

## 🔧 Configuration

### .elisp-ci.yml Example

```yaml
project:
  name: "my-package"
  entry: "my-package.el"
  
emacs_versions:
  - "27.1"
  - "28.2" 
  - "29.1"
  - "29.4"
  - "snapshot"

dependencies:
  - "dash"
  - "s"

test:
  framework: "ert"
  directory: "tests/"
  pattern: "test-*.el"
  timeout: 120
  
coverage:
  enabled: true
  threshold: 85

docker:
  enabled: true
  
github_actions:
  enabled: true
  continue_on_error_for_snapshot: true
```

## 📋 Commands

### Core Commands

- `elisp-ci init` - Initialize project with elisp-ci
- `elisp-ci test` - Run tests locally
- `elisp-ci analyze` - Analyze project structure and dependencies
- `elisp-ci validate` - Validate configuration

### Docker Commands

- `elisp-ci docker-build` - Build test environment images
- `elisp-ci docker-test` - Run tests in Docker containers

### Template Commands

- `elisp-ci template github-actions` - Generate GitHub Actions workflow

### Development Commands

- `elisp-ci test --watch` - Watch mode for development
- `elisp-ci test --coverage` - Generate coverage report
- `elisp-ci benchmark` - Performance testing across versions

## 🎯 Project Structure

Elisp-CI works with standard Emacs Lisp project structures:

```
your-project/
├── my-package.el              # Main entry point
├── src/                       # Source files (optional)
│   ├── my-package-core.el
│   └── my-package-utils.el
├── tests/                     # Test files
│   ├── test-my-package.el
│   └── test-my-package-core.el
├── .elisp-ci.yml             # Configuration
├── Makefile                   # Build targets
└── .github/workflows/        # CI/CD workflows
    └── elisp-ci.yml
```

## 🧪 Testing Framework Integration

### ERT (Built-in)

```elisp
;;; tests/test-my-package.el
(require 'ert)
(require 'my-package)

(ert-deftest test-my-package-loads ()
  "Test that package loads correctly."
  (should (featurep 'my-package)))

(ert-deftest test-my-function ()
  "Test my-function behavior."
  (should (equal (my-function "input") "expected-output")))
```

### Buttercup (Optional)

```elisp
;;; tests/test-my-package.el
(require 'buttercup)
(require 'my-package)

(describe "my-package"
  (it "should load correctly"
    (expect (featurep 'my-package) :to-be t))
    
  (it "should process input correctly"
    (expect (my-function "input") :to-equal "expected-output")))
```

## 🐳 Docker Integration

### Local Docker Testing

```bash
# Build test environments
elisp-ci docker-build

# Test all versions in Docker
elisp-ci docker-test --all-versions

# Test specific version
elisp-ci docker-test --version 29.1
```

### Custom Docker Configuration

```yaml
# .elisp-ci.yml
docker:
  enabled: true
  base_image: "ubuntu:22.04"
  registry: "ghcr.io/your-org"
  cache_layers: true
```

## 🔄 GitHub Actions Integration

Elisp-CI generates optimized GitHub Actions workflows:

```yaml
# .github/workflows/elisp-ci.yml
name: Elisp CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    continue-on-error: ${{ matrix.emacs_version == 'snapshot' }}
    
    strategy:
      matrix:
        emacs_version: ["27.1", "28.2", "29.1", "29.4", "snapshot"]
    
    steps:
      - uses: actions/checkout@v4
      - uses: purcell/setup-emacs@master
        with:
          version: ${{ matrix.emacs_version }}
      - name: Run Tests
        run: elisp-ci test --version ${{ matrix.emacs_version }}
```

## 📊 Coverage Reports

Generate and track test coverage:

```bash
# Generate coverage report
elisp-ci test --coverage

# View coverage report
open .elisp-ci-cache/coverage.html

# Set coverage threshold
# In .elisp-ci.yml:
coverage:
  enabled: true
  threshold: 85
```

## 🔍 Dependency Analysis

Automatic dependency detection and validation:

```bash
# Analyze project dependencies
elisp-ci analyze

# Output example:
# External dependencies detected:
#   - dash
#   - s
#   - request
# 
# Suggestions:
#   - Add missing dependencies to .elisp-ci.yml
#   - Consider using package-lint for additional checks
```

## 🎨 Integration with Existing Projects

### ETM Example

```bash
cd emacs-tab-manager/
elisp-ci init
elisp-ci test --all-versions

# Results in reliable testing across:
# ✓ Emacs 27.1  ✓ Emacs 28.2  ✓ Emacs 29.1
# ✓ Emacs 29.4  ✓ Emacs snapshot
```

### Package.el Projects

```yaml
# .elisp-ci.yml for package.el projects
project:
  name: "my-package"
  entry: "my-package.el"

dependencies:
  - "package-lint"
  - "checkdoc"

test:
  pre_hooks:
    - "package-lint-batch-and-exit my-package.el"
    - "checkdoc-file my-package.el"
```

## 🚀 Advanced Usage

### Watch Mode for Development

```bash
# Automatically run tests on file changes
elisp-ci test --watch

# Watch specific test file
elisp-ci test --watch --pattern "test-specific.el"
```

### Performance Benchmarking

```bash
# Compare performance across Emacs versions
elisp-ci benchmark

# Results:
# Emacs 27.1: 1.23s  (100%)
# Emacs 28.2: 1.15s  (93.5%)  
# Emacs 29.1: 1.08s  (87.8%)
# Emacs 29.4: 1.02s  (82.9%)
```

### Custom Test Runners

```yaml
# .elisp-ci.yml
test:
  framework: "custom"
  runner: "./scripts/custom-test-runner.sh"
  pattern: "**/*-test.el"
```

## 🌟 Benefits for Emacs Ecosystem

### For Package Maintainers
- **Quality Assurance**: Consistent testing across Emacs versions
- **CI/CD Standardization**: Familiar workflow across projects
- **Reduced Setup Time**: Zero-config testing for standard projects
- **Community Standards**: Shared best practices

### For Contributors
- **Lower Barrier**: Easy to contribute to well-tested projects
- **Confidence**: Clear test results before submitting PRs
- **Learning**: Consistent patterns across Elisp projects

### For Users
- **Reliability**: Packages tested across their Emacs version
- **Compatibility**: Clear version support information
- **Quality**: Higher quality packages due to better testing

## 🔧 Troubleshooting

### Common Issues

**Tests not found:**
```bash
# Check test directory and pattern
elisp-ci validate

# Adjust configuration
# In .elisp-ci.yml:
test:
  directory: "test/"  # Note: singular form
  pattern: "*-test.el"
```

**Dependency issues:**
```bash
# Analyze dependencies
elisp-ci analyze

# Add missing dependencies to .elisp-ci.yml
dependencies:
  - "missing-package"
```

**Docker issues:**
```bash
# Rebuild Docker images
elisp-ci docker-build

# Clear Docker cache
docker system prune -a
```

## 🤝 Contributing

Elisp-CI is designed to serve the entire Emacs community. Contributions welcome!

```bash
# Test elisp-ci itself
cd ~/.claude/to_claude/bin/elisp-ci/
elisp-ci init
elisp-ci test --all-versions

# Submit improvements
git checkout -b feature/enhancement
# ... make changes ...
git commit -m "Enhance: feature description"
# Submit PR
```

## 📚 Examples

See real-world usage in:
- [Emacs Tab Manager (ETM)](https://github.com/ywatanabe1989/emacs-tab-manager)
- More projects adopting elisp-ci...

## 🔗 Links

- **Issues & Feature Requests**: Create GitHub issues for the host project
- **Documentation**: This README and inline help (`elisp-ci --help`)
- **Community**: Share your elisp-ci configurations!

---

**Elisp-CI** - Making Emacs Lisp development more reliable, one test at a time! 🎯