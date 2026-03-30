from django.contrib import admin
from .models import Member, Ministry, FollowUp, Event, EventAttendance, Message, PrayerRequest, Attendance, Note


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ['get_full_name', 'email', 'phone', 'status', 'first_visit_date', 'assigned_to']
    list_filter = ['status', 'gender', 'is_baptized', 'is_active']
    search_fields = ['first_name', 'last_name', 'email', 'phone']
    date_hierarchy = 'first_visit_date'
    raw_id_fields = ['assigned_to', 'created_by']


@admin.register(Ministry)
class MinistryAdmin(admin.ModelAdmin):
    list_display = ['name', 'leader', 'is_active']


@admin.register(FollowUp)
class FollowUpAdmin(admin.ModelAdmin):
    list_display = ['member', 'follow_up_type', 'status', 'assigned_to', 'due_date', 'priority']
    list_filter = ['status', 'follow_up_type', 'priority']
    search_fields = ['member__first_name', 'member__last_name']


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['title', 'event_type', 'status', 'start_date', 'venue', 'organizer']
    list_filter = ['status', 'event_type']
    search_fields = ['title']


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['title', 'message_type', 'status', 'sender', 'total_sent', 'created_at']
    list_filter = ['status', 'message_type']
    search_fields = ['title', 'body']


@admin.register(PrayerRequest)
class PrayerRequestAdmin(admin.ModelAdmin):
    list_display = ['member', 'status', 'is_anonymous', 'created_at', 'handled_by']
    list_filter = ['status', 'is_anonymous']


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['member', 'service_type', 'date', 'recorded_by']
    list_filter = ['service_type']
    date_hierarchy = 'date'


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ['member', 'created_by', 'created_at', 'is_private']
