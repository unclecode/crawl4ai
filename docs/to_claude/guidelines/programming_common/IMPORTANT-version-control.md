<!-- ---
!-- Timestamp: 2025-06-14 06:21:02
!-- Author: ywatanabe
!-- File: /home/ywatanabe/.dotfiles/.claude/to_claude/guidelines/programming_common/IMPORTANT-version-control.md
!-- --- -->

## Test-Driven Development
ANY COMMIT MUST BE ASSOCIATED WITH THE LATEST TESTING REPORT
This ensures the quality of the commited contents

## Git/GitHub Availability
- `git` and `gh` commands available
- SSH public key is registered in GitHub account `ywatanabe1989`
- `git push` to `origin/main` is not accepted

## Our Version Control Workflow

### Standard Workflow (Single Working Directory)
01. Using `git status`, `git log`, `git stash list`, and so on, understand our step in the workflow
02. Start from `develop` branch
03. Checkout to `feature/<verb>-<object>`
04. Confirmed `feature/<verb>-<object>` is correctly implemented
05. Once the feature implementation is verified using tests, merge back `feature/<verb>-<object>`into `develop`
06. Once `feature/<verb>-<object>` branch merged correctly without any problems, delete `feature/<verb>-<object>` branch for cleanliness
07. Push to origin/develop
08. For important update, create PR with auto merging from `origin/develop` to `origin/main`
09. Once PR merged, udpate local `main`
10. Add tag based on the previous tags conventions
11. Add release using the tag with descriptive messages
12. Don't forget to switch back to `develop` branch locally


## Merge Rules
When conflicts found, check if they are minor problems. If it is a tiny problem solve it immediately. Otherwise, let's work on in a safe, dedicated manner

## Before Git Handling
Let me know your opinion, available plans (e.g., Plan A, Plan B, and Plan C), and reasons in the order of your recommendation
Once agreed plans determined, process git commands baesd on the agreements

## Rollback
If the project gets stacked or going not well. Roll back to the recent stable commit.

## Your Understanding Check
Did you understand the guideline? If yes, please say:
`CLAUDE UNDERSTOOD: <THIS FILE PATH HERE>`

<!-- EOF -->