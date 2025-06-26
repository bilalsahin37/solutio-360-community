# -*- coding: utf-8 -*-
"""
Reinforcement Learning Module for Solutio 360 PWA
=================================================

AI-powered reinforcement learning system for complaint resolution optimization
"""

import json
import logging
import pickle
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from django.core.cache import cache
from django.db.models import Avg, Count, F, Q
from django.utils import timezone

import numpy as np
from sklearn.linear_model import SGDClassifier
from sklearn.preprocessing import StandardScaler

from complaints.models import Complaint, ComplaintCategory
from users.models import User

logger = logging.getLogger(__name__)


class ComplaintResolutionAgent:
    """
    Pekiştirmeli öğrenme ile şikayet çözüm sürecini optimize eden agent
    """

    def __init__(self):
        self.q_table = defaultdict(lambda: defaultdict(float))
        self.learning_rate = 0.1
        self.discount_factor = 0.9
        self.epsilon = 0.1  # Exploration rate
        self.epsilon_decay = 0.995
        self.min_epsilon = 0.01

        # Action history for learning
        self.action_history = deque(maxlen=1000)

        # Performance metrics
        self.total_rewards = 0
        self.episode_count = 0
        self.success_rate = 0.0

        # Load existing model if available
        self._load_model()

    def get_state(self, complaint) -> Tuple[str, str, str, str]:
        """Şikayet durumunu state olarak temsil eder"""
        try:
            priority = complaint.priority or "MEDIUM"
            category = complaint.category.name if complaint.category else "OTHER"

            # Complexity calculation based on description length and category
            description_length = len(complaint.description) if complaint.description else 0
            if description_length > 500:
                complexity = "HIGH"
            elif description_length > 200:
                complexity = "MEDIUM"
            else:
                complexity = "LOW"

            # Time of day factor
            hour = complaint.created_at.hour
            if 9 <= hour <= 17:
                time_factor = "BUSINESS_HOURS"
            elif 18 <= hour <= 22:
                time_factor = "EVENING"
            else:
                time_factor = "OFF_HOURS"

            return (priority, category, complexity, time_factor)

        except Exception as e:
            logger.error(f"Error getting state: {e}")
            return ("MEDIUM", "OTHER", "LOW", "BUSINESS_HOURS")

    def get_possible_actions(self) -> List[str]:
        """Mevcut eylemler listesi"""
        return [
            "assign_to_expert",
            "escalate_to_manager",
            "auto_resolve",
            "request_more_info",
            "schedule_callback",
            "refer_to_department",
        ]

    def choose_action(self, state: Tuple[str, str, str, str]) -> str:
        """Epsilon-greedy action selection"""
        if np.random.random() < self.epsilon:
            # Exploration: random action
            return np.random.choice(self.get_possible_actions())
        else:
            # Exploitation: best known action
            actions = self.get_possible_actions()
            q_values = [self.q_table[state][action] for action in actions]

            if max(q_values) == 0:  # No experience yet
                return np.random.choice(actions)

            best_action_idx = np.argmax(q_values)
            return actions[best_action_idx]

    def update_q_value(self, state: Tuple, action: str, reward: float, next_state: Tuple):
        """Q-değerini güncelle"""
        try:
            current_q = self.q_table[state][action]

            # Next state'deki en iyi Q değeri
            next_actions = self.get_possible_actions()
            next_q_values = [self.q_table[next_state][a] for a in next_actions]
            max_next_q = max(next_q_values) if next_q_values else 0

            # Q-Learning formülü
            new_q = current_q + self.learning_rate * (
                reward + self.discount_factor * max_next_q - current_q
            )

            self.q_table[state][action] = new_q

            # Epsilon decay
            self.epsilon = max(self.min_epsilon, self.epsilon * self.epsilon_decay)

            # Update metrics
            self.total_rewards += reward
            self.episode_count += 1

            logger.info(
                f"Q-value updated: State={state}, Action={action}, Reward={reward}, New Q={new_q:.3f}"
            )

        except Exception as e:
            logger.error(f"Error updating Q-value: {e}")

    def get_reward(self, complaint, action: str, outcome: Dict[str, Any]) -> float:
        """Ödül hesaplama sistemi"""
        reward = 0.0

        try:
            # Hızlı çözüm ödülü
            if outcome.get("resolved_quickly", False):
                reward += 15.0

            # Müşteri memnuniyeti ödülü
            satisfaction = outcome.get("customer_satisfaction", 0)
            if satisfaction >= 4:
                reward += 10.0
            elif satisfaction >= 3:
                reward += 5.0
            elif satisfaction < 2:
                reward -= 10.0

            # Escalation cezası
            if action == "escalate_to_manager":
                reward -= 5.0

            # Otomatik çözüm başarı ödülü
            if action == "auto_resolve" and outcome.get("resolved_successfully", False):
                reward += 20.0
            elif action == "auto_resolve" and not outcome.get("resolved_successfully", False):
                reward -= 15.0

            # Uzman atama verimliliği
            if action == "assign_to_expert":
                resolution_time = outcome.get("resolution_time_hours", 24)
                if resolution_time < 4:
                    reward += 12.0
                elif resolution_time < 12:
                    reward += 8.0
                elif resolution_time > 48:
                    reward -= 8.0

            # Bilgi talep etme uygunluğu
            if action == "request_more_info":
                if outcome.get("info_provided", False):
                    reward += 5.0
                else:
                    reward -= 3.0

            logger.info(f"Reward calculated: Action={action}, Outcome={outcome}, Reward={reward}")

        except Exception as e:
            logger.error(f"Error calculating reward: {e}")

        return reward

    def train_from_historical_data(self):
        """Geçmiş verilerden öğrenme"""
        try:
            resolved_complaints = Complaint.objects.filter(
                status="RESOLVED",
                resolution_date__isnull=False,
                created_at__gte=timezone.now() - timedelta(days=30),
            ).order_by("created_at")

            logger.info(f"Training from {resolved_complaints.count()} historical complaints")

            for complaint in resolved_complaints:
                state = self.get_state(complaint)

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

                # Calculate reward based on actual outcome
                outcome = {
                    "resolved_quickly": resolution_time < 24,
                    "customer_satisfaction": complaint.satisfaction_rating or 3,
                    "resolved_successfully": True,
                    "resolution_time_hours": resolution_time,
                }

                reward = self.get_reward(complaint, action, outcome)

                # Update Q-table
                next_state = ("RESOLVED", "COMPLETED", "DONE", "BUSINESS_HOURS")
                self.update_q_value(state, action, reward, next_state)

            self._save_model()
            logger.info(
                f"Training completed. Episodes: {self.episode_count}, Total Reward: {self.total_rewards}"
            )

        except Exception as e:
            logger.error(f"Error in training: {e}")

    def get_recommendation(self, complaint) -> Dict[str, Any]:
        """Şikayet için eylem önerisi"""
        try:
            state = self.get_state(complaint)
            recommended_action = self.choose_action(state)

            # Confidence calculation
            q_values = [self.q_table[state][action] for action in self.get_possible_actions()]
            max_q = max(q_values) if q_values else 0
            confidence = min(100, max(50, abs(max_q) * 10))  # Scale to 50-100%

            return {
                "recommended_action": recommended_action,
                "confidence": confidence,
                "state": state,
                "q_values": dict(zip(self.get_possible_actions(), q_values)),
                "epsilon": self.epsilon,
                "episodes_trained": self.episode_count,
            }

        except Exception as e:
            logger.error(f"Error getting recommendation: {e}")
            return {
                "recommended_action": "assign_to_expert",
                "confidence": 50,
                "error": str(e),
            }

    def _save_model(self):
        """Model durumunu kaydet"""
        try:
            model_data = {
                "q_table": dict(self.q_table),
                "epsilon": self.epsilon,
                "episode_count": self.episode_count,
                "total_rewards": self.total_rewards,
                "last_updated": timezone.now().isoformat(),
            }

            cache.set("rl_agent_model", model_data, timeout=86400)  # 24 hours
            logger.info("RL model saved to cache")

        except Exception as e:
            logger.error(f"Error saving model: {e}")

    def _load_model(self):
        """Kaydedilmiş model durumunu yükle"""
        try:
            model_data = cache.get("rl_agent_model")
            if model_data:
                self.q_table = defaultdict(lambda: defaultdict(float), model_data["q_table"])
                self.epsilon = model_data.get("epsilon", self.epsilon)
                self.episode_count = model_data.get("episode_count", 0)
                self.total_rewards = model_data.get("total_rewards", 0)

                logger.info(f"RL model loaded from cache. Episodes: {self.episode_count}")

        except Exception as e:
            logger.error(f"Error loading model: {e}")

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Performance metrikleri"""
        return {
            "episode_count": self.episode_count,
            "total_rewards": self.total_rewards,
            "average_reward": self.total_rewards / max(1, self.episode_count),
            "epsilon": self.epsilon,
            "q_table_size": len(self.q_table),
            "exploration_rate": self.epsilon * 100,
            "last_updated": timezone.now().isoformat(),
        }


class AdaptiveThresholdManager:
    """
    Eşik değerlerini otomatik olarak ayarlayan sistem
    """

    def __init__(self):
        self.thresholds = {
            "high_volume": 50,
            "slow_resolution": 72,
            "low_satisfaction": 3.0,
            "system_performance": 80,
        }
        self.learning_rate = 0.01
        self.performance_history = deque(maxlen=100)
        self.adjustment_history = deque(maxlen=50)

        self._load_thresholds()

    def update_thresholds(self, performance_metrics: Dict[str, float]):
        """Performans metriklerine göre threshold'ları güncelle"""
        try:
            self.performance_history.append(
                {"timestamp": timezone.now(), "metrics": performance_metrics.copy()}
            )

            # Her metrik için threshold ayarlaması
            for metric_name, current_value in performance_metrics.items():
                if metric_name in self.thresholds:
                    old_threshold = self.thresholds[metric_name]

                    # Performance-based adjustment
                    if metric_name == "high_volume":
                        # Eğer sık alarm çalıyorsa threshold'u artır
                        alert_frequency = self._calculate_alert_frequency(metric_name)
                        if alert_frequency > 0.3:  # %30'dan fazla alarm
                            adjustment = self.learning_rate * old_threshold * 0.1
                            self.thresholds[metric_name] += adjustment

                    elif metric_name == "slow_resolution":
                        # Çözüm süresi performansına göre ayarla
                        avg_resolution_time = self._get_average_resolution_time()
                        if avg_resolution_time < old_threshold * 0.8:
                            # Performans iyiyse threshold'u düşür
                            self.thresholds[metric_name] *= 1 - self.learning_rate
                        elif avg_resolution_time > old_threshold * 1.2:
                            # Performans kötüyse threshold'u artır
                            self.thresholds[metric_name] *= 1 + self.learning_rate

                    elif metric_name == "low_satisfaction":
                        # Memnuniyet oranına göre ayarla
                        recent_satisfaction = self._get_recent_satisfaction()
                        if recent_satisfaction > 4.0:
                            # Memnuniyet yüksekse daha hassas ol
                            self.thresholds[metric_name] = max(2.5, old_threshold - 0.1)

                    # Log the adjustment
                    if old_threshold != self.thresholds[metric_name]:
                        adjustment_info = {
                            "timestamp": timezone.now(),
                            "metric": metric_name,
                            "old_value": old_threshold,
                            "new_value": self.thresholds[metric_name],
                            "reason": "performance_based_adjustment",
                        }
                        self.adjustment_history.append(adjustment_info)
                        logger.info(f"Threshold adjusted: {adjustment_info}")

            self._save_thresholds()

        except Exception as e:
            logger.error(f"Error updating thresholds: {e}")

    def _calculate_alert_frequency(self, metric_name: str) -> float:
        """Son 24 saatte bir metrik için alarm sıklığını hesapla"""
        try:
            # Bu gerçek implementasyonda alert history'den hesaplanacak
            # Şimdilik mock data
            return 0.2  # %20 alarm oranı
        except:
            return 0.0

    def _get_average_resolution_time(self) -> float:
        """Son 7 günün ortalama çözüm süresi (saat)"""
        try:
            week_ago = timezone.now() - timedelta(days=7)
            avg_time = Complaint.objects.filter(
                status="RESOLVED", resolution_date__gte=week_ago
            ).aggregate(avg_time=Avg(F("resolution_date") - F("created_at")))["avg_time"]

            if avg_time:
                return avg_time.total_seconds() / 3600  # Convert to hours
            return 48.0  # Default

        except Exception as e:
            logger.error(f"Error calculating average resolution time: {e}")
            return 48.0

    def _get_recent_satisfaction(self) -> float:
        """Son 7 günün ortalama memnuniyet puanı"""
        try:
            week_ago = timezone.now() - timedelta(days=7)
            avg_satisfaction = Complaint.objects.filter(
                satisfaction_rating__isnull=False, resolution_date__gte=week_ago
            ).aggregate(avg_rating=Avg("satisfaction_rating"))["avg_rating"]

            return avg_satisfaction or 3.0

        except Exception as e:
            logger.error(f"Error calculating recent satisfaction: {e}")
            return 3.0

    def get_adaptive_thresholds(self) -> Dict[str, float]:
        """Mevcut adaptive threshold değerleri"""
        return self.thresholds.copy()

    def _save_thresholds(self):
        """Threshold'ları cache'e kaydet"""
        try:
            threshold_data = {
                "thresholds": self.thresholds,
                "last_updated": timezone.now().isoformat(),
                "adjustment_history": list(self.adjustment_history)[-10],  # Son 10 ayarlama
            }
            cache.set("adaptive_thresholds", threshold_data, timeout=86400)

        except Exception as e:
            logger.error(f"Error saving thresholds: {e}")

    def _load_thresholds(self):
        """Kaydedilmiş threshold'ları yükle"""
        try:
            threshold_data = cache.get("adaptive_thresholds")
            if threshold_data:
                self.thresholds.update(threshold_data["thresholds"])
                if threshold_data.get("adjustment_history"):
                    self.adjustment_history.extend(threshold_data["adjustment_history"])
                logger.info("Adaptive thresholds loaded from cache")

        except Exception as e:
            logger.error(f"Error loading thresholds: {e}")


