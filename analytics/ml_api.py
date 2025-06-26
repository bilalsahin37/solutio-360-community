# -*- coding: utf-8 -*-
"""
Machine Learning API for Solutio 360 PWA
========================================

REST API endpoints for ML Engine functionality
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List

from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from complaints.models import Complaint

from .ml_engine import (
    get_incremental_model,
    get_nlp_processor,
    get_rl_agent,
    get_threshold_manager,
)

logger = logging.getLogger(__name__)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def ml_engine_status(request):
    """
    Get ML Engine status and metrics
    """
    try:
        rl_agent = get_rl_agent()
        threshold_manager = get_threshold_manager()
        incremental_model = get_incremental_model()
        nlp_processor = get_nlp_processor()

        status_data = {
            "ml_engine_status": "active",
            "components": {
                "reinforcement_learning": {
                    "episodes_trained": rl_agent.episode_count,
                    "total_rewards": rl_agent.total_rewards,
                    "exploration_rate": rl_agent.epsilon * 100,
                    "q_table_size": len(rl_agent.q_table),
                    "status": "active",
                },
                "adaptive_thresholds": {
                    "current_thresholds": threshold_manager.get_adaptive_thresholds(),
                    "learning_rate": threshold_manager.learning_rate,
                    "status": "active",
                },
                "incremental_learning": {
                    "is_trained": incremental_model.is_trained,
                    "feature_count": len(incremental_model.feature_names),
                    "classes": incremental_model.classes,
                    "status": ("active" if incremental_model.is_trained else "training_needed"),
                },
                "nlp_processing": {
                    "status": "active",
                    "methods": [
                        "category_prediction",
                        "sentiment_analysis",
                        "anomaly_detection",
                    ],
                },
            },
            "last_updated": timezone.now().isoformat(),
        }

        return Response(status_data, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error getting ML engine status: {e}")
        return Response(
            {"error": "Failed to get ML engine status", "details": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def get_rl_recommendation(request):
    """
    Get RL agent recommendation for a complaint
    """
    try:
        complaint_id = request.data.get("complaint_id")
        if not complaint_id:
            return Response(
                {"error": "complaint_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            complaint = Complaint.objects.get(id=complaint_id)
        except Complaint.DoesNotExist:
            return Response({"error": "Complaint not found"}, status=status.HTTP_404_NOT_FOUND)

        rl_agent = get_rl_agent()
        recommendation = rl_agent.get_recommendation(complaint)

        # Add complaint context
        recommendation.update(
            {
                "complaint_id": complaint_id,
                "complaint_status": complaint.status,
                "complaint_priority": complaint.priority,
                "created_at": complaint.created_at.isoformat(),
            }
        )

        return Response(recommendation, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error getting RL recommendation: {e}")
        return Response(
            {"error": "Failed to get RL recommendation", "details": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def train_rl_agent(request):
    """
    Train RL agent with feedback
    """
    try:
        complaint_id = request.data.get("complaint_id")
        action_taken = request.data.get("action_taken")
        outcome = request.data.get("outcome", {})

        if not all([complaint_id, action_taken]):
            return Response(
                {"error": "complaint_id and action_taken are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            complaint = Complaint.objects.get(id=complaint_id)
        except Complaint.DoesNotExist:
            return Response({"error": "Complaint not found"}, status=status.HTTP_404_NOT_FOUND)

        rl_agent = get_rl_agent()

        # Get state and next state
        state = rl_agent.get_state(complaint)
        next_state = (
            "RESOLVED",
            "COMPLETED",
            "DONE",
            "BUSINESS_HOURS",
        )  # Assuming resolution

        # Calculate reward based on outcome
        default_outcome = {
            "resolved_quickly": outcome.get("resolved_quickly", False),
            "customer_satisfaction": outcome.get("customer_satisfaction", 3),
            "resolved_successfully": outcome.get("resolved_successfully", True),
            "resolution_time_hours": outcome.get("resolution_time_hours", 24),
        }

        reward = rl_agent.get_reward(complaint, action_taken, default_outcome)

        # Update Q-value
        rl_agent.update_q_value(state, action_taken, reward, next_state)

        return Response(
            {
                "message": "RL agent trained successfully",
                "training_data": {
                    "state": state,
                    "action": action_taken,
                    "reward": reward,
                    "episode_count": rl_agent.episode_count,
                    "total_rewards": rl_agent.total_rewards,
                },
            },
            status=status.HTTP_200_OK,
        )

    except Exception as e:
        logger.error(f"Error training RL agent: {e}")
        return Response(
            {"error": "Failed to train RL agent", "details": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def analyze_with_nlp(request):
    """
    Analyze text with NLP processor
    """
    try:
        text = request.data.get("text")
        analysis_type = request.data.get(
            "analysis_type", "all"
        )  # all, category, sentiment, anomaly

        if not text:
            return Response({"error": "text is required"}, status=status.HTTP_400_BAD_REQUEST)

        nlp_processor = get_nlp_processor()
        results = {}

        if analysis_type in ["all", "category"]:
            results["category"] = nlp_processor.predict_category(text)

        if analysis_type in ["all", "sentiment"]:
            results["sentiment"] = nlp_processor.predict_sentiment(text)

        if analysis_type in ["all", "anomaly"]:
            # For anomaly detection, we need additional parameters
            user_id = request.data.get("user_id", request.user.id)
            created_at = timezone.now()
            results["anomaly"] = nlp_processor.predict_anomaly(text, user_id, created_at)

        return Response(
            {
                "text": text,
                "analysis_type": analysis_type,
                "results": results,
                "analyzed_at": timezone.now().isoformat(),
            },
            status=status.HTTP_200_OK,
        )

    except Exception as e:
        logger.error(f"Error in NLP analysis: {e}")
        return Response(
            {"error": "Failed to analyze text", "details": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def update_incremental_model(request):
    """
    Update incremental model with new training data
    """
    try:
        # Get recent resolved complaints for training
        days_back = request.data.get("days_back", 7)
        min_complaints = request.data.get("min_complaints", 5)

        recent_complaints = Complaint.objects.filter(
            status="RESOLVED",
            resolution_date__isnull=False,
            created_at__gte=timezone.now() - timedelta(days=days_back),
        )

        if recent_complaints.count() < min_complaints:
            return Response(
                {
                    "error": f"Not enough training data. Need at least {min_complaints} resolved complaints."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        incremental_model = get_incremental_model()

        # Perform incremental training
        complaints_list = list(recent_complaints)
        incremental_model.partial_fit(complaints_list)

        return Response(
            {
                "message": "Incremental model updated successfully",
                "training_info": {
                    "complaints_processed": len(complaints_list),
                    "model_trained": incremental_model.is_trained,
                    "feature_count": len(incremental_model.feature_names),
                    "classes": incremental_model.classes,
                },
                "updated_at": timezone.now().isoformat(),
            },
            status=status.HTTP_200_OK,
        )

    except Exception as e:
        logger.error(f"Error updating incremental model: {e}")
        return Response(
            {"error": "Failed to update incremental model", "details": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_adaptive_thresholds(request):
    """
    Get current adaptive thresholds
    """
    try:
        threshold_manager = get_threshold_manager()
        current_thresholds = threshold_manager.get_adaptive_thresholds()

        # Get recent performance metrics
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
        }

        return Response(
            {
                "adaptive_thresholds": current_thresholds,
                "current_metrics": current_metrics,
                "threshold_status": {
                    metric: ("BREACH" if current_metrics.get(metric, 0) > threshold else "OK")
                    for metric, threshold in current_thresholds.items()
                    if metric in current_metrics
                },
                "learning_rate": threshold_manager.learning_rate,
                "last_updated": timezone.now().isoformat(),
            },
            status=status.HTTP_200_OK,
        )

    except Exception as e:
        logger.error(f"Error getting adaptive thresholds: {e}")
        return Response(
            {"error": "Failed to get adaptive thresholds", "details": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def update_adaptive_thresholds(request):
    """
    Manually trigger adaptive threshold update
    """
    try:
        threshold_manager = get_threshold_manager()

        # Get current performance metrics
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
            "system_performance": request.data.get(
                "system_performance", 85
            ),  # Can be provided by monitoring
        }

        # Store old thresholds for comparison
        old_thresholds = threshold_manager.get_adaptive_thresholds().copy()

        # Update thresholds
        threshold_manager.update_thresholds(current_metrics)
        new_thresholds = threshold_manager.get_adaptive_thresholds()

        # Calculate changes
        threshold_changes = {
            metric: {
                "old_value": old_thresholds.get(metric, 0),
                "new_value": new_thresholds.get(metric, 0),
                "change": new_thresholds.get(metric, 0) - old_thresholds.get(metric, 0),
            }
            for metric in new_thresholds.keys()
            if metric in old_thresholds
        }

        return Response(
            {
                "message": "Adaptive thresholds updated successfully",
                "threshold_changes": threshold_changes,
                "current_metrics": current_metrics,
                "new_thresholds": new_thresholds,
                "updated_at": timezone.now().isoformat(),
            },
            status=status.HTTP_200_OK,
        )

    except Exception as e:
        logger.error(f"Error updating adaptive thresholds: {e}")
        return Response(
            {"error": "Failed to update adaptive thresholds", "details": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_ml_insights(request):
    """
    Get comprehensive ML insights
    """
    try:
        # Get days parameter
        days_back = int(request.GET.get("days", 7))

        rl_agent = get_rl_agent()
        threshold_manager = get_threshold_manager()
        incremental_model = get_incremental_model()
        nlp_processor = get_nlp_processor()

        insights = {
            "rl_performance": {
                "episodes_trained": rl_agent.episode_count,
                "total_rewards": rl_agent.total_rewards,
                "average_reward": rl_agent.total_rewards / max(1, rl_agent.episode_count),
                "exploration_rate": rl_agent.epsilon * 100,
                "q_table_coverage": len(rl_agent.q_table),
            },
            "model_status": {
                "incremental_model_trained": incremental_model.is_trained,
                "feature_engineering": {
                    "feature_count": len(incremental_model.feature_names),
                    "features": incremental_model.feature_names,
                },
                "classification_classes": incremental_model.classes,
            },
            "threshold_intelligence": {
                "adaptive_thresholds": threshold_manager.get_adaptive_thresholds(),
                "learning_rate": threshold_manager.learning_rate,
                "performance_history_size": len(threshold_manager.performance_history),
            },
            "nlp_capabilities": {
                "available_methods": [
                    "category_prediction",
                    "sentiment_analysis",
                    "anomaly_detection",
                ],
                "language_support": ["Turkish", "English"],
                "rule_based_fallbacks": True,
            },
        }

        # Add recent complaint analysis
        recent_complaints = Complaint.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=days_back)
        )[:20]

        if recent_complaints:
            sample_analysis = []
            for complaint in recent_complaints[:5]:  # Sample 5 complaints
                analysis = {
                    "complaint_id": complaint.id,
                    "rl_recommendation": rl_agent.get_recommendation(complaint),
                    "ml_prediction": incremental_model.predict(complaint),
                }

                if complaint.description:
                    analysis.update(
                        {
                            "nlp_category": nlp_processor.predict_category(complaint.description),
                            "nlp_sentiment": nlp_processor.predict_sentiment(complaint.description),
                        }
                    )

                sample_analysis.append(analysis)

            insights["sample_analysis"] = sample_analysis

        return Response(
            {
                "insights": insights,
                "analysis_period_days": days_back,
                "generated_at": timezone.now().isoformat(),
            },
            status=status.HTTP_200_OK,
        )

    except Exception as e:
        logger.error(f"Error getting ML insights: {e}")
        return Response(
            {"error": "Failed to get ML insights", "details": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
