# -*- coding: utf-8 -*-
"""
Database Optimization Module for Solutio 360 PWA
================================================

World-class database optimization techniques inspired by:
- Netflix's database scaling practices
- Instagram's performance optimization
- Discord's database architecture
- Shopify's performance engineering
"""

import logging
import time
from functools import wraps
from typing import Any, Dict, List

from django.core.cache import cache
from django.db import connection, transaction
from django.db.models import Prefetch, Q
from django.utils import timezone

logger = logging.getLogger(__name__)


class DatabaseOptimizer:
    """
    Database optimization utilities for enhanced performance
    """

    @staticmethod
    def analyze_query_performance():
        """
        Analyze and log slow queries for optimization
        """
        queries = connection.queries
        slow_queries = []

        for query in queries:
            time_taken = float(query["time"])
            if time_taken > 0.1:  # Queries slower than 100ms
                slow_queries.append({"sql": query["sql"], "time": time_taken})

        if slow_queries:
            logger.warning(f"Found {len(slow_queries)} slow queries")
            for query in slow_queries:
                logger.warning(
                    f"Slow query ({query['time']}s): {query['sql'][:100]}..."
                )

        return slow_queries

    @staticmethod
    def optimize_complaint_queries():
        """
        Optimized queries for complaint operations
        """
        from complaints.models import Complaint

        # Optimized complaint list with select_related and prefetch_related
        return Complaint.objects.select_related(
            "category", "submitter", "assigned_to", "department"
        ).prefetch_related(
            "tags",
            "complained_institutions",
            "complained_units",
            "complained_subunits",
            "complained_people",
            Prefetch(
                "comments",
                queryset=ComplaintComment.objects.select_related("sender", "receiver"),
            ),
            "attachments",
        )

    @staticmethod
    def get_complaint_statistics_optimized():
        """
        Optimized statistics queries using aggregation
        """
        from django.db.models import Avg, Count, Q

        from complaints.models import Complaint

        stats = Complaint.objects.aggregate(
            total_complaints=Count("id"),
            pending_complaints=Count(
                "id", filter=Q(status__in=["SUBMITTED", "IN_REVIEW"])
            ),
            resolved_complaints=Count("id", filter=Q(status="RESOLVED")),
            avg_resolution_days=Avg("resolution_date__date" - "created_at__date"),
        )

        return stats

    @staticmethod
    def create_database_indexes():
        """
        Create additional indexes for performance
        """
        from django.db import connection

        with connection.cursor() as cursor:
            # Index for complaint filtering
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_complaint_status_priority 
                ON complaints_complaint(status, priority);
            """
            )

            # Index for date range queries
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_complaint_created_date 
                ON complaints_complaint(created_at);
            """
            )

            # Index for user complaints
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_complaint_submitter_status 
                ON complaints_complaint(submitter_id, status);
            """
            )

            # Composite index for common queries
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_complaint_category_status_created 
                ON complaints_complaint(category_id, status, created_at);
            """
            )


