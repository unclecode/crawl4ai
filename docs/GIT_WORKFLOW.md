# Git Workflow & Development Ceremony

This document outlines the standardized Git workflow for the Crawl4AI microservices project.

---

## 🔄 Development Workflow

### For Each Major Code Task:

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/<descriptive-name>
   # Examples:
   # git checkout -b feature/uv-workspace-setup
   # git checkout -b feature/browser-service
   # git checkout -b feature/basic-cli
   ```

2. **Implement Changes**
   - Write code according to task requirements
   - Follow project conventions and style guides
   - Add tests for new functionality
   - Update documentation as needed

3. **Commit Changes**
   ```bash
   # Stage all changes
   git add .
   
   # Commit with descriptive message
   git commit -m "feat: <short description>
   
   <detailed description of changes>
   
   - Bullet point 1
   - Bullet point 2
   - Closes #<issue-number> (if applicable)
   "
   ```
   
   **Commit Message Convention:**
   - `feat:` - New feature
   - `fix:` - Bug fix
   - `docs:` - Documentation changes
   - `refactor:` - Code refactoring
   - `test:` - Adding or updating tests
   - `chore:` - Maintenance tasks
   - `perf:` - Performance improvements

4. **Push to Remote**
   ```bash
   git push -u origin feature/<branch-name>
   ```

5. **Create Pull Request**
   - Go to GitHub repository
   - Click "Compare & pull request"
   - Fill in PR template:
     - Clear title describing the change
     - Detailed description of what was changed and why
     - Link related issues
     - Add screenshots/examples if applicable
   - Request review from CodeRabbit (automatic)

6. **Code Review with CodeRabbit**
   - Wait for CodeRabbit's automated review
   - Read all review comments carefully
   - **Implement changes for:**
     - ✅ **Critical** priority items (MUST fix)
     - ✅ **High** priority items (MUST fix)
     - 🤔 **Medium** priority items (evaluate case-by-case)
     - 💡 **Low** priority items (optional, use judgment)
   
   **Addressing Review Comments:**
   ```bash
   # Make fixes on the same branch
   git add .
   git commit -m "fix: address CodeRabbit review - <specific issue>"
   git push
   ```

7. **Human Approval & Merge**
   - **ONLY THE HUMAN (Jason)** merges the PR
   - Human reviews final changes
   - Human clicks "Squash and merge" or "Merge pull request"
   - Human deletes the feature branch on GitHub

8. **Local Sync**
   ```bash
   # After human confirms merge
   git checkout main
   git pull origin main
   git branch -d feature/<branch-name>  # Delete local feature branch
   ```

9. **Begin Next Task**
   - Update todo list
   - Start next feature branch

---

## 📋 PR Template

```markdown
## Description
Brief description of what this PR does.

## Changes
- List of specific changes
- Another change
- And another

## Related Issues
Closes #<issue-number>

## Type of Change
- [ ] New feature
- [ ] Bug fix
- [ ] Documentation update
- [ ] Refactoring
- [ ] Performance improvement

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing completed

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No new warnings introduced
- [ ] Tests pass locally
```

---

## 🎯 Example Workflow

### Task: Setup UV Workspace

```bash
# 1. Create feature branch
git checkout -b feature/uv-workspace-setup

# 2. Implement changes
# - Create pyproject.toml
# - Set up workspace structure
# - Add shared libraries
# etc...

# 3. Commit
git add .
git commit -m "feat: setup UV workspace structure

- Create root pyproject.toml with workspace config
- Add services/, packages/, shared/ directories
- Configure shared core, client, and schemas libraries
- Add uv.lock for dependency management
- Update documentation with workspace layout

Closes #1"

# 4. Push
git push -u origin feature/uv-workspace-setup

# 5. Create PR on GitHub
# (GitHub UI)

# 6. Wait for CodeRabbit review
# Read all comments, implement Critical/High priority fixes

# 7. Address review (if needed)
git add .
git commit -m "fix: address CodeRabbit review - add type hints to core models"
git push

# 8. Wait for human merge
# (Jason merges on GitHub)

# 9. Sync locally
git checkout main
git pull origin main
git branch -d feature/uv-workspace-setup

# 10. Start next task
git checkout -b feature/browser-service
```

---

## 🚫 Important Rules

### ❌ DO NOT:
- Merge your own PRs (human only)
- Delete feature branches manually before human confirms merge
- Ignore Critical or High priority CodeRabbit reviews
- Push directly to `main` branch
- Create PRs without proper descriptions
- Commit without testing

### ✅ DO:
- Create descriptive branch names
- Write clear commit messages
- Implement Critical/High priority fixes
- Wait for human approval
- Keep PRs focused on single tasks
- Update documentation with code changes
- Add tests for new features
- Sync with main after merge

---

## 🏷️ Branch Naming Convention

```
feature/<descriptive-name>     # New features
fix/<bug-description>          # Bug fixes
docs/<doc-update>              # Documentation only
refactor/<what-refactored>     # Code refactoring
test/<test-description>        # Test additions/updates
chore/<maintenance-task>       # Maintenance tasks
```

**Examples:**
- `feature/uv-workspace-setup`
- `feature/browser-service`
- `feature/basic-cli`
- `fix/browser-manager-memory-leak`
- `docs/api-specification`
- `refactor/extraction-strategy`

---

## 📊 Code Review Priority Guide

### Critical 🔴
**MUST FIX** - Blocks merge
- Security vulnerabilities
- Data loss risks
- Breaking changes
- Severe bugs

### High 🟠
**MUST FIX** - Should fix before merge
- Performance issues
- Memory leaks
- Poor error handling
- API design flaws

### Medium 🟡
**EVALUATE** - Use judgment
- Code style issues
- Minor optimizations
- Refactoring suggestions
- Documentation improvements

### Low 🟢
**OPTIONAL** - Nice to have
- Naming suggestions
- Comment additions
- Minor formatting
- Best practice tips

---

## 🔍 Pre-PR Checklist

Before creating a PR, verify:

- [ ] Code runs without errors
- [ ] Tests pass (`uv run pytest`)
- [ ] Linting passes (`uv run ruff check`)
- [ ] Type checking passes (`uv run mypy`)
- [ ] Documentation updated
- [ ] Commit messages follow convention
- [ ] Branch is up to date with main
- [ ] No sensitive data in commits

---

## 🎓 Additional Resources

- [Conventional Commits](https://www.conventionalcommits.org/)
- [Git Flow](https://nvie.com/posts/a-successful-git-branching-model/)
- [Writing Good Commit Messages](https://chris.beams.io/posts/git-commit/)

---

**Last Updated:** 2025-10-18  
**Maintained By:** Crawl4AI Development Team
