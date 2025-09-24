### Task 15: Add authentication and security measures

**Description:**
```
This task focuses on securing the application.

- [ ] 15. Add authentication and security measures

  - Implement API key validation middleware
  - Create separate admin API key authentication
  - Add SSRF protection by blocking internal IP ranges
  - Implement request size limits and input sanitization
  - Create security headers and CORS configuration
  - Write security tests for authentication and SSRF protection
  - _Requirements: 1.4, 7.4, 8.3_

**Authentication and Authorization:**
- Implement API key validation middleware for core endpoints.
- Create separate admin API key authentication for `/admin` routes.
- Keys should be managed via environment variables.

**Input Validation & Security:**
- Ensure robust SSRF protection is implemented (see Task 2).
- Add request size limits to the FastAPI app.
- Implement security headers (e.g., using middleware) and configure CORS.
```

**Globs:**
```
app/middleware/auth_middleware.py
app/core/security.py
app/core/dependencies.py
app/core/validation.py
tests/test_security.py
```