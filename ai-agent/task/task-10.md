Task 10: Implement background worker for job processing
Description:
This task is to create the asynchronous background worker that processes jobs from the Redis queue. The worker will be designed to handle concurrent job execution within configurable limits. It will be responsible for orchestrating the entire crawl-extract-convert pipeline, updating the job status in Redis at each stage, and managing job failures gracefully. The worker must also support a graceful shutdown process to finish in-progress jobs.


10. Implement background worker for job processing
- Create BackgroundWorker class for async job processing
- Implement concurrent job execution with configurable limits
- Add job status updates throughout processing pipeline
- Create error handling and job failure management
- Implement graceful shutdown and job cleanup
- Write integration tests for worker functionality and concurrency
Requirements: 6.1, 6.2, 7.1, 7.2

**Globs:**
```
app/worker.py
app/services/job_processor.py
app/services/crawler.py
app/services/extractor.py
app/services/markdown_converter.py
```
