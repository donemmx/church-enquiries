# enquiries/views.py
# Section-aware: every queryset is filtered to the current user's section.
# Superusers / global admins (section='all') see everything.

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.contrib.auth.models import User
from datetime import datetime, timedelta
from django.core.mail import send_mail
from django.conf import settings
import requests

from .models import Member, FollowUp, Event, Message, PrayerRequest, Attendance, Note, Ministry, EventAttendance, ContactLog, Integration
from .forms import MemberForm, FollowUpForm, EventForm, MessageForm, PrayerRequestForm, AttendanceForm, NoteForm, MinistryForm, IntegrationForm, ContactLogForm
from accounts.models import UserProfile


# ─────────────────────────────────────────────
#  SMS HELPER
# ─────────────────────────────────────────────

def send_sms(phone, message):
    """
    Sends an SMS using the Termii API.
    Expects `phone` to be in international format: +234XXXXXXXXXX
    """
    if not phone or not message:
        return None

    if not phone.startswith('+'):
        phone = '+' + phone

    payload = {
        "to": phone,
        "from": settings.TERMII_SENDER_ID,
        "sms": message,
        "type": "plain",
        "channel": "generic",
        "api_key": settings.TERMII_API_KEY,
    }

    try:
        response = requests.post(settings.TERMII_SMS_URL, json=payload, timeout=10)
        response.raise_for_status()
        result = response.json()
        if result.get("status") != "success":
            print(f"SMS not sent: {result}")
        return result
    except requests.exceptions.RequestException as e:
        print(f"SMS request failed: {e}")
        return None
    except ValueError:
        print("Failed to decode JSON response from SMS API")
        return None


# ─────────────────────────────────────────────
#  SECTION / ROLE HELPERS
# ─────────────────────────────────────────────

def get_profile(user):
    """Always returns a UserProfile, creating one if needed."""
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile


def get_section(user):
    """Returns the user's section string: 'greeters' / 'followup' / 'all'."""
    return get_profile(user).section


def can_see_all(user):
    """True only for Django superusers or role=admin + section=all."""
    if user.is_superuser:
        return True
    profile = get_profile(user)
    return profile.role == 'admin' and profile.section == 'all'


def is_section_admin(user):
    """True for section_admin and above (including global admin and superuser)."""
    if user.is_superuser:
        return True
    return get_profile(user).role in ('admin', 'section_admin')


def section_staff_qs(user):
    """
    Returns a queryset of active Users in the same section as `user`.
    Superusers / all-section admins get every active user.
    """
    if can_see_all(user):
        return User.objects.filter(is_active=True)
    section = get_section(user)
    return User.objects.filter(
        is_active=True,
        profile__section__in=[section, 'all']
    )


# ─────────────────────────────────────────────
#  SCOPED QUERYSETS
# ─────────────────────────────────────────────

def member_qs(user):
    """
    Base Member queryset filtered by section.
    - Section admins see ALL active members (so they can assign).
    - Greeter staff  → only members where greeter_assigned_to == user.
    - Followup staff → only members where assigned_to == user.
    - Superuser / all-section → everyone.
    """
    qs = Member.objects.filter(is_active=True)
    if can_see_all(user):
        return qs
    profile = get_profile(user)
    if profile.role in ('admin', 'section_admin'):
        return qs
    if profile.section == 'greeters':
        return qs.filter(greeter_assigned_to=user)
    return qs.filter(assigned_to=user)   # followup staff


def followup_qs(user):
    """
    Follow-ups scoped to section.
    Greeters cannot see follow-ups at all.
    """
    if can_see_all(user):
        return FollowUp.objects.all()
    profile = get_profile(user)
    if profile.section == 'greeters':
        return FollowUp.objects.none()
    if profile.role in ('admin', 'section_admin'):
        return FollowUp.objects.all()
    return FollowUp.objects.filter(assigned_to=user)


# ─────────────────────────────────────────────
#  DASHBOARD
# ─────────────────────────────────────────────

