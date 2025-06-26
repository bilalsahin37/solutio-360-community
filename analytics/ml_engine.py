# -*- coding: utf-8 -*-
"""
Machine Learning Engine for Solutio 360 PWA
===========================================

Comprehensive AI-powered ML system with:
- Reinforcement Learning
- Adaptive Thresholds
- Incremental Learning
- Real-time NLP
"""

import json
import logging
import pickle
import re
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from django.core.cache import cache
from django.db.models import Avg, Count, F, Q
from django.utils import timezone

import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import SGDClassifier
from sklearn.naive_bayes import MultinomialNB
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
        self.epsilon = 0.1
        self.episode_count = 0
        self.total_rewards = 0

    def get_state(self, complaint) -> Tuple[str, str, str, str]:
        """State representation"""
        try:
            priority = complaint.priority or "MEDIUM"
            category = complaint.category.name if complaint.category else "OTHER"

            description_length = len(complaint.description) if complaint.description else 0
            if description_length > 500:
                complexity = "HIGH"
            elif description_length > 200:
                complexity = "MEDIUM"
            else:
                complexity = "LOW"

            hour = complaint.created_at.hour
            if 9 <= hour <= 17:
                time_factor = "BUSINESS_HOURS"
            else:
                time_factor = "OFF_HOURS"

            return (priority, category, complexity, time_factor)
        except:
            return ("MEDIUM", "OTHER", "LOW", "BUSINESS_HOURS")

    def get_possible_actions(self) -> List[str]:
        return [
            "assign_to_expert",
            "escalate_to_manager",
            "auto_resolve",
            "request_more_info",
        ]

    def choose_action(self, state) -> str:
        if np.random.random() < self.epsilon:
            return np.random.choice(self.get_possible_actions())
        else:
            actions = self.get_possible_actions()
            q_values = [self.q_table[state][action] for action in actions]
            if max(q_values) == 0:
                return np.random.choice(actions)
            return actions[np.argmax(q_values)]

    def get_recommendation(self, complaint) -> Dict[str, Any]:
        """Get action recommendation"""
        try:
            state = self.get_state(complaint)
            recommended_action = self.choose_action(state)

            q_values = [self.q_table[state][action] for action in self.get_possible_actions()]
            max_q = max(q_values) if q_values else 0
            confidence = min(100, max(50, abs(max_q) * 10))

            return {
                "recommended_action": recommended_action,
                "confidence": confidence,
                "state": state,
                "q_values": dict(zip(self.get_possible_actions(), q_values)),
            }
        except Exception as e:
            return {
                "recommended_action": "assign_to_expert",
                "confidence": 50,
                "error": str(e),
            }

    def update_q_value(self, state, action, reward, next_state):
        """Update Q-value"""
        current_q = self.q_table[state][action]
        next_actions = self.get_possible_actions()
        next_q_values = [self.q_table[next_state][a] for a in next_actions]
        max_next_q = max(next_q_values) if next_q_values else 0

        new_q = current_q + self.learning_rate * (
            reward + self.discount_factor * max_next_q - current_q
        )
        self.q_table[state][action] = new_q

        self.episode_count += 1
        self.total_rewards += reward
        if self.epsilon > 0.01:
            self.epsilon *= 0.995


def get_rl_agent() -> ComplaintResolutionAgent:
    """Get singleton RL agent"""
    if not hasattr(get_rl_agent, "_instance"):
        get_rl_agent._instance = ComplaintResolutionAgent()
    return get_rl_agent._instance


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