def query_debugger(func):
    """
    Decorator to debug and log query performance
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        reset_queries()
        start_time = time.time()

        result = func(*args, **kwargs)

        end_time = time.time()
        execution_time = end_time - start_time

        queries = connection.queries
        total_queries = len(queries)
        total_time = sum(float(q["time"]) for q in queries)

        logger.info(
            f"""
        Function: {func.__name__}
        Execution Time: {execution_time:.4f}s
        Database Queries: {total_queries}
        Database Time: {total_time:.4f}s
        """
        )

        # Log slow queries
        for query in queries:
            if float(query["time"]) > 0.05:  # 50ms threshold
                logger.warning(
                    f"Slow query: {query['sql'][:100]}... ({query['time']}s)"
                )

        return result

    return wrapper


def reset_queries():
    """Reset Django connection queries for debugging"""
    connection.queries_log.clear()


class CacheManager:
    """
    Intelligent caching manager for database operations
    """

    CACHE_TIMEOUTS = {
        "statistics": 300,  # 5 minutes
        "categories": 3600,  # 1 hour
        "users": 1800,  # 30 minutes
        "reports": 600,  # 10 minutes
    }

    @classmethod
    def get_or_set(
        cls, key: str, fetch_func, timeout: int = None, cache_type: str = "default"
    ):
        """
        Get data from cache or fetch and cache it
        """
        cache_key = f"solutio360:{cache_type}:{key}"

        # Try to get from cache
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return cached_data

        # Fetch data
        data = fetch_func()

        # Cache the data
        if timeout is None:
            timeout = cls.CACHE_TIMEOUTS.get(cache_type, 300)

        cache.set(cache_key, data, timeout)
        return data

    @classmethod
    def invalidate_cache_pattern(cls, pattern: str):
        """
        Invalidate cache keys matching a pattern
        """
        # This would require a cache backend that supports pattern matching
        # For Redis: cache.delete_pattern(f"solutio360:{pattern}:*")
        pass

    @classmethod
    def get_complaint_statistics_cached(cls):
        """
        Get complaint statistics with caching
        """

        def fetch_stats():
            return DatabaseOptimizer.get_complaint_statistics_optimized()

        return cls.get_or_set("complaint_stats", fetch_stats, cache_type="statistics")


class QueryOptimizer:
    """
    Query optimization utilities
    """

    @staticmethod
    def optimize_complaint_filters(queryset, filters: Dict[str, Any]):
        """
        Optimize complaint filtering with efficient database queries
        """
        from django.db.models import Q

        # Build Q objects for complex filtering
        query = Q()

        if filters.get("status"):
            query &= Q(status__in=filters["status"])

        if filters.get("priority"):
            query &= Q(priority__in=filters["priority"])

        if filters.get("category"):
            query &= Q(category_id__in=filters["category"])

        if filters.get("date_from"):
            query &= Q(created_at__gte=filters["date_from"])

        if filters.get("date_to"):
            query &= Q(created_at__lte=filters["date_to"])

        if filters.get("search"):
            search_query = Q(title__icontains=filters["search"]) | Q(
                description__icontains=filters["search"]
            )
            query &= search_query

        return queryset.filter(query)

    @staticmethod
    def paginate_efficiently(queryset, page: int, per_page: int = 25):
        """
        Efficient pagination with cursor-based pagination for large datasets
        """
        from django.core.paginator import Paginator

        # For small datasets, use offset-based pagination
        if queryset.count() < 10000:
            paginator = Paginator(queryset, per_page)
            return paginator.get_page(page)

        # For large datasets, use cursor-based pagination
        # This is more efficient for large offsets
        offset = (page - 1) * per_page
        return queryset[offset : offset + per_page]


class DatabaseMonitor:
    """
    Database performance monitoring utilities
    """

    @staticmethod
    def monitor_connection_pool():
        """
        Monitor database connection pool usage
        """
        from django.db import connections

        stats = {}
        for alias in connections:
            conn = connections[alias]
            stats[alias] = {
                "queries_count": len(conn.queries),
                "is_usable": conn.is_usable(),
            }

        return stats

    @staticmethod
    def analyze_table_sizes():
        """
        Analyze database table sizes for optimization
        """
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT 
                    table_name,
                    pg_size_pretty(pg_total_relation_size(table_name::regclass)) as size,
                    pg_total_relation_size(table_name::regclass) as size_bytes
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY pg_total_relation_size(table_name::regclass) DESC;
            """
            )

            return cursor.fetchall()

    @staticmethod
    def get_slow_queries_report():
        """
        Generate report of slow queries from PostgreSQL
        """
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT 
                    query,
                    calls,
                    total_time,
                    mean_time,
                    rows
                FROM pg_stat_statements 
                ORDER BY total_time DESC 
                LIMIT 10;
            """
            )

            return cursor.fetchall()


# Batch Operations for Bulk Processing
class BatchProcessor:
    """
    Efficient batch processing for large datasets
    """

    @staticmethod
    def bulk_update_complaints(complaint_ids: List[int], update_data: Dict[str, Any]):
        """
        Efficiently update multiple complaints
        """
        from complaints.models import Complaint

        with transaction.atomic():
            Complaint.objects.filter(id__in=complaint_ids).update(**update_data)

    @staticmethod
    def bulk_create_notifications(notifications_data: List[Dict[str, Any]]):
        """
        Efficiently create multiple notifications
        """
        from complaints.models import ComplaintNotification

        notifications = [ComplaintNotification(**data) for data in notifications_data]

        ComplaintNotification.objects.bulk_create(notifications, batch_size=1000)

    @staticmethod
    def process_in_batches(queryset, batch_size: int = 1000):
        """
        Process large querysets in batches to avoid memory issues
        """
        total = queryset.count()
        processed = 0

        while processed < total:
            batch = queryset[processed : processed + batch_size]
            yield batch
            processed += batch_size


# Database Maintenance Tasks
class DatabaseMaintenance:
    """
    Database maintenance and optimization tasks
    """

    @staticmethod
    def vacuum_analyze_tables():
        """
        Run VACUUM ANALYZE on PostgreSQL tables
        """
        with connection.cursor() as cursor:
            cursor.execute("VACUUM ANALYZE;")

    @staticmethod
    def update_table_statistics():
        """
        Update table statistics for query planner
        """
        with connection.cursor() as cursor:
            cursor.execute("ANALYZE;")

    @staticmethod
    def cleanup_old_sessions():
        """
        Clean up old Django sessions
        """
        from django.contrib.sessions.models import Session

        expired_sessions = Session.objects.filter(expire_date__lt=timezone.now())

        count = expired_sessions.count()
        expired_sessions.delete()

        logger.info(f"Cleaned up {count} expired sessions")
        return count

    @staticmethod
    def archive_old_complaints():
        """
        Archive complaints older than 2 years
        """
        from datetime import timedelta

        from complaints.models import Complaint

        cutoff_date = timezone.now() - timedelta(days=730)  # 2 years

        old_complaints = Complaint.objects.filter(
            created_at__lt=cutoff_date, status="CLOSED"
        )

        # Move to archive table or mark as archived
        count = old_complaints.update(is_archived=True)

        logger.info(f"Archived {count} old complaints")
        return count


# Performance Testing Utilities
class PerformanceTester:
    """
    Utilities for testing database performance
    """

    @staticmethod
    def benchmark_query(query_func, iterations: int = 100):
        """
        Benchmark a query function
        """
        times = []

        for _ in range(iterations):
            reset_queries()
            start_time = time.time()

            result = query_func()

            end_time = time.time()
            execution_time = end_time - start_time
            times.append(execution_time)

        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)

        return {
            "average": avg_time,
            "minimum": min_time,
            "maximum": max_time,
            "iterations": iterations,
        }

    @staticmethod
    def load_test_complaints(num_complaints: int = 1000):
        """
        Create test data for load testing
        """
        from tests.test_factories import ComplaintFactory

        start_time = time.time()

        # Use bulk_create for better performance
        complaints = []
        for i in range(num_complaints):
            complaints.append(ComplaintFactory.build())

        Complaint.objects.bulk_create(complaints, batch_size=100)

        end_time = time.time()
        creation_time = end_time - start_time

        logger.info(f"Created {num_complaints} complaints in {creation_time:.2f}s")
        return creation_time
