"""
Multi-Departmental Complaint Routing System
Enterprise-grade intelligent routing inspired by LeewayHertz solutions
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from django.db import models
from django.utils import timezone

from complaints.models import Complaint
from users.models import User

logger = logging.getLogger(__name__)


@dataclass
class DepartmentCapacity:
    """Department capacity and workload information"""

    department_id: str
    name: str
    current_workload: int
    max_capacity: int
    average_resolution_time: float
    specialization_score: float
    availability_status: str  # 'available', 'busy', 'offline'


@dataclass
class RoutingRule:
    """Smart routing rule definition"""

    rule_id: str
    name: str
    priority: int
    conditions: Dict
    target_department: str
    confidence_threshold: float
    is_active: bool


class DepartmentRouter:
    """
    Intelligent multi-departmental complaint routing system
    Features enterprise-level department management and load balancing
    """

    def __init__(self):
        self.departments = {
            "technical_support": {
                "name": "Teknik Destek",
                "specializations": ["bug", "error", "system", "software", "technical"],
                "max_capacity": 50,
                "priority_handling": ["critical", "high"],
                "working_hours": {"start": 9, "end": 18},
                "escalation_threshold": 4,  # hours
            },
            "billing": {
                "name": "Faturalama",
                "specializations": [
                    "payment",
                    "bill",
                    "refund",
                    "subscription",
                    "pricing",
                ],
                "max_capacity": 30,
                "priority_handling": ["critical", "high", "medium"],
                "working_hours": {"start": 9, "end": 17},
                "escalation_threshold": 24,  # hours
            },
            "customer_service": {
                "name": "Müşteri Hizmetleri",
                "specializations": ["service", "support", "general", "experience"],
                "max_capacity": 40,
                "priority_handling": ["medium", "low"],
                "working_hours": {"start": 8, "end": 20},
                "escalation_threshold": 48,  # hours
            },
            "product_quality": {
                "name": "Ürün Kalitesi",
                "specializations": ["product", "quality", "defective", "functionality"],
                "max_capacity": 25,
                "priority_handling": ["critical", "high"],
                "working_hours": {"start": 9, "end": 18},
                "escalation_threshold": 8,  # hours
            },
            "logistics": {
                "name": "Lojistik",
                "specializations": ["delivery", "shipping", "tracking", "warehouse"],
                "max_capacity": 35,
                "priority_handling": ["high", "medium"],
                "working_hours": {"start": 8, "end": 19},
                "escalation_threshold": 12,  # hours
            },
        }

        self.routing_rules = self._initialize_routing_rules()
        self.load_balancing_enabled = True
        self.smart_escalation_enabled = True

    def route_complaint(self, complaint: Complaint, ai_analysis: Dict = None) -> Dict:
        """
        Route complaint to appropriate department with intelligent load balancing

        Returns:
            {
                'primary_department': str,
                'secondary_departments': List[str],
                'routing_confidence': float,
                'estimated_resolution_time': int,
                'assigned_agent': Optional[str],
                'routing_reasoning': str,
                'escalation_path': List[str]
            }
        """
        try:
            # Get department capacities
            dept_capacities = self._get_department_capacities()

            # Apply routing rules
            routing_scores = self._calculate_routing_scores(
                complaint, ai_analysis, dept_capacities
            )

            # Select primary department
            primary_dept = self._select_primary_department(
                routing_scores, dept_capacities
            )

            # Generate secondary options
            secondary_depts = self._get_secondary_departments(
                routing_scores, primary_dept
            )

            # Estimate resolution time
            estimated_time = self._estimate_resolution_time(
                primary_dept, complaint, ai_analysis
            )

            # Create escalation path
            escalation_path = self._create_escalation_path(
                primary_dept,
                complaint.priority if hasattr(complaint, "priority") else "medium",
            )

            # Generate routing reasoning
            reasoning = self._generate_routing_reasoning(
                primary_dept, routing_scores, dept_capacities
            )

            routing_result = {
                "primary_department": primary_dept,
                "secondary_departments": secondary_depts,
                "routing_confidence": routing_scores.get(primary_dept, {}).get(
                    "confidence", 0.7
                ),
                "estimated_resolution_time": estimated_time,
                "assigned_agent": self._assign_best_agent(primary_dept, complaint),
                "routing_reasoning": reasoning,
                "escalation_path": escalation_path,
                "load_balancing_applied": self.load_balancing_enabled,
                "routing_timestamp": timezone.now().isoformat(),
            }

            # Log routing decision
            self._log_routing_decision(complaint, routing_result)

            return routing_result

        except Exception as e:
            logger.error(f"Routing error for complaint {complaint.id}: {str(e)}")
            return self._fallback_routing(complaint)

    def _get_department_capacities(self) -> Dict[str, DepartmentCapacity]:
        """Get current department capacities and workloads"""

        capacities = {}

        for dept_id, dept_info in self.departments.items():
            # Calculate current workload (active complaints)
            current_workload = Complaint.objects.filter(
                assigned_department=dept_id,
                status__in=["submitted", "in_progress", "pending"],
            ).count()

            # Calculate average resolution time
            resolved_complaints = Complaint.objects.filter(
                assigned_department=dept_id,
                status="resolved",
                resolved_at__gte=timezone.now() - timedelta(days=30),
            )

            if resolved_complaints.exists():
                avg_resolution = (
                    sum(
                        [
                            (c.resolved_at - c.created_at).total_seconds() / 3600
                            for c in resolved_complaints
                            if c.resolved_at
                        ]
                    )
                    / resolved_complaints.count()
                )
            else:
                avg_resolution = dept_info["escalation_threshold"]

            # Calculate specialization score (performance metric)
            specialization_score = self._calculate_specialization_score(dept_id)

            # Determine availability status
            availability = self._get_department_availability(dept_id, dept_info)

            capacities[dept_id] = DepartmentCapacity(
                department_id=dept_id,
                name=dept_info["name"],
                current_workload=current_workload,
                max_capacity=dept_info["max_capacity"],
                average_resolution_time=avg_resolution,
                specialization_score=specialization_score,
                availability_status=availability,
            )

        return capacities

    def _calculate_routing_scores(
        self, complaint: Complaint, ai_analysis: Dict, dept_capacities: Dict
    ) -> Dict:
        """Calculate routing scores for each department"""

        scores = {}
        complaint_text = complaint.description.lower()

        for dept_id, dept_info in self.departments.items():
            score_components = {}

            # 1. Keyword matching score
            keyword_score = 0
            for keyword in dept_info["specializations"]:
                if keyword in complaint_text:
                    keyword_score += 1
            score_components["keyword_match"] = min(
                keyword_score / len(dept_info["specializations"]), 1.0
            )

            # 2. AI analysis score
            ai_score = 0
            if ai_analysis:
                category = ai_analysis.get("category", {}).get("primary", "")
                if category == dept_id or category in dept_info["specializations"]:
                    ai_score = ai_analysis.get("category", {}).get("confidence", 0.5)
            score_components["ai_confidence"] = ai_score

            # 3. Department capacity score
            capacity = dept_capacities[dept_id]
            if capacity.max_capacity > 0:
                capacity_ratio = capacity.current_workload / capacity.max_capacity
                capacity_score = max(0, 1 - capacity_ratio)
            else:
                capacity_score = 0
            score_components["capacity_available"] = capacity_score

            # 4. Specialization performance score
            score_components["specialization_performance"] = (
                capacity.specialization_score
            )

            # 5. Priority handling capability
            complaint_priority = getattr(complaint, "priority", "medium")
            priority_score = (
                1.0 if complaint_priority in dept_info["priority_handling"] else 0.3
            )
            score_components["priority_capability"] = priority_score

            # 6. Availability score
            availability_score = (
                1.0 if capacity.availability_status == "available" else 0.5
            )
            score_components["availability"] = availability_score

            # Calculate weighted total score
            weights = {
                "keyword_match": 0.25,
                "ai_confidence": 0.30,
                "capacity_available": 0.20,
                "specialization_performance": 0.15,
                "priority_capability": 0.10,
            }

            total_score = sum(
                score_components[component] * weights[component]
                for component in weights
            )

            scores[dept_id] = {
                "total_score": total_score,
                "confidence": min(total_score + 0.1, 1.0),
                "components": score_components,
            }

        return scores

    def _select_primary_department(
        self, routing_scores: Dict, dept_capacities: Dict
    ) -> str:
        """Select primary department based on scores and load balancing"""

        # Sort departments by score
        sorted_depts = sorted(
            routing_scores.items(), key=lambda x: x[1]["total_score"], reverse=True
        )

        # If load balancing is enabled, consider capacity
        if self.load_balancing_enabled and len(sorted_depts) > 1:
            top_dept = sorted_depts[0][0]
            second_dept = sorted_depts[1][0]

            top_capacity = dept_capacities[top_dept]
            second_capacity = dept_capacities[second_dept]

            # If top department is overloaded and second has similar score
            score_diff = (
                sorted_depts[0][1]["total_score"] - sorted_depts[1][1]["total_score"]
            )
            if (
                score_diff < 0.15
                and top_capacity.current_workload >= top_capacity.max_capacity * 0.9
                and second_capacity.current_workload
                < second_capacity.max_capacity * 0.7
            ):
                return second_dept

        return sorted_depts[0][0]

    def _get_secondary_departments(
        self, routing_scores: Dict, primary_dept: str
    ) -> List[str]:
        """Get secondary department options"""

        sorted_depts = sorted(
            [
                (dept, score)
                for dept, score in routing_scores.items()
                if dept != primary_dept
            ],
            key=lambda x: x[1]["total_score"],
            reverse=True,
        )

        return [dept for dept, score in sorted_depts[:2] if score["total_score"] > 0.3]

    def _estimate_resolution_time(
        self, department: str, complaint: Complaint, ai_analysis: Dict = None
    ) -> int:
        """Estimate resolution time in hours"""

        dept_info = self.departments[department]
        base_time = dept_info["escalation_threshold"]

        # Adjust based on complexity
        complexity_multiplier = 1.0
        if ai_analysis:
            complexity = ai_analysis.get("complexity_score", 0.5)
            complexity_multiplier = 0.5 + complexity

        # Adjust based on priority
        priority = getattr(complaint, "priority", "medium")
        priority_multipliers = {
            "critical": 0.25,
            "high": 0.5,
            "medium": 1.0,
            "low": 1.5,
        }

        estimated_hours = int(
            base_time * complexity_multiplier * priority_multipliers.get(priority, 1.0)
        )

        return max(1, estimated_hours)

    def _create_escalation_path(self, primary_dept: str, priority: str) -> List[str]:
        """Create escalation path for the complaint"""

        escalation_path = [primary_dept]

        # Add manager escalation for high priority
        if priority in ["critical", "high"]:
            escalation_path.append(f"{primary_dept}_manager")

        # Add general manager for critical issues
        if priority == "critical":
            escalation_path.append("general_manager")
            escalation_path.append("executive_team")

        return escalation_path

    def _assign_best_agent(
        self, department: str, complaint: Complaint
    ) -> Optional[str]:
        """Assign best available agent in the department"""

        try:
            # Get agents in the department with lowest current workload
            agents = (
                User.objects.filter(role__department=department, is_active=True)
                .annotate(
                    current_complaints=models.Count(
                        "assigned_complaints",
                        filter=models.Q(
                            assigned_complaints__status__in=["submitted", "in_progress"]
                        ),
                    )
                )
                .order_by("current_complaints")
            )

            if agents.exists():
                return agents.first().username

        except Exception as e:
            logger.error(f"Agent assignment error: {str(e)}")

        return None

    def _calculate_specialization_score(self, dept_id: str) -> float:
        """Calculate department specialization performance score"""

        # Get recent resolved complaints for this department
        recent_complaints = Complaint.objects.filter(
            assigned_department=dept_id,
            status="resolved",
            resolved_at__gte=timezone.now() - timedelta(days=30),
        )

        if not recent_complaints.exists():
            return 0.7  # Default score

        # Calculate average satisfaction (if available)
        # For now, use resolution time as proxy for performance
        avg_resolution_time = (
            sum(
                [
                    (c.resolved_at - c.created_at).total_seconds() / 3600
                    for c in recent_complaints
                    if c.resolved_at
                ]
            )
            / recent_complaints.count()
        )

        dept_threshold = self.departments[dept_id]["escalation_threshold"]

        # Score based on how well they meet their threshold
        if avg_resolution_time <= dept_threshold * 0.5:
            return 1.0
        elif avg_resolution_time <= dept_threshold:
            return 0.8
        elif avg_resolution_time <= dept_threshold * 1.5:
            return 0.6
        else:
            return 0.4

    def _get_department_availability(self, dept_id: str, dept_info: Dict) -> str:
        """Check department availability based on working hours and capacity"""

        current_hour = timezone.now().hour
        working_start = dept_info["working_hours"]["start"]
        working_end = dept_info["working_hours"]["end"]

        # Check working hours
        if not (working_start <= current_hour <= working_end):
            return "offline"

        # Check capacity (simplified - would integrate with real-time agent status)
        return "available"

    def _generate_routing_reasoning(
        self, primary_dept: str, routing_scores: Dict, dept_capacities: Dict
    ) -> str:
        """Generate human-readable routing reasoning"""

        score_info = routing_scores[primary_dept]
        capacity_info = dept_capacities[primary_dept]

        reasons = []

        # Top scoring factors
        components = score_info["components"]
        top_factors = sorted(components.items(), key=lambda x: x[1], reverse=True)[:2]

        for factor, score in top_factors:
            if score > 0.7:
                if factor == "keyword_match":
                    reasons.append("güçlü kelime eşleşmesi")
                elif factor == "ai_confidence":
                    reasons.append("AI kategorilendirme güveni")
                elif factor == "capacity_available":
                    reasons.append("departman kapasitesi uygun")
                elif factor == "specialization_performance":
                    reasons.append("yüksek uzmanlaşma performansı")

        if capacity_info.current_workload < capacity_info.max_capacity * 0.5:
            reasons.append("düşük iş yükü")

        reasoning = (
            f"{self.departments[primary_dept]['name']} departmanına yönlendirildi: "
            + ", ".join(reasons)
        )

        return reasoning

    def _log_routing_decision(self, complaint: Complaint, routing_result: Dict):
        """Log routing decision for analysis and improvement"""

        try:
            # Would integrate with analytics system
            logger.info(
                f"Complaint {complaint.id} routed to {routing_result['primary_department']} "
                f"with confidence {routing_result['routing_confidence']:.2f}"
            )
        except Exception as e:
            logger.error(f"Routing logging error: {str(e)}")

    def _fallback_routing(self, complaint: Complaint) -> Dict:
        """Fallback routing when main system fails"""

        return {
            "primary_department": "customer_service",
            "secondary_departments": ["technical_support"],
            "routing_confidence": 0.5,
            "estimated_resolution_time": 24,
            "assigned_agent": None,
            "routing_reasoning": "Fallback routing to customer service",
            "escalation_path": ["customer_service", "customer_service_manager"],
            "fallback_mode": True,
        }

    def _initialize_routing_rules(self) -> List[RoutingRule]:
        """Initialize smart routing rules"""

        return [
            RoutingRule(
                rule_id="critical_technical",
                name="Critical Technical Issues",
                priority=1,
                conditions={
                    "priority": "critical",
                    "category": "technical",
                    "keywords": ["system down", "critical error", "data loss"],
                },
                target_department="technical_support",
                confidence_threshold=0.9,
                is_active=True,
            ),
            RoutingRule(
                rule_id="billing_disputes",
                name="Billing Disputes",
                priority=2,
                conditions={
                    "category": "billing",
                    "keywords": ["refund", "charge", "billing error", "payment"],
                },
                target_department="billing",
                confidence_threshold=0.8,
                is_active=True,
            ),
            # Add more rules as needed
        ]

    def update_routing_performance(
        self, complaint_id: str, actual_resolution_data: Dict
    ):
        """Update routing performance based on actual resolution outcomes"""

        try:
            # This would update ML models and routing algorithms
            # based on actual performance data
            logger.info(f"Updating routing performance for complaint {complaint_id}")

            # Analytics for continuous improvement
            resolution_time = actual_resolution_data.get("resolution_time_hours", 0)
            satisfaction = actual_resolution_data.get("satisfaction_score", 0)

            # Would update department performance scores
            # and routing algorithm weights

        except Exception as e:
            logger.error(f"Performance update error: {str(e)}")


# Global instance
department_router = DepartmentRouter()