class NLPProcessor:
    """
    Gerçek NLP işlemleri için production-ready sınıf
    """

    def __init__(self):
        self.category_model = MultinomialNB()
        self.sentiment_model = SGDClassifier(loss="log", random_state=42)
        self.vectorizer = TfidfVectorizer(max_features=5000, stop_words="english")

        self.is_category_trained = False
        self.is_sentiment_trained = False

        # Turkish words for better processing
        self.turkish_stopwords = [
            "bir",
            "bu",
            "da",
            "de",
            "den",
            "için",
            "ile",
            "ve",
            "ki",
            "o",
            "olan",
            "var",
            "gibi",
            "olan",
            "kadar",
            "daha",
            "çok",
            "ben",
            "sen",
            "biz",
        ]

        self._load_models()

    def predict_category(self, text: str) -> Dict[str, Any]:
        """Şikayet kategorisi tahmini"""
        try:
            if not self.is_category_trained:
                # Fallback to rule-based classification
                return self._rule_based_category(text)

            # Preprocess text
            cleaned_text = self._preprocess_text(text)
            text_vector = self.vectorizer.transform([cleaned_text])

            # Predict
            predicted_category = self.category_model.predict(text_vector)[0]
            probabilities = self.category_model.predict_proba(text_vector)[0]

            confidence = max(probabilities)

            return {
                "predicted_category": predicted_category,
                "confidence": confidence,
                "method": "ml_model",
            }

        except Exception as e:
            logger.error(f"Error in category prediction: {e}")
            return self._rule_based_category(text)

    def predict_sentiment(self, text: str) -> Dict[str, Any]:
        """Duygu analizi"""
        try:
            if not self.is_sentiment_trained:
                return self._rule_based_sentiment(text)

            # Preprocess text
            cleaned_text = self._preprocess_text(text)
            text_vector = self.vectorizer.transform([cleaned_text])

            # Predict sentiment
            sentiment = self.sentiment_model.predict(text_vector)[0]
            probabilities = self.sentiment_model.predict_proba(text_vector)[0]

            confidence = max(probabilities)

            return {
                "sentiment": sentiment,
                "confidence": confidence,
                "method": "ml_model",
            }

        except Exception as e:
            logger.error(f"Error in sentiment prediction: {e}")
            return self._rule_based_sentiment(text)

    def predict_anomaly(self, text: str, user_id: int, created_at: datetime) -> Dict[str, Any]:
        """Gelişmiş anomali tespiti"""
        try:
            anomaly_score = 0.0
            reasons = []

            # Text-based anomaly detection
            text_length = len(text)
            if text_length < 10:
                anomaly_score += 0.3
                reasons.append("Too short description")
            elif text_length > 5000:
                anomaly_score += 0.4
                reasons.append("Extremely long description")

            # Spam detection
            repeated_chars = len(re.findall(r"(.)\1{4,}", text))
            if repeated_chars > 3:
                anomaly_score += 0.5
                reasons.append("Repeated characters detected")

            # URL detection (potential spam)
            urls = re.findall(
                r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+",
                text,
            )
            if len(urls) > 2:
                anomaly_score += 0.6
                reasons.append("Multiple URLs detected")

            # User history based anomaly
            user_complaint_count = Complaint.objects.filter(
                submitter_id=user_id, created_at__gte=timezone.now() - timedelta(days=1)
            ).count()

            if user_complaint_count > 5:
                anomaly_score += 0.7
                reasons.append("High complaint frequency from user")

            # Time-based anomaly
            hour = created_at.hour
            if hour < 6 or hour > 23:  # Late night complaints
                anomaly_score += 0.2
                reasons.append("Unusual time of complaint")

            is_anomaly = anomaly_score > 0.5

            return {
                "is_anomaly": is_anomaly,
                "anomaly_score": min(1.0, anomaly_score),
                "reasons": reasons,
                "method": "rule_based_advanced",
            }

        except Exception as e:
            logger.error(f"Error in anomaly detection: {e}")
            return {
                "is_anomaly": False,
                "anomaly_score": 0.0,
                "reasons": ["Error in processing"],
                "error": str(e),
            }

    def _preprocess_text(self, text: str) -> str:
        """Metin ön işleme"""
        try:
            # Convert to lowercase
            text = text.lower()

            # Remove special characters and numbers
            text = re.sub(r"[^a-zA-ZğüşıöçĞÜŞIÖÇ\s]", " ", text)

            # Remove extra whitespaces
            text = re.sub(r"\s+", " ", text)

            # Remove Turkish stopwords
            words = text.split()
            words = [word for word in words if word not in self.turkish_stopwords]

            return " ".join(words)

        except Exception as e:
            logger.error(f"Error preprocessing text: {e}")
            return text

    def _rule_based_category(self, text: str) -> Dict[str, Any]:
        """Kural tabanlı kategori tahmini"""
        try:
            text_lower = text.lower()

            # Define category keywords
            category_keywords = {
                "Teknik Sorun": [
                    "sistem",
                    "hata",
                    "çalışmıyor",
                    "bozuk",
                    "internet",
                    "uygulama",
                ],
                "Faturalandırma": [
                    "fatura",
                    "ücret",
                    "ödeme",
                    "para",
                    "tahsilat",
                    "kesinti",
                ],
                "Hizmet Kalitesi": [
                    "personel",
                    "davranış",
                    "hizmet",
                    "müşteri",
                    "temizlik",
                ],
                "Genel Şikayet": ["memnun", "değilim", "sorun", "problem", "şikayet"],
            }

            scores = {}
            for category, keywords in category_keywords.items():
                score = sum(1 for keyword in keywords if keyword in text_lower)
                scores[category] = score

            if scores:
                best_category = max(scores, key=scores.get)
                confidence = scores[best_category] / max(1, len(text_lower.split()) // 10)
            else:
                best_category = "Genel Şikayet"
                confidence = 0.5

            return {
                "predicted_category": best_category,
                "confidence": min(1.0, confidence),
                "method": "rule_based",
            }

        except Exception as e:
            logger.error(f"Error in rule-based category: {e}")
            return {
                "predicted_category": "Genel Şikayet",
                "confidence": 0.5,
                "method": "fallback",
            }

    def _rule_based_sentiment(self, text: str) -> Dict[str, Any]:
        """Kural tabanlı duygu analizi"""
        try:
            text_lower = text.lower()

            # Define sentiment words
            positive_words = [
                "teşekkür",
                "memnun",
                "iyi",
                "güzel",
                "harika",
                "başarılı",
                "sevindim",
                "mükemmel",
                "beğendim",
            ]

            negative_words = [
                "kötü",
                "berbat",
                "rezalet",
                "sinir",
                "öfke",
                "şikayet",
                "problem",
                "sorun",
                "memnuniyetsiz",
                "kalitesiz",
            ]

            positive_score = sum(1 for word in positive_words if word in text_lower)
            negative_score = sum(1 for word in negative_words if word in text_lower)

            if negative_score > positive_score:
                sentiment = "negative"
                confidence = min(1.0, negative_score / max(1, len(text_lower.split()) // 5))
            elif positive_score > negative_score:
                sentiment = "positive"
                confidence = min(1.0, positive_score / max(1, len(text_lower.split()) // 5))
            else:
                sentiment = "neutral"
                confidence = 0.5

            return {
                "sentiment": sentiment,
                "confidence": confidence,
                "method": "rule_based",
            }

        except Exception as e:
            logger.error(f"Error in rule-based sentiment: {e}")
            return {"sentiment": "neutral", "confidence": 0.5, "method": "fallback"}

    def train_category_model(self):
        """Kategori modelini eğit"""
        try:
            # Get training data from existing complaints
            complaints = Complaint.objects.filter(
                category__isnull=False, description__isnull=False
            ).values("description", "category__name")[:1000]

            if len(complaints) < 10:
                logger.warning("Not enough data to train category model")
                return

            texts = [self._preprocess_text(c["description"]) for c in complaints]
            categories = [c["category__name"] for c in complaints]

            # Vectorize texts
            X = self.vectorizer.fit_transform(texts)

            # Train model
            self.category_model.fit(X, categories)
            self.is_category_trained = True

            self._save_models()
            logger.info(f"Category model trained with {len(complaints)} complaints")

        except Exception as e:
            logger.error(f"Error training category model: {e}")

    def _save_models(self):
        """NLP modellerini kaydet"""
        try:
            model_data = {
                "category_model": (
                    pickle.dumps(self.category_model) if self.is_category_trained else None
                ),
                "sentiment_model": (
                    pickle.dumps(self.sentiment_model) if self.is_sentiment_trained else None
                ),
                "vectorizer": pickle.dumps(self.vectorizer),
                "is_category_trained": self.is_category_trained,
                "is_sentiment_trained": self.is_sentiment_trained,
                "last_updated": timezone.now().isoformat(),
            }
            cache.set("nlp_models", model_data, timeout=86400)

        except Exception as e:
            logger.error(f"Error saving NLP models: {e}")

    def _load_models(self):
        """NLP modellerini yükle"""
        try:
            model_data = cache.get("nlp_models")
            if model_data:
                if model_data.get("category_model"):
                    self.category_model = pickle.loads(model_data["category_model"])
                    self.is_category_trained = True

                if model_data.get("sentiment_model"):
                    self.sentiment_model = pickle.loads(model_data["sentiment_model"])
                    self.is_sentiment_trained = True

                self.vectorizer = pickle.loads(model_data["vectorizer"])
                logger.info("NLP models loaded from cache")

        except Exception as e:
            logger.error(f"Error loading NLP models: {e}")


# Global instances - singleton pattern
_threshold_manager = None
_incremental_model = None
_nlp_processor = None


def get_threshold_manager() -> AdaptiveThresholdManager:
    global _threshold_manager
    if _threshold_manager is None:
        _threshold_manager = AdaptiveThresholdManager()
    return _threshold_manager


def get_incremental_model() -> IncrementalMLModel:
    global _incremental_model
    if _incremental_model is None:
        _incremental_model = IncrementalMLModel()
    return _incremental_model


def get_nlp_processor() -> NLPProcessor:
    global _nlp_processor
    if _nlp_processor is None:
        _nlp_processor = NLPProcessor()
    return _nlp_processor