@login_required
def dashboard(request):
    today   = timezone.now().date()
    profile = get_profile(request.user)
    section = profile.section

    base_members = member_qs(request.user)

    total_members   = base_members.count()
    new_this_week   = base_members.filter(first_visit_date__gte=today - timedelta(days=7)).count()
    upcoming_events = Event.objects.filter(start_date__gte=timezone.now(), status='upcoming').count()
    prayer_requests = PrayerRequest.objects.filter(status='pending').count()

    pending_followups = followup_qs(request.user).filter(status='pending').count()
    overdue_followups = followup_qs(request.user).filter(
        status__in=['pending', 'in_progress'], due_date__lt=today
    ).count()

    my_followups   = followup_qs(request.user).filter(
        status__in=['pending', 'in_progress']
    ).select_related('member')[:5]
    recent_members = base_members.select_related('assigned_to', 'greeter_assigned_to')[:5]

    upcoming_event_list = Event.objects.filter(
        start_date__gte=timezone.now(), status='upcoming'
    ).order_by('start_date')[:4]

    status_data   = base_members.values('status').annotate(count=Count('status'))
    status_counts = {item['status']: item['count'] for item in status_data}

    weekly_data = []
    for i in range(7, -1, -1):
        week_start = today - timedelta(weeks=i + 1)
        week_end   = today - timedelta(weeks=i)
        count = base_members.filter(
            first_visit_date__gte=week_start,
            first_visit_date__lt=week_end,
        ).count()
        weekly_data.append({'week': week_end.strftime('%b %d'), 'count': count})


    from .models import Integration

    total_registered  = base_members.count()
    total_integrated  = base_members.filter(status='integrated').count()
    conversion_rate   = round((total_integrated / total_registered * 100), 1) if total_registered else 0

    # Monthly integration trend (last 6 months)
    integration_trend = []
    for i in range(5, -1, -1):
        month_start = (today.replace(day=1) - timedelta(days=i * 30)).replace(day=1)
        month_end   = (month_start + timedelta(days=32)).replace(day=1)
        count = Integration.objects.filter(
            integrated_on__gte=month_start, integrated_on__lt=month_end
        ).count()
        integration_trend.append({'month': month_start.strftime('%b'), 'count': count})

    context = {
        'total_members':      total_members,
        'new_this_week':      new_this_week,
        'pending_followups':  pending_followups,
        'upcoming_events':    upcoming_events,
        'prayer_requests':    prayer_requests,
        'my_followups':       my_followups,
        'recent_members':     recent_members,
        'upcoming_event_list': upcoming_event_list,
        'overdue_followups':  overdue_followups,
        'status_counts':      status_counts,
        'weekly_data':        weekly_data,
        # section context for templates
        'section':            section,
        'profile':            profile,
        'is_greeters':        section == 'greeters',
        'is_followup':        section == 'followup',
        'can_see_all':        can_see_all(request.user),
        'is_section_admin':   is_section_admin(request.user),
        'total_registered':  total_registered,
        'total_integrated':  total_integrated,
        'conversion_rate':   conversion_rate,
        'integration_trend': integration_trend,
    }
    return render(request, 'enquiries/dashboard.html', context)


# ─────────────────────────────────────────────
#  MEMBERS
# ─────────────────────────────────────────────

@login_required
def member_list(request):
    queryset        = member_qs(request.user).select_related('assigned_to', 'greeter_assigned_to')
    search          = request.GET.get('search', '')
    status_filter   = request.GET.get('status', '')
    assigned_filter = request.GET.get('assigned', '')


    date_from = request.GET.get('date_from', '')
    date_to   = request.GET.get('date_to', '')

    if date_from:
        queryset = queryset.filter(first_visit_date__gte=date_from)

    if date_to:
        queryset = queryset.filter(first_visit_date__lte=date_to)


    if search:
        queryset = queryset.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)  |
            Q(email__icontains=search)      |
            Q(phone__icontains=search)
        )
    if status_filter:
        queryset = queryset.filter(status=status_filter)
    if assigned_filter:
        if get_section(request.user) == 'greeters':
            queryset = queryset.filter(greeter_assigned_to_id=assigned_filter)
        else:
            queryset = queryset.filter(assigned_to_id=assigned_filter)

    paginator = Paginator(queryset, 15)
    members   = paginator.get_page(request.GET.get('page'))
    staff     = section_staff_qs(request.user)


    context = {
        'date_from': date_from,
        'date_to': date_to,
        'members':          members,
        'search':           search,
        'status_filter':    status_filter,
        'assigned_filter':  assigned_filter,
        'staff':            staff,
        'status_choices':   Member.STATUS_CHOICES,
        'total_count':      queryset.count(),
        'section':          get_section(request.user),
        'is_section_admin': is_section_admin(request.user),
    }
    return render(request, 'enquiries/member_list.html', context)


@login_required
def member_detail(request, pk):
    member          = get_object_or_404(member_qs(request.user), pk=pk)
    follow_ups      = member.follow_ups.all().select_related('assigned_to')
    notes           = member.member_notes.all().select_related('created_by')
    prayer_requests = member.prayer_list.all()
    attendance      = member.attendance_records.all()[:10]
    contact_logs    = member.contact_logs.select_related('logged_by').all()   # ← add this
    note_form       = NoteForm()
    profile         = get_profile(request.user)

    if request.method == 'POST':
        note_form = NoteForm(request.POST)
        if note_form.is_valid():
            note            = note_form.save(commit=False)
            note.member     = member
            note.created_by = request.user
            note.save()
            messages.success(request, 'Note added successfully.')
            return redirect('member_detail', pk=pk)

    context = {
        'member':           member,
        'follow_ups':       follow_ups,
        'notes':            notes,
        'prayer_requests':  prayer_requests,
        'attendance':       attendance,
        'contact_logs':     contact_logs,                                      # ← add this
        'note_form':        note_form,
        'contact_log_form': ContactLogForm(initial={'contacted_on': timezone.now().date()}),  # ← add this
        'section':          profile.section,
        'is_section_admin': is_section_admin(request.user),
        'is_followup':      profile.section in ('followup', 'all') or can_see_all(request.user),
        'is_greeters':      profile.section in ('greeters', 'all') or can_see_all(request.user),
        'followup_staff':   User.objects.filter(is_active=True, profile__section__in=['followup', 'all']),
        'greeter_staff':    User.objects.filter(is_active=True, profile__section__in=['greeters', 'all']),
    }
    return render(request, 'enquiries/member_detail.html', context)


