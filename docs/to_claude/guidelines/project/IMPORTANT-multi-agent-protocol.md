<!-- ---
!-- Timestamp: 2025-05-26 02:32:59
!-- Author: ywatanabe
!-- File: /ssh:ywatanabe@sp:/home/ywatanabe/.dotfiles/.claude/to_claude/guidelines/project/IMPORTANT-multi-agent-protocol.md
!-- --- -->

# Multi-Agent Communication Protocol
## Core Principles
1. Use `$CLAUDE_ID` for agent identification: `{role}-CLAUDE-{id}-{date}`
2. Single coordination file: `PROJECT_ROOT/project_management/AGENT_BULLETIN_BOARD.md`
3. Clear module ownership with small overlap to avoid conflicts
4. File-based async communication

## Bulletin Board Structure
```markdown
# Project Agent Bulletin Board
## Agent Status
| Agent ID | Module | Status | Progress | Last Update |
|----------|--------|--------|----------|-------------|
| core-CLAUDE-123-20250526 | auth | 🔄 | 75% | 14:30 |
| test-CLAUDE-456-20250526 | auth-tests | ⏳ | 0% | waiting |

## Current Work
### 🔄 IN PROGRESS
- auth module (core-CLAUDE-123)
- database layer (db-CLAUDE-789)

### ✅ COMPLETED 
- user model (model-CLAUDE-101) → ready for integration

### 🆘 BLOCKED
- payment service → needs auth completion

## Dependencies
auth → auth-tests → integration-tests
database → auth → payment
```

## Communication Protocol
### Claiming Work
1. Check bulletin board availability
2. Add agent entry with timeline
3. Update status to 🔄 IN PROGRESS

### Progress Updates
```markdown
### Agent: core-CLAUDE-123-20250526
Module: auth
Status: 🔄 75%
Last: 2025-05-26 14:30
Completed: login, logout
Next: password reset
Blockers: none
Ready for: auth-tests agent can start
```

### Completion Handoff
```markdown
### HANDOFF: auth module
From: core-CLAUDE-123
Status: ✅ COMPLETE
Files: src/auth.py, tests/test_auth.py
Interface: AuthService.login(user, pass) → token
Dependencies: database layer required
Ready for: test-CLAUDE-456 integration
```

## Work Areas
```
PROJECT_ROOT/
├── project_management/
│   └── AGENT_BULLETIN_BOARD.md
```

## Status Indicators
- 🔄 In Progress
- ✅ Complete  
- ⏳ Waiting
- 🆘 Blocked
- ❌ Failed

## Best Practices
1. Update bulletin board every 1 chain of work
2. Signal completion before switching modules
3. Document interfaces for dependent agents
4. Use clear file paths in handoffs
5. Test integration points before handoff
6. Keep one agent per module boundary

## Conflict Resolution
1. Check bulletin board for ownership conflicts
2. Document blockers immediately
3. Escalate integration issues to bulletin board
4. Use dependency order for priority
```

<!-- EOF -->