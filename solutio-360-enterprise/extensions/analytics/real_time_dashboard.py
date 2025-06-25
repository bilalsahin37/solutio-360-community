# -*- coding: utf-8 -*-
"""
Real-time Analytics Dashboard for Solutio 360 PWA
=================================================

AI-powered real-time analytics inspired by:
- Netflix's analytics platform
- Spotify's real-time dashboard
- Uber's surge analytics
- Airbnb's data science platform
"""

import asyncio
import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.core.cache import cache
from django.db import connection
from django.db.models import Avg, Count, F, Q
from django.utils import timezone
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from complaints.models import Complaint, ComplaintCategory
from users.models import User

from .ml_engine import (
    get_incremental_model,
    get_nlp_processor,
    get_rl_agent,
    get_threshold_manager,
)


@dataclass
class MetricSnapshot:
    """Data class for metric snapshots"""

    timestamp: datetime
    value: float
    metric_name: str
    metadata: Dict[str, Any] = None


class RealTimeMetrics:
    """
    Real-time metrics collector and processor
    """

    def __init__(self):
        self.cache_timeout = 60  # 1 minute cache

    async def get_live_metrics(self) -> Dict[str, Any]:
        """
        Get comprehensive live metrics
        """
        metrics = await asyncio.gather(
            self.get_complaint_metrics(),
            self.get_user_activity_metrics(),
            self.get_performance_metrics(),
            self.get_ai_insights(),
            return_exceptions=True,
        )

        return {
            "complaint_metrics": metrics[0],
            "user_activity": metrics[1],
            "performance": metrics[2],
            "ai_insights": metrics[3],
            "timestamp": timezone.now().isoformat(),
        }

    @database_sync_to_async
    def get_complaint_metrics(self) -> Dict[str, Any]:
        """
        Get real-time complaint metrics
        """
        now = timezone.now()
        today = now.date()
        this_week = now - timedelta(days=7)
        this_month = now - timedelta(days=30)

        # Basic counts
        total_complaints = Complaint.objects.count()
        today_complaints = Complaint.objects.filter(created_at__date=today).count()

        # Status distribution
        status_distribution = dict(
            Complaint.objects.values("status")
            .annotate(count=Count("id"))
            .values_list("status", "count")
        )

        # Priority distribution
        priority_distribution = dict(
            Complaint.objects.values("priority")
            .annotate(count=Count("id"))
            .values_list("priority", "count")
        )

        # Resolution rate
        resolved_this_week = Complaint.objects.filter(
            resolution_date__gte=this_week, status="RESOLVED"
        ).count()

        submitted_this_week = Complaint.objects.filter(
            created_at__gte=this_week
        ).count()

        resolution_rate = (
            (resolved_this_week / submitted_this_week * 100)
            if submitted_this_week > 0
            else 0
        )

        # Average resolution time
        avg_resolution_time = Complaint.objects.filter(
            status="RESOLVED", resolution_date__isnull=False
        ).aggregate(avg_time=Avg(F("resolution_date") - F("created_at")))["avg_time"]

        # Trending categories
        trending_categories = list(
            Complaint.objects.filter(created_at__gte=this_week)
            .values("category__name")
            .annotate(count=Count("id"))
            .order_by("-count")[:5]
        )

        return {
            "totals": {
                "total_complaints": total_complaints,
                "today_complaints": today_complaints,
                "resolution_rate": round(resolution_rate, 2),
                "avg_resolution_hours": (
                    avg_resolution_time.total_seconds() / 3600
                    if avg_resolution_time
                    else 0
                ),
            },
            "distributions": {
                "status": status_distribution,
                "priority": priority_distribution,
            },
            "trending": {"categories": trending_categories},
        }

    @database_sync_to_async
    def get_user_activity_metrics(self) -> Dict[str, Any]:
        """
        Get real-time user activity metrics
        """
        now = timezone.now()
        last_hour = now - timedelta(hours=1)
        today = now.date()

        # Active users
        active_users_hour = User.objects.filter(last_login__gte=last_hour).count()

        active_users_today = User.objects.filter(last_login__date=today).count()

        # User registration trend
        new_users_today = User.objects.filter(date_joined__date=today).count()

        # Activity heatmap data
        activity_by_hour = []
        for hour in range(24):
            hour_start = now.replace(hour=hour, minute=0, second=0)
            hour_end = hour_start + timedelta(hours=1)

            activity_count = Complaint.objects.filter(
                created_at__range=(hour_start, hour_end), created_at__date=today
            ).count()

            activity_by_hour.append({"hour": hour, "activity": activity_count})

        return {
            "active_users": {
                "last_hour": active_users_hour,
                "today": active_users_today,
            },
            "registrations": {"today": new_users_today},
            "activity_pattern": activity_by_hour,
        }

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get system performance metrics
        """
        # Database query performance
        slow_queries = await self._get_slow_queries()

        # Cache hit rate
        cache_stats = await self._get_cache_statistics()

        # Memory usage (would require system monitoring)
        memory_usage = await self._get_memory_usage()

        return {
            "database": {
                "slow_queries": len(slow_queries),
                "connection_count": await self._get_db_connections(),
            },
            "cache": cache_stats,
            "memory": memory_usage,
        }

    async def get_ai_insights(self) -> Dict[str, Any]:
        """
        Generate AI-powered insights using ML Engine
        """
        insights = []

        # Get ML engine instances
        rl_agent = get_rl_agent()
        threshold_manager = get_threshold_manager()
        incremental_model = get_incremental_model()
        nlp_processor = get_nlp_processor()

        # Anomaly detection with enhanced ML
        anomalies = await self._detect_anomalies_ml()
        if anomalies:
            insights.extend(anomalies)

        # Reinforcement Learning insights
        rl_insights = await self._get_rl_insights()
        if rl_insights:
            insights.extend(rl_insights)

        # Adaptive threshold insights
        threshold_insights = await self._get_threshold_insights()
        if threshold_insights:
            insights.extend(threshold_insights)

        # Predictive analytics with incremental learning
        predictions = await self._generate_ml_predictions()
        if predictions:
            insights.extend(predictions)

        # NLP-based trend analysis
        nlp_trends = await self._analyze_nlp_trends()
        if nlp_trends:
            insights.extend(nlp_trends)

        return {
            "insights": insights,
            "generated_at": timezone.now().isoformat(),
            "ml_engine_status": {
                "rl_agent_episodes": rl_agent.episode_count,
                "incremental_model_trained": incremental_model.is_trained,
                "adaptive_thresholds": threshold_manager.get_adaptive_thresholds(),
            },
        }

    @database_sync_to_async
    def _get_slow_queries(self):
        """Get slow database queries"""
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT query, calls, total_time, mean_time
                FROM pg_stat_statements 
                WHERE mean_time > 100  -- queries slower than 100ms
                ORDER BY total_time DESC 
                LIMIT 5;
            """
            )
            return cursor.fetchall()

    async def _get_cache_statistics(self):
        """Get cache performance statistics"""
        # This would be implemented based on your cache backend
        return {
            "hit_rate": 85.5,  # Mock data
            "miss_rate": 14.5,
            "memory_usage": "45MB",
        }

    async def _get_memory_usage(self):
        """Get memory usage statistics"""
        # This would integrate with system monitoring
        return {"used_mb": 512, "total_mb": 2048, "percentage": 25}

    async def _get_db_connections(self):
        """Get database connection count"""
        return 15  # Mock data

    @database_sync_to_async
    def _detect_anomalies(self) -> List[Dict[str, Any]]:
        """
        Detect anomalies in complaint patterns using ML
        """
        try:
            # Get recent complaint data
            complaints_data = list(
                Complaint.objects.filter(
                    created_at__gte=timezone.now() - timedelta(days=30)
                )
                .values("created_at__hour", "priority", "category_id")
                .annotate(count=Count("id"))
            )

            if not complaints_data:
                return []

            # Prepare data for ML
            df = pd.DataFrame(complaints_data)
            features = ["created_at__hour", "count"]

            if len(df) < 10:  # Need minimum data points
                return []

            # Isolation Forest for anomaly detection
            iso_forest = IsolationForest(contamination=0.1, random_state=42)
            anomalies = iso_forest.fit_predict(df[features])

            # Find anomalous patterns
            anomaly_insights = []
            for idx, is_anomaly in enumerate(anomalies):
                if is_anomaly == -1:  # Anomaly detected
                    row = df.iloc[idx]
                    anomaly_insights.append(
                        {
                            "type": "anomaly",
                            "severity": "medium",
                            "title": f"Unusual complaint pattern detected",
                            "description": f'Abnormal number of complaints ({row["count"]}) at hour {row["created_at__hour"]}',
                            "timestamp": timezone.now().isoformat(),
                        }
                    )

            return anomaly_insights

        except Exception as e:
            return [
                {
                    "type": "error",
                    "severity": "low",
                    "title": "Anomaly detection unavailable",
                    "description": f"ML analysis failed: {str(e)}",
                }
            ]

    @database_sync_to_async
    def _generate_predictions(self) -> List[Dict[str, Any]]:
        """
        Generate predictive insights
        """
        predictions = []

        # Predict peak hours
        current_hour = timezone.now().hour
        historical_data = Complaint.objects.filter(
            created_at__hour=current_hour,
            created_at__gte=timezone.now() - timedelta(days=7),
        ).count()

        if historical_data > 10:  # Threshold for prediction
            predictions.append(
                {
                    "type": "prediction",
                    "severity": "info",
                    "title": "High complaint volume expected",
                    "description": f"Based on historical data, expect {historical_data} complaints in the next hour",
                    "confidence": 75,
                }
            )

        return predictions

    @database_sync_to_async
    def _analyze_trends(self) -> List[Dict[str, Any]]:
        """
        Analyze trending patterns
        """
        trends = []

        # Category trends
        week_ago = timezone.now() - timedelta(days=7)
        two_weeks_ago = timezone.now() - timedelta(days=14)

        current_week_cats = dict(
            Complaint.objects.filter(created_at__gte=week_ago)
            .values("category__name")
            .annotate(count=Count("id"))
            .values_list("category__name", "count")
        )

        previous_week_cats = dict(
            Complaint.objects.filter(created_at__range=(two_weeks_ago, week_ago))
            .values("category__name")
            .annotate(count=Count("id"))
            .values_list("category__name", "count")
        )

        for category, current_count in current_week_cats.items():
            previous_count = previous_week_cats.get(category, 0)
            if previous_count > 0:
                change_percent = (
                    (current_count - previous_count) / previous_count
                ) * 100
                if abs(change_percent) > 25:  # Significant change
                    trend_direction = "increase" if change_percent > 0 else "decrease"
                    trends.append(
                        {
                            "type": "trend",
                            "severity": "medium" if abs(change_percent) > 50 else "low",
                            "title": f"{category} complaints {trend_direction}",
                            "description": f"{abs(change_percent):.1f}% {trend_direction} compared to last week",
                            "category": category,
                            "change_percent": change_percent,
                        }
                    )

        return trends

    @database_sync_to_async
    def _detect_anomalies_ml(self) -> List[Dict[str, Any]]:
        """
        Enhanced anomaly detection using ML Engine
        """
        try:
            nlp_processor = get_nlp_processor()
            anomaly_insights = []

            # Get recent complaints for anomaly analysis
            recent_complaints = Complaint.objects.filter(
                created_at__gte=timezone.now() - timedelta(hours=24)
            ).order_by("-created_at")[:100]

            for complaint in recent_complaints:
                # Use NLP processor for advanced anomaly detection
                anomaly_result = nlp_processor.predict_anomaly(
                    complaint.description or "",
                    complaint.submitter_id,
                    complaint.created_at,
                )

                if anomaly_result.get("is_anomaly", False):
                    anomaly_insights.append(
                        {
                            "type": "ml_anomaly",
                            "severity": (
                                "high"
                                if anomaly_result["anomaly_score"] > 0.8
                                else "medium"
                            ),
                            "title": f"Suspicious complaint detected (ID: {complaint.id})",
                            "description": f"Anomaly score: {anomaly_result['anomaly_score']:.2f}. Reasons: {', '.join(anomaly_result.get('reasons', []))}",
                            "timestamp": complaint.created_at.isoformat(),
                            "complaint_id": complaint.id,
                        }
                    )

            return anomaly_insights[:5]  # Limit to top 5 anomalies

        except Exception as e:
            return [
                {
                    "type": "error",
                    "severity": "low",
                    "title": "ML Anomaly detection unavailable",
                    "description": f"Advanced ML analysis failed: {str(e)}",
                }
            ]

    @database_sync_to_async
    def _get_rl_insights(self) -> List[Dict[str, Any]]:
        """
        Get insights from Reinforcement Learning agent
        """
        try:
            rl_agent = get_rl_agent()
            insights = []

            # Get recent unresolved complaints for RL recommendations
            unresolved_complaints = Complaint.objects.filter(
                status__in=["SUBMITTED", "IN_PROGRESS"]
            ).order_by("-priority", "created_at")[:10]

            high_confidence_recommendations = 0
            total_recommendations = 0

            for complaint in unresolved_complaints:
                recommendation = rl_agent.get_recommendation(complaint)
                total_recommendations += 1

                if recommendation.get("confidence", 0) > 80:
                    high_confidence_recommendations += 1
                    insights.append(
                        {
                            "type": "rl_recommendation",
                            "severity": "info",
                            "title": f"High-confidence action recommended",
                            "description": f"Complaint {complaint.id}: {recommendation['recommended_action']} (confidence: {recommendation['confidence']:.1f}%)",
                            "complaint_id": complaint.id,
                            "recommended_action": recommendation["recommended_action"],
                            "confidence": recommendation["confidence"],
                        }
                    )

            # Overall RL performance insight
            if total_recommendations > 0:
                confidence_rate = (
                    high_confidence_recommendations / total_recommendations
                ) * 100
                insights.append(
                    {
                        "type": "rl_performance",
                        "severity": "info",
                        "title": f"RL Agent Performance Update",
                        "description": f"Agent confidence rate: {confidence_rate:.1f}% ({high_confidence_recommendations}/{total_recommendations} high-confidence predictions)",
                        "metrics": {
                            "episodes_trained": rl_agent.episode_count,
                            "total_rewards": rl_agent.total_rewards,
                            "exploration_rate": rl_agent.epsilon * 100,
                        },
                    }
                )

            return insights[:3]  # Limit insights

        except Exception as e:
            return [
                {
                    "type": "error",
                    "severity": "low",
                    "title": "RL insights unavailable",
                    "description": f"Reinforcement learning analysis failed: {str(e)}",
                }
            ]

    @database_sync_to_async
    def _get_threshold_insights(self) -> List[Dict[str, Any]]:
        """
        Get insights from Adaptive Threshold Manager
        """
        try:
            threshold_manager = get_threshold_manager()
            insights = []

            # Get current system metrics
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

            # Update thresholds based on current metrics
            threshold_manager.update_thresholds(current_metrics)
            current_thresholds = threshold_manager.get_adaptive_thresholds()

            # Check for threshold breaches
            for metric_name, current_value in current_metrics.items():
                if metric_name in current_thresholds:
                    threshold = current_thresholds[metric_name]
                    if current_value > threshold:
                        severity = (
                            "high" if current_value > threshold * 1.5 else "medium"
                        )
                        insights.append(
                            {
                                "type": "threshold_breach",
                                "severity": severity,
                                "title": f"Adaptive threshold exceeded: {metric_name}",
                                "description": f"Current: {current_value}, Threshold: {threshold:.1f} (adaptive)",
                                "metric": metric_name,
                                "current_value": current_value,
                                "threshold": threshold,
                            }
                        )

            # Threshold adjustment notifications
            if (
                hasattr(threshold_manager, "adjustment_history")
                and threshold_manager.adjustment_history
            ):
                recent_adjustments = [
                    adj
                    for adj in threshold_manager.adjustment_history
                    if adj["timestamp"] > timezone.now() - timedelta(hours=1)
                ]

                for adjustment in recent_adjustments[-2:]:  # Last 2 adjustments
                    insights.append(
                        {
                            "type": "threshold_adjustment",
                            "severity": "info",
                            "title": f"Threshold auto-adjusted: {adjustment['metric']}",
                            "description": f"Adjusted from {adjustment['old_value']:.1f} to {adjustment['new_value']:.1f}",
                            "reason": adjustment.get(
                                "reason", "performance_optimization"
                            ),
                        }
                    )

            return insights

        except Exception as e:
            return [
                {
                    "type": "error",
                    "severity": "low",
                    "title": "Adaptive threshold insights unavailable",
                    "description": f"Threshold analysis failed: {str(e)}",
                }
            ]

    @database_sync_to_async
    def _generate_ml_predictions(self) -> List[Dict[str, Any]]:
        """
        Generate predictions using Incremental ML Model
        """
        try:
            incremental_model = get_incremental_model()
            predictions = []

            # Get recent unresolved complaints for prediction
            unresolved_complaints = Complaint.objects.filter(
                status__in=["SUBMITTED", "IN_PROGRESS"]
            ).order_by("-created_at")[:5]

            for complaint in unresolved_complaints:
                prediction_result = incremental_model.predict(complaint)

                if prediction_result.get("confidence", 0) > 0.6:
                    predictions.append(
                        {
                            "type": "ml_prediction",
                            "severity": "info",
                            "title": f"Resolution prediction for complaint {complaint.id}",
                            "description": f"Predicted category: {prediction_result['prediction']} (confidence: {prediction_result['confidence']:.1f})",
                            "complaint_id": complaint.id,
                            "prediction": prediction_result["prediction"],
                            "confidence": prediction_result["confidence"],
                        }
                    )

            # Model performance insight
            if incremental_model.is_trained:
                predictions.append(
                    {
                        "type": "ml_model_status",
                        "severity": "info",
                        "title": "Incremental ML Model Status",
                        "description": f"Model trained and active. Ready for real-time learning.",
                        "model_info": {
                            "is_trained": incremental_model.is_trained,
                            "feature_count": len(incremental_model.feature_names),
                            "classes": incremental_model.classes,
                        },
                    }
                )
            else:
                predictions.append(
                    {
                        "type": "ml_model_warning",
                        "severity": "medium",
                        "title": "ML Model Not Trained",
                        "description": "Incremental learning model needs training data. Feed resolved complaints to improve predictions.",
                    }
                )

            return predictions

        except Exception as e:
            return [
                {
                    "type": "error",
                    "severity": "low",
                    "title": "ML predictions unavailable",
                    "description": f"Incremental learning prediction failed: {str(e)}",
                }
            ]

    @database_sync_to_async
    def _analyze_nlp_trends(self) -> List[Dict[str, Any]]:
        """
        Analyze trends using NLP processing
        """
        try:
            nlp_processor = get_nlp_processor()
            trends = []

            # Get recent complaints for NLP analysis
            recent_complaints = (
                Complaint.objects.filter(
                    created_at__gte=timezone.now() - timedelta(days=7)
                )
                .exclude(description__isnull=True)
                .exclude(description="")[:50]
            )

            # Sentiment analysis trends
            sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}
            category_predictions = {}

            for complaint in recent_complaints:
                # Sentiment analysis
                sentiment_result = nlp_processor.predict_sentiment(
                    complaint.description
                )
                sentiment = sentiment_result.get("sentiment", "neutral")
                sentiment_counts[sentiment] += 1

                # Category prediction
                category_result = nlp_processor.predict_category(complaint.description)
                predicted_category = category_result.get(
                    "predicted_category", "Unknown"
                )
                category_predictions[predicted_category] = (
                    category_predictions.get(predicted_category, 0) + 1
                )

            # Sentiment trend insight
            total_complaints = sum(sentiment_counts.values())
            if total_complaints > 0:
                negative_ratio = sentiment_counts["negative"] / total_complaints
                if negative_ratio > 0.6:
                    trends.append(
                        {
                            "type": "sentiment_trend",
                            "severity": "high",
                            "title": "High negative sentiment detected",
                            "description": f"{negative_ratio:.1%} of recent complaints show negative sentiment",
                            "sentiment_distribution": sentiment_counts,
                        }
                    )
                elif negative_ratio < 0.3:
                    trends.append(
                        {
                            "type": "sentiment_trend",
                            "severity": "info",
                            "title": "Positive sentiment trend",
                            "description": f"Only {negative_ratio:.1%} negative sentiment in recent complaints",
                            "sentiment_distribution": sentiment_counts,
                        }
                    )

            # Top predicted categories
            if category_predictions:
                top_category = max(category_predictions, key=category_predictions.get)
                trends.append(
                    {
                        "type": "category_trend",
                        "severity": "info",
                        "title": f"Trending complaint category: {top_category}",
                        "description": f"NLP analysis shows {category_predictions[top_category]} complaints in {top_category} category",
                        "category_distribution": dict(
                            sorted(
                                category_predictions.items(),
                                key=lambda x: x[1],
                                reverse=True,
                            )[:5]
                        ),
                    }
                )

            return trends

        except Exception as e:
            return [
                {
                    "type": "error",
                    "severity": "low",
                    "title": "NLP trend analysis unavailable",
                    "description": f"NLP processing failed: {str(e)}",
                }
            ]