class IncrementalMLModel:
    """
    Artımlı öğrenme yapabilen ML modeli
    """

    def __init__(self):
        self.model = SGDClassifier(
            loss="hinge", learning_rate="adaptive", eta0=0.01, random_state=42
        )
        self.scaler = StandardScaler()
        self.is_trained = False
        self.feature_names = [
            "priority_high",
            "priority_medium",
            "priority_low",
            "hour_of_day",
            "day_of_week",
            "description_length",
            "category_encoding",
            "user_complaint_count",
        ]
        self.classes = ["QUICK_RESOLVE", "NORMAL_RESOLVE", "ESCALATE"]

        self._load_model()

    def extract_features(self, complaint) -> np.ndarray:
        """Şikayetten özellik çıkarma"""
        try:
            features = []

            # Priority encoding (one-hot)
            priority = complaint.priority or "MEDIUM"
            features.extend(
                [
                    1 if priority == "HIGH" else 0,
                    1 if priority == "MEDIUM" else 0,
                    1 if priority == "LOW" else 0,
                ]
            )

            # Time features
            features.append(complaint.created_at.hour)
            features.append(complaint.created_at.weekday())

            # Text features
            description_len = len(complaint.description) if complaint.description else 0
            features.append(min(description_len, 1000))  # Cap at 1000

            # Category encoding (hash-based)
            category_name = complaint.category.name if complaint.category else "OTHER"
            category_hash = hash(category_name) % 100  # Simple encoding
            features.append(category_hash)

            # User history
            user_complaint_count = Complaint.objects.filter(submitter=complaint.submitter).count()
            features.append(min(user_complaint_count, 50))  # Cap at 50

            return np.array(features).reshape(1, -1)

        except Exception as e:
            logger.error(f"Error extracting features: {e}")
            return np.zeros((1, len(self.feature_names)))

    def get_resolution_category(self, complaint) -> str:
        """Çözüm kategorisini belirle"""
        try:
            if complaint.status != "RESOLVED" or not complaint.resolution_date:
                return "NORMAL_RESOLVE"

            resolution_hours = (
                complaint.resolution_date - complaint.created_at
            ).total_seconds() / 3600

            if resolution_hours < 4:
                return "QUICK_RESOLVE"
            elif resolution_hours > 48 or complaint.escalation_count > 0:
                return "ESCALATE"
            else:
                return "NORMAL_RESOLVE"

        except Exception as e:
            logger.error(f"Error determining resolution category: {e}")
            return "NORMAL_RESOLVE"

    def partial_fit(self, complaints: List[Complaint]):
        """Yeni şikayetlerle modeli güncelle"""
        try:
            if not complaints:
                return

            # Feature extraction
            X = []
            y = []

            for complaint in complaints:
                features = self.extract_features(complaint)
                X.append(features.flatten())
                y.append(self.get_resolution_category(complaint))

            X = np.array(X)
            y = np.array(y)

            # Scale features
            if not self.is_trained:
                X_scaled = self.scaler.fit_transform(X)
                self.model.partial_fit(X_scaled, y, classes=self.classes)
                self.is_trained = True
            else:
                X_scaled = self.scaler.transform(X)
                self.model.partial_fit(X_scaled, y)

            logger.info(f"Model updated with {len(complaints)} complaints")
            self._save_model()

        except Exception as e:
            logger.error(f"Error in partial fit: {e}")

    def predict(self, complaint) -> Dict[str, Any]:
        """Çözüm kategorisi tahmini"""
        try:
            if not self.is_trained:
                return {
                    "prediction": "NORMAL_RESOLVE",
                    "confidence": 0.5,
                    "error": "Model not trained yet",
                }

            features = self.extract_features(complaint)
            X_scaled = self.scaler.transform(features)

            prediction = self.model.predict(X_scaled)[0]

            # Confidence calculation
            if hasattr(self.model, "decision_function"):
                decision_scores = self.model.decision_function(X_scaled)[0]
                confidence = max(0.0, min(1.0, max(decision_scores) / 2.0))
            else:
                confidence = 0.7  # Default confidence

            return {
                "prediction": prediction,
                "confidence": confidence,
                "features_used": self.feature_names,
                "model_trained": self.is_trained,
            }

        except Exception as e:
            logger.error(f"Error in prediction: {e}")
            return {"prediction": "NORMAL_RESOLVE", "confidence": 0.5, "error": str(e)}

    def retrain_full(self):
        """Tam model yeniden eğitimi"""
        try:
            recent_complaints = Complaint.objects.filter(
                status="RESOLVED", created_at__gte=timezone.now() - timedelta(days=30)
            )

            if recent_complaints.count() < 10:
                logger.warning("Not enough data for full retraining")
                return

            # Reset model
            self.model = SGDClassifier(
                loss="hinge", learning_rate="adaptive", eta0=0.01, random_state=42
            )
            self.scaler = StandardScaler()
            self.is_trained = False

            # Train with all recent data
            self.partial_fit(list(recent_complaints))
            logger.info(f"Full retraining completed with {recent_complaints.count()} complaints")

        except Exception as e:
            logger.error(f"Error in full retrain: {e}")

    def _save_model(self):
        """Model durumunu kaydet"""
        try:
            if self.is_trained:
                model_data = {
                    "model": pickle.dumps(self.model),
                    "scaler": pickle.dumps(self.scaler),
                    "is_trained": self.is_trained,
                    "feature_names": self.feature_names,
                    "classes": self.classes,
                    "last_updated": timezone.now().isoformat(),
                }
                cache.set("incremental_ml_model", model_data, timeout=86400)

        except Exception as e:
            logger.error(f"Error saving incremental model: {e}")

    def _load_model(self):
        """Kaydedilmiş modeli yükle"""
        try:
            model_data = cache.get("incremental_ml_model")
            if model_data:
                self.model = pickle.loads(model_data["model"])
                self.scaler = pickle.loads(model_data["scaler"])
                self.is_trained = model_data["is_trained"]
                self.feature_names = model_data["feature_names"]
                self.classes = model_data["classes"]
                logger.info("Incremental ML model loaded from cache")

        except Exception as e:
            logger.error(f"Error loading incremental model: {e}")