@login_required
def member_create(request):
    if request.method == 'POST':
        form = MemberForm(request.POST, request.FILES)
        if form.is_valid():
            member            = form.save(commit=False)
            member.created_by = request.user
            member.save()
            form.save_m2m()
            messages.success(request, f'{member.get_full_name()} has been added successfully!')
            return redirect('member_detail', pk=member.pk)
        else:
            print("MemberForm errors:", form.errors)
    else:
        form = MemberForm()
    return render(request, 'enquiries/member_form.html', {'form': form, 'title': 'Register New Member'})


@login_required
def member_edit(request, pk):
    member = get_object_or_404(member_qs(request.user), pk=pk)
    if request.method == 'POST':
        form = MemberForm(request.POST, request.FILES, instance=member)
        if form.is_valid():
            form.save()
            messages.success(request, f'{member.get_full_name()} updated successfully!')
            return redirect('member_detail', pk=pk)
    else:
        form = MemberForm(instance=member)
    return render(request, 'enquiries/member_form.html', {
        'form': form, 'title': 'Edit Member', 'member': member
    })


@login_required
def member_delete(request, pk):
    member = get_object_or_404(member_qs(request.user), pk=pk)
    if request.method == 'POST':
        member.is_active = False
        member.save()
        messages.success(request, f'{member.get_full_name()} has been removed.')
        return redirect('member_list')
    return render(request, 'enquiries/confirm_delete.html', {'object': member, 'type': 'member'})


@login_required
def member_assign(request, pk):
    if not is_section_admin(request.user):
        messages.error(request, 'Access denied.')
        return redirect('member_detail', pk=pk)

    member   = get_object_or_404(Member, pk=pk, is_active=True)
    staff_id = request.POST.get('staff_id')

    if staff_id:
        staff_user = get_object_or_404(section_staff_qs(request.user), pk=staff_id)
        assign_as  = request.POST.get('assign_as', get_section(request.user))

        if assign_as == 'greeters':
            member.greeter_assigned_to = staff_user
            label = 'Greeter'
        else:
            member.assigned_to = staff_user
            label = 'Follow-up'

            # Auto-create a FollowUp task if one doesn't already exist
            from django.utils import timezone
            from datetime import timedelta
            existing = FollowUp.objects.filter(
                member=member,
                status__in=['pending', 'in_progress']
            ).exists()

            if not existing:
                FollowUp.objects.create(
                    member=member,
                    assigned_to=staff_user,
                    assigned_by=request.user,
                    follow_up_type='call',
                    status='pending',
                    priority=2,
                    due_date=timezone.now().date() + timedelta(days=3),
                    notes='Auto-created on assignment.',
                )

        member.save()
        messages.success(request, f'{member.get_full_name()} assigned to {staff_user.get_full_name()} ({label}).')
    else:
        messages.error(request, 'No staff member selected.')

    # Redirect back to wherever the form was submitted from
    next_url = request.POST.get('next', '')
    if next_url == 'followup_list':
        return redirect('followup_list')
    return redirect('member_detail', pk=pk)


# ─────────────────────────────────────────────
#  PUBLIC REGISTRATION (no login required)
# ─────────────────────────────────────────────

def public_member_register(request):
    if request.method == 'POST':
        form = MemberForm(request.POST, request.FILES)
        form.fields['assigned_to'].required = False
        form.fields['status'].required      = False

        if form.is_valid():
            member        = form.save(commit=False)
            member.status = 'new'
            member.save()
            form.save_m2m()
            messages.success(request, "Thank you for registering! We will contact you soon.")
            return redirect('public_member_thankyou')
        else:
            print("Public form errors:", form.errors)
    else:
        form = MemberForm()
        form.fields['assigned_to'].required = False
        form.fields['status'].required      = False

    return render(request, 'enquiries/public_member_form.html', {'form': form})


def public_member_thankyou(request):
    return render(request, 'enquiries/public_member_thankyou.html')


# ─────────────────────────────────────────────
#  FOLLOW-UPS  (followup section only)
# ─────────────────────────────────────────────

@login_required
def followup_list(request):
    if get_section(request.user) == 'greeters' and not can_see_all(request.user):
        messages.error(request, 'Follow-ups are managed by the Follow-Up section.')
        return redirect('dashboard')

    # Query Members assigned for follow-up, not FollowUp records
    qs = Member.objects.filter(is_active=True).select_related('assigned_to')

    # Regular staff only see their own assigned members
    if not can_see_all(request.user) and not is_section_admin(request.user):
        qs = qs.filter(assigned_to=request.user)

    search          = request.GET.get('search', '')
    status_filter   = request.GET.get('status', '')
    assigned_filter = request.GET.get('assigned', '')

    if search:
        qs = qs.filter(Q(first_name__icontains=search) | Q(last_name__icontains=search))
    if status_filter:
        qs = qs.filter(status=status_filter)
    if assigned_filter:
        qs = qs.filter(assigned_to_id=assigned_filter)

    unassigned_count = Member.objects.filter(is_active=True, assigned_to__isnull=True).count()
    staff = User.objects.filter(is_active=True, profile__section__in=['followup', 'all'])

    paginator = Paginator(qs, 15)
    members   = paginator.get_page(request.GET.get('page'))

    context = {
        'members':          members,
        'search':           search,
        'status_filter':    status_filter,
        'assigned_filter':  assigned_filter,
        'staff':            staff,
        'unassigned_count': unassigned_count,
        'status_choices':   Member.STATUS_CHOICES,
        'is_section_admin': is_section_admin(request.user),
    }
    return render(request, 'enquiries/followup_list.html', context)

