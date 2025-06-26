# ML Background Tasks
import logging
from datetime import timedelta

from django.utils import timezone

from celery import shared_task

from complaints.models import Complaint

from .ml_engine import get_incremental_model, get_rl_agent

logger = logging.getLogger(__name__)


@shared_task
def train_rl_agent():
    """Train RL agent with historical data"""
    try:
        rl_agent = get_rl_agent()
        resolved_complaints = Complaint.objects.filter(
            status="RESOLVED", created_at__gte=timezone.now() - timedelta(days=30)
        )[:100]

        training_count = 0
        for complaint in resolved_complaints:
            state = rl_agent.get_state(complaint)
            action = "assign_to_expert"  # Default action
            reward = 1.0  # Simple reward
            next_state = ("RESOLVED", "COMPLETED", "DONE", "BUSINESS_HOURS")

            rl_agent.update_q_value(state, action, reward, next_state)
            training_count += 1

        return {"status": "success", "trained_count": training_count}
    except Exception as e:
        logger.error(f"RL training failed: {e}")
        return {"status": "error", "message": str(e)}


@shared_task
def update_ml_models():
    """Update incremental ML models"""
    try:
        model = get_incremental_model()
        recent_complaints = Complaint.objects.filter(
            status="RESOLVED", created_at__gte=timezone.now() - timedelta(days=7)
        )

        if recent_complaints.exists():
            model.partial_fit(list(recent_complaints))
            return {"status": "success", "updated": True}

        return {"status": "success", "updated": False, "reason": "no_new_data"}
    except Exception as e:
        logger.error(f"Model update failed: {e}")
        return {"status": "error", "message": str(e)}
