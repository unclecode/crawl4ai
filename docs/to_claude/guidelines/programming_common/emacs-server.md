<!-- ---
!-- Timestamp: 2025-05-25 23:21:21
!-- Author: ywatanabe
!-- File: /ssh:sp:/home/ywatanabe/.claude/to_claude/guidelines/elisp/emacs-server.md
!-- --- -->

# Emacs Server Usage Guidelines

## Overview
- You have access to the Emacs server for direct interaction with the editor
- Available through the `claude-emacs-server.sh` utility

## Basic Commands
- Send message: `claude-emacs-server.sh -s "Your message"`
- Read content: `claude-emacs-server.sh -r`
- Run Elisp code: `claude-emacs-server.sh -e "(your-elisp-code)"`

## Best Practices
1. Always work in the dedicated Claude frame
   - Frame is automatically created with proper dimensions
   - Named "claude-frame" for easy identification

2. Maintain workflow isolation
   - Keep your operations in your frame
   - Avoid disrupting user's existing buffers

3. Provide clear feedback
   - Include status messages when performing operations
   - Make results visible in your dedicated frame

4. Efficient communication
   - Use the dedicated scratch buffer for messages
   - Reuse the existing frame for multiple operations

5. Run arbitrary code with caution
   - Use the -e/--eval option for Elisp evaluation
   - Document any significant changes made to the environment

<!-- EOF -->