@login_required
def followup_create(request, member_pk=None):
    if get_section(request.user) == 'greeters' and not can_see_all(request.user):
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    member = Member.objects.get(pk=member_pk) if member_pk else None

    if request.method == 'POST':
        form = FollowUpForm(request.POST)
        if form.is_valid():
            followup             = form.save(commit=False)
            followup.assigned_by = request.user
            followup.status      = 'pending'
            if not followup.assigned_to:
                followup.assigned_to = request.user
            followup.save()
            messages.success(request, 'Follow-up assigned successfully!')
            return redirect('followup_list')
    else:
        form = FollowUpForm(initial={'member': member})
        form.fields['assigned_to'].queryset = User.objects.filter(
            is_active=True, profile__section__in=['followup', 'all']
        )

    return render(request, 'enquiries/followup_form.html', {
        'form': form, 'followup': None, 'title': 'Assign Follow-Up'
    })


@login_required
def followup_edit(request, pk):
    if get_section(request.user) == 'greeters' and not can_see_all(request.user):
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    followup = get_object_or_404(followup_qs(request.user), pk=pk)
    if request.method == 'POST':
        form = FollowUpForm(request.POST, instance=followup)
        if form.is_valid():
            form.save()
            messages.success(request, 'Follow-up updated.')
            return redirect('followup_list')
    else:
        form = FollowUpForm(instance=followup)
        form.fields['assigned_to'].queryset = User.objects.filter(
            is_active=True, profile__section__in=['followup', 'all']
        )
    return render(request, 'enquiries/followup_form.html', {
        'form': form, 'title': 'Edit Follow-up', 'followup': followup
    })


@login_required
def followup_delete(request, pk):
    followup = get_object_or_404(followup_qs(request.user), pk=pk)
    if request.method == 'POST':
        followup.delete()
        messages.success(request, 'Follow-up deleted successfully.')
        return redirect('followup_list')
    return render(request, 'enquiries/confirm_delete.html', {
        'object': followup, 'type': 'follow-up'
    })


@login_required
def followup_complete(request, pk):
    followup = get_object_or_404(followup_qs(request.user), pk=pk)
    if request.method == 'POST':
        followup.status         = 'completed'
        followup.completed_date = timezone.now().date()
        outcome = request.POST.get('outcome', '')
        if outcome:
            followup.outcome = outcome
        followup.save()

        # Auto-create round 2 only if this was round 1 and round 2 doesn't exist yet
        if followup.follow_up_round == 1:
            already_has_round2 = FollowUp.objects.filter(
                member=followup.member,
                follow_up_round=2,
            ).exists()
            if not already_has_round2:
                FollowUp.objects.create(
                    member          = followup.member,
                    assigned_to     = followup.assigned_to,
                    assigned_by     = followup.assigned_by,
                    follow_up_type  = followup.follow_up_type,
                    status          = 'pending',
                    priority        = followup.priority,
                    follow_up_round = 2,
                    due_date        = timezone.now().date() + timedelta(days=7),
                    notes           = f'Auto-created: second follow-up for {followup.member.get_full_name()}.',
                )
                messages.success(request, 'Follow-up completed! A second follow-up has been scheduled for next week.')
            else:
                messages.success(request, 'Follow-up marked as completed!')
        else:
            messages.success(request, 'Follow-up marked as completed!')

    return redirect('followup_tasks')


# ─────────────────────────────────────────────
#  EVENTS
# ─────────────────────────────────────────────

@login_required
def event_list(request):
    upcoming = Event.objects.filter(start_date__gte=timezone.now()).order_by('start_date')
    past     = Event.objects.filter(start_date__lt=timezone.now()).order_by('-start_date')[:10]
    return render(request, 'enquiries/event_list.html', {'upcoming': upcoming, 'past': past})


@login_required
def event_create(request):
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event           = form.save(commit=False)
            event.organizer = request.user
            event.status    = 'upcoming'
            event.save()
            messages.success(request, f'Event "{event.title}" created!')
            return redirect('event_list')
    else:
        form = EventForm()
    return render(request, 'enquiries/event_form.html', {'form': form, 'title': 'Create Event'})


@login_required
def event_detail(request, pk):
    event       = get_object_or_404(Event, pk=pk)
    attendances = event.attendances.select_related('member')
    return render(request, 'enquiries/event_detail.html', {'event': event, 'attendances': attendances})


@login_required
def event_edit(request, pk):
    event = get_object_or_404(Event, pk=pk)
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, 'Event updated!')
            return redirect('event_detail', pk=pk)
    else:
        form = EventForm(instance=event)
    return render(request, 'enquiries/event_form.html', {'form': form, 'title': 'Edit Event', 'event': event})


# ─────────────────────────────────────────────
#  MESSAGES
# ─────────────────────────────────────────────

@login_required
def message_list(request):
    msgs        = Message.objects.all().select_related('sender').order_by('-created_at')
    type_filter = request.GET.get('type', '')
    if type_filter:
        msgs = msgs.filter(message_type=type_filter)

    paginator     = Paginator(msgs, 10)
    messages_list = paginator.get_page(request.GET.get('page'))

    context = {
        'messages_list': messages_list,
        'type_filter':   type_filter,
        'type_choices':  Message.TYPE_CHOICES,
    }
    return render(request, 'enquiries/message_list.html', context)


