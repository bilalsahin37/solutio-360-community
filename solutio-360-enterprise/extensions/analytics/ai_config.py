"""
Cost-Effective AI Configuration
Hibrit yaklaşım: ücretsiz + ücretli API'lerin optimal kullanımı
"""

import logging
import os
from enum import Enum
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class AIProvider(Enum):
    """AI service providers"""

    LOCAL = "local"  # Ücretsiz, local models
    HUGGINGFACE = "huggingface"  # Ücretsiz
    OLLAMA = "ollama"  # Ücretsiz, local deployment
    GEMINI = "gemini"  # Limited free tier
    OPENAI = "openai"  # Ücretli, en kaliteli
    ANTHROPIC = "anthropic"  # Limited free tier


class AIConfigManager:
    """
    AI Provider yönetimi ve maliyet optimizasyonu

    Strategy:
    1. Basit görevler -> Local/Free models
    2. Orta görevler -> Gemini/Claude free tier
    3. Kritik görevler -> OpenAI (ücretli)
    """

    def __init__(self):
        self.providers_config = {
            AIProvider.LOCAL: {
                "enabled": True,
                "cost_per_request": 0.0,
                "max_requests_per_day": float("inf"),
                "quality_score": 7.0,
                "use_cases": [
                    "simple_sentiment",
                    "keyword_extraction",
                    "basic_classification",
                ],
            },
            AIProvider.HUGGINGFACE: {
                "enabled": True,  # ✅ Always FREE
                "cost_per_request": 0.0,
                "max_requests_per_day": 1000,  # Generous free limit
                "quality_score": 8.5,
                "use_cases": [
                    "sentiment_analysis",
                    "text_classification",
                    "turkish_nlp",
                    "complex_analysis",
                    "response_generation",
                ],
                "api_key": "",  # No API key needed for public models
                "models": {
                    "turkish_sentiment": "savasy/bert-base-turkish-sentiment-cased",
                    "turkish_ner": "akdeniz27/bert-base-turkish-cased-ner",
                    "text_classification": "microsoft/DialoGPT-medium",
                    "turkish_bert": "dbmdz/bert-base-turkish-cased",
                },
                "priority": 1,  # First choice after local
            },
            AIProvider.OLLAMA: {
                "enabled": True,  # ✅ FREE - Enable for local AI
                "cost_per_request": 0.0,
                "max_requests_per_day": float("inf"),
                "quality_score": 9.0,
                "use_cases": [
                    "complex_analysis",
                    "conversation",
                    "text_generation",
                    "response_generation",
                ],
                "base_url": "http://localhost:11434",
                "models": [
                    "llama3.1",
                    "mistral",
                    "neural-chat",
                    "aya",
                ],  # Aya is great for Turkish
                "priority": 2,  # Second choice after Hugging Face
            },
            AIProvider.GEMINI: {
                "enabled": True,  # ✅ FREE TIER - 15 requests/day
                "cost_per_request": 0.0,
                "max_requests_per_day": 15,  # Free limit
                "quality_score": 9.5,
                "use_cases": [
                    "complex_analysis",
                    "response_generation",
                    "critical_analysis",
                ],
                "api_key": os.getenv("GEMINI_API_KEY", ""),
                "model": "gemini-pro",
                "priority": 3,  # Third choice - save for complex tasks
            },
            AIProvider.OPENAI: {
                "enabled": False,  # ❌ DISABLED - Ücretli olduğu için kapalı
                "cost_per_request": 0.002,
                "max_requests_per_day": 0,  # Completely disabled
                "quality_score": 10.0,
                "use_cases": [],  # No use cases - disabled
                "api_key": "",
                "model": "gpt-4o-mini",
                "priority": 999,  # Last priority - disabled
            },
            AIProvider.ANTHROPIC: {
                "enabled": True,  # ✅ FREE TIER - 5 requests/day
                "cost_per_request": 0.0,
                "max_requests_per_day": 5,  # Very limited but free
                "quality_score": 9.8,
                "use_cases": ["critical_analysis"],  # Save for most important tasks
                "api_key": os.getenv("ANTHROPIC_API_KEY", ""),
                "model": "claude-3-haiku-20240307",
                "priority": 4,  # Last resort for critical tasks
            },
        }

        # Daily usage tracking
        self.daily_usage = {}
        self.reset_daily_usage()

    def reset_daily_usage(self):
        """Reset daily usage counters"""
        from datetime import date

        today = date.today().isoformat()

        if not hasattr(self, "last_reset_date") or self.last_reset_date != today:
            old_usage = dict(self.daily_usage) if hasattr(self, "daily_usage") else {}
            self.daily_usage = {provider: 0 for provider in AIProvider}
            self.last_reset_date = today
            if old_usage:
                logger.info(f"🔄 Daily AI usage counters reset. Previous usage: {old_usage}")

    def get_usage_status(self) -> dict:
        """
        🆓 FREE Provider Usage Status - Real-time monitoring
        """
        self.reset_daily_usage()
        status = {}

        for provider, config in self.providers_config.items():
            if config["enabled"]:
                used = self.daily_usage[provider]
                limit = config["max_requests_per_day"]
                remaining = limit - used if limit != float("inf") else "unlimited"

                status[provider.value] = {
                    "used": used,
                    "limit": limit if limit != float("inf") else "unlimited",
                    "remaining": remaining,
                    "percentage": (used / limit * 100) if limit != float("inf") else 0,
                    "status": (
                        "🟢 Available"
                        if (limit == float("inf") or used < limit)
                        else "🔴 Exhausted"
                    ),
                    "cost": (
                        "FREE"
                        if config["cost_per_request"] == 0
                        else f"${config['cost_per_request']}/req"
                    ),
                }

        return status

    def check_and_switch_provider(self, current_provider: AIProvider, task_type: str) -> AIProvider:
        """
        🔄 Auto-switch when current provider limit is exceeded
        """
        current_config = self.providers_config[current_provider]
        current_usage = self.daily_usage[current_provider]

        if current_usage >= current_config["max_requests_per_day"]:
            logger.warning(
                f"🚨 {current_provider.value} limit exceeded ({current_usage}/{current_config['max_requests_per_day']})"
            )
            new_provider = self.get_best_provider_for_task(task_type)
            logger.info(f"🔄 Auto-switching from {current_provider.value} to {new_provider.value}")
            return new_provider

        return current_provider

    def get_free_providers_status(self) -> str:
        """
        🆓 Quick status of all free providers
        """
        status = self.get_usage_status()
        free_status = []

        for provider, info in status.items():
            if info["cost"] == "FREE":
                if info["limit"] == "unlimited":
                    free_status.append(f"{provider}: {info['used']} used (unlimited)")
                else:
                    free_status.append(
                        f"{provider}: {info['used']}/{info['limit']} ({info['remaining']} left)"
                    )

        return " | ".join(free_status)

    def get_best_provider_for_task(self, task_type: str, priority: str = "medium") -> AIProvider:
        """
        🆓 COST-FREE Provider Selection with Smart Auto-Fallback

        Strategy:
        1. LOCAL models (always first - unlimited)
        2. HUGGING FACE (1000/day - Turkish models)
        3. GEMINI (15/day - complex tasks)
        4. ANTHROPIC (5/day - critical only)
        5. Rule-based fallback (always works)

        OpenAI is DISABLED (ücretli)
        """
        self.reset_daily_usage()

        # 🎯 FREE-FIRST Fallback Chain
        free_fallback_chain = [
            AIProvider.LOCAL,  # Unlimited, always available
            AIProvider.HUGGINGFACE,  # 1000/day - Great for Turkish
            AIProvider.GEMINI,  # 15/day - High quality
            AIProvider.ANTHROPIC,  # 5/day - Best quality for critical
        ]

        # Task type'a uygun provider'ları filtrele
        suitable_providers = []

        for provider in free_fallback_chain:
            config = self.providers_config[provider]
            if (
                config["enabled"]
                and (task_type in config["use_cases"] or provider == AIProvider.LOCAL)
                and self.daily_usage[provider] < config["max_requests_per_day"]
            ):
                suitable_providers.append((provider, config))

        if not suitable_providers:
            # Always fallback to LOCAL - never fail
            logger.warning(f"All providers exhausted for '{task_type}', falling back to LOCAL")
            return AIProvider.LOCAL

        # 🚀 Smart Selection Logic
        for provider, config in suitable_providers:
            # LOCAL: Always use first if suitable
            if provider == AIProvider.LOCAL:
                selected_provider = provider
                break

            # HUGGING FACE: Prefer for Turkish and basic tasks
            elif provider == AIProvider.HUGGINGFACE and (
                "turkish" in task_type or "sentiment" in task_type
            ):
                selected_provider = provider
                break

            # GEMINI: Use for complex tasks when HF is not suitable
            elif (
                provider == AIProvider.GEMINI
                and priority in ["medium", "high"]
                and task_type in ["complex_analysis", "response_generation"]
            ):
                selected_provider = provider
                break

            # ANTHROPIC: Save for critical tasks only
            elif provider == AIProvider.ANTHROPIC and priority == "critical":
                selected_provider = provider
                break

            # Default: First available in chain
            else:
                selected_provider = provider
                break
        else:
            # If no specific selection, use first available
            selected_provider = suitable_providers[0][0]

        # Update usage counter
        self.daily_usage[selected_provider] += 1

        logger.info(
            f"🆓 Selected {selected_provider.value} for '{task_type}' (priority: {priority}) - Usage: {self.daily_usage[selected_provider]}"
        )
        return selected_provider

    def get_provider_config(self, provider: AIProvider) -> Dict[str, Any]:
        """Get configuration for specific provider"""
        return self.providers_config.get(provider, {})

    def is_provider_available(self, provider: AIProvider) -> bool:
        """Check if provider is available and within limits"""
        self.reset_daily_usage()
        config = self.providers_config.get(provider, {})

        return config.get("enabled", False) and self.daily_usage[provider] < config.get(
            "max_requests_per_day", 0
        )

    def get_cost_estimate(self, provider: AIProvider, requests_count: int) -> float:
        """Estimate cost for given number of requests"""
        config = self.providers_config.get(provider, {})
        return config.get("cost_per_request", 0) * requests_count

    def get_daily_budget_status(self) -> Dict[str, Any]:
        """Get current budget and usage status"""
        self.reset_daily_usage()

        total_cost_today = 0
        status = {}

        for provider, usage in self.daily_usage.items():
            config = self.providers_config[provider]
            cost = self.get_cost_estimate(provider, usage)
            total_cost_today += cost

            status[provider.value] = {
                "usage": usage,
                "limit": config["max_requests_per_day"],
                "cost": cost,
                "remaining": max(0, config["max_requests_per_day"] - usage),
            }

        return {
            "total_cost_today": total_cost_today,
            "providers": status,
            "recommended_actions": self._get_budget_recommendations(),
        }

    def _get_budget_recommendations(self) -> list:
        """Get budget optimization recommendations"""
        recommendations = []

        # Check if we're hitting free tier limits
        for provider, usage in self.daily_usage.items():
            config = self.providers_config[provider]
            usage_ratio = (
                usage / config["max_requests_per_day"]
                if config["max_requests_per_day"] != float("inf")
                else 0
            )

            if usage_ratio > 0.8:
                recommendations.append(
                    f"⚠️ {provider.value} kullanımı %{usage_ratio*100:.0f} - Alternatif provider'lar kullanın"
                )

        if self.daily_usage[AIProvider.OPENAI] > 50:
            recommendations.append(
                "💰 OpenAI kullanımı yüksek - Basit görevler için local models kullanın"
            )

        if not self.providers_config[AIProvider.HUGGINGFACE]["enabled"]:
            recommendations.append(
                "🆓 Hugging Face'i etkinleştirin - Ücretsiz Turkish NLP modelleri"
            )

        return recommendations


