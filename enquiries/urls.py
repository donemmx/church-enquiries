from django.urls import path
from . import views

urlpatterns = [
    path('', views.member_list, name='member_list'),
    path('dashboard/', views.dashboard, name='dashboard'),

    # Members
    path('members/', views.member_list, name='member_list'),
    path('members/new/', views.member_create, name='member_create'),
    path('members/<int:pk>/', views.member_detail, name='member_detail'),
    path('members/<int:pk>/edit/', views.member_edit, name='member_edit'),
    path('members/<int:pk>/delete/', views.member_delete, name='member_delete'),
    path("messages/<int:pk>/delete/", views.message_delete, name="message_delete"),
    path('members/<int:pk>/assign/', views.member_assign, name='member_assign'),

    # urls.py
    path('register/', views.public_member_register, name='public_member_register'),
    path('register/thank-you/', views.public_member_thankyou, name='public_member_thankyou'),
    path('message/send-draft/<int:pk>/', views.send_draft_message, name='send_draft_message'),

    # Follow-ups
    path('follow-ups/', views.followup_list, name='followup_list'),
    path('follow-ups/tasks/', views.followup_tasks, name='followup_tasks'),
    path('follow-ups/new/', views.followup_create, name='followup_create'),
    path('follow-ups/new/<int:member_pk>/', views.followup_create, name='followup_create_for_member'),
    path('follow-ups/<int:pk>/edit/', views.followup_edit, name='followup_edit'),
    path('follow-ups/<int:pk>/complete/', views.followup_complete, name='followup_complete'),
    path("followups/<int:pk>/delete/", views.followup_delete, name="followup_delete"),

    # Events
    path('events/', views.event_list, name='event_list'),
    path('events/new/', views.event_create, name='event_create'),
    path('events/<int:pk>/', views.event_detail, name='event_detail'),
    path('events/<int:pk>/edit/', views.event_edit, name='event_edit'),

    # Messages
    path('messages/', views.message_list, name='message_list'),
    path('messages/compose/', views.message_create, name='message_create'),
    path('messages/<int:pk>/', views.message_detail, name='message_detail'),

    # Prayer Requests
    path('prayer-requests/', views.prayer_list, name='prayer_list'),
    path('prayer-requests/new/', views.prayer_create, name='prayer_create'),
    path('prayer-requests/<int:pk>/update/', views.prayer_update, name='prayer_update'),

    # Attendance
    path('attendance/', views.attendance_list, name='attendance_list'),
    path('attendance/record/', views.attendance_create, name='attendance_create'),

    # Ministries
    path('ministries/', views.ministry_list, name='ministry_list'),
    path('ministries/new/', views.ministry_create, name='ministry_create'),

    # Admin Panel
    path('admin-panel/', views.admin_panel, name='admin_panel'),
    # path('admin-panel/staff/', views.admin_staff, name='admin_staff'),
    path('admin-panel/reports/', views.admin_reports, name='admin_reports'),
    path("staff/<int:pk>/delete/", views.staff_delete, name="staff_delete"),



    # Greeters
    path('greeters/', views.greeter_list, name='greeter_list'),
    path('greeters/assign/<int:pk>/',    views.greeter_assign_quick, name='greeter_assign_quick'),
    path('integration/',                 views.integration_list,     name='integration_list'),
    path('integration/add/',             views.integration_create,   name='integration_create'),
    path('integration/add/<int:member_pk>/', views.integration_create, name='integration_create_for_member'),
    path('integration/<int:pk>/edit/',   views.integration_update,   name='integration_update'),
    path('members/<int:member_pk>/quick-integrate/', views.integration_quick, name='integration_quick'),



    #Contact Logs
    path('members/<int:member_pk>/log-contact/',  views.contact_log_create, name='contact_log_create'),
    path('contact-logs/<int:pk>/delete/',         views.contact_log_delete,  name='contact_log_delete'),
    # path('contact-logs/',                         views.contact_log_list,    name='contact_log_list'),
    
]
