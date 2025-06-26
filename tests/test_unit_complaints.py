# -*- coding: utf-8 -*-
"""
Unit Tests for Complaints Module
===============================

Comprehensive unit tests inspired by:
- Google's Test Engineering best practices
- Django testing documentation
- Test-Driven Development principles
"""

from datetime import timedelta
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase, TransactionTestCase
from django.urls import reverse
from django.utils import timezone

import pytest

from complaints.models import (
    Complaint,
    ComplaintCategory,
    ComplaintComment,
    ComplaintTag,
    Institution,
)
from tests.test_factories import (
    ComplaintCategoryFactory,
    ComplaintFactory,
    InstitutionFactory,
    UserFactory,
)

User = get_user_model()


@pytest.mark.unit
class ComplaintModelTests(TestCase):
    """Test cases for Complaint model"""

    def setUp(self):
        """Set up test data"""
        self.user = UserFactory()
        self.category = ComplaintCategoryFactory()

    def test_complaint_creation(self):
        """Test complaint model creation"""
        complaint = ComplaintFactory(submitter=self.user, category=self.category)

        self.assertTrue(isinstance(complaint, Complaint))
        self.assertEqual(complaint.submitter, self.user)
        self.assertEqual(complaint.category, self.category)
        self.assertEqual(complaint.status, "SUBMITTED")

    def test_complaint_str_representation(self):
        """Test complaint string representation"""
        complaint = ComplaintFactory(title="Test Complaint", status="SUBMITTED")

        expected = f"Test Complaint (Submitted)"
        self.assertEqual(str(complaint), expected)

    def test_complaint_absolute_url(self):
        """Test complaint get_absolute_url method"""
        complaint = ComplaintFactory()
        expected_url = reverse("complaints:complaint_detail", args=[str(complaint.id)])

        self.assertEqual(complaint.get_absolute_url(), expected_url)

    def test_complaint_is_overdue_property(self):
        """Test complaint is_overdue property"""
        # Test with no due date
        complaint = ComplaintFactory(due_date=None)
        self.assertFalse(complaint.is_overdue)

        # Test with future due date
        future_date = timezone.now() + timedelta(days=1)
        complaint = ComplaintFactory(due_date=future_date)
        self.assertFalse(complaint.is_overdue)

        # Test with past due date
        past_date = timezone.now() - timedelta(days=1)
        complaint = ComplaintFactory(due_date=past_date)
        self.assertTrue(complaint.is_overdue)

    def test_complaint_sla_status_property(self):
        """Test complaint sla_status property"""
        # Test with no due date
        complaint = ComplaintFactory(due_date=None)
        self.assertEqual(complaint.sla_status, "NO_SLA")

        # Test pending SLA
        future_date = timezone.now() + timedelta(days=1)
        complaint = ComplaintFactory(due_date=future_date, status="IN_PROGRESS")
        self.assertEqual(complaint.sla_status, "PENDING")

        # Test SLA met
        past_date = timezone.now() - timedelta(days=1)
        resolution_date = timezone.now() - timedelta(days=2)
        complaint = ComplaintFactory(
            due_date=past_date, status="RESOLVED", resolution_date=resolution_date
        )
        self.assertEqual(complaint.sla_status, "MET")

    def test_complaint_save_auto_resolution_date(self):
        """Test automatic resolution date setting"""
        complaint = ComplaintFactory(status="IN_PROGRESS")
        self.assertIsNone(complaint.resolution_date)

        # Change status to RESOLVED
        complaint.status = "RESOLVED"
        complaint.save()

        self.assertIsNotNone(complaint.resolution_date)


@pytest.mark.unit
class ComplaintCategoryModelTests(TestCase):
    """Test cases for ComplaintCategory model"""

    def test_category_creation(self):
        """Test category creation"""
        category = ComplaintCategoryFactory()

        self.assertTrue(isinstance(category, ComplaintCategory))
        self.assertTrue(category.name)

    def test_category_with_parent(self):
        """Test category with parent relationship"""
        parent_category = ComplaintCategoryFactory()
        child_category = ComplaintCategoryFactory(parent=parent_category)

        self.assertEqual(child_category.parent, parent_category)
        self.assertIn(child_category, parent_category.children.all())

    def test_category_str_representation(self):
        """Test category string representation"""
        parent = ComplaintCategoryFactory(name="Parent Category")
        child = ComplaintCategoryFactory(name="Child Category", parent=parent)

        self.assertEqual(str(parent), "Parent Category")
        self.assertEqual(str(child), "Parent Category > Child Category")


