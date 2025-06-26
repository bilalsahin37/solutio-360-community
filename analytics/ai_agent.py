"""
Advanced AI Customer Service Agent
Enterprise-grade GenAI capabilities for complaint management
Inspired by LeewayHertz AI solutions
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from django.conf import settings
from django.utils import timezone

import openai

from complaints.models import Complaint
from users.models import User

from .models import AnomalyDetection, MLInsight

logger = logging.getLogger(__name__)


class GenAICustomerServiceAgent:
    """
    Enterprise GenAI Customer Service Agent
    Multi-departmental complaint processing with advanced AI capabilities
    """

    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=getattr(settings, "OPENAI_API_KEY", ""))
        self.model_name = "gpt-4-turbo-preview"
        self.max_tokens = 1000
        self.temperature = 0.7

        # Department routing matrix
        self.department_keywords = {
            "technical": [
                "bug",
                "error",
                "crash",
                "system",
                "software",
                "app",
                "website",
                "login",
                "password",
                "technical",
                "teknical",
            ],
            "billing": [
                "fatura",
                "ödeme",
                "payment",
                "bill",
                "charge",
                "refund",
                "iade",
                "price",
                "cost",
                "subscription",
                "abonelik",
            ],
            "customer_service": [
                "service",
                "support",
                "help",
                "assistance",
                "rude",
                "slow",
                "response",
                "quality",
                "experience",
            ],
            "product": [
                "product",
                "ürün",
                "quality",
                "kalite",
                "defective",
                "broken",
                "damage",
                "functionality",
                "feature",
            ],
            "delivery": [
                "delivery",
                "shipping",
                "kargo",
                "teslimat",
                "late",
                "delayed",
                "missing",
                "lost",
                "tracking",
            ],
        }

        # Priority levels
        self.priority_keywords = {
            "critical": [
                "urgent",
                "emergency",
                "asap",
                "critical",
                "serious",
                "acil",
                "kritik",
                "immediately",
                "lawsuit",
                "legal",
            ],
            "high": [
                "important",
                "high",
                "priority",
                "escalate",
                "manager",
                "supervisor",
                "complaint",
                "unsatisfied",
            ],
            "medium": [
                "medium",
                "normal",
                "standard",
                "question",
                "inquiry",
                "request",
                "suggestion",
            ],
            "low": [
                "low",
                "minor",
                "small",
                "simple",
                "easy",
                "feedback",
                "comment",
                "recommendation",
            ],
        }

    def process_complaint_with_genai(
        self, complaint_text: str, customer_context: Dict = None
    ) -> Dict:
        """
        Process complaint using GenAI with multi-departmental routing

        Returns comprehensive analysis including:
        - Sentiment analysis
        - Category classification
        - Priority assessment
        - Department routing
        - Response suggestions
        - Resolution recommendations
        """
        try:
            # Create comprehensive prompt
            prompt = self._create_analysis_prompt(complaint_text, customer_context)

            # Call OpenAI API
            response = self.openai_client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert AI customer service agent specialized in Turkish complaint management. Analyze complaints with enterprise-level accuracy.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                response_format={"type": "json_object"},
            )

            # Parse response
            ai_analysis = json.loads(response.choices[0].message.content)

            # Enhance with rule-based analysis
            enhanced_analysis = self._enhance_with_rules(complaint_text, ai_analysis)

            # Add confidence scores
            enhanced_analysis["confidence_score"] = self._calculate_confidence(ai_analysis)

            return enhanced_analysis

        except Exception as e:
            logger.error(f"GenAI processing error: {str(e)}")
            return self._fallback_analysis(complaint_text)

    def _create_analysis_prompt(self, complaint_text: str, customer_context: Dict = None) -> str:
        """Create comprehensive analysis prompt"""

        context_info = ""
        if customer_context:
            context_info = f"""
            Customer Context:
            - Previous complaints: {customer_context.get('previous_complaints', 0)}
            - Customer tier: {customer_context.get('tier', 'standard')}
            - Account status: {customer_context.get('status', 'active')}
            - Subscription plan: {customer_context.get('plan', 'basic')}
            """

        prompt = f"""
        Analyze the following customer complaint and provide a comprehensive JSON response:
        
        Complaint Text: "{complaint_text}"
        {context_info}
        
        Please provide analysis in the following JSON format:
        {{
            "sentiment": {{
                "overall": "positive/neutral/negative",
                "confidence": 0.0-1.0,
                "emotional_intensity": "low/medium/high",
                "key_emotions": ["anger", "frustration", "disappointment", etc.]
            }},
            "category": {{
                "primary": "technical/billing/customer_service/product/delivery",
                "secondary": "specific subcategory",
                "confidence": 0.0-1.0
            }},
            "priority": {{
                "level": "critical/high/medium/low",
                "reasoning": "explanation for priority level",
                "urgency_indicators": ["specific urgent keywords found"]
            }},
            "department_routing": {{
                "primary_department": "department name",
                "secondary_departments": ["additional departments if needed"],
                "routing_confidence": 0.0-1.0
            }},
            "key_issues": [
                "list of main issues identified"
            ],
            "resolution_suggestions": [
                "actionable resolution steps"
            ],
            "response_tone": "empathetic/professional/urgent/standard",
            "estimated_resolution_time": "hours or days",
            "escalation_required": true/false,
            "language": "tr/en",
            "complexity_score": 0.0-1.0
        }}
        
        Focus on Turkish context and business culture. Be precise and actionable.
        """

        return prompt

    def _enhance_with_rules(self, complaint_text: str, ai_analysis: Dict) -> Dict:
        """Enhance AI analysis with rule-based improvements"""

        text_lower = complaint_text.lower()

        # Department routing enhancement
        department_scores = {}
        for dept, keywords in self.department_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                department_scores[dept] = score

        if department_scores:
            best_dept = max(department_scores, key=department_scores.get)
            ai_analysis.setdefault("department_routing", {})

            # Override if rule-based confidence is higher
            if department_scores[best_dept] >= 3:
                ai_analysis["department_routing"]["primary_department"] = best_dept
                ai_analysis["department_routing"]["rule_based_confidence"] = 0.9

        # Priority enhancement
        priority_scores = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for priority, keywords in self.priority_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            priority_scores[priority] = score

        if max(priority_scores.values()) > 0:
            best_priority = max(priority_scores, key=priority_scores.get)
            ai_analysis.setdefault("priority", {})

            # Critical override
            if priority_scores["critical"] > 0:
                ai_analysis["priority"]["level"] = "critical"
                ai_analysis["priority"]["rule_override"] = True

        # Add Turkish-specific enhancements
        turkish_indicators = self._detect_turkish_context(text_lower)
        ai_analysis["turkish_context"] = turkish_indicators

        return ai_analysis

    def _detect_turkish_context(self, text_lower: str) -> Dict:
        """Detect Turkish-specific context and cultural nuances"""

        formal_indicators = [
            "sayın",
            "saygılarımla",
            "saygilarimla",
            "teşekkür ederim",
            "memnun kalırım",
            "rica ederim",
        ]

        informal_indicators = ["abi", "kardeş", "ya", "yani", "işte", "böyle"]

        urgency_turkish = [
            "acil",
            "hemen",
            "şimdi",
            "derhal",
            "ivedi",
            "bekleyemem",
            "sabırsızım",
        ]

        politeness_level = "neutral"
        if any(indicator in text_lower for indicator in formal_indicators):
            politeness_level = "formal"
        elif any(indicator in text_lower for indicator in informal_indicators):
            politeness_level = "informal"

        urgency_detected = any(word in text_lower for word in urgency_turkish)

        return {
            "politeness_level": politeness_level,
            "urgency_detected": urgency_detected,
            "language_confidence": (
                0.95
                if any(word in text_lower for word in ["bir", "bu", "şu", "ve", "ile"])
                else 0.3
            ),
        }

    def _calculate_confidence(self, ai_analysis: Dict) -> float:
        """Calculate overall confidence score for the analysis"""

        confidence_factors = []

        # Sentiment confidence
        if "sentiment" in ai_analysis and "confidence" in ai_analysis["sentiment"]:
            confidence_factors.append(ai_analysis["sentiment"]["confidence"])

        # Category confidence
        if "category" in ai_analysis and "confidence" in ai_analysis["category"]:
            confidence_factors.append(ai_analysis["category"]["confidence"])

        # Routing confidence
        if (
            "department_routing" in ai_analysis
            and "routing_confidence" in ai_analysis["department_routing"]
        ):
            confidence_factors.append(ai_analysis["department_routing"]["routing_confidence"])

        return sum(confidence_factors) / len(confidence_factors) if confidence_factors else 0.7

    def _fallback_analysis(self, complaint_text: str) -> Dict:
        """Fallback analysis when AI is unavailable"""

        text_lower = complaint_text.lower()

        # Simple sentiment detection
        negative_words = ["kötü", "berbat", "poor", "bad", "terrible", "awful"]
        positive_words = ["good", "great", "excellent", "iyi", "harika", "mükemmel"]

        negative_count = sum(1 for word in negative_words if word in text_lower)
        positive_count = sum(1 for word in positive_words if word in text_lower)

        if negative_count > positive_count:
            sentiment = "negative"
        elif positive_count > negative_count:
            sentiment = "positive"
        else:
            sentiment = "neutral"

        # Simple category detection
        category = "general"
        for dept, keywords in self.department_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                category = dept
                break

        return {
            "sentiment": {
                "overall": sentiment,
                "confidence": 0.6,
                "emotional_intensity": "medium",
            },
            "category": {"primary": category, "confidence": 0.6},
            "priority": {"level": "medium", "reasoning": "Fallback analysis"},
            "department_routing": {
                "primary_department": category,
                "routing_confidence": 0.6,
            },
            "fallback_mode": True,
        }

    def generate_auto_response(self, complaint_analysis: Dict, complaint_text: str) -> str:
        """Generate automated response based on analysis"""

        try:
            sentiment = complaint_analysis.get("sentiment", {}).get("overall", "neutral")
            category = complaint_analysis.get("category", {}).get("primary", "general")
            priority = complaint_analysis.get("priority", {}).get("level", "medium")

            response_prompt = f"""
            Generate a professional, empathetic response to this customer complaint in Turkish:
            
            Complaint: "{complaint_text}"
            
            Analysis Context:
            - Sentiment: {sentiment}
            - Category: {category}
            - Priority: {priority}
            
            Guidelines:
            - Be empathetic and understanding
            - Acknowledge the customer's concern
            - Provide clear next steps
            - Use professional Turkish
            - Keep it concise but comprehensive
            - Include estimated resolution time if applicable
            
            Generate only the response text, no additional formatting.
            """

            response = self.openai_client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional Turkish customer service representative. Generate empathetic, solution-focused responses.",
                    },
                    {"role": "user", "content": response_prompt},
                ],
                max_tokens=500,
                temperature=0.8,
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"Auto-response generation error: {str(e)}")
            return self._generate_fallback_response(complaint_analysis)

    def _generate_fallback_response(self, complaint_analysis: Dict) -> str:
        """Generate fallback response when AI is unavailable"""

        sentiment = complaint_analysis.get("sentiment", {}).get("overall", "neutral")
        priority = complaint_analysis.get("priority", {}).get("level", "medium")

        if sentiment == "negative" and priority in ["critical", "high"]:
            return """
            Sayın Müşterimiz,
            
            Yaşadığınız sorunu çok iyi anlıyorum ve bu durumdan dolayı özür dilerim. 
            Konunuz en yüksek öncelikle değerlendirilerek 24 saat içinde size dönüş yapılacaktır.
            
            Bu süreçte herhangi bir sorunuz olursa lütfen bizimle iletişime geçmekten çekinmeyin.
            
            Saygılarımla,
            Solutio 360 Müşteri Hizmetleri
            """
        else:
            return """
            Sayın Müşterimiz,
            
            Bizimle paylaştığınız geri bildirim için teşekkür ederim. 
            Konunuz ilgili departmanımız tarafından incelenerek en kısa sürede size dönüş yapılacaktır.
            
            Değerli zamanınız için teşekkür ederim.
            
            Saygılarımla,
            Solutio 360 Müşteri Hizmetleri
            """

    def create_resolution_workflow(self, complaint_analysis: Dict) -> List[Dict]:
        """Create step-by-step resolution workflow"""

        priority = complaint_analysis.get("priority", {}).get("level", "medium")
        category = complaint_analysis.get("category", {}).get("primary", "general")
        department = complaint_analysis.get("department_routing", {}).get(
            "primary_department", "customer_service"
        )

        workflow_steps = []

        # Immediate acknowledgment
        workflow_steps.append(
            {
                "step": 1,
                "action": "immediate_acknowledgment",
                "description": "Send automatic acknowledgment to customer",
                "timeline": "0-5 minutes",
                "responsible": "system",
                "status": "pending",
            }
        )

        # Priority-based routing
        if priority == "critical":
            workflow_steps.append(
                {
                    "step": 2,
                    "action": "escalate_to_manager",
                    "description": "Escalate to department manager immediately",
                    "timeline": "5-15 minutes",
                    "responsible": "manager",
                    "status": "pending",
                }
            )

            workflow_steps.append(
                {
                    "step": 3,
                    "action": "personal_contact",
                    "description": "Direct phone call to customer",
                    "timeline": "30 minutes",
                    "responsible": department,
                    "status": "pending",
                }
            )
        else:
            workflow_steps.append(
                {
                    "step": 2,
                    "action": "assign_to_specialist",
                    "description": f"Assign to {department} specialist",
                    "timeline": "2-4 hours",
                    "responsible": department,
                    "status": "pending",
                }
            )

        # Investigation
        workflow_steps.append(
            {
                "step": len(workflow_steps) + 1,
                "action": "investigate_issue",
                "description": "Thorough investigation of the reported issue",
                "timeline": "1-2 business days",
                "responsible": department,
                "status": "pending",
            }
        )

        # Resolution
        workflow_steps.append(
            {
                "step": len(workflow_steps) + 1,
                "action": "implement_solution",
                "description": "Implement solution and inform customer",
                "timeline": "2-3 business days",
                "responsible": department,
                "status": "pending",
            }
        )

        # Follow-up
        workflow_steps.append(
            {
                "step": len(workflow_steps) + 1,
                "action": "follow_up",
                "description": "Follow up with customer satisfaction",
                "timeline": "1 week after resolution",
                "responsible": "customer_service",
                "status": "pending",
            }
        )

        return workflow_steps

    def track_resolution_effectiveness(self, complaint_id: str, resolution_data: Dict) -> Dict:
        """Track and analyze resolution effectiveness"""

        try:
            # Calculate resolution metrics
            resolution_time = resolution_data.get("resolution_time_hours", 0)
            customer_satisfaction = resolution_data.get("satisfaction_score", 0)
            escalation_count = resolution_data.get("escalation_count", 0)

            # Effectiveness score calculation
            time_score = max(0, 1 - (resolution_time / 168))  # 1 week baseline
            satisfaction_score = customer_satisfaction / 5.0  # 5-star scale
            escalation_penalty = max(0, 1 - (escalation_count * 0.2))

            effectiveness_score = (time_score + satisfaction_score + escalation_penalty) / 3

            # Generate insights
            insights = []
            if resolution_time > 72:
                insights.append("Resolution time exceeded 3 days - consider process optimization")

            if customer_satisfaction < 3:
                insights.append("Low customer satisfaction - review resolution quality")

            if escalation_count > 1:
                insights.append("Multiple escalations - improve first-level resolution")

            if effectiveness_score > 0.8:
                insights.append("Excellent resolution performance")

            return {
                "effectiveness_score": effectiveness_score,
                "resolution_time_hours": resolution_time,
                "customer_satisfaction": customer_satisfaction,
                "escalation_count": escalation_count,
                "insights": insights,
                "improvement_recommendations": self._generate_improvement_recommendations(
                    resolution_data
                ),
            }

        except Exception as e:
            logger.error(f"Resolution tracking error: {str(e)}")
            return {"error": str(e)}

    def _generate_improvement_recommendations(self, resolution_data: Dict) -> List[str]:
        """Generate AI-powered improvement recommendations"""

        recommendations = []

        resolution_time = resolution_data.get("resolution_time_hours", 0)
        satisfaction = resolution_data.get("satisfaction_score", 0)
        category = resolution_data.get("category", "general")

        if resolution_time > 48:
            recommendations.append(f"Implement faster {category} issue resolution procedures")

        if satisfaction < 4:
            recommendations.append("Enhance customer communication during resolution process")

        recommendations.append(
            "Consider implementing AI-powered auto-resolution for similar issues"
        )

        return recommendations


# Global instance
genai_agent = GenAICustomerServiceAgent()
