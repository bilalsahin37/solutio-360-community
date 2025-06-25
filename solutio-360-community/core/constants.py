"""
Core app constants
"""

# Notification types
NOTIFICATION_TYPES = (
    ("INFO", "Bilgi"),
    ("WARNING", "Uyarı"),
    ("ERROR", "Hata"),
    ("SUCCESS", "Başarı"),
    ("COMPLAINT_CREATED", "Şikayet Oluşturuldu"),
    ("COMPLAINT_UPDATED", "Şikayet Güncellendi"),
    ("COMPLAINT_ASSIGNED", "Şikayet Atandı"),
    ("COMPLAINT_RESOLVED", "Şikayet Çözüldü"),
    ("REPORT_GENERATED", "Rapor Oluşturuldu"),
)

# Webhook event choices
WEBHOOK_EVENT_CHOICES = (
    ("COMPLAINT_CREATED", "Şikayet Oluşturuldu"),
    ("COMPLAINT_UPDATED", "Şikayet Güncellendi"),
    ("COMPLAINT_ASSIGNED", "Şikayet Atandı"),
    ("COMPLAINT_RESOLVED", "Şikayet Çözüldü"),
    ("USER_REGISTERED", "Kullanıcı Kaydı"),
    ("REPORT_GENERATED", "Rapor Oluşturuldu"),
)

# System settings defaults
DEFAULT_SETTINGS = {
    "SITE_NAME": "Solutio 360",
    "SITE_DESCRIPTION": "Şikayet Yönetim Sistemi",
    "CONTACT_EMAIL": "info@solutio360.com",
    "DEFAULT_SLA_HOURS": 24,
    "MAX_FILE_SIZE": 10 * 1024 * 1024,  # 10 MB
    "ALLOWED_FILE_TYPES": ["pdf", "doc", "docx", "jpg", "jpeg", "png", "gif"],
    "NOTIFICATION_ENABLED": True,
    "EMAIL_NOTIFICATIONS": True,
    "SMS_NOTIFICATIONS": False,
    "AUTO_ASSIGNMENT": True,
    "ANONYMOUS_COMPLAINTS": True,
    "PUBLIC_DASHBOARD": False,
}

# Cache keys
CACHE_KEYS = {
    "DASHBOARD_STATS": "dashboard_stats_{user_id}",
    "COMPLAINT_CATEGORIES": "complaint_categories",
    "SYSTEM_SETTINGS": "system_settings",
    "USER_NOTIFICATIONS": "user_notifications_{user_id}",
}

# Cache timeouts (seconds)
CACHE_TIMEOUTS = {
    "SHORT": 300,  # 5 minutes
    "MEDIUM": 1800,  # 30 minutes
    "LONG": 3600,  # 1 hour
    "DAY": 86400,  # 24 hours
}

# File upload paths
UPLOAD_PATHS = {
    "COMPLAINTS": "complaints/attachments/%Y/%m/",
    "REPORTS": "reports/%Y/%m/",
    "PROFILES": "profiles/avatars/",
    "TEMPLATES": "reports/templates/",
}

# Status colors
STATUS_COLORS = {
    "DRAFT": "#6B7280",
    "SUBMITTED": "#F59E0B",
    "IN_REVIEW": "#3B82F6",
    "IN_PROGRESS": "#8B5CF6",
    "RESOLVED": "#10B981",
    "CLOSED": "#6B7280",
    "REOPENED": "#EF4444",
}

# Priority levels
PRIORITY_LEVELS = {
    1: {"name": "Düşük", "color": "#10B981"},
    2: {"name": "Normal", "color": "#3B82F6"},
    3: {"name": "Yüksek", "color": "#F59E0B"},
    4: {"name": "Acil", "color": "#EF4444"},
    5: {"name": "Kritik", "color": "#7C2D12"},
}

# Export formats
EXPORT_FORMATS = {
    "PDF": {
        "extension": "pdf",
        "content_type": "application/pdf",
        "icon": "📄",
    },
    "EXCEL": {
        "extension": "xlsx",
        "content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "icon": "📊",
    },
    "CSV": {
        "extension": "csv",
        "content_type": "text/csv",
        "icon": "📝",
    },
    "JSON": {
        "extension": "json",
        "content_type": "application/json",
        "icon": "📋",
    },
}
