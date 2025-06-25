# -*- coding: utf-8 -*-
"""
Background Tasks for ML Engine
==============================

Celery tasks for automated ML training and monitoring
"""

import logging
from datetime import datetime, timedelta

from celery import shared_task
from django.core.cache import cache
from django.db.models import Avg, Count, F
from django.utils import timezone

from complaints.models import Complaint, ComplaintCategory
from users.models import User

from .ml_engine import (
    get_incremental_model,
    get_nlp_processor,
    get_rl_agent,
    get_threshold_manager,
)

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def train_rl_agent_with_historical_data(self):
    """
    Otomatik RL agent eğitimi - geçmiş verilerle
    """
    try:
        rl_agent = get_rl_agent()

        # Get resolved complaints from last 30 days
        resolved_complaints = Complaint.objects.filter(
            status="RESOLVED",
            resolution_date__isnull=False,
            created_at__gte=timezone.now() - timedelta(days=30),
        ).order_by("created_at")

        if resolved_complaints.count() < 10:
            logger.warning("Not enough resolved complaints for RL training")
            return {
                "status": "skipped",
                "reason": "insufficient_data",
                "complaint_count": resolved_complaints.count(),
            }

        training_count = 0
        total_reward = 0

        for complaint in resolved_complaints[:200]:  # Limit to prevent timeout
            try:
                state = rl_agent.get_state(complaint)

                # Simulate action based on actual resolution
                resolution_time = (
                    complaint.resolution_date - complaint.created_at
                ).total_seconds() / 3600

                if resolution_time < 2:
                    action = "auto_resolve"
                elif resolution_time < 8:
                    action = "assign_to_expert"
                elif complaint.assigned_to:
                    action = "escalate_to_manager"
                else:
                    action = "request_more_info"

                # Calculate outcome
                outcome = {
                    "resolved_quickly": resolution_time < 24,
                    "customer_satisfaction": complaint.satisfaction_rating or 3,
                    "resolved_successfully": True,
                    "resolution_time_hours": resolution_time,
                }

                reward = rl_agent.get_reward(complaint, action, outcome)

                # Update Q-table
                next_state = ("RESOLVED", "COMPLETED", "DONE", "BUSINESS_HOURS")
                rl_agent.update_q_value(state, action, reward, next_state)

                training_count += 1
                total_reward += reward

            except Exception as e:
                logger.error(f"Error training on complaint {complaint.id}: {e}")
                continue

        # Save the trained model
        rl_agent._save_model()

        result = {
            "status": "completed",
            "training_count": training_count,
            "total_reward": total_reward,
            "average_reward": total_reward / max(1, training_count),
            "agent_episodes": rl_agent.episode_count,
            "exploration_rate": rl_agent.epsilon * 100,
            "trained_at": timezone.now().isoformat(),
        }

        # Cache the training result
        cache.set("last_rl_training_result", result, timeout=86400)

        logger.info(f"RL agent training completed: {result}")
        return result

    except Exception as e:
        logger.error(f"RL agent training failed: {e}")
        self.retry(countdown=60, exc=e)
        return {"status": "failed", "error": str(e)}


@shared_task(bind=True, max_retries=2)
def update_incremental_learning_model(self):
    """
    Artımlı öğrenme modeli güncelleme
    """
    try:
        incremental_model = get_incremental_model()

        # Get recent resolved complaints for incremental learning
        since_date = timezone.now() - timedelta(days=7)
        recent_complaints = Complaint.objects.filter(
            status="RESOLVED", resolution_date__isnull=False, created_at__gte=since_date
        )

        if recent_complaints.count() < 5:
            return {
                "status": "skipped",
                "reason": "insufficient_new_data",
                "complaint_count": recent_complaints.count(),
            }

        # Perform incremental training
        complaints_list = list(recent_complaints)
        incremental_model.partial_fit(complaints_list)

        result = {
            "status": "completed",
            "complaints_processed": len(complaints_list),
            "model_trained": incremental_model.is_trained,
            "feature_count": len(incremental_model.feature_names),
            "classes": incremental_model.classes,
            "updated_at": timezone.now().isoformat(),
        }

        cache.set("last_incremental_training_result", result, timeout=86400)

        logger.info(f"Incremental model update completed: {result}")
        return result

    except Exception as e:
        logger.error(f"Incremental model update failed: {e}")
        self.retry(countdown=60, exc=e)
        return {"status": "failed", "error": str(e)}


