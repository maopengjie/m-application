import pytest
from unittest.mock import MagicMock, patch
from apscheduler.schedulers.background import BackgroundScheduler
from app.tasks.scheduler import SchedulerManager, LEADER_LOCK_KEY, INSTANCE_ID

@pytest.fixture
def mock_redis():
    mock = MagicMock()
    # Default is not leader
    mock.get.return_value = "other_instance"
    mock.set.return_value = False
    return mock

def test_scheduler_job_registration_parameters():
    mock_scheduler = MagicMock(spec=BackgroundScheduler)
    
    from app.tasks.jobs.alert_jobs import register_alert_jobs
    register_alert_jobs(mock_scheduler)
    
    # Verify alert job parameters
    args, kwargs = mock_scheduler.add_job.call_args
    assert kwargs["id"] == "alert-price-scan"
    assert kwargs["max_instances"] == 1
    assert kwargs["coalesce"] is True
    assert kwargs["misfire_grace_time"] == 30

def test_scheduler_leader_acquisition_starts_logic(mock_redis):
    with patch("app.tasks.scheduler.get_redis_client", return_value=mock_redis), \
         patch("app.tasks.scheduler.scheduler") as mock_sched:
        
        # 1. Mock becoming leader
        mock_redis.set.return_value = True
        mock_redis.get.return_value = INSTANCE_ID
        mock_sched.running = False
        
        # Execute one loop iteration logic
        SchedulerManager._leader_election_loop_iteration(mock_redis)
        
        # Verify
        assert SchedulerManager._is_leader is True
        assert mock_sched.start.called

def test_scheduler_leadership_loss_shutdowns_logic(mock_redis):
    with patch("app.tasks.scheduler.get_redis_client", return_value=mock_redis), \
         patch("app.tasks.scheduler.scheduler") as mock_sched:
        
        # 1. Start as leader
        SchedulerManager._is_leader = True
        mock_sched.running = True
        
        # 2. Lose leadership
        mock_redis.get.return_value = "different_instance"
        
        # Execute loop iteration
        SchedulerManager._leader_election_loop_iteration(mock_redis)
        
        # Verify
        assert SchedulerManager._is_leader is False
        assert mock_sched.shutdown.called
