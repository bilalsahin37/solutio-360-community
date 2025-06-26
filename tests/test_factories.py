# -*- coding: utf-8 -*-
"""
Test Data Factories for Solutio 360 PWA Project
===============================================

Factory classes for generating test data using factory_boy.
Inspired by best practices from GitHub, Spotify, and Airbnb.
"""

import uuid
from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone

import factory

from complaints.models import (
    Complaint,
    ComplaintAttachment,
    ComplaintCategory,
    ComplaintComment,
    ComplaintTag,
    Institution,
    Person,
    Priority,
    Status,
    Subunit,
    Unit,
)
from users.models import Department

User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    """Factory for creating test users"""

    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@test.com")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    is_active = True
    is_staff = False
    date_joined = factory.LazyFunction(timezone.now)

    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        if extracted:
            self.set_password(extracted)
        else:
            self.set_password("testpass123")


class AdminUserFactory(UserFactory):
    """Factory for creating admin users"""

    is_staff = True
    is_superuser = True


class DepartmentFactory(factory.django.DjangoModelFactory):
    """Factory for creating departments"""

    class Meta:
        model = Department

    name = factory.Faker("company")
    description = factory.Faker("text", max_nb_chars=200)
    is_active = True


class InstitutionFactory(factory.django.DjangoModelFactory):
    """Factory for creating institutions"""

    class Meta:
        model = Institution

    name = factory.Faker("company")
    description = factory.Faker("text", max_nb_chars=200)


class UnitFactory(factory.django.DjangoModelFactory):
    """Factory for creating units"""

    class Meta:
        model = Unit

    name = factory.Faker("word")
    description = factory.Faker("text", max_nb_chars=200)
    institution = factory.SubFactory(InstitutionFactory)


class ComplaintCategoryFactory(factory.django.DjangoModelFactory):
    """Factory for creating complaint categories"""

    class Meta:
        model = ComplaintCategory

    name = factory.Faker("word")
    description = factory.Faker("text", max_nb_chars=200)
    icon = factory.Faker("word")
    color = factory.Faker("hex_color")
    order = factory.Sequence(lambda n: n)
    sla_hours = factory.Faker("random_int", min=1, max=168)
    responsible_department = factory.SubFactory(DepartmentFactory)


class ComplaintFactory(factory.django.DjangoModelFactory):
    """Factory for creating complaints"""

    class Meta:
        model = Complaint

    title = factory.Faker("sentence", nb_words=4)
    description = factory.Faker("text", max_nb_chars=1000)
    submitter = factory.SubFactory(UserFactory)
    category = factory.SubFactory(ComplaintCategoryFactory)
    status = "SUBMITTED"
    priority = "MEDIUM"
    department = factory.SubFactory(DepartmentFactory)
    due_date = factory.LazyFunction(lambda: timezone.now() + timedelta(days=7))
    is_anonymous = False
    is_confidential = False
