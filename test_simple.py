#!/usr/bin/env python
import os
import sys

import django

# Django ayarlarını yükle
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "solutio_360.settings")
django.setup()

from django.contrib.auth import get_user_model

from complaints.models import Complaint

User = get_user_model()

# Kullanıcı bul
user = User.objects.first()
print(f"User: {user}")

# Şikayet bul
complaint = Complaint.objects.filter(submitter=user).first()
if complaint:
    print(f"Complaint: {complaint.title}")
    print(f"Status: {complaint.status}")
    print(f"can_withdraw: {complaint.can_withdraw}")
    print(f"is_withdrawn: {complaint.is_withdrawn}")
    print(f"can_be_withdrawn: {complaint.can_be_withdrawn}")
else:
    print("No complaints found")
