<!-- ---
!-- Timestamp: 2025-05-26 10:25:00
!-- Author: ywatanabe
!-- File: /home/ywatanabe/proj/gPAC/docs/to_claude/guidelines/project/general-multi-agent-coordination.md
!-- --- -->

# General Multi-Agent Coordination Guidelines

## 🎯 Core Philosophy

Multiple AI agents can work together efficiently by following these principles:
1. **Clear Boundaries**: Each agent owns specific modules/files
2. **Asynchronous Communication**: No blocking waits between agents
3. **Human-Readable State**: All coordination visible in plain text
4. **Graceful Failures**: System continues even if agents crash

## 📋 Quick Start Checklist

```bash
# 1. Set agent identity
export CLAUDE_ID="<role>-CLAUDE-<uuid>-<timestamp>"

# 2. Check bulletin board before starting
cat ./project_management/AGENT_BULLETIN_BOARD.md

# 3. Claim your work area
echo "Claiming: <module> by $CLAUDE_ID" >> AGENT_BULLETIN_BOARD.md

# 4. Work independently
# ... do your work ...

# 5. Update status regularly (every 5-10 min)
# 6. Hand off when complete
```

## 🏗️ Standard Project Structure

```
project_root/
├── project_management/
│   ├── AGENT_BULLETIN_BOARD.md    # Central coordination
│   ├── .locks/                     # Lightweight locks (optional)
│   └── .events/                    # Event notifications (optional)
├── src/                            # Source code
├── tests/                          # Test files
├── docs/                           # Documentation
└── scripts/                        # Utility scripts
```

## 📝 Bulletin Board Format

```markdown
# Project Agent Bulletin Board

## Active Agents
| Agent ID | Role | Module | Status | Progress | Last Update |
|----------|------|--------|--------|----------|-------------|
| core-CLAUDE-abc123-20250526 | Core Dev | auth | 🔄 | 75% | 10:30 |
| test-CLAUDE-def456-20250526 | Testing | auth-tests | ⏳ | 0% | 10:25 |

## Work Claims
| Module/File | Agent | Claimed At | ETA |
|-------------|-------|------------|-----|
| src/auth.py | core-CLAUDE-abc123 | 10:15 | 11:00 |

## Recent Handoffs
| From | To | Module | Status | Time |
|------|-----|--------|--------|------|
| core-CLAUDE-abc123 | test-CLAUDE-* | auth | ✅ READY | 10:45 |

## Blocked Work
| Agent | Blocked On | Reason | Since |
|-------|------------|--------|-------|
| pay-CLAUDE-xyz789 | auth module | Needs auth.login() | 10:20 |
```

## 🔄 Communication Protocol

### 1. Status Indicators
- 🔄 **IN_PROGRESS**: Actively working
- ✅ **COMPLETE**: Finished, ready for next
- ⏳ **WAITING**: Waiting for dependency
- 🆘 **BLOCKED**: Need help
- ❌ **FAILED**: Task failed

### 2. Update Frequency
- **Starting work**: Immediate claim
- **Progress update**: Every 5-10 minutes
- **Blocking issue**: Immediate
- **Completion**: Immediate
- **Checking board**: Based on status (1-5 min)

### 3. Message Templates

#### Claiming Work
```markdown
### CLAIM: <module_name>
Agent: <CLAUDE_ID>
Time: <timestamp>
Files: <file_list>
Dependencies: <none|list>
ETA: <estimated_time>
```

#### Status Update
```markdown
### UPDATE: <module_name>
Agent: <CLAUDE_ID>
Status: 🔄 <percentage>%
Current: <what_doing>
Next: <what_next>
Blockers: <none|list>
```

#### Handoff
```markdown
### HANDOFF: <module_name>
From: <CLAUDE_ID>
To: <role-CLAUDE-*|specific_id>
Files: <modified_files>
Tests: <pass|fail|pending>
Notes: <important_info>
```

## 🚦 Coordination Strategies

### Strategy 1: Module-Based (Recommended)
```
Agent 1: src/auth/* (authentication)
Agent 2: src/api/* (API endpoints)
Agent 3: tests/* (all testing)
Agent 4: docs/* (documentation)
```

### Strategy 2: Layer-Based
```
Agent 1: Database layer
Agent 2: Business logic
Agent 3: API layer
Agent 4: Frontend
```

