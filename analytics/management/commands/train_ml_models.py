# ML Training Command
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from analytics.ml_engine import get_incremental_model, get_rl_agent
from complaints.models import Complaint


class Command(BaseCommand):
    help = "Train ML models for Solutio 360"

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=30, help="Days of data to use")
        parser.add_argument(
            "--component", choices=["rl", "incremental", "all"], default="all"
        )

    def handle(self, *args, **options):
        days = options["days"]
        component = options["component"]

        self.stdout.write("Starting ML model training...")

        # Get historical data
        since_date = timezone.now() - timedelta(days=days)
        resolved_complaints = Complaint.objects.filter(
            status="RESOLVED", created_at__gte=since_date
        )

        total_count = resolved_complaints.count()
        self.stdout.write(f"Found {total_count} resolved complaints")

        if total_count < 5:
            self.stdout.write(self.style.ERROR("Not enough data for training"))
            return

        # Train RL Agent
        if component in ["rl", "all"]:
            self.stdout.write("Training RL agent...")
            rl_agent = get_rl_agent()

            for complaint in resolved_complaints[:100]:
                state = rl_agent.get_state(complaint)
                action = "assign_to_expert"
                reward = 1.0
                next_state = ("RESOLVED", "COMPLETED", "DONE", "BUSINESS_HOURS")
                rl_agent.update_q_value(state, action, reward, next_state)

            self.stdout.write(
                self.style.SUCCESS(
                    f"RL agent trained: {rl_agent.episode_count} episodes"
                )
            )

        # Train Incremental Model
        if component in ["incremental", "all"]:
            self.stdout.write("Training incremental model...")
            model = get_incremental_model()
            model.partial_fit(list(resolved_complaints))

            self.stdout.write(
                self.style.SUCCESS(f"Incremental model trained: {model.is_trained}")
            )

        self.stdout.write(self.style.SUCCESS("ML training completed!"))
