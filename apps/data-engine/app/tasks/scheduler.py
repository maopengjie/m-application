import logging
import threading
import time
import socket
import os
from contextlib import suppress

from apscheduler.schedulers.background import BackgroundScheduler

from app.tasks.jobs.alert_jobs import register_alert_jobs
from app.tasks.jobs.crawler_jobs import register_crawler_jobs
from app.tasks.jobs.price_jobs import register_price_jobs
from app.core.redis import get_redis_client

logger = logging.getLogger(__name__)
scheduler = BackgroundScheduler()

# Distributed Leader Election Config
LEADER_LOCK_KEY = "scheduler:leader_lock"
LOCK_TTL_SECONDS = 30
LOCK_RENEW_SECONDS = 10
INSTANCE_ID = f"{socket.gethostname()}_{os.getpid()}"

class SchedulerManager:
    _stop_event = threading.Event()
    _heartbeat_thread: threading.Thread | None = None
    _is_leader = False

    @classmethod
    def start(cls):
        if cls._heartbeat_thread and cls._heartbeat_thread.is_alive():
            return
        
        cls._stop_event.clear()
        cls._heartbeat_thread = threading.Thread(target=cls._leader_election_loop, daemon=True)
        cls._heartbeat_thread.start()
        logger.info(f"Leader election manager initialized for instance {INSTANCE_ID}")

    @classmethod
    def stop(cls):
        cls._stop_event.set()
        if cls._heartbeat_thread:
            cls._heartbeat_thread.join(timeout=5)
        cls._shutdown_scheduler()

    @classmethod
    def _leader_election_loop(cls):
        redis = get_redis_client()
        while not cls._stop_event.is_set():
            cls._leader_election_loop_iteration(redis)
            time.sleep(LOCK_RENEW_SECONDS)

    @classmethod
    def _leader_election_loop_iteration(cls, redis):
        try:
            # Try to acquire or renew the lock
            acquired = redis.set(
                LEADER_LOCK_KEY, 
                INSTANCE_ID, 
                ex=LOCK_TTL_SECONDS, 
                nx=not cls._is_leader, # NX if not current leader, XX to renew
                px=None
            )
            
            # If we are renewal (XX), we use a different path in some redis clients, 
            # but standard set with ex and value checks works too.
            current_leader = redis.get(LEADER_LOCK_KEY)
            
            if current_leader == INSTANCE_ID:
                # We are the leader or just renewed
                redis.expire(LEADER_LOCK_KEY, LOCK_TTL_SECONDS)
                if not cls._is_leader:
                    cls._is_leader = True
                    cls._start_scheduler_logic()
            else:
                # Someone else is leader
                if cls._is_leader:
                    logger.warning(f"Leadership lost to {current_leader}. Stopping scheduler.")
                    cls._is_leader = False
                    cls._shutdown_scheduler()
                
        except Exception as e:
            logger.error(f"Leader election error: {e}")
            if cls._is_leader:
                # In case of Redis outage, be safe and stop
                cls._is_leader = False
                cls._shutdown_scheduler()

    @classmethod
    def _start_scheduler_logic(cls):
        if scheduler.running:
            return
        logger.info(f"Instance {INSTANCE_ID} acquired leadership. Starting scheduler...")
        register_crawler_jobs(scheduler)
        register_price_jobs(scheduler)
        register_alert_jobs(scheduler)
        scheduler.start()

    @classmethod
    def _shutdown_scheduler(cls):
        with suppress(Exception):
            if scheduler.running:
                # Removing all jobs to prevent double execution if we regain leadership 
                # (registering them again in _start_scheduler_logic)
                scheduler.remove_all_jobs()
                scheduler.shutdown(wait=False)
                logger.info("Scheduler shut down successfully.")

def start_scheduler() -> None:
    SchedulerManager.start()

def stop_scheduler() -> None:
    SchedulerManager.stop()