### Strategy 3: Feature-Based
```
Agent 1: User management feature
Agent 2: Payment feature
Agent 3: Reporting feature
Agent 4: Integration tests
```

## 🔐 Conflict Prevention

### 1. File-Level Coordination
```python
# Before modifying a file, check if it's claimed
def can_modify_file(filepath, bulletin_board):
    claims = parse_bulletin_board(bulletin_board)
    return filepath not in claims or claims[filepath]['agent'] == my_id
```

### 2. Merge Coordination
```bash
# Only one agent merges at a time
if acquire_lock("merge.lock"); then
    git merge feature/my-branch
    release_lock("merge.lock")
    update_bulletin("MERGED: feature/my-branch")
fi
```

### 3. Dependency Management
```markdown
## Dependency Graph
auth → api → frontend
     ↘ payments ↗
```

## 🛠️ Tools and Helpers

### 1. Simple Lock Manager (Bash)
```bash
#!/bin/bash
# lock.sh - Simple file-based locking

acquire_lock() {
    local resource=$1
    local lockfile=".locks/${resource}.lock"
    
    # Try to create lock (atomic operation)
    if (set -C; echo "$CLAUDE_ID:$(date +%s)" > "$lockfile") 2>/dev/null; then
        return 0  # Success
    else
        return 1  # Failed
    fi
}

release_lock() {
    local resource=$1
    rm -f ".locks/${resource}.lock"
}

# Usage
if acquire_lock "merge"; then
    echo "Got lock, proceeding..."
    # Do work
    release_lock "merge"
else
    echo "Could not acquire lock"
fi
```

### 2. Bulletin Board Updater (Python)
```python
import re
from datetime import datetime

def update_bulletin_board(agent_id, module, status, progress):
    with open('AGENT_BULLETIN_BOARD.md', 'r') as f:
        content = f.read()
    
    # Update or add agent status
    timestamp = datetime.now().strftime("%H:%M")
    new_row = f"| {agent_id} | {module} | {status} | {progress}% | {timestamp} |"
    
    # Update existing or append new
    if agent_id in content:
        # Update existing row
        pattern = rf"\| {agent_id} \|.*\|"
        content = re.sub(pattern, new_row, content)
    else:
        # Add new row (implementation depends on format)
        pass
    
    with open('AGENT_BULLETIN_BOARD.md', 'w') as f:
        f.write(content)
```

## 📊 Best Practices

### DO:
1. ✅ Update bulletin board regularly
2. ✅ Use clear, descriptive agent IDs
3. ✅ Document your changes in handoffs
4. ✅ Check for conflicts before starting
5. ✅ Clean up stale locks/claims
6. ✅ Keep updates concise but informative

### DON'T:
1. ❌ Modify files claimed by others
2. ❌ Hold locks longer than necessary
3. ❌ Skip status updates
4. ❌ Make assumptions about other agents' work
5. ❌ Create complex dependencies
6. ❌ Use blocking waits

## 🚨 Emergency Procedures

### 1. Deadlock Resolution
```markdown
If all agents blocked > 10 minutes:
1. Check dependency graph
2. Identify circular dependencies
3. One agent backs out
4. Document in bulletin board
```

### 2. Abandoned Work
```markdown
If no update > 30 minutes:
1. Work becomes claimable
2. New agent can take over
3. Document takeover in board
```

### 3. Merge Conflicts
```markdown
1. Agent who created conflict resolves
2. Other agents pause merging
3. Post resolution to board
4. Others can resume
```

## 📈 Scaling Guidelines

### 2-5 Agents
- Simple bulletin board
- No locks needed
- Check board every 5 min

### 5-10 Agents  
- Bulletin board + event files
- Lightweight locks for merges
- Check board every 2-3 min

### 10+ Agents
- Consider message queue
- Dedicated coordinator role
- Automated conflict detection

## 🎯 Success Metrics

1. **No file conflicts**: Zero parallel edits to same file
2. **High throughput**: Agents working in parallel 80%+ time
3. **Low latency**: Handoffs complete within 5 minutes
4. **Clear history**: Can trace all changes through bulletin board

## Your Understanding Check
Did you understand the guideline? If yes, please say:
`CLAUDE UNDERSTOOD: <THIS FILE PATH HERE>`

<!-- EOF -->