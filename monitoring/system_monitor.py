# -*- coding: utf-8 -*-
"""
System Monitoring Module for Solutio 360 PWA
===========================================

Enterprise-grade monitoring inspired by:
- Netflix's monitoring infrastructure
- Google's SRE monitoring practices
- Datadog's APM system
- New Relic's observability platform
"""

import asyncio
import json
import logging
import threading
import time
from collections import deque
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from django.conf import settings
from django.core.cache import cache
from django.db import connection
from django.utils import timezone

import prometheus_client
import psutil
import requests
from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram

logger = logging.getLogger(__name__)


@dataclass
class SystemMetrics:
    """System metrics data structure"""

    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_total_mb: float
    disk_percent: float
    disk_used_gb: float
    disk_total_gb: float
    network_bytes_sent: int
    network_bytes_recv: int
    active_connections: int
    load_average: List[float]


@dataclass
class DatabaseMetrics:
    """Database metrics data structure"""

    timestamp: datetime
    connection_count: int
    active_queries: int
    slow_queries: int
    cache_hit_ratio: float
    database_size_mb: float
    longest_query_time: float
    avg_query_time: float


@dataclass
class ApplicationMetrics:
    """Application-specific metrics"""

    timestamp: datetime
    request_count: int
    response_time_avg: float
    error_rate: float
    active_users: int
    complaint_processing_rate: float
    memory_usage_mb: float
    cache_hit_rate: float


class PrometheusMetrics:
    """
    Prometheus metrics collector for monitoring
    """

    def __init__(self):
        # System metrics
        self.cpu_usage = Gauge("system_cpu_usage_percent", "CPU usage percentage")
        self.memory_usage = Gauge("system_memory_usage_percent", "Memory usage percentage")
        self.disk_usage = Gauge("system_disk_usage_percent", "Disk usage percentage")

        # Database metrics
        self.db_connections = Gauge("database_connections_active", "Active database connections")
        self.db_query_time = Histogram("database_query_duration_seconds", "Database query duration")
        self.db_slow_queries = Counter("database_slow_queries_total", "Total slow database queries")

        # Application metrics
        self.http_requests = Counter(
            "http_requests_total",
            "Total HTTP requests",
            ["method", "endpoint", "status"],
        )
        self.response_time = Histogram("http_request_duration_seconds", "HTTP request duration")
        self.active_users = Gauge("application_active_users", "Currently active users")
        self.complaint_processing = Counter(
            "complaints_processed_total", "Total complaints processed", ["status"]
        )

        # Error metrics
        self.errors = Counter(
            "application_errors_total", "Total application errors", ["type", "severity"]
        )

    def update_system_metrics(self, metrics: SystemMetrics):
        """Update Prometheus system metrics"""
        self.cpu_usage.set(metrics.cpu_percent)
        self.memory_usage.set(metrics.memory_percent)
        self.disk_usage.set(metrics.disk_percent)

    def update_database_metrics(self, metrics: DatabaseMetrics):
        """Update Prometheus database metrics"""
        self.db_connections.set(metrics.connection_count)
        if metrics.slow_queries > 0:
            self.db_slow_queries.inc(metrics.slow_queries)

    def record_request(self, method: str, endpoint: str, status: int, duration: float):
        """Record HTTP request metrics"""
        self.http_requests.labels(method=method, endpoint=endpoint, status=status).inc()
        self.response_time.observe(duration)

    def record_error(self, error_type: str, severity: str = "error"):
        """Record application error"""
        self.errors.labels(type=error_type, severity=severity).inc()


