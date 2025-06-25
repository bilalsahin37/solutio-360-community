# -*- coding: utf-8 -*-
"""
Test Data Factories for Solutio 360 PWA Project
===============================================

Factory classes for generating test data using factory_boy.
Inspired by best practices from:
- GitHub's factory_boy patterns
- Spotify's test data generation
- Airbnb's testing infrastructure
"""

import uuid
from datetime import datetime, timedelta

import factory
from django.contrib.auth import get_user_model
from django.utils import timezone

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
    address = factory.Faker("address")
    phone = factory.Faker("phone_number")
    email = factory.Faker("email")
    website = factory.Faker("url")
    is_active = True


class UnitFactory(factory.django.DjangoModelFactory):
    """Factory for creating units"""

    class Meta:
        model = Unit

    name = factory.Faker("word")
    description = factory.Faker("text", max_nb_chars=200)
    institution = factory.SubFactory(InstitutionFactory)
    is_active = True


class SubunitFactory(factory.django.DjangoModelFactory):
    """Factory for creating subunits"""

    class Meta:
        model = Subunit

    name = factory.Faker("word")
    description = factory.Faker("text", max_nb_chars=200)
    unit = factory.SubFactory(UnitFactory)
    is_active = True


class PersonFactory(factory.django.DjangoModelFactory):
    """Factory for creating persons"""

    class Meta:
        model = Person

    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    title = factory.Faker("job")
    phone = factory.Faker("phone_number")
    email = factory.Faker("email")
    institution = factory.SubFactory(InstitutionFactory)
    is_active = True


