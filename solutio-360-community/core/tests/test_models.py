import pytest
from django.core.exceptions import ValidationError
from django.test import TestCase

from core.models import BaseModel


class TestBaseModel(TestCase):
    """Test cases for BaseModel."""

    def setUp(self):
        """Set up test data."""
        self.model = BaseModel()

    def test_created_at_auto_set(self):
        """Test that created_at is automatically set."""
        self.model.save()
        self.assertIsNotNone(self.model.created_at)

    def test_updated_at_auto_update(self):
        """Test that updated_at is automatically updated."""
        self.model.save()
        old_updated_at = self.model.updated_at
        self.model.save()
        self.assertGreater(self.model.updated_at, old_updated_at)

    def test_is_active_default(self):
        """Test that is_active defaults to True."""
        self.model.save()
        self.assertTrue(self.model.is_active)
