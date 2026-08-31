# Privacy Policy

**Last updated: April 20, 2026**

Crawl4AI ("we", "us", "our") provides web crawling, scraping, and structured data extraction services through our open-source library, hosted API ("Crawl4AI Cloud"), dashboard, integrations, and Workspace add-ons. This Privacy Policy explains what we collect, how we use it, and the choices you have.

By creating an account or using our services, you agree to this Policy.

---

## 1. Who we are

Crawl4AI is operated by **CRAWL4AI**, located at 38 Beach Road, #26-12, South Beach Tower, Singapore 189767. Contact: [unclecode@crawl4ai.com](mailto:unclecode@crawl4ai.com).

## 2. Information we collect

We collect only what we need to operate the service.

**Account information** — when you sign up via Google or GitHub OAuth, we receive your email address, display name, profile picture URL, and a stable account identifier from the provider. We do not receive or store your password.

**Usage data** — for jobs you submit (crawls, extractions, enrichments, screenshots, scans), we record: the input URLs or keywords, the configuration you chose, timestamps, billable credits consumed, status, and links to results stored in our object storage. We retain results for the period defined by your plan (typically 30 days).

**API keys** — when you generate an API key, we store a hashed version on our servers. The plaintext is shown to you once at creation and never stored in retrievable form afterwards.

**Operational logs** — request method, path, status code, latency, IP address, user agent, and request ID. Used for debugging, abuse prevention, capacity planning, and security incident response.

**Payment information** — handled by our payment processor (Stripe). We do not store full card numbers; we keep only the customer reference, plan, and the last four digits of the card for display.

**Cookies** — minimal session cookies for authentication and CSRF protection. We do not use third-party advertising cookies.

## 3. How we use your information

- Operate, maintain, and secure the Crawl4AI services
- Authenticate you and authorise API requests against your plan
- Bill and meter usage
- Notify you about service status, security issues, and material changes
- Improve product quality through aggregate, de-identified usage analysis
- Comply with legal obligations and respond to lawful requests

We do **not** sell your personal information. We do not use the contents of pages you crawl, the keywords you submit, or the results we extract for advertising or to train third-party machine-learning models.

## 4. Crawl4AI Workspace add-ons (Google Sheets, etc.)

Our Google Workspace add-ons run within your Google account using Apps Script. Specifically:

- **Sheet contents** — the add-on reads the active spreadsheet you have open and writes results back into the same spreadsheet. Sheet contents are sent to our API only as part of jobs you explicitly trigger (for example, by clicking "Generate Data"). Cell contents are not stored beyond the duration of the job.
- **API key storage** — the add-on stores your Crawl4AI API key in Google's per-user `PropertiesService`, which is encrypted at rest by Google and scoped to your Google account.
- **Email** — when granted, we read your Google account email address solely to display it in the sidebar so you know which account is in use.
- **Limited use** — we follow Google's [Limited Use Requirements](https://developers.google.com/terms/api-services-user-data-policy#additional_requirements_for_specific_api_scopes) for Workspace API data. We do not transfer Workspace data to third parties except as necessary to provide the user-facing feature, comply with applicable law, or as part of a merger / acquisition where successor entity is bound by an at-least-equally-protective policy. We do not use Workspace data for advertising, and we do not allow humans to read it except with your explicit permission, for security investigations, or to comply with applicable law.

## 5. How we share information

We share information only when needed to run the service:

- **Sub-processors** — we use a small set of vendors for hosting (Hetzner, AWS), object storage, transactional email (Postmark), payment processing (Stripe), error tracking, LLM inference (OpenAI, Anthropic, Google), and search (Serper). Each is bound by data-processing terms.
- **Legal compliance** — we may disclose information if required by law, subpoena, or to protect rights, property, or safety.
- **Business transfers** — if the service is acquired or merged, your information may transfer to the successor under an at-least-equally-protective policy.

## 6. Data retention

- Account information — kept while your account is active
- Job results and stored objects — retained per your plan, typically 30 days, then permanently deleted
- Operational logs — typically 90 days
- Billing records — kept for at least 7 years where required by tax law
- Deletion requests — see Section 9

## 7. Security

We use TLS in transit, encryption at rest for stored objects and database backups, scoped service credentials, network isolation, and least-privilege access controls. No system is perfectly secure; if we become aware of a breach affecting your data, we will notify you without undue delay.

## 8. International data transfers

We host primarily in the EU (Hetzner) and the US (AWS). When we transfer personal data across regions, we rely on standard contractual clauses or other legally recognised transfer mechanisms.

## 9. Your rights

Depending on where you live, you may have the right to:

- Access the personal data we hold about you
- Correct inaccurate data
- Delete your data ("right to be forgotten")
- Export your data in a portable format
- Object to or restrict certain processing
- Withdraw consent

To exercise any of these rights, email [unclecode@crawl4ai.com](mailto:unclecode@crawl4ai.com). We will respond within 30 days. We will not discriminate against you for exercising these rights.

## 10. Children

Our services are not directed to children under 16, and we do not knowingly collect personal information from them. If you believe a child has provided us personal information, contact us and we will delete it.

## 11. Changes to this Policy

We may update this Policy from time to time. Material changes will be announced via email and through an in-product notice at least 14 days before they take effect. The "Last updated" date at the top reflects the latest revision.

## 12. Contact

Questions, complaints, or requests:

**Crawl4AI**
38 Beach Road, #26-12, South Beach Tower, Singapore 189767
[unclecode@crawl4ai.com](mailto:unclecode@crawl4ai.com)
