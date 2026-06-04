# Security Credits

We thank the following security researchers for their responsible disclosure:

| Researcher | Contact | Vulnerability | Date Reported |
|---|---|---|---|
| Song Binglin (q1uf3ng) | q1uf3ng@proton.me | AST sandbox escape via gi_frame.f_back chain (CVSS 9.8) | 2026-03-29 |
| Jeongbean Jeon | wjswjdqls7@gmail.com | File write, SSRF, monitor auth bypass, stored XSS | 2026-04-13 |
| wulonchia | wulonchia@gmail.com | File write via output_path (independent report) | 2026-04-13 |
| by111 (August829) | GitHub: [August829](https://github.com/August829) | Hardcoded JWT secret, eval in /config/dump, /execute_js, hook sandbox escape | 2026-04-14 |
| secsys_codex ([FORIMOC](https://github.com/FORIMOC)) | secsys_codex@163.com | SSRF via /md, /crawl, /llm endpoints (URL destination validation) | 2026-04-18 |
| Velayutham Selvaraj | [LinkedIn](https://www.linkedin.com/in/velayuthamselvaraj) | SSRF via missing host validation in validate_url_scheme (independent report) | 2026-05-06 |
| IcySun & Yashon | icysun@qq.com, liyaoyin@qq.com | SSRF, file write via output_path, missing auth by default, hook sandbox bypass via asyncio (independent report) | 2026-05-15 |
| Geo ([geo-chen](https://github.com/geo-chen)) | cve@sageby.com | LLM API key exfiltration via unvalidated base_url (0.8.8) | 2026-06-02 |
| Geo ([geo-chen](https://github.com/geo-chen)) | cve@sageby.com | SSRF via proxy_config.server bypassing the SSRF check (0.8.9) | 2026-06-04 |