@pytest.mark.unit
class ComplaintViewTests(TestCase):
    """Test cases for Complaint views"""

    def setUp(self):
        """Set up test data"""
        self.user = UserFactory()
        self.admin_user = UserFactory(is_staff=True, is_superuser=True)
        self.complaint = ComplaintFactory(submitter=self.user)

    def test_complaint_list_view_requires_login(self):
        """Test that complaint list view requires authentication"""
        response = self.client.get(reverse("complaints:complaint_list"))
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_complaint_list_view_authenticated(self):
        """Test complaint list view with authenticated user"""
        self.client.force_login(self.user)
        response = self.client.get(reverse("complaints:complaint_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.complaint.title)

    def test_complaint_detail_view(self):
        """Test complaint detail view"""
        self.client.force_login(self.user)
        response = self.client.get(reverse("complaints:complaint_detail", args=[self.complaint.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.complaint.title)
        self.assertContains(response, self.complaint.description)

    def test_complaint_create_view_get(self):
        """Test complaint create view GET request"""
        self.client.force_login(self.user)
        response = self.client.get(reverse("complaints:complaint_create"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "form")

    def test_complaint_create_view_post(self):
        """Test complaint create view POST request"""
        self.client.force_login(self.user)
        category = ComplaintCategoryFactory()

        data = {
            "title": "New Test Complaint",
            "description": "Test complaint description",
            "category": category.id,
            "priority": "HIGH",
            "is_anonymous": False,
            "is_confidential": False,
        }

        response = self.client.post(reverse("complaints:complaint_create"), data)

        self.assertEqual(response.status_code, 302)  # Redirect after creation

        # Verify complaint was created
        complaint = Complaint.objects.get(title="New Test Complaint")
        self.assertEqual(complaint.submitter, self.user)
        self.assertEqual(complaint.category, category)

    def test_complaint_update_view_owner_only(self):
        """Test that only complaint owner can update"""
        other_user = UserFactory()
        self.client.force_login(other_user)

        response = self.client.get(reverse("complaints:complaint_update", args=[self.complaint.id]))

        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_complaint_update_view_owner_access(self):
        """Test complaint owner can access update view"""
        self.client.force_login(self.user)

        response = self.client.get(reverse("complaints:complaint_update", args=[self.complaint.id]))

        self.assertEqual(response.status_code, 200)


@pytest.mark.unit
class ComplaintFormTests(TestCase):
    """Test cases for Complaint forms"""

    def setUp(self):
        """Set up test data"""
        self.user = UserFactory()
        self.category = ComplaintCategoryFactory()

    def test_complaint_form_valid_data(self):
        """Test complaint form with valid data"""
        from complaints.forms import ComplaintForm

        form_data = {
            "title": "Test Complaint",
            "description": "Test description",
            "category": self.category.id,
            "priority": "MEDIUM",
            "is_anonymous": False,
            "is_confidential": False,
        }

        form = ComplaintForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_complaint_form_missing_required_fields(self):
        """Test complaint form with missing required fields"""
        from complaints.forms import ComplaintForm

        form_data = {
            "title": "",  # Missing required field
            "description": "Test description",
        }

        form = ComplaintForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("title", form.errors)


@pytest.mark.unit
class ComplaintAPITests(TestCase):
    """Test cases for Complaint API endpoints"""

    def setUp(self):
        """Set up test data"""
        self.user = UserFactory()
        self.complaint = ComplaintFactory(submitter=self.user)

    def test_complaint_api_list_authenticated(self):
        """Test complaint API list endpoint with authentication"""
        self.client.force_login(self.user)
        response = self.client.get("/api/v1/complaints/")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("results", data)

    def test_complaint_api_detail(self):
        """Test complaint API detail endpoint"""
        self.client.force_login(self.user)
        response = self.client.get(f"/api/v1/complaints/{self.complaint.id}/")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["title"], self.complaint.title)


@pytest.mark.performance
class ComplaintPerformanceTests(TransactionTestCase):
    """Performance tests for complaint operations"""

    def test_complaint_list_query_performance(self):
        """Test query performance for complaint list"""
        # Create test data
        users = UserFactory.create_batch(10)
        categories = ComplaintCategoryFactory.create_batch(5)

        complaints = []
        for i in range(100):
            complaint = ComplaintFactory(
                submitter=users[i % len(users)],
                category=categories[i % len(categories)],
            )
            complaints.append(complaint)

        self.client.force_login(users[0])

        # Test query performance
        with self.assertNumQueries(10):  # Should be optimized to ~10 queries
            response = self.client.get(reverse("complaints:complaint_list"))
            self.assertEqual(response.status_code, 200)

    def test_complaint_detail_query_performance(self):
        """Test query performance for complaint detail"""
        complaint = ComplaintFactory()

        # Add related objects
        for i in range(5):
            ComplaintComment.objects.create(complaint=complaint, content=f"Test comment {i}")

        self.client.force_login(complaint.submitter)

        # Test query performance
        with self.assertNumQueries(5):  # Should be optimized
            response = self.client.get(reverse("complaints:complaint_detail", args=[complaint.id]))
            self.assertEqual(response.status_code, 200)


@pytest.mark.integration
class ComplaintIntegrationTests(TransactionTestCase):
    """Integration tests for complaint workflow"""

    def test_complete_complaint_workflow(self):
        """Test complete complaint lifecycle"""
        # Create users and category
        submitter = UserFactory()
        reviewer = UserFactory()
        category = ComplaintCategoryFactory()

        self.client.force_login(submitter)

        # Step 1: Create complaint
        complaint_data = {
            "title": "Integration Test Complaint",
            "description": "Test description for integration",
            "category": category.id,
            "priority": "HIGH",
        }

        response = self.client.post(reverse("complaints:complaint_create"), complaint_data)
        self.assertEqual(response.status_code, 302)

        # Verify complaint was created
        complaint = Complaint.objects.get(title="Integration Test Complaint")
        self.assertEqual(complaint.status, "SUBMITTED")

        # Step 2: Add comment
        comment_data = {"content": "Test comment from submitter"}

        response = self.client.post(
            reverse("complaints:add_comment", args=[complaint.id]), comment_data
        )

        # Verify comment was added
        self.assertTrue(complaint.comments.filter(content="Test comment from submitter").exists())

        # Step 3: Update status (as reviewer)
        self.client.force_login(reviewer)

        status_data = {
            "status": "IN_PROGRESS",
            "comment": "Starting to work on this complaint",
        }

        response = self.client.post(
            reverse("complaints:update_status", args=[complaint.id]), status_data
        )

        # Verify status was updated
        complaint.refresh_from_db()
        self.assertEqual(complaint.status, "IN_PROGRESS")

        # Step 4: Resolve complaint
        complaint.status = "RESOLVED"
        complaint.resolution = "Issue has been resolved"
        complaint.save()

        # Verify resolution date was set automatically
        self.assertIsNotNone(complaint.resolution_date)


if __name__ == "__main__":
    pytest.main([__file__])