class SystemMonitor:
    """
    Comprehensive system monitoring class
    """

    def __init__(self, collection_interval: int = 60):
        self.collection_interval = collection_interval
        self.metrics_history = deque(maxlen=1440)  # Store 24 hours of metrics (1 min intervals)
        self.prometheus = PrometheusMetrics()
        self.is_monitoring = False
        self.monitor_thread = None

    def start_monitoring(self):
        """Start the monitoring process"""
        if not self.is_monitoring:
            self.is_monitoring = True
            self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            self.monitor_thread.start()
            logger.info("System monitoring started")

    def stop_monitoring(self):
        """Stop the monitoring process"""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()
        logger.info("System monitoring stopped")

    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.is_monitoring:
            try:
                # Collect system metrics
                system_metrics = self._collect_system_metrics()
                self.prometheus.update_system_metrics(system_metrics)

                # Collect database metrics
                db_metrics = self._collect_database_metrics()
                self.prometheus.update_database_metrics(db_metrics)

                # Store in history
                self.metrics_history.append(
                    {
                        "system": asdict(system_metrics),
                        "database": asdict(db_metrics),
                        "timestamp": timezone.now().isoformat(),
                    }
                )

                # Check for alerts
                self._check_alert_conditions(system_metrics, db_metrics)

                time.sleep(self.collection_interval)

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(self.collection_interval)

    def _collect_system_metrics(self) -> SystemMetrics:
        """Collect system-level metrics"""

        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)

        # Memory usage
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_used_mb = memory.used / (1024 * 1024)
        memory_total_mb = memory.total / (1024 * 1024)

        # Disk usage
        disk = psutil.disk_usage("/")
        disk_percent = (disk.used / disk.total) * 100
        disk_used_gb = disk.used / (1024 * 1024 * 1024)
        disk_total_gb = disk.total / (1024 * 1024 * 1024)

        # Network usage
        network = psutil.net_io_counters()

        # System load
        try:
            load_avg = list(psutil.getloadavg())
        except AttributeError:
            # Windows doesn't have getloadavg
            load_avg = [0.0, 0.0, 0.0]

        # Active connections
        active_connections = len(psutil.net_connections())

        return SystemMetrics(
            timestamp=timezone.now(),
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            memory_used_mb=memory_used_mb,
            memory_total_mb=memory_total_mb,
            disk_percent=disk_percent,
            disk_used_gb=disk_used_gb,
            disk_total_gb=disk_total_gb,
            network_bytes_sent=network.bytes_sent,
            network_bytes_recv=network.bytes_recv,
            active_connections=active_connections,
            load_average=load_avg,
        )

    def _collect_database_metrics(self) -> DatabaseMetrics:
        """Collect database-specific metrics"""

        with connection.cursor() as cursor:
            # Connection count
            cursor.execute(
                """
                SELECT count(*) FROM pg_stat_activity
                WHERE state = 'active';
            """
            )
            connection_count = cursor.fetchone()[0]

            # Active queries
            cursor.execute(
                """
                SELECT count(*) FROM pg_stat_activity
                WHERE state = 'active' AND query != '<IDLE>';
            """
            )
            active_queries = cursor.fetchone()[0]

            # Slow queries (queries running longer than 5 seconds)
            cursor.execute(
                """
                SELECT count(*) FROM pg_stat_activity
                WHERE state = 'active' 
                AND now() - query_start > interval '5 seconds';
            """
            )
            slow_queries = cursor.fetchone()[0]

            # Database size
            cursor.execute(
                """
                SELECT pg_size_pretty(pg_database_size(current_database()));
            """
            )
            db_size_str = cursor.fetchone()[0]

            # Extract numeric value (simplified)
            try:
                db_size_mb = float(db_size_str.split()[0])
                if "GB" in db_size_str:
                    db_size_mb *= 1024
            except:
                db_size_mb = 0.0

            # Query statistics
            cursor.execute(
                """
                SELECT 
                    COALESCE(max(EXTRACT(EPOCH FROM (now() - query_start))), 0) as longest_query,
                    COALESCE(avg(EXTRACT(EPOCH FROM (now() - query_start))), 0) as avg_query_time
                FROM pg_stat_activity
                WHERE state = 'active' AND query != '<IDLE>';
            """
            )
            query_stats = cursor.fetchone()
            longest_query_time = query_stats[0] if query_stats[0] else 0.0
            avg_query_time = query_stats[1] if query_stats[1] else 0.0

        # Cache hit ratio (mock calculation)
        cache_hit_ratio = 95.0  # This would be calculated from actual cache stats

        return DatabaseMetrics(
            timestamp=timezone.now(),
            connection_count=connection_count,
            active_queries=active_queries,
            slow_queries=slow_queries,
            cache_hit_ratio=cache_hit_ratio,
            database_size_mb=db_size_mb,
            longest_query_time=longest_query_time,
            avg_query_time=avg_query_time,
        )

    def _check_alert_conditions(self, system: SystemMetrics, database: DatabaseMetrics):
        """Check for alert conditions and trigger notifications"""

        alerts = []

        # High CPU usage
        if system.cpu_percent > 80:
            alerts.append(
                {
                    "type": "cpu_high",
                    "severity": "warning" if system.cpu_percent < 90 else "critical",
                    "message": f"High CPU usage: {system.cpu_percent:.1f}%",
                    "value": system.cpu_percent,
                    "threshold": 80,
                }
            )

        # High memory usage
        if system.memory_percent > 85:
            alerts.append(
                {
                    "type": "memory_high",
                    "severity": "warning" if system.memory_percent < 95 else "critical",
                    "message": f"High memory usage: {system.memory_percent:.1f}%",
                    "value": system.memory_percent,
                    "threshold": 85,
                }
            )

        # High disk usage
        if system.disk_percent > 90:
            alerts.append(
                {
                    "type": "disk_high",
                    "severity": "critical",
                    "message": f"High disk usage: {system.disk_percent:.1f}%",
                    "value": system.disk_percent,
                    "threshold": 90,
                }
            )

        # Too many database connections
        if database.connection_count > 80:
            alerts.append(
                {
                    "type": "db_connections_high",
                    "severity": "warning",
                    "message": f"High database connections: {database.connection_count}",
                    "value": database.connection_count,
                    "threshold": 80,
                }
            )

        # Slow queries detected
        if database.slow_queries > 0:
            alerts.append(
                {
                    "type": "slow_queries",
                    "severity": "warning",
                    "message": f"Slow queries detected: {database.slow_queries}",
                    "value": database.slow_queries,
                    "threshold": 0,
                }
            )

        # Send alerts if any
        if alerts:
            self._send_alerts(alerts)

    def _send_alerts(self, alerts: List[Dict[str, Any]]):
        """Send alerts to notification channels"""

        for alert in alerts:
            # Log the alert
            logger.warning(f"ALERT: {alert['message']}")

            # Send to Slack (if configured)
            self._send_slack_alert(alert)

            # Send to email (if configured)
            self._send_email_alert(alert)

            # Store in database for dashboard
            self._store_alert(alert)

    def _send_slack_alert(self, alert: Dict[str, Any]):
        """Send alert to Slack"""

        slack_webhook = getattr(settings, "SLACK_WEBHOOK_URL", None)
        if not slack_webhook:
            return

        color = {"warning": "#ffcc00", "critical": "#ff0000", "info": "#00ff00"}.get(
            alert["severity"], "#ffcc00"
        )

        payload = {
            "username": "Solutio360 Monitor",
            "icon_emoji": ":warning:",
            "attachments": [
                {
                    "color": color,
                    "title": f"System Alert - {alert['type']}",
                    "text": alert["message"],
                    "fields": [
                        {
                            "title": "Severity",
                            "value": alert["severity"].upper(),
                            "short": True,
                        },
                        {
                            "title": "Current Value",
                            "value": str(alert["value"]),
                            "short": True,
                        },
                        {
                            "title": "Threshold",
                            "value": str(alert["threshold"]),
                            "short": True,
                        },
                        {
                            "title": "Time",
                            "value": timezone.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "short": True,
                        },
                    ],
                }
            ],
        }

        try:
            requests.post(slack_webhook, json=payload, timeout=10)
        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")

    def _send_email_alert(self, alert: Dict[str, Any]):
        """Send alert via email"""

        from django.core.mail import send_mail

        try:
            subject = f"[Solutio360] System Alert - {alert['type']}"
            message = f"""
            System Alert Detected
            
            Type: {alert['type']}
            Severity: {alert['severity'].upper()}
            Message: {alert['message']}
            Current Value: {alert['value']}
            Threshold: {alert['threshold']}
            Time: {timezone.now()}
            
            Please check the system dashboard for more details.
            """

            admin_emails = [admin[1] for admin in settings.ADMINS]
            if admin_emails:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    admin_emails,
                    fail_silently=True,
                )
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")

    def _store_alert(self, alert: Dict[str, Any]):
        """Store alert in database for dashboard display"""

        try:
            from core.models import SystemAlert

            SystemAlert.objects.create(
                alert_type=alert["type"],
                severity=alert["severity"],
                message=alert["message"],
                current_value=alert["value"],
                threshold_value=alert["threshold"],
                is_resolved=False,
            )
        except Exception as e:
            logger.error(f"Failed to store alert in database: {e}")

    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current system metrics"""

        system_metrics = self._collect_system_metrics()
        db_metrics = self._collect_database_metrics()

        return {
            "system": asdict(system_metrics),
            "database": asdict(db_metrics),
            "timestamp": timezone.now().isoformat(),
        }

    def get_metrics_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get metrics history for specified hours"""

        cutoff_time = timezone.now() - timedelta(hours=hours)

        return [
            metric
            for metric in self.metrics_history
            if datetime.fromisoformat(metric["timestamp"].replace("Z", "+00:00")) > cutoff_time
        ]

    def get_system_health_score(self) -> Dict[str, Any]:
        """Calculate overall system health score"""

        if not self.metrics_history:
            return {"score": 100, "status": "unknown"}

        recent_metrics = list(self.metrics_history)[-10:]  # Last 10 readings

        scores = []
        for metric_set in recent_metrics:
            system = metric_set["system"]
            database = metric_set["database"]

            # CPU score (0-100, inverted)
            cpu_score = max(0, 100 - system["cpu_percent"])

            # Memory score (0-100, inverted)
            memory_score = max(0, 100 - system["memory_percent"])

            # Disk score (0-100, inverted)
            disk_score = max(0, 100 - system["disk_percent"])

            # Database score
            db_score = 100
            if database["slow_queries"] > 0:
                db_score -= 20
            if database["connection_count"] > 50:
                db_score -= 10
            if database["avg_query_time"] > 1.0:
                db_score -= 15

            # Overall score (weighted average)
            overall_score = cpu_score * 0.3 + memory_score * 0.3 + disk_score * 0.2 + db_score * 0.2

            scores.append(overall_score)

        avg_score = sum(scores) / len(scores)

        # Determine status
        if avg_score >= 90:
            status = "excellent"
        elif avg_score >= 80:
            status = "good"
        elif avg_score >= 70:
            status = "fair"
        elif avg_score >= 60:
            status = "poor"
        else:
            status = "critical"

        return {
            "score": round(avg_score, 1),
            "status": status,
            "scores_history": scores,
        }