@shared_task(bind=True, max_retries=2)
def update_adaptive_thresholds_task(self):
    """
    Adaptive threshold'ları otomatik güncelleme
    """
    try:
        threshold_manager = get_threshold_manager()

        # Calculate current system metrics
        current_metrics = {
            "high_volume": Complaint.objects.filter(
                created_at__gte=timezone.now() - timedelta(hours=1)
            ).count(),
            "slow_resolution": Complaint.objects.filter(
                status="IN_PROGRESS",
                created_at__lte=timezone.now() - timedelta(hours=48),
            ).count(),
            "low_satisfaction": Complaint.objects.filter(
                satisfaction_rating__lt=3,
                created_at__gte=timezone.now() - timedelta(days=7),
            ).count(),
            "system_performance": 85,  # Would be calculated from actual system metrics
        }

        # Store old thresholds for comparison
        old_thresholds = threshold_manager.get_adaptive_thresholds().copy()

        # Update thresholds
        threshold_manager.update_thresholds(current_metrics)
        new_thresholds = threshold_manager.get_adaptive_thresholds()

        # Calculate changes
        threshold_changes = {}
        for metric in new_thresholds.keys():
            if metric in old_thresholds:
                change = new_thresholds[metric] - old_thresholds[metric]
                threshold_changes[metric] = {
                    "old_value": old_thresholds[metric],
                    "new_value": new_thresholds[metric],
                    "change": change,
                    "change_percent": (
                        (change / old_thresholds[metric] * 100)
                        if old_thresholds[metric] != 0
                        else 0
                    ),
                }

        result = {
            "status": "completed",
            "current_metrics": current_metrics,
            "threshold_changes": threshold_changes,
            "new_thresholds": new_thresholds,
            "updated_at": timezone.now().isoformat(),
        }

        cache.set("last_threshold_update_result", result, timeout=86400)

        logger.info(f"Adaptive thresholds updated: {result}")
        return result

    except Exception as e:
        logger.error(f"Adaptive threshold update failed: {e}")
        self.retry(countdown=60, exc=e)
        return {"status": "failed", "error": str(e)}


@shared_task(bind=True, max_retries=2)
def analyze_complaints_with_nlp(self):
    """
    NLP ile şikayet analizi yapma
    """
    try:
        nlp_processor = get_nlp_processor()

        # Get recent unprocessed complaints
        unprocessed_complaints = Complaint.objects.filter(
            created_at__gte=timezone.now() - timedelta(hours=24),
            description__isnull=False,
        ).exclude(description="")[:100]

        if not unprocessed_complaints:
            return {"status": "skipped", "reason": "no_unprocessed_complaints"}

        analysis_results = {
            "processed_count": 0,
            "category_predictions": {},
            "sentiment_distribution": {"positive": 0, "negative": 0, "neutral": 0},
            "anomalies_detected": 0,
            "high_confidence_predictions": 0,
        }

        for complaint in unprocessed_complaints:
            try:
                # Category prediction
                category_result = nlp_processor.predict_category(complaint.description)
                predicted_category = category_result.get(
                    "predicted_category", "Unknown"
                )
                confidence = category_result.get("confidence", 0)

                if predicted_category not in analysis_results["category_predictions"]:
                    analysis_results["category_predictions"][predicted_category] = 0
                analysis_results["category_predictions"][predicted_category] += 1

                if confidence > 0.8:
                    analysis_results["high_confidence_predictions"] += 1

                # Sentiment analysis
                sentiment_result = nlp_processor.predict_sentiment(
                    complaint.description
                )
                sentiment = sentiment_result.get("sentiment", "neutral")
                analysis_results["sentiment_distribution"][sentiment] += 1

                # Anomaly detection
                anomaly_result = nlp_processor.predict_anomaly(
                    complaint.description, complaint.submitter_id, complaint.created_at
                )

                if anomaly_result.get("is_anomaly", False):
                    analysis_results["anomalies_detected"] += 1

                    # Log high-severity anomalies
                    if anomaly_result.get("anomaly_score", 0) > 0.8:
                        logger.warning(
                            f"High-severity anomaly detected in complaint {complaint.id}: {anomaly_result}"
                        )

                analysis_results["processed_count"] += 1

            except Exception as e:
                logger.error(f"Error analyzing complaint {complaint.id}: {e}")
                continue

        result = {
            "status": "completed",
            "analysis_results": analysis_results,
            "analyzed_at": timezone.now().isoformat(),
        }

        cache.set("last_nlp_analysis_result", result, timeout=86400)

        logger.info(f"NLP analysis completed: {result}")
        return result

    except Exception as e:
        logger.error(f"NLP analysis failed: {e}")
        self.retry(countdown=60, exc=e)
        return {"status": "failed", "error": str(e)}


