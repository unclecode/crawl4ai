### Task 5: Implement job queue management system

**Description:**

```
This task is to build the core job queuing system using Redis. We will create a `JobQueueManager` class that:
- Manages the Redis-based job queue according to the defined schema.
- Handles job status tracking and updates (`pending` -> `processing` -> `completed`/`failed`).
- Implements priority queuing by user tier (e.g., separate lists like `queue:pending:enterprise`, `queue:pending:pro`).
- Provides the complete job lifecycle management logic.
```

5. Implement job queue management system

- Create JobQueueManager class for Redis-based job queuing
- Implement job creation, status tracking, and result storage
- Add priority queuing based on user tier (free, pro, enterprise)
- Create job lifecycle management (pending → processing → completed/failed)
- Implement queue depth monitoring and overflow handling
- Write unit tests for queue operations and priority handling
  Requirements: 6.1, 6.2, 6.3, 6.4

**Globs:**

```
app/services/job_queue.py
app/models/job.py
tests/services/test_job_queue.py
```
