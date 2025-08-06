<!-- ---
!-- Timestamp: 2025-05-31 18:09:11
!-- Author: ywatanabe
!-- File: /home/ywatanabe/.dotfiles/.claude/to_claude/guidelines/project/IMPORTANT-project-management-bulletin-board.md
!-- --- -->

# Bulletin Board - Agent Communication

In this project, other agents may be working simultaneously. As an inter-agent communication tool, we adopt a bulletin board system using a markdown file (`./project_management/BULLETIN-BOARD.md`). This aims to coordinate better, by reducing conflicts, sharing knowledge, and think from various aspects.



## Usage Rules

1. Read before starting work
2. Write when:
   - Starting new task
   - Completing task
   - Finding important information
   - Need coordination

## Entry Format

```
## Agent: $CLAUDE_ID
Role: [your role] (Required)
Status: [working on / completed] (Optional)
Task: [brief description] (Required)
Notes: [key findings/issues/suggestions/ideas/concerns] (Optional)
@mentions: [if targeting specific agent] (Optional)
Timestamp: YYYY-MMDD-HH:mm (Required)
```

## Other communication channels
You are also expected to use these project-level files in a collaborative manner with keep shared space clean and tidy.
- `./project_management/progress.md`
- `./project_management/bug-reports/bug-repoort-<title>.md`
  - If solved, move bug-report entry to:
    `./project_management/bug-reports/solved/bug-repoort-<title>.md`
- `./project_management/feature-requests/feature-request-<title>.md`
  - If solved, move bug-report entry to:
    `./project_management/feature-requests/solved/feature-request-<title>.md`

## Your Understanding Check
Did you understand the guideline? If yes, please say:
`CLAUDE UNDERSTOOD: <THIS FILE PATH HERE>`

<!-- EOF -->