class DashboardWebSocket(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time dashboard updates
    """

    async def connect(self):
        """Accept WebSocket connection"""
        await self.accept()

        # Add to dashboard group
        await self.channel_layer.group_add("dashboard_updates", self.channel_name)

        # Send initial data
        metrics = RealTimeMetrics()
        initial_data = await metrics.get_live_metrics()
        await self.send(text_data=json.dumps(initial_data))

    async def disconnect(self, close_code):
        """Remove from dashboard group"""
        await self.channel_layer.group_discard("dashboard_updates", self.channel_name)

    async def dashboard_update(self, event):
        """Send dashboard update to WebSocket"""
        await self.send(text_data=json.dumps(event["data"]))


class ChartGenerator:
    """
    Generate interactive charts for dashboard
    """

    @staticmethod
    def create_complaint_timeline_chart(data: List[Dict]) -> str:
        """
        Create timeline chart for complaints
        """
        df = pd.DataFrame(data)

        fig = px.line(
            df,
            x="date",
            y="count",
            title="Complaint Volume Over Time",
            color_discrete_sequence=["#1f77b4"],
        )

        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Number of Complaints",
            height=400,
            showlegend=False,
        )

        return fig.to_json()

    @staticmethod
    def create_status_distribution_chart(data: Dict[str, int]) -> str:
        """
        Create pie chart for status distribution
        """
        fig = px.pie(
            values=list(data.values()),
            names=list(data.keys()),
            title="Complaint Status Distribution",
        )

        fig.update_traces(textinfo="percent+label")

        return fig.to_json()

    @staticmethod
    def create_category_heatmap(data: List[Dict]) -> str:
        """
        Create heatmap for category vs time analysis
        """
        df = pd.DataFrame(data)
        pivot_df = df.pivot(index="category", columns="hour", values="count")

        fig = px.imshow(
            pivot_df,
            title="Complaint Categories by Hour",
            color_continuous_scale="Blues",
        )

        return fig.to_json()

    @staticmethod
    def create_performance_gauge(value: float, title: str) -> str:
        """
        Create gauge chart for performance metrics
        """
        fig = go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=value,
                domain={"x": [0, 1], "y": [0, 1]},
                title={"text": title},
                gauge={
                    "axis": {"range": [None, 100]},
                    "bar": {"color": "darkblue"},
                    "steps": [
                        {"range": [0, 50], "color": "lightgray"},
                        {"range": [50, 80], "color": "gray"},
                    ],
                    "threshold": {
                        "line": {"color": "red", "width": 4},
                        "thickness": 0.75,
                        "value": 90,
                    },
                },
            )
        )

        return fig.to_json()


class PredictiveAnalytics:
    """
    Advanced predictive analytics for complaints
    """

    @database_sync_to_async
    def predict_complaint_volume(self, days_ahead: int = 7) -> Dict[str, Any]:
        """
        Predict complaint volume for upcoming days
        """
        try:
            # Get historical data
            historical_data = list(
                Complaint.objects.filter(
                    created_at__gte=timezone.now() - timedelta(days=30)
                )
                .extra(select={"date": "DATE(created_at)"})
                .values("date")
                .annotate(count=Count("id"))
                .order_by("date")
            )

            if len(historical_data) < 7:
                return {"error": "Insufficient data for prediction"}

            # Simple linear regression for prediction
            df = pd.DataFrame(historical_data)
            df["date"] = pd.to_datetime(df["date"])
            df["days_since_start"] = (df["date"] - df["date"].min()).dt.days

            # Fit simple model
            X = df[["days_since_start"]].values
            y = df["count"].values

            # Calculate trend
            slope = np.polyfit(X.flatten(), y, 1)[0]

            # Generate predictions
            predictions = []
            last_day = df["days_since_start"].max()

            for i in range(1, days_ahead + 1):
                predicted_count = max(0, int(y[-1] + slope * i))
                prediction_date = df["date"].max() + timedelta(days=i)

                predictions.append(
                    {
                        "date": prediction_date.strftime("%Y-%m-%d"),
                        "predicted_count": predicted_count,
                        "confidence": max(0.5, 1 - (i * 0.1)),  # Decreasing confidence
                    }
                )

            return {
                "predictions": predictions,
                "trend": "increasing" if slope > 0 else "decreasing",
                "model_accuracy": 0.75,  # Mock accuracy
            }

        except Exception as e:
            return {"error": f"Prediction failed: {str(e)}"}

    @database_sync_to_async
    def predict_resolution_time(self, complaint_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict resolution time for a new complaint
        """
        try:
            # Get historical resolution times for similar complaints
            similar_complaints = Complaint.objects.filter(
                category_id=complaint_data.get("category_id"),
                priority=complaint_data.get("priority"),
                status="RESOLVED",
                resolution_date__isnull=False,
            ).annotate(resolution_hours=F("resolution_date") - F("created_at"))

            if not similar_complaints.exists():
                return {"error": "No similar complaints found"}

            # Calculate average resolution time
            resolution_times = [
                comp.resolution_hours.total_seconds() / 3600
                for comp in similar_complaints
            ]

            avg_resolution_hours = np.mean(resolution_times)
            std_resolution_hours = np.std(resolution_times)

            # Confidence interval
            confidence_lower = max(0, avg_resolution_hours - std_resolution_hours)
            confidence_upper = avg_resolution_hours + std_resolution_hours

            return {
                "predicted_hours": round(avg_resolution_hours, 1),
                "confidence_interval": [
                    round(confidence_lower, 1),
                    round(confidence_upper, 1),
                ],
                "similar_complaints_count": len(resolution_times),
                "confidence_score": min(0.9, len(resolution_times) / 100),
            }

        except Exception as e:
            return {"error": f"Resolution prediction failed: {str(e)}"}


class AlertSystem:
    """
    Intelligent alerting system for dashboard
    """

    def __init__(self):
        self.alert_thresholds = {
            "high_volume": 50,  # complaints per hour
            "slow_resolution": 72,  # hours
            "low_satisfaction": 3.0,  # rating
            "system_performance": 80,  # percentage
        }

    async def check_alerts(self) -> List[Dict[str, Any]]:
        """
        Check for alert conditions
        """
        alerts = []

        # High complaint volume alert
        volume_alert = await self._check_volume_alert()
        if volume_alert:
            alerts.append(volume_alert)

        # Slow resolution alert
        resolution_alert = await self._check_resolution_alert()
        if resolution_alert:
            alerts.append(resolution_alert)

        # Low satisfaction alert
        satisfaction_alert = await self._check_satisfaction_alert()
        if satisfaction_alert:
            alerts.append(satisfaction_alert)

        return alerts

    @database_sync_to_async
    def _check_volume_alert(self) -> Optional[Dict[str, Any]]:
        """Check for high complaint volume"""
        current_hour = timezone.now().replace(minute=0, second=0, microsecond=0)
        hour_complaints = Complaint.objects.filter(created_at__gte=current_hour).count()

        if hour_complaints > self.alert_thresholds["high_volume"]:
            return {
                "type": "volume",
                "severity": "high",
                "title": "High Complaint Volume",
                "message": f"{hour_complaints} complaints in the last hour",
                "threshold": self.alert_thresholds["high_volume"],
                "current_value": hour_complaints,
            }

        return None

    @database_sync_to_async
    def _check_resolution_alert(self) -> Optional[Dict[str, Any]]:
        """Check for slow resolution times"""
        slow_complaints = Complaint.objects.filter(
            status__in=["IN_PROGRESS", "IN_REVIEW"],
            created_at__lt=timezone.now()
            - timedelta(hours=self.alert_thresholds["slow_resolution"]),
        ).count()

        if slow_complaints > 0:
            return {
                "type": "resolution",
                "severity": "medium",
                "title": "Slow Resolution Times",
                "message": f"{slow_complaints} complaints overdue",
                "threshold": self.alert_thresholds["slow_resolution"],
                "current_value": slow_complaints,
            }

        return None

    @database_sync_to_async
    def _check_satisfaction_alert(self) -> Optional[Dict[str, Any]]:
        """Check for low satisfaction ratings"""
        recent_ratings = Complaint.objects.filter(
            satisfaction_rating__isnull=False,
            resolution_date__gte=timezone.now() - timedelta(days=7),
        ).aggregate(avg_rating=Avg("satisfaction_rating"))

        avg_rating = recent_ratings.get("avg_rating", 5.0)

        if avg_rating < self.alert_thresholds["low_satisfaction"]:
            return {
                "type": "satisfaction",
                "severity": "high",
                "title": "Low Satisfaction Rating",
                "message": f"Average rating: {avg_rating:.1f}/5.0",
                "threshold": self.alert_thresholds["low_satisfaction"],
                "current_value": avg_rating,
            }

        return None