from django.utils import timezone
from django.contrib import messages
from django.shortcuts import render, redirect
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth.decorators import login_required

@login_required
def message_create(request):
    staff = section_staff_qs(request.user)

    if request.method == 'POST':
        form = MessageForm(request.POST)

        if form.is_valid():
            msg = form.save(commit=False)
            msg.sender = request.user
            msg.save()
            form.save_m2m()

            action = request.POST.get('action', 'draft')
            send_to_all = request.POST.get('send_to_all') == 'on'

            # 🔥 START WITH BASE QUERYSET
            members = Member.objects.filter(is_active=True)

            # 🔥 APPLY FILTERS ONLY IF NOT "SEND TO ALL"
            if not send_to_all:
                date_from = request.POST.get('date_from')
                date_to = request.POST.get('date_to')

                # If recipients manually selected → use them
                if msg.recipients.exists():
                    members = msg.recipients.all()
                else:
                    if date_from:
                        members = members.filter(created_at__date__gte=date_from)

                    if date_to:
                        members = members.filter(created_at__date__lte=date_to)


            # 🚀 ACTION HANDLING
            if action == 'send':
                if msg.scheduled_at and msg.scheduled_at > timezone.now():
                    msg.status = 'scheduled'
                    messages.success(
                        request,
                        f'Message "{msg.title}" scheduled for {msg.scheduled_at}.'
                    )
                else:
                    msg.status = 'sent'
                    msg.sent_at = timezone.now()

                    total_sent = 0

                    for member in members:
                        if msg.message_type in ('email', 'both') and member.email:
                            send_mail(
                                msg.title,
                                msg.body,
                                settings.DEFAULT_FROM_EMAIL,
                                [member.email],
                                fail_silently=False
                            )

                        if msg.message_type in ('sms', 'both') and member.phone:
                            send_sms(member.phone, msg.body)

                        total_sent += 1

                    msg.total_sent = total_sent

                    messages.success(
                        request,
                        f'Message "{msg.title}" sent to {total_sent} recipients!'
                    )

            else:
                msg.status = 'draft'
                messages.success(
                    request,
                    f'Message "{msg.title}" saved as draft.'
                )

            msg.save()
            return redirect('message_list')

    else:
        form = MessageForm()

    return render(request, 'enquiries/message_form.html', {
        'form': form,
        'title': 'Compose Message',
        'staff': staff,
        'status_choices': Member.STATUS_CHOICES,
    })


@login_required
def send_draft_message(request, pk):
    msg = get_object_or_404(Message, pk=pk)

    if request.method == 'POST':
        members    = Member.objects.filter(is_active=True) if msg.send_to_all else msg.recipients.all()
        total_sent = 0

        for member in members:
            if msg.message_type in ('email', 'both') and member.email:
                send_mail(msg.title, msg.body, settings.DEFAULT_FROM_EMAIL, [member.email], fail_silently=False)
            if msg.message_type in ('sms', 'both') and member.phone:
                send_sms(member.phone, msg.body)
            total_sent += 1

        msg.status     = 'sent'
        msg.sent_at    = timezone.now()
        msg.total_sent = total_sent
        msg.save()
        messages.success(request, f'Message "{msg.title}" sent to {total_sent} recipients!')

    return redirect('message_list')


@login_required
def message_detail(request, pk):
    msg = get_object_or_404(Message, pk=pk)
    return render(request, 'enquiries/message_detail.html', {'msg': msg})


@login_required
def message_delete(request, pk):
    msg = get_object_or_404(Message, pk=pk)
    if request.method == 'POST':
        msg.delete()
        messages.success(request, 'Message deleted successfully.')
        return redirect('message_list')
    return render(request, 'enquiries/confirm_delete.html', {'object': msg, 'type': 'message'})


# ─────────────────────────────────────────────
#  PRAYER REQUESTS
# ─────────────────────────────────────────────

@login_required
def prayer_list(request):
    prayers       = PrayerRequest.objects.all().select_related('member', 'handled_by')
    status_filter = request.GET.get('status', '')
    if status_filter:
        prayers = prayers.filter(status=status_filter)
    return render(request, 'enquiries/prayer_list.html', {
        'prayers':        prayers,
        'status_filter':  status_filter,
        'status_choices': PrayerRequest.STATUS_CHOICES,
    })


@login_required
def prayer_create(request):
    if request.method == 'POST':
        form = PrayerRequestForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Prayer request logged.')
            return redirect('prayer_list')
    else:
        form = PrayerRequestForm()
    return render(request, 'enquiries/prayer_form.html', {'form': form, 'title': 'New Prayer Request'})


@login_required
def prayer_update(request, pk):
    prayer = get_object_or_404(PrayerRequest, pk=pk)
    if request.method == 'POST':
        form = PrayerRequestForm(request.POST, instance=prayer)
        if form.is_valid():
            form.save()
            messages.success(request, 'Prayer request updated.')
            return redirect('prayer_list')
    else:
        form = PrayerRequestForm(instance=prayer)
    return render(request, 'enquiries/prayer_form.html', {
        'form': form, 'title': 'Update Prayer Request', 'prayer': prayer
    })


