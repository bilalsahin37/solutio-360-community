from django.contrib import admin
from .models import User, Role

# Register your models here.


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "is_personnel",
        "is_active",
        "is_superuser",
    )
    search_fields = ("username", "email", "first_name", "last_name")
    list_filter = ("is_active", "is_superuser")


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "code",
        "is_staff",
        "is_reviewer",
        "department",
        "is_system",
    )
    search_fields = ("name", "code")
    list_filter = ("is_staff", "is_reviewer", "is_system")
