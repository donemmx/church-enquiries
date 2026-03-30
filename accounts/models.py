# accounts/models.py

from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Administrator'),          # superuser-level, sees everything
        ('section_admin', 'Section Admin'),  # admin of their own section only
        ('staff', 'Staff'),                  # regular staff within their section
    ]

    SECTION_CHOICES = [
        ('greeters', 'Greeters'),
        ('followup', 'Follow-Up / First Timers'),
        ('all', 'All Sections'),             # only for superusers / global admins
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='staff')
    section = models.CharField(max_length=20, choices=SECTION_CHOICES, default='followup')

    phone = models.CharField(max_length=20, null=True, blank=True)
    photo = models.ImageField(upload_to='staff/', null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    department = models.CharField(max_length=100, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_active = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.get_role_display()} — {self.get_section_display()})"

    # ── Convenience helpers used throughout views ──────────────────────────

    @property
    def is_superuser(self):
        return self.user.is_superuser

    @property
    def is_section_admin(self):
        """True for both global admins and section admins."""
        return self.role in ('admin', 'section_admin') or self.user.is_superuser

    @property
    def can_see_all(self):
        """Only Django superusers or role=admin with section=all see everything."""
        return self.user.is_superuser or (self.role == 'admin' and self.section == 'all')

    @property
    def is_greeter_section(self):
        return self.section == 'greeters' or self.can_see_all

    @property
    def is_followup_section(self):
        return self.section == 'followup' or self.can_see_all

    @property
    def initials(self):
        name = self.user.get_full_name() or self.user.username
        parts = name.split()
        if len(parts) >= 2:
            return f"{parts[0][0]}{parts[1][0]}".upper()
        return name[0].upper()

    @property
    def display_role(self):
        return dict(self.ROLE_CHOICES).get(self.role, self.role)

    @property
    def display_section(self):
        return dict(self.SECTION_CHOICES).get(self.section, self.section)