# ─────────────────────────────────────────────
#  ATTENDANCE
# ─────────────────────────────────────────────

@login_required
def attendance_list(request):
    records = Attendance.objects.all().select_related('member', 'recorded_by').order_by('-date')[:50]
    return render(request, 'enquiries/attendance_list.html', {'records': records})


@login_required
def attendance_create(request):
    if request.method == 'POST':
        form = AttendanceForm(request.POST)
        if form.is_valid():
            att             = form.save(commit=False)
            att.recorded_by = request.user
            att.save()
            messages.success(request, 'Attendance recorded.')
            return redirect('attendance_list')
    else:
        form = AttendanceForm()
    return render(request, 'enquiries/attendance_form.html', {'form': form})


# ─────────────────────────────────────────────
#  MINISTRIES
# ─────────────────────────────────────────────

@login_required
def ministry_list(request):
    ministries = Ministry.objects.filter(is_active=True).annotate(member_count=Count('interested_members'))
    return render(request, 'enquiries/ministry_list.html', {'ministries': ministries})


@login_required
def ministry_create(request):
    if request.method == 'POST':
        form = MinistryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Ministry created!')
            return redirect('ministry_list')
    else:
        form = MinistryForm()
    return render(request, 'enquiries/ministry_form.html', {'form': form, 'title': 'Add Ministry'})


# ─────────────────────────────────────────────
#  ADMIN PANEL
# ─────────────────────────────────────────────

@login_required
def admin_panel(request):
    if not is_section_admin(request.user):
        messages.error(request, 'Access denied. Admin only.')
        return redirect('dashboard')

    from .models import Integration

    base_members  = member_qs(request.user)
    staff         = section_staff_qs(request.user).select_related('profile').order_by('-date_joined')
    all_followups = followup_qs(request.user).count()
    today         = timezone.now().date()

    top_staff = section_staff_qs(request.user).annotate(
        followup_count=Count('assigned_followups', filter=Q(assigned_followups__status='completed'))
    ).order_by('-followup_count')[:5]

    recent_activity = []
    for m in base_members.order_by('-created_at')[:5]:
        recent_activity.append({'type': 'member', 'obj': m, 'time': m.created_at})
    for fu in followup_qs(request.user).filter(status='completed').order_by('-updated_at')[:5]:
        recent_activity.append({'type': 'followup', 'obj': fu, 'time': fu.updated_at})
    recent_activity.sort(key=lambda x: x['time'], reverse=True)

    # ── Integration / conversion stats ──
    total_registered = base_members.count()
    total_integrated = base_members.filter(status='integrated').count()
    conversion_rate  = round((total_integrated / total_registered * 100), 1) if total_registered else 0

    integration_trend = []
    for i in range(5, -1, -1):
        month_start = (today.replace(day=1) - timedelta(days=i * 30)).replace(day=1)
        month_end   = (month_start + timedelta(days=32)).replace(day=1)
        count = Integration.objects.filter(
            integrated_on__gte=month_start, integrated_on__lt=month_end
        ).count()
        integration_trend.append({'month': month_start.strftime('%b'), 'count': count})

    context = {
        'staff':             staff,
        'all_members':       base_members.count(),
        'all_followups':     all_followups,
        'all_messages':      Message.objects.count(),
        'all_events':        Event.objects.count(),
        'all_prayers':       PrayerRequest.objects.count(),
        'all_ministries':    Ministry.objects.count(),
        'top_staff':         top_staff,
        'recent_activity':   recent_activity[:8],
        'section':           get_section(request.user),
        'can_see_all':       can_see_all(request.user),
        # Integration
        'total_registered':  total_registered,
        'total_integrated':  total_integrated,
        'conversion_rate':   conversion_rate,
        'integration_trend': integration_trend,
    }
    return render(request, 'admin_panel/dashboard.html', context)


@login_required
def staff_delete(request, pk):
    if not is_section_admin(request.user):
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    staff   = get_object_or_404(User, pk=pk)
    profile = get_profile(staff)

    if not can_see_all(request.user) and profile.section != get_section(request.user):
        messages.error(request, 'Access denied.')
        return redirect('staff_list')

    if request.method == 'POST':
        staff.is_active = False
        staff.save()
        messages.success(request, 'Staff member deactivated successfully.')
        return redirect('staff_list')

    return render(request, 'enquiries/confirm_delete.html', {
        'object': staff, 'type': 'staff member'
    })


@login_required
def admin_reports(request):
    if not is_section_admin(request.user):
        return redirect('dashboard')

    now         = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    base        = member_qs(request.user)

    monthly_new            = base.filter(first_visit_date__gte=month_start).count()
    monthly_followups_done = followup_qs(request.user).filter(completed_date__gte=month_start).count()
    monthly_messages       = Message.objects.filter(sent_at__gte=month_start).count()

    status_breakdown   = base.values('status').annotate(count=Count('status'))
    followup_breakdown = followup_qs(request.user).values('status').annotate(count=Count('status'))

    context = {
        'monthly_new':            monthly_new,
        'monthly_followups_done': monthly_followups_done,
        'monthly_messages':       monthly_messages,
        'status_breakdown':       status_breakdown,
        'followup_breakdown':     followup_breakdown,
        'section':                get_section(request.user),
    }
    return render(request, 'admin_panel/reports.html', context)









