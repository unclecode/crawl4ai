C4A-Script API Reference
========================

Complete reference for all C4A-Script commands, syntax, and advanced features.

Command Categories
------------------

### 🧭 Navigation Commands

Navigate between pages and manage browser history.

#### `GO <url>`

Navigate to a specific URL.

**Syntax:**

```
GO <url>
```

**Parameters:**
- `url` - Target URL (string)

**Examples:**

```
GO https://example.com
GO https://api.example.com/login
GO /relative/path
```

**Notes:**
- Supports both absolute and relative URLs
- Automatically handles protocol detection
- Waits for page load to complete

---

#### `RELOAD`

Refresh the current page.

**Syntax:**

```
RELOAD
```

**Examples:**

```
RELOAD
```

**Notes:**
- Equivalent to pressing F5 or clicking browser refresh
- Waits for page reload to complete
- Preserves current URL

---