class PriorityFactory(factory.django.DjangoModelFactory):
    """Factory for creating priorities"""

    class Meta:
        model = Priority

    name = factory.Iterator(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
    description = factory.Faker("text", max_nb_chars=100)
    order = factory.Sequence(lambda n: n)
    color = factory.Faker("hex_color")
    is_active = True


class StatusFactory(factory.django.DjangoModelFactory):
    """Factory for creating statuses"""

    class Meta:
        model = Status

    name = factory.Iterator(
        ["SUBMITTED", "UNDER_REVIEW", "IN_PROGRESS", "RESOLVED", "CLOSED"]
    )
    description = factory.Faker("text", max_nb_chars=100)
    order = factory.Sequence(lambda n: n)
    color = factory.Faker("hex_color")
    is_active = True


class ComplaintCategoryFactory(factory.django.DjangoModelFactory):
    """Factory for creating complaint categories"""

    class Meta:
        model = ComplaintCategory

    name = factory.Faker("word")
    description = factory.Faker("text", max_nb_chars=200)
    icon = factory.Faker("word")
    color = factory.Faker("hex_color")
    order = factory.Sequence(lambda n: n)
    sla_hours = factory.Faker("random_int", min=1, max=168)  # 1 hour to 1 week
    responsible_department = factory.SubFactory(DepartmentFactory)


class ComplaintTagFactory(factory.django.DjangoModelFactory):
    """Factory for creating complaint tags"""

    class Meta:
        model = ComplaintTag

    name = factory.Faker("word")
    description = factory.Faker("text", max_nb_chars=100)
    color = factory.Faker("hex_color")


class ComplaintFactory(factory.django.DjangoModelFactory):
    """Factory for creating complaints"""

    class Meta:
        model = Complaint

    title = factory.Faker("sentence", nb_words=4)
    description = factory.Faker("text", max_nb_chars=1000)
    submitter = factory.SubFactory(UserFactory)
    category = factory.SubFactory(ComplaintCategoryFactory)
    priority = factory.SubFactory(PriorityFactory)
    status = factory.SubFactory(StatusFactory)
    department = factory.SubFactory(DepartmentFactory)
    due_date = factory.LazyFunction(lambda: timezone.now() + timedelta(days=7))
    is_anonymous = False
    is_confidential = False

    @factory.post_generation
    def tags(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for tag in extracted:
                self.tags.add(tag)
        else:
            # Add random tags
            tags = ComplaintTagFactory.create_batch(2)
            for tag in tags:
                self.tags.add(tag)

    @factory.post_generation
    def complained_institutions(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for institution in extracted:
                self.complained_institutions.add(institution)
        else:
            institution = InstitutionFactory()
            self.complained_institutions.add(institution)


class ComplaintCommentFactory(factory.django.DjangoModelFactory):
    """Factory for creating complaint comments"""

    class Meta:
        model = ComplaintComment

    complaint = factory.SubFactory(ComplaintFactory)
    content = factory.Faker("text", max_nb_chars=500)
    sender = factory.SubFactory(UserFactory)
    receiver = factory.SubFactory(UserFactory)
    is_internal = False


class ComplaintAttachmentFactory(factory.django.DjangoModelFactory):
    """Factory for creating complaint attachments"""

    class Meta:
        model = ComplaintAttachment

    complaint = factory.SubFactory(ComplaintFactory)
    filename = factory.Faker("file_name")
    file_type = factory.Iterator(["pdf", "doc", "jpg", "png"])
    file_size = factory.Faker("random_int", min=1024, max=5242880)  # 1KB to 5MB
    description = factory.Faker("sentence")


# Batch factories for creating multiple instances
class ComplaintBatchFactory:
    """Utility class for creating batches of related test data"""

    @staticmethod
    def create_complaint_with_full_data():
        """Create a complaint with all related data"""

        # Create users
        submitter = UserFactory()
        reviewer = UserFactory()
        inspector = UserFactory()

        # Create organization structure
        institution = InstitutionFactory()
        unit = UnitFactory(institution=institution)
        subunit = SubunitFactory(unit=unit)
        person = PersonFactory(institution=institution)

        # Create complaint metadata
        category = ComplaintCategoryFactory()
        priority = PriorityFactory()
        status = StatusFactory()
        tags = ComplaintTagFactory.create_batch(3)

        # Create complaint
        complaint = ComplaintFactory(
            submitter=submitter,
            category=category,
            priority=priority,
            status=status,
        )

        # Add relationships
        complaint.complained_institutions.add(institution)
        complaint.complained_units.add(unit)
        complaint.complained_subunits.add(subunit)
        complaint.complained_people.add(person)
        complaint.reviewers.add(reviewer)
        complaint.inspectors.add(inspector)

        for tag in tags:
            complaint.tags.add(tag)

        # Add comments and attachments
        ComplaintCommentFactory.create_batch(3, complaint=complaint)
        ComplaintAttachmentFactory.create_batch(2, complaint=complaint)

        return complaint

    @staticmethod
    def create_test_dataset(num_complaints=10):
        """Create a complete test dataset"""

        # Create base data
        departments = DepartmentFactory.create_batch(3)
        institutions = InstitutionFactory.create_batch(5)
        categories = ComplaintCategoryFactory.create_batch(5)
        priorities = PriorityFactory.create_batch(4)
        statuses = StatusFactory.create_batch(5)

        # Create users with different roles
        users = UserFactory.create_batch(10)
        admin_users = AdminUserFactory.create_batch(2)

        # Create complaints with varied data
        complaints = []
        for i in range(num_complaints):
            complaint = ComplaintFactory(
                submitter=factory.random.randint(0, len(users) - 1),
                category=factory.random.randint(0, len(categories) - 1),
                priority=factory.random.randint(0, len(priorities) - 1),
                status=factory.random.randint(0, len(statuses) - 1),
            )
            complaints.append(complaint)

        return {
            "departments": departments,
            "institutions": institutions,
            "categories": categories,
            "priorities": priorities,
            "statuses": statuses,
            "users": users,
            "admin_users": admin_users,
            "complaints": complaints,
        }


# Performance test factories
class PerformanceTestFactory:
    """Factory for creating performance test data"""

    @staticmethod
    def create_large_dataset(size="medium"):
        """Create large datasets for performance testing"""

        sizes = {
            "small": {"complaints": 100, "users": 20, "institutions": 10},
            "medium": {"complaints": 1000, "users": 100, "institutions": 50},
            "large": {"complaints": 10000, "users": 500, "institutions": 200},
        }

        config = sizes.get(size, sizes["medium"])

        # Create institutions and related data
        institutions = InstitutionFactory.create_batch(config["institutions"])

        # Create users
        users = UserFactory.create_batch(config["users"])

        # Create categories and metadata
        categories = ComplaintCategoryFactory.create_batch(10)
        priorities = PriorityFactory.create_batch(4)
        statuses = StatusFactory.create_batch(5)

        # Create complaints
        complaints = []
        for i in range(config["complaints"]):
            complaint = ComplaintFactory(
                submitter=users[i % len(users)],
                category=categories[i % len(categories)],
                priority=priorities[i % len(priorities)],
                status=statuses[i % len(statuses)],
            )

            # Add random institution
            complaint.complained_institutions.add(institutions[i % len(institutions)])

            complaints.append(complaint)

        return {
            "institutions": institutions,
            "users": users,
            "categories": categories,
            "priorities": priorities,
            "statuses": statuses,
            "complaints": complaints,
        }