# ─────────────────────────────────────────────
#  GREETER ASSIGNMENTS
# ─────────────────────────────────────────────

@login_required
def greeter_list(request):
    if get_section(request.user) == 'followup' and not can_see_all(request.user):
        messages.error(request, 'Greeter assignments are managed by the Greeters section.')
        return redirect('dashboard')

    qs = member_qs(request.user).select_related('greeter_assigned_to')
    status_filter   = request.GET.get('status', '')
    assigned_filter = request.GET.get('assigned', '')
    search          = request.GET.get('search', '')

    if search:
        qs = qs.filter(Q(first_name__icontains=search) | Q(last_name__icontains=search))
    if status_filter:
        qs = qs.filter(status=status_filter)
    if assigned_filter:
        qs = qs.filter(greeter_assigned_to_id=assigned_filter)

    unassigned_count = qs.filter(greeter_assigned_to__isnull=True).count()

    paginator = Paginator(qs, 15)
    members   = paginator.get_page(request.GET.get('page'))
    staff     = User.objects.filter(is_active=True, profile__section__in=['greeters', 'all'])

    return render(request, 'enquiries/greeter_list.html', {
        'members':          members,
        'staff':            staff,
        'search':           search,
        'status_filter':    status_filter,
        'assigned_filter':  assigned_filter,
        'unassigned_count': unassigned_count,
        'status_choices':   Member.STATUS_CHOICES,
        'is_section_admin': is_section_admin(request.user),
    })


@login_required
def greeter_assign_quick(request, pk):
    """Quick POST to assign/reassign a greeter from the greeter list."""
    if not is_section_admin(request.user):
        messages.error(request, 'Access denied.')
        return redirect('greeter_list')

    member   = get_object_or_404(member_qs(request.user), pk=pk)
    staff_id = request.POST.get('staff_id')
    if staff_id:
        staff_user = get_object_or_404(
            User.objects.filter(is_active=True, profile__section__in=['greeters', 'all']), pk=staff_id
        )
        member.greeter_assigned_to = staff_user
        member.save()
        messages.success(request, f'Assigned {member.get_full_name()} to {staff_user.get_full_name()}.')
    return redirect('greeter_list')


# ─────────────────────────────────────────────
#  INTEGRATION UNIT
# ─────────────────────────────────────────────

from .models import Integration
from .forms  import IntegrationForm   # create this form (see below)

@login_required
def integration_list(request):
    if not can_see_all(request.user) and get_section(request.user) not in ('followup',):
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    integrations  = Integration.objects.select_related('member', 'integrated_by').order_by('-integrated_on')
    pathway_filter = request.GET.get('pathway', '')
    if pathway_filter:
        integrations = integrations.filter(pathway=pathway_filter)

    # Candidates: members who are 'regular' but not yet integrated
    candidates = Member.objects.filter(is_active=True, status='regular').exclude(
        integration__isnull=False
    ).count()

    paginator    = Paginator(integrations, 15)
    integrations = paginator.get_page(request.GET.get('page'))

    return render(request, 'enquiries/integration_list.html', {
        'integrations':    integrations,
        'pathway_filter':  pathway_filter,
        'pathway_choices': Integration.PATHWAY_CHOICES,
        'candidates':      candidates,
    })


@login_required
def integration_create(request, member_pk=None):
    if not can_see_all(request.user) and get_section(request.user) not in ('followup',):
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    member = get_object_or_404(Member, pk=member_pk) if member_pk else None

    if request.method == 'POST':
        form = IntegrationForm(request.POST)
        if form.is_valid():
            integration              = form.save(commit=False)
            integration.integrated_by = request.user
            integration.save()
            # Promote member status to integrated
            integration.member.status = 'integrated'
            integration.member.save()
            messages.success(request, f'{integration.member.get_full_name()} marked as integrated!')
            return redirect('integration_list')
    else:
        form = IntegrationForm(initial={'member': member})

    return render(request, 'enquiries/integration_form.html', {
        'form': form, 'title': 'Mark Member as Integrated'
    })


@login_required
def integration_update(request, pk):
    integration = get_object_or_404(Integration, pk=pk)
    if request.method == 'POST':
        form = IntegrationForm(request.POST, instance=integration)
        if form.is_valid():
            form.save()
            messages.success(request, 'Integration record updated.')
            return redirect('integration_list')
    else:
        form = IntegrationForm(instance=integration)
    return render(request, 'enquiries/integration_form.html', {
        'form': form, 'title': 'Edit Integration Record', 'integration': integration
    })



# ─────────────────────────────────────────────
#  CONTACT LOGS
# ─────────────────────────────────────────────

@login_required
def contact_log_create(request, member_pk):
    """
    Staff logs a contact attempt / interaction with a member.
    Works for both greeters and follow-up staff.
    Redirects back to the member detail page.
    """
    member  = get_object_or_404(member_qs(request.user), pk=member_pk)
    profile = get_profile(request.user)

    if request.method == 'POST':
        form = ContactLogForm(request.POST)
        if form.is_valid():
            log            = form.save(commit=False)
            log.member     = member
            log.logged_by  = request.user
            log.section    = profile.section if profile.section != 'all' else 'followup'
            log.save()
            messages.success(request, f'Contact log recorded for {member.get_full_name()}.')
            return redirect('member_detail', pk=member_pk)
    else:
        form = ContactLogForm(initial={'contacted_on': timezone.now().date()})

    return render(request, 'enquiries/contact_log_form.html', {
        'form':   form,
        'member': member,
        'title':  f'Log Contact — {member.get_full_name()}',
    })