class FeedbackLearningSystem:
    """
    Kullanıcı feedback'i ile öğrenen sistem
    """

    def __init__(self):
        self.feedback_history = deque(maxlen=1000)
        self.model_accuracy_history = deque(maxlen=100)
        self.prediction_outcomes = {}  # prediction_id -> outcome

    def record_prediction(self, prediction_id: str, prediction_data: Dict[str, Any]):
        """Tahmin kaydı oluştur"""
        try:
            self.prediction_outcomes[prediction_id] = {
                "prediction": prediction_data,
                "timestamp": timezone.now(),
                "outcome": None,
                "feedback": None,
            }

            # Cache'e kaydet
            cache.set(f"prediction_{prediction_id}", prediction_data, timeout=604800)  # 7 days

        except Exception as e:
            logger.error(f"Error recording prediction: {e}")

    def process_user_feedback(
        self,
        prediction_id: str,
        actual_outcome: Dict[str, Any],
        user_satisfaction: float,
    ):
        """Kullanıcı feedback'ini işle"""
        try:
            if prediction_id not in self.prediction_outcomes:
                logger.warning(f"Prediction ID {prediction_id} not found")
                return

            # Update outcome
            self.prediction_outcomes[prediction_id]["outcome"] = actual_outcome
            self.prediction_outcomes[prediction_id]["feedback"] = {
                "satisfaction": user_satisfaction,
                "timestamp": timezone.now(),
            }

            # Calculate accuracy
            prediction_accuracy = self._calculate_accuracy(prediction_id, actual_outcome)

            self.model_accuracy_history.append(
                {
                    "prediction_id": prediction_id,
                    "accuracy": prediction_accuracy,
                    "satisfaction": user_satisfaction,
                    "timestamp": timezone.now(),
                }
            )

            # Feedback-based learning
            feedback_entry = {
                "prediction_id": prediction_id,
                "accuracy": prediction_accuracy,
                "satisfaction": user_satisfaction,
                "outcome": actual_outcome,
                "timestamp": timezone.now(),
            }
            self.feedback_history.append(feedback_entry)

            # Trigger model updates if accuracy is low
            if prediction_accuracy < 0.7:
                self._trigger_model_retraining()

            # Adjust thresholds based on satisfaction
            if user_satisfaction < 3.0:
                self._adjust_thresholds_based_on_satisfaction(user_satisfaction)

            logger.info(
                f"Feedback processed: ID={prediction_id}, Accuracy={prediction_accuracy:.3f}, Satisfaction={user_satisfaction}"
            )

        except Exception as e:
            logger.error(f"Error processing feedback: {e}")

    def _calculate_accuracy(self, prediction_id: str, actual_outcome: Dict[str, Any]) -> float:
        """Tahmin doğruluğunu hesapla"""
        try:
            prediction_data = self.prediction_outcomes[prediction_id]["prediction"]

            # Resolution time accuracy
            predicted_time = prediction_data.get("predicted_hours", 24)
            actual_time = actual_outcome.get("actual_resolution_hours", 24)

            time_accuracy = 1.0 - min(
                1.0,
                abs(predicted_time - actual_time) / max(predicted_time, actual_time),
            )

            # Action accuracy
            predicted_action = prediction_data.get("recommended_action", "")
            actual_action = actual_outcome.get("actual_action", "")

            action_accuracy = 1.0 if predicted_action == actual_action else 0.0

            # Combined accuracy
            overall_accuracy = (time_accuracy * 0.6) + (action_accuracy * 0.4)

            return overall_accuracy

        except Exception as e:
            logger.error(f"Error calculating accuracy: {e}")
            return 0.5

    def _trigger_model_retraining(self):
        """Model yeniden eğitimini tetikle"""
        try:
            # Bu gerçek implementasyonda asenkron bir görev olacak
            logger.info("Model retraining triggered due to low accuracy")

            # Background task için Celery kullanılabilir
            # retrain_models.delay()

        except Exception as e:
            logger.error(f"Error triggering retraining: {e}")

    def _adjust_thresholds_based_on_satisfaction(self, satisfaction: float):
        """Memnuniyete göre eşik değerlerini ayarla"""
        try:
            threshold_manager = AdaptiveThresholdManager()

            if satisfaction < 2.0:
                # Çok düşük memnuniyet - daha hassas alertler
                adjustment_factor = 0.9
            elif satisfaction < 3.0:
                # Düşük memnuniyet - biraz daha hassas
                adjustment_factor = 0.95
            else:
                return  # Normal memnuniyet, ayarlama yok

            current_thresholds = threshold_manager.get_adaptive_thresholds()
            adjusted_thresholds = {
                key: value * adjustment_factor
                for key, value in current_thresholds.items()
                if key in ["high_volume", "slow_resolution"]
            }

            threshold_manager.thresholds.update(adjusted_thresholds)
            threshold_manager._save_thresholds()

            logger.info(f"Thresholds adjusted based on satisfaction: {satisfaction}")

        except Exception as e:
            logger.error(f"Error adjusting thresholds: {e}")

    def get_feedback_analytics(self) -> Dict[str, Any]:
        """Feedback analitikleri"""
        try:
            if not self.model_accuracy_history:
                return {"error": "No feedback data available"}

            recent_accuracy = [
                entry["accuracy"] for entry in list(self.model_accuracy_history)[-20:]
            ]
            recent_satisfaction = [
                entry["satisfaction"] for entry in list(self.model_accuracy_history)[-20:]
            ]

            return {
                "total_feedback_count": len(self.feedback_history),
                "recent_average_accuracy": (np.mean(recent_accuracy) if recent_accuracy else 0),
                "recent_average_satisfaction": (
                    np.mean(recent_satisfaction) if recent_satisfaction else 0
                ),
                "accuracy_trend": (
                    "improving"
                    if len(recent_accuracy) > 1 and recent_accuracy[-1] > recent_accuracy[0]
                    else "stable"
                ),
                "satisfaction_trend": (
                    "improving"
                    if len(recent_satisfaction) > 1
                    and recent_satisfaction[-1] > recent_satisfaction[0]
                    else "stable"
                ),
                "last_updated": timezone.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error getting feedback analytics: {e}")
            return {"error": str(e)}


# Global instances
rl_agent = ComplaintResolutionAgent()
threshold_manager = AdaptiveThresholdManager()
incremental_model = IncrementalMLModel()
feedback_system = FeedbackLearningSystem()
