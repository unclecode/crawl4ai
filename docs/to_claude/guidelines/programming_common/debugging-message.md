<!-- ---
!-- Timestamp: 2025-05-25 02:41:39
!-- Author: ywatanabe
!-- File: /home/ywatanabe/.dotfiles/.claude/to_claude/guidelines/guidelines-programming-Debug-Message-Rules.md
!-- --- -->

# Debug Message Implementation Guidelines

Debugging Message is quite useful, especially with flag and prefixes.
Follow the exmaples below and keep debugginge messages in src, scripts, and tests, especially for critical functions.

## Language-Specific Examples

### Elisp
```elisp
;; Buffer-local debug state
(defvar-local my-module-debug-enabled nil)

;; Write to *Messages* without minibuffer echo
(defun package-name-debug-message (debug-message)
  "Send DEBUG-MESSAGE to *Messages* buffer without minibuffer echo."
  (when my-module-debug-enabled
    (let ((inhibit-message t))  ; This prevents echo in minibuffer
      (message "[MY-MODULE DEBUG %s] %s" (buffer-name) debug-message))))
```

### Python
```python
import logging

# Per-module logger
logger = logging.getLogger(__name__)

# Context-specific formatting
logger.debug(f"[{self.__class__.__name__}] Processing: {item}")
```

## Best Practices

1. **Default to Silent**: Debug should be opt-in, not opt-out
2. **Respect User Preferences**: Allow users to configure debug behavior
3. **Document Debug Options**: Clearly explain how to enable/view debug output
4. **Clean Up**: Remove or compile out debug code in production builds
5. **Consistent Format**: Maintain consistent message format across the codebase

## Implementation Checklist

- [ ] Context-specific debug states implemented
- [ ] Consistent message formatting established
- [ ] User documentation provided especially for flag

<!-- EOF -->