@login_required
def contact_log_delete(request, pk):
    log = get_object_or_404(ContactLog, pk=pk, logged_by=request.user)
    member_pk = log.member.pk
    if request.method == 'POST':
        log.delete()
        messages.success(request, 'Contact log deleted.')
    return redirect('member_detail', pk=member_pk)


@login_required
def contact_log_list(request):
    """
    Section heads / admins see all logs in their section.
    Regular staff see only their own logs.
    """
    profile = get_profile(request.user)

    if can_see_all(request.user):
        logs = ContactLog.objects.all()
    elif is_section_admin(request.user):
        logs = ContactLog.objects.filter(section=profile.section)
    else:
        logs = ContactLog.objects.filter(logged_by=request.user)

    logs = logs.select_related('member', 'logged_by').order_by('-contacted_on', '-created_at')

    # Filters
    section_filter = request.GET.get('section', '')
    method_filter  = request.GET.get('method', '')
    staff_filter   = request.GET.get('staff', '')

    if section_filter and can_see_all(request.user):
        logs = logs.filter(section=section_filter)
    if method_filter:
        logs = logs.filter(method=method_filter)
    if staff_filter and is_section_admin(request.user):
        logs = logs.filter(logged_by_id=staff_filter)

    paginator = Paginator(logs, 20)
    logs      = paginator.get_page(request.GET.get('page'))
    staff     = section_staff_qs(request.user)

    return render(request, 'enquiries/contact_log_list.html', {
        'logs':            logs,
        'section_filter':  section_filter,
        'method_filter':   method_filter,
        'staff_filter':    staff_filter,
        'staff':           staff,
        'method_choices':  ContactLog.METHOD_CHOICES,
        'section_choices': [('greeters', 'Greeters'), ('followup', 'Follow-Up')],
        'is_section_admin': is_section_admin(request.user),
        'can_see_all':     can_see_all(request.user),
        'section':         profile.section,
    })









@login_required
def followup_tasks(request):
    if get_section(request.user) == 'greeters' and not can_see_all(request.user):
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    qs = followup_qs(request.user).select_related('member', 'assigned_to')

    search          = request.GET.get('search', '')
    status_filter   = request.GET.get('status', '')
    type_filter     = request.GET.get('type', '')
    assigned_filter = request.GET.get('assigned', '')
    priority_filter = request.GET.get('priority', '')

    if search:
        qs = qs.filter(
            Q(member__first_name__icontains=search) |
            Q(member__last_name__icontains=search)
        )
    if status_filter:
        qs = qs.filter(status=status_filter)
    if type_filter:
        qs = qs.filter(follow_up_type=type_filter)
    if assigned_filter:
        qs = qs.filter(assigned_to_id=assigned_filter)
    if priority_filter:
        qs = qs.filter(priority=priority_filter)

    today = timezone.now().date()

    total_count     = qs.count()
    pending_count   = qs.filter(status__in=['pending', 'in_progress']).count()
    overdue_count   = qs.filter(status__in=['pending', 'in_progress'], due_date__lt=today).count()
    completed_count = qs.filter(status='completed').count()

    paginator  = Paginator(qs, 20)
    follow_ups = paginator.get_page(request.GET.get('page'))
    staff      = User.objects.filter(is_active=True, profile__section__in=['followup', 'all'])

    context = {
        'follow_ups':       follow_ups,
        'search':           search,
        'status_filter':    status_filter,
        'type_filter':      type_filter,
        'assigned_filter':  assigned_filter,
        'priority_filter':  priority_filter,
        'staff':            staff,
        'total_count':      total_count,
        'pending_count':    pending_count,
        'overdue_count':    overdue_count,
        'completed_count':  completed_count,
        'status_choices':   FollowUp.STATUS_CHOICES,
        'type_choices':     FollowUp.TYPE_CHOICES,
        'is_section_admin': is_section_admin(request.user),
    }
    return render(request, 'enquiries/followup_tasks.html', context)




@login_required
def integration_quick(request, member_pk):
    """
    One-click promote a member to 'integrated'.
    Creates an Integration record and updates the member's status.
    Redirects back to wherever the user came from.
    """
    if not can_see_all(request.user) and get_section(request.user) not in ('followup',):
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    member = get_object_or_404(Member, pk=member_pk, is_active=True)

    if request.method == 'POST':
        if member.status != 'integrated':
            # Only create a record if one doesn't already exist
            if not Integration.objects.filter(member=member).exists():
                Integration.objects.create(
                    member=member,
                    integrated_by=request.user,
                    integrated_on=timezone.now().date(),
                    pathway='general',   # sensible default — edit if you have a preferred one
                )
            member.status = 'integrated'
            member.save()
            messages.success(request, f'{member.get_full_name()} has been marked as integrated.')
        else:
            messages.info(request, f'{member.get_full_name()} is already integrated.')

    return redirect(request.POST.get('next', 'member_list'))