# Global instance
ai_config = AIConfigManager()


# 🆓 FREE-FIRST Task-specific provider mapping
TASK_PROVIDER_MAP = {
    "simple_sentiment": [AIProvider.LOCAL, AIProvider.HUGGINGFACE],
    "turkish_nlp": [AIProvider.HUGGINGFACE, AIProvider.LOCAL, AIProvider.GEMINI],
    "keyword_extraction": [AIProvider.LOCAL, AIProvider.HUGGINGFACE],
    "basic_classification": [AIProvider.LOCAL, AIProvider.HUGGINGFACE],
    "sentiment_analysis": [AIProvider.HUGGINGFACE, AIProvider.LOCAL, AIProvider.GEMINI],
    "complex_analysis": [
        AIProvider.GEMINI,
        AIProvider.ANTHROPIC,
        AIProvider.HUGGINGFACE,
    ],  # OpenAI removed
    "response_generation": [
        AIProvider.GEMINI,
        AIProvider.ANTHROPIC,
        AIProvider.HUGGINGFACE,
    ],  # OpenAI removed
    "conversation": [
        AIProvider.OLLAMA,
        AIProvider.GEMINI,
        AIProvider.HUGGINGFACE,
    ],  # OpenAI removed
    "enterprise_features": [AIProvider.GEMINI, AIProvider.ANTHROPIC],  # OpenAI removed
    "critical_analysis": [
        AIProvider.ANTHROPIC,
        AIProvider.GEMINI,
        AIProvider.HUGGINGFACE,
    ],  # OpenAI removed
}