@shared_task(bind=True, max_retries=2)
def generate_ml_performance_report(self):
    """
    ML performans raporu oluşturma
    """
    try:
        rl_agent = get_rl_agent()
        threshold_manager = get_threshold_manager()
        incremental_model = get_incremental_model()

        # Get recent training results
        last_rl_training = cache.get("last_rl_training_result", {})
        last_incremental_training = cache.get("last_incremental_training_result", {})
        last_threshold_update = cache.get("last_threshold_update_result", {})
        last_nlp_analysis = cache.get("last_nlp_analysis_result", {})

        # Calculate performance metrics
        performance_report = {
            "report_generated_at": timezone.now().isoformat(),
            "rl_agent_performance": {
                "total_episodes": rl_agent.episode_count,
                "total_rewards": rl_agent.total_rewards,
                "average_reward": rl_agent.total_rewards
                / max(1, rl_agent.episode_count),
                "exploration_rate": rl_agent.epsilon * 100,
                "q_table_coverage": len(rl_agent.q_table),
                "last_training": last_rl_training,
            },
            "incremental_model_performance": {
                "is_trained": incremental_model.is_trained,
                "feature_count": len(incremental_model.feature_names),
                "supported_classes": incremental_model.classes,
                "last_update": last_incremental_training,
            },
            "adaptive_thresholds_performance": {
                "current_thresholds": threshold_manager.get_adaptive_thresholds(),
                "learning_rate": threshold_manager.learning_rate,
                "last_update": last_threshold_update,
            },
            "nlp_analysis_performance": {"last_analysis": last_nlp_analysis},
        }

        # Add system-wide ML statistics
        today = timezone.now().date()
        week_ago = timezone.now() - timedelta(days=7)

        ml_statistics = {
            "complaints_today": Complaint.objects.filter(
                created_at__date=today
            ).count(),
            "complaints_this_week": Complaint.objects.filter(
                created_at__gte=week_ago
            ).count(),
            "resolved_this_week": Complaint.objects.filter(
                status="RESOLVED", resolution_date__gte=week_ago
            ).count(),
            "average_resolution_time_hours": 0,
        }

        # Calculate average resolution time
        avg_resolution = Complaint.objects.filter(
            status="RESOLVED", resolution_date__isnull=False, created_at__gte=week_ago
        ).aggregate(avg_time=Avg(F("resolution_date") - F("created_at")))["avg_time"]

        if avg_resolution:
            ml_statistics["average_resolution_time_hours"] = (
                avg_resolution.total_seconds() / 3600
            )

        performance_report["system_statistics"] = ml_statistics

        # Cache the performance report
        cache.set(
            "ml_performance_report", performance_report, timeout=3600
        )  # 1 hour cache

        logger.info("ML performance report generated successfully")
        return performance_report

    except Exception as e:
        logger.error(f"ML performance report generation failed: {e}")
        self.retry(countdown=60, exc=e)
        return {"status": "failed", "error": str(e)}


@shared_task(bind=True, max_retries=2)
def cleanup_ml_cache(self):
    """
    ML cache temizleme görevi
    """
    try:
        cache_keys_to_cleanup = [
            "rl_agent_model",
            "adaptive_thresholds",
            "incremental_ml_model",
            "nlp_models",
            "last_rl_training_result",
            "last_incremental_training_result",
            "last_threshold_update_result",
            "last_nlp_analysis_result",
        ]

        cleaned_count = 0
        for key in cache_keys_to_cleanup:
            # Check if key exists and is older than 1 day
            cached_data = cache.get(key)
            if cached_data:
                # For model data, check last_updated field
                if isinstance(cached_data, dict) and "last_updated" in cached_data:
                    try:
                        last_updated = datetime.fromisoformat(
                            cached_data["last_updated"].replace("Z", "+00:00")
                        )
                        if (
                            timezone.now() - last_updated
                        ).total_seconds() > 86400:  # 24 hours
                            cache.delete(key)
                            cleaned_count += 1
                    except (ValueError, TypeError):
                        pass  # Skip if date parsing fails

        result = {
            "status": "completed",
            "cache_keys_cleaned": cleaned_count,
            "cleaned_at": timezone.now().isoformat(),
        }

        logger.info(f"ML cache cleanup completed: {result}")
        return result

    except Exception as e:
        logger.error(f"ML cache cleanup failed: {e}")
        return {"status": "failed", "error": str(e)}


# Periodic task scheduling helper
def schedule_ml_tasks():
    """
    Periyodik ML görevlerini zamanlama yardımcısı
    """
    from celery.schedules import crontab

    return {
        # Her 4 saatte bir RL agent training
        "train-rl-agent": {
            "task": "analytics.tasks.train_rl_agent_with_historical_data",
            "schedule": crontab(minute=0, hour="*/4"),
        },
        # Her 2 saatte bir incremental model update
        "update-incremental-model": {
            "task": "analytics.tasks.update_incremental_learning_model",
            "schedule": crontab(minute=30, hour="*/2"),
        },
        # Her saatte bir adaptive threshold update
        "update-adaptive-thresholds": {
            "task": "analytics.tasks.update_adaptive_thresholds_task",
            "schedule": crontab(minute=15),
        },
        # Her 30 dakikada bir NLP analysis
        "analyze-complaints-nlp": {
            "task": "analytics.tasks.analyze_complaints_with_nlp",
            "schedule": crontab(minute="*/30"),
        },
        # Günde bir kez performance report
        "generate-performance-report": {
            "task": "analytics.tasks.generate_ml_performance_report",
            "schedule": crontab(hour=6, minute=0),
        },
        # Günde bir kez cache cleanup
        "cleanup-ml-cache": {
            "task": "analytics.tasks.cleanup_ml_cache",
            "schedule": crontab(hour=2, minute=0),
        },
    }
