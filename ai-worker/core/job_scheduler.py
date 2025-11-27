"""
Async Background Job Scheduler & Event Loop
Manages background tasks, scheduled jobs, and async operations
"""

import logging
import asyncio
from typing import Dict, Any, Optional, Callable, List, Coroutine
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import uuid

from core.errors import JobError, JobNotFoundError, JobCancelledError, JobTimeoutError

logger = logging.getLogger(__name__)


class JobStatus(str, Enum):
    """Job status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Job:
    """Background job"""
    id: str
    name: str
    func: Callable
    args: tuple
    kwargs: dict
    status: JobStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Any = None
    error: Optional[str] = None
    timeout: Optional[int] = None


class JobScheduler:
    """
    Async background job scheduler
    Manages background tasks and scheduled jobs
    """
    
    def __init__(self, loop: Optional[asyncio.AbstractEventLoop] = None):
        """
        Initialize job scheduler
        
        Args:
            loop: Event loop (creates new one if None)
        """
        self.loop = loop or asyncio.new_event_loop()
        self.jobs: Dict[str, Job] = {}
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self._shutdown = False
        
        logger.info("JobScheduler initialized")
    
    def submit_job(
        self,
        func: Callable,
        *args,
        name: Optional[str] = None,
        timeout: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Submit job for background execution
        
        Args:
            func: Function to execute (can be sync or async)
            *args: Positional arguments
            name: Job name
            timeout: Timeout in seconds
            **kwargs: Keyword arguments
        
        Returns:
            Job ID
        """
        job_id = str(uuid.uuid4())
        job_name = name or func.__name__
        
        job = Job(
            id=job_id,
            name=job_name,
            func=func,
            args=args,
            kwargs=kwargs,
            status=JobStatus.PENDING,
            created_at=datetime.now(),
            timeout=timeout
        )
        
        self.jobs[job_id] = job
        
        # Schedule job
        task = self.loop.create_task(self._execute_job(job_id))
        self.running_tasks[job_id] = task
        
        logger.info(f"Job submitted: {job_name} ({job_id})")
        
        return job_id
    
    async def _execute_job(self, job_id: str):
        """Execute job"""
        job = self.jobs[job_id]
        
        try:
            job.status = JobStatus.RUNNING
            job.started_at = datetime.now()
            
            logger.info(f"Job started: {job.name} ({job_id})")
            
            # Execute function
            if asyncio.iscoroutinefunction(job.func):
                # Async function
                if job.timeout:
                    result = await asyncio.wait_for(
                        job.func(*job.args, **job.kwargs),
                        timeout=job.timeout
                    )
                else:
                    result = await job.func(*job.args, **job.kwargs)
            else:
                # Sync function
                if job.timeout:
                    result = await asyncio.wait_for(
                        self.loop.run_in_executor(
                            None,
                            lambda: job.func(*job.args, **job.kwargs)
                        ),
                        timeout=job.timeout
                    )
                else:
                    result = await self.loop.run_in_executor(
                        None,
                        lambda: job.func(*job.args, **job.kwargs)
                    )
            
            job.result = result
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.now()
            
            logger.info(f"Job completed: {job.name} ({job_id})")
        
        except asyncio.CancelledError:
            job.status = JobStatus.CANCELLED
            job.completed_at = datetime.now()
            logger.warning(f"Job cancelled: {job.name} ({job_id})")
        
        except asyncio.TimeoutError:
            job.status = JobStatus.FAILED
            job.error = f"Timeout after {job.timeout}s"
            job.completed_at = datetime.now()
            logger.error(f"Job timeout: {job.name} ({job_id})")
        
        except Exception as e:
            job.status = JobStatus.FAILED
            job.error = str(e)
            job.completed_at = datetime.now()
            logger.error(f"Job failed: {job.name} ({job_id}) - {e}")
        
        finally:
            # Cleanup
            if job_id in self.running_tasks:
                del self.running_tasks[job_id]
    
    def get_job(self, job_id: str) -> Job:
        """
        Get job by ID
        
        Args:
            job_id: Job identifier
        
        Returns:
            Job object
        
        Raises:
            JobNotFoundError: If job not found
        """
        if job_id not in self.jobs:
            raise JobNotFoundError(f"Job not found: {job_id}")
        
        return self.jobs[job_id]
    
    def get_job_status(self, job_id: str) -> JobStatus:
        """Get job status"""
        job = self.get_job(job_id)
        return job.status
    
    def get_job_result(self, job_id: str) -> Any:
        """
        Get job result
        
        Args:
            job_id: Job identifier
        
        Returns:
            Job result
        
        Raises:
            JobError: If job not completed or failed
        """
        job = self.get_job(job_id)
        
        if job.status == JobStatus.PENDING or job.status == JobStatus.RUNNING:
            raise JobError(f"Job not completed: {job_id}")
        
        if job.status == JobStatus.FAILED:
            raise JobError(f"Job failed: {job.error}")
        
        if job.status == JobStatus.CANCELLED:
            raise JobCancelledError(f"Job was cancelled: {job_id}")
        
        return job.result
    
    async def wait_for_job(
        self,
        job_id: str,
        timeout: Optional[int] = None
    ) -> Any:
        """
        Wait for job to complete
        
        Args:
            job_id: Job identifier
            timeout: Timeout in seconds
        
        Returns:
            Job result
        """
        if job_id not in self.running_tasks:
            # Job already completed
            return self.get_job_result(job_id)
        
        task = self.running_tasks[job_id]
        
        try:
            if timeout:
                await asyncio.wait_for(task, timeout=timeout)
            else:
                await task
        except asyncio.TimeoutError:
            raise JobTimeoutError(f"Job wait timeout: {job_id}")
        
        return self.get_job_result(job_id)
    
    def cancel_job(self, job_id: str):
        """
        Cancel running job
        
        Args:
            job_id: Job identifier
        """
        if job_id in self.running_tasks:
            task = self.running_tasks[job_id]
            task.cancel()
            logger.info(f"Job cancelled: {job_id}")
    
    def list_jobs(
        self,
        status: Optional[JobStatus] = None
    ) -> List[Dict[str, Any]]:
        """
        List all jobs
        
        Args:
            status: Filter by status
        
        Returns:
            List of job dictionaries
        """
        jobs = []
        
        for job in self.jobs.values():
            if status is None or job.status == status:
                jobs.append({
                    "id": job.id,
                    "name": job.name,
                    "status": job.status,
                    "created_at": job.created_at.isoformat(),
                    "started_at": job.started_at.isoformat() if job.started_at else None,
                    "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                    "error": job.error
                })
        
        return jobs
    
    def cleanup_completed_jobs(self, max_age_hours: int = 24):
        """
        Remove old completed jobs
        
        Args:
            max_age_hours: Maximum age in hours
        """
        cutoff = datetime.now() - timedelta(hours=max_age_hours)
        
        to_remove = []
        for job_id, job in self.jobs.items():
            if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                if job.completed_at and job.completed_at < cutoff:
                    to_remove.append(job_id)
        
        for job_id in to_remove:
            del self.jobs[job_id]
        
        if to_remove:
            logger.info(f"Cleaned up {len(to_remove)} old jobs")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get scheduler statistics"""
        stats = {
            "total_jobs": len(self.jobs),
            "pending": 0,
            "running": 0,
            "completed": 0,
            "failed": 0,
            "cancelled": 0
        }
        
        for job in self.jobs.values():
            if job.status == JobStatus.PENDING:
                stats["pending"] += 1
            elif job.status == JobStatus.RUNNING:
                stats["running"] += 1
            elif job.status == JobStatus.COMPLETED:
                stats["completed"] += 1
            elif job.status == JobStatus.FAILED:
                stats["failed"] += 1
            elif job.status == JobStatus.CANCELLED:
                stats["cancelled"] += 1
        
        return stats
    
    async def shutdown(self):
        """Shutdown scheduler and cancel all running jobs"""
        self._shutdown = True
        
        logger.info("Shutting down job scheduler...")
        
        # Cancel all running tasks
        for job_id, task in list(self.running_tasks.items()):
            task.cancel()
        
        # Wait for all tasks to complete
        if self.running_tasks:
            await asyncio.gather(*self.running_tasks.values(), return_exceptions=True)
        
        logger.info("Job scheduler shutdown complete")


# Global scheduler instance
_global_scheduler: Optional[JobScheduler] = None


def get_job_scheduler() -> JobScheduler:
    """Get global job scheduler instance"""
    global _global_scheduler
    if _global_scheduler is None:
        _global_scheduler = JobScheduler()
    return _global_scheduler


if __name__ == "__main__":
    # Test job scheduler
    import time
    
    async def test():
        print("Testing Job Scheduler")
        print("=" * 50)
        
        scheduler = JobScheduler()
        
        # Test async job
        async def async_task(x):
            await asyncio.sleep(1)
            return x * 2
        
        job_id = scheduler.submit_job(async_task, 5, name="async_test")
        print(f"Submitted job: {job_id}")
        
        result = await scheduler.wait_for_job(job_id)
        print(f"Result: {result}")
        
        # Test sync job
        def sync_task(x):
            time.sleep(1)
            return x + 10
        
        job_id2 = scheduler.submit_job(sync_task, 5, name="sync_test")
        result2 = await scheduler.wait_for_job(job_id2)
        print(f"Result: {result2}")
        
        # Test stats
        stats = scheduler.get_stats()
        print(f"\nStats: {stats}")
        
        print("=" * 50)
    
    asyncio.run(test())