class ApplicationMonitor:
    """
    Application-specific monitoring for Django
    """

    def __init__(self):
        self.request_times = deque(maxlen=1000)
        self.error_count = 0
        self.request_count = 0

    def record_request(self, request, response, process_time):
        """Record request metrics"""

        self.request_count += 1
        self.request_times.append(process_time)

        # Record in Prometheus
        prometheus = PrometheusMetrics()
        prometheus.record_request(
            method=request.method,
            endpoint=request.path,
            status=response.status_code,
            duration=process_time,
        )

        # Log slow requests
        if process_time > 2.0:  # Requests slower than 2 seconds
            logger.warning(f"Slow request: {request.method} {request.path} - {process_time:.2f}s")

    def record_error(self, error_type: str, severity: str = "error"):
        """Record application error"""

        self.error_count += 1

        prometheus = PrometheusMetrics()
        prometheus.record_error(error_type, severity)

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get application performance metrics"""

        if not self.request_times:
            return {
                "avg_response_time": 0,
                "p95_response_time": 0,
                "request_rate": 0,
                "error_rate": 0,
            }

        times = list(self.request_times)

        return {
            "avg_response_time": sum(times) / len(times),
            "p95_response_time": sorted(times)[int(len(times) * 0.95)],
            "request_rate": len(times) / 60,  # Requests per minute
            "error_rate": (
                (self.error_count / self.request_count) * 100 if self.request_count > 0 else 0
            ),
        }


# Global monitor instances
system_monitor = SystemMonitor()
application_monitor = ApplicationMonitor()


def start_monitoring():
    """Start all monitoring systems"""
    system_monitor.start_monitoring()
    logger.info("All monitoring systems started")


def stop_monitoring():
    """Stop all monitoring systems"""
    system_monitor.stop_monitoring()
    logger.info("All monitoring systems stopped")


def get_comprehensive_status() -> Dict[str, Any]:
    """Get comprehensive system status"""

    return {
        "system_metrics": system_monitor.get_current_metrics(),
        "application_metrics": application_monitor.get_performance_metrics(),
        "health_score": system_monitor.get_system_health_score(),
        "timestamp": timezone.now().isoformat(),
    }