def get_optimal_provider(task_type: str, priority: str = "medium") -> AIProvider:
    """Get optimal provider for given task with cost consideration"""
    return ai_config.get_best_provider_for_task(task_type, priority)


def get_budget_status() -> Dict[str, Any]:
    """Get current budget and usage information"""
    return ai_config.get_daily_budget_status()


def is_free_tier_available() -> bool:
    """Check if any free tier providers are available"""
    free_providers = [AIProvider.LOCAL, AIProvider.HUGGINGFACE, AIProvider.GEMINI]
    return any(ai_config.is_provider_available(provider) for provider in free_providers)


# 🆓 100% FREE Cost optimization tips
COST_OPTIMIZATION_TIPS = [
    "🆓 %100 ÜCRETSIZ: OpenAI devre dışı, sadece free tier kullanıyoruz!",
    "🔄 AUTO-FALLBACK: Local (∞) -> Hugging Face (1000/day) -> Gemini (15/day) -> Anthropic (5/day)",
    "🎯 TURKISH NLP: Hugging Face Turkish models (savasy/bert-base-turkish-sentiment-cased)",
    "⚡ LOCAL MODELS: Ollama ile sınırsız AI processing",
    "💡 GEMINI FREE: Günde 15 complex analysis ücretsiz",
    "🔍 ANTHROPIC FREE: Günde 5 kritik analiz ücretsiz",
    "📊 REAL-TIME MONITORING: Limit dolduğunda otomatik provider değişimi",
    "🚀 ZERO COST: Hiçbir API ücreti ödemiyoruz!",
]
