from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Member(models.Model):
    # ================== CHOICES ==================
    GENDER_CHOICES = [('M', 'Male'), ('F', 'Female')]

    STATUS_CHOICES = [
        ('new', 'New Visitor'),
        # ('returning', 'Returning Visitor'),
        # ('regular', 'Regular Attendee'),
        # ('member', 'Full Member'),
        ('integrated', 'Integrated Member'),
        ('inactive', 'Inactive'),
    ]

    MARITAL_CHOICES = [
        ('single', 'Single'),
        ('married', 'Married'),
        ('divorced', 'Divorced'),
        ('widowed', 'Widowed'),
    ]

    AGE_BRACKET_CHOICES = [
        ('under_18', 'Under 18'),
        ('18_25', '18 – 25'),
        ('26_35', '26 – 35'),
        ('36_45', '36 – 45'),
        ('46_55', '46 – 55'),
        ('56_65', '56 – 65'),
        ('above_65', 'Above 65'),
    ]

    BORN_AGAIN_CHOICES = [
        ('yes', 'Yes'),
        ('no', 'No'),
        ('not_sure', 'Not Sure'),
    ]

    JOINING_CHOICES = [
        ('yes', 'Yes'),
        ('no', 'No'),
        ('considering', 'Still Considering'),
    ]

    VISIT_TIME_CHOICES = [
        ('weekday_morning', 'Weekday Morning'),
        ('weekday_afternoon', 'Weekday Afternoon'),
        ('weekday_evening', 'Weekday Evening'),
        ('saturday_morning', 'Saturday Morning'),
        ('saturday_afternoon', 'Saturday Afternoon'),
        ('sunday_after_service', 'Sunday After Service'),
    ]

    # ================== PERSONAL INFO ==================
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True, null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    whatsapp = models.CharField(max_length=20, null=True, blank=True)

    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)

    age_bracket = models.CharField(
        max_length=20, choices=AGE_BRACKET_CHOICES, null=True, blank=True
    )

    marital_status = models.CharField(
        max_length=20, choices=MARITAL_CHOICES, null=True, blank=True
    )

    address = models.TextField(null=True, blank=True)
    vocation_address = models.TextField(null=True, blank=True)
    occupation = models.CharField(max_length=100, null=True, blank=True)

    # ================== CHURCH / VISITOR INFO ==================
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    first_visit_date = models.DateField(default=timezone.now)

    how_did_you_hear = models.CharField(max_length=200, null=True, blank=True)
    previous_church = models.CharField(max_length=200, null=True, blank=True)

    invitee = models.CharField(
        max_length=200, null=True, blank=True,
        help_text="Name of the person who invited this visitor"
    )

    is_born_again = models.CharField(
        max_length=10, choices=BORN_AGAIN_CHOICES, null=True, blank=True
    )

    joining_church = models.CharField(
        max_length=20, choices=JOINING_CHOICES, null=True, blank=True
    )

    preferred_visit_time = models.CharField(
        max_length=30, choices=VISIT_TIME_CHOICES, null=True, blank=True
    )

    prayer_requests = models.TextField(null=True, blank=True)

    observation = models.TextField(
        null=True, blank=True,
        help_text="Staff observations about the visitor"
    )

    interests = models.ManyToManyField(
        'Ministry', blank=True, related_name='interested_members'
    )

    # ================== SYSTEM ==================
    # Follow-Up section assignment
    assigned_to = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='assigned_members',
        help_text="Staff member responsible for follow-up / visitation"
    )
 
    # Greeters section assignment  ← NEW
    greeter_assigned_to = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='greeter_assigned_members',
        help_text="Greeter staff member assigned to welcome this visitor"
    )

    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='created_members'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    notes = models.TextField(null=True, blank=True)
    profile_photo = models.ImageField(upload_to='members/', null=True, blank=True)

    is_baptized = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.last_name} {self.first_name}"

    def get_full_name(self):
        return f"{self.last_name} {self.first_name}"

    @property
    def initials(self):
        return f"{self.first_name[0]}{self.last_name[0]}".upper()




class Ministry(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    leader = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    icon = models.CharField(max_length=50, default='church', help_text='Icon name')
    color = models.CharField(max_length=20, default='gold', help_text='Tailwind color')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Ministries'

    def __str__(self):
        return self.name


class FollowUp(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('no_response', 'No Response'),
    ]
    TYPE_CHOICES = [
        ('call', 'Phone Call'),
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('visit', 'Personal Visit'),
        ('whatsapp', 'WhatsApp'),
    ]

    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='follow_ups')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='assigned_followups')
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='delegated_followups')
    follow_up_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='call')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    due_date = models.DateField()
    completed_date = models.DateField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    outcome = models.TextField(null=True, blank=True)
    priority = models.IntegerField(choices=[(1, 'Low'), (2, 'Medium'), (3, 'High')], default=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    follow_up_round = models.IntegerField(
        default=1,
        choices=[(1, 'First Follow-Up'), (2, 'Second Follow-Up')],
        help_text="Which follow-up round this is"
    )

    class Meta:
        ordering = ['-priority', 'due_date']

    def __str__(self):
        return f"Follow-up: {self.member} by {self.assigned_to}"

    # @property
    # def is_overdue(self):
    #     return self.status != 'completed' and self.due_date < timezone.now().date()

    @property
    def is_overdue(self):
        return (
            self.status in ('pending', 'in_progress') and
            self.due_date is not None and
            self.due_date < timezone.now().date()
        )


class Event(models.Model):
    STATUS_CHOICES = [
        ('upcoming', 'Upcoming'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    TYPE_CHOICES = [
        ('service', 'Church Service'),
        ('program', 'Special Program'),
        ('retreat', 'Retreat'),
        ('outreach', 'Outreach'),
        ('training', 'Training'),
        ('social', 'Social Gathering'),
        ('other', 'Other'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    event_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='service')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='upcoming')
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    venue = models.CharField(max_length=200)
    organizer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    max_attendees = models.IntegerField(null=True, blank=True)
    banner = models.ImageField(upload_to='events/', null=True, blank=True)
    send_notifications = models.BooleanField(default=True)
    target_audience = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['start_date']

    def __str__(self):
        return self.title


class EventAttendance(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='attendances')
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    registered_at = models.DateTimeField(auto_now_add=True)
    attended = models.BooleanField(default=False)

    class Meta:
        unique_together = ['event', 'member']


class Message(models.Model):
    TYPE_CHOICES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('both', 'Email & SMS'),
        # ('prayer', 'Prayer Message'),
        # ('notification', 'Event Notification'),
        # ('welcome', 'Welcome Message'),
        # ('announcement', 'Announcement'),
    ]
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    ]

    title = models.CharField(max_length=200)
    message_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    subject = models.CharField(max_length=200, null=True, blank=True)
    body = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    recipients = models.ManyToManyField(Member, blank=True, related_name='received_messages')
    send_to_all = models.BooleanField(default=False)
    scheduled_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    total_sent = models.IntegerField(default=0)
    total_failed = models.IntegerField(default=0)
    related_event = models.ForeignKey(Event, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class PrayerRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Prayer'),
        ('praying', 'Being Prayed For'),
        ('answered', 'Answered'),
    ]

    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='prayer_list')
    request = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    is_anonymous = models.BooleanField(default=False)
    testimony = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    handled_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Prayer: {self.member} - {self.status}"


class Attendance(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField()
    service_type = models.CharField(max_length=100, default='Sunday Service')
    notes = models.CharField(max_length=200, null=True, blank=True)
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']
        unique_together = ['member', 'date', 'service_type']

    def __str__(self):
        return f"{self.member} - {self.date}"


class Note(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='member_notes')
    content = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_private = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Note for {self.member} by {self.created_by}"






class Integration(models.Model):
    PATHWAY_CHOICES = [
        ('Fully Integrated', 'Fully Integrated'),
        # ('membership_class', 'Membership Class'),
        # ('water_baptism', 'Water Baptism'),
        # ('cell_group', 'Cell Group'),
        # ('ministry', 'Ministry Involvement'),
        # ('other', 'Other'),
    ]
    member = models.OneToOneField(Member, on_delete=models.CASCADE, related_name='integration')
    integrated_on = models.DateField(default=timezone.now)
    pathway = models.CharField(max_length=30, choices=PATHWAY_CHOICES)
    integrated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='integrations_handled')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.member.get_full_name()} — integrated {self.integrated_on}"







class ContactLog(models.Model):
    METHOD_CHOICES = [
        ('call',    'Phone Call'),
        ('sms',     'SMS'),
        ('email',   'Email'),
        ('visit',   'In-Person Visit'),
        ('whatsapp','WhatsApp'),
        ('other',   'Other'),
    ]
    OUTCOME_CHOICES = [
        ('reached',       'Reached — spoke with member'),
        ('no_answer',     'No answer'),
        ('left_message',  'Left a message'),
        ('not_available', 'Not available'),
        ('visited',       'Visit completed'),
        ('other',         'Other'),
    ]

    member     = models.ForeignKey('Member', on_delete=models.CASCADE, related_name='contact_logs')
    logged_by  = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='contact_logs')
    section    = models.CharField(max_length=20, choices=[('greeters','Greeters'),('followup','Follow-Up')], default='followup')
    method     = models.CharField(max_length=20, choices=METHOD_CHOICES)
    outcome    = models.CharField(max_length=20, choices=OUTCOME_CHOICES)
    notes      = models.TextField(blank=True)
    contacted_on = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-contacted_on', '-created_at']

    def __str__(self):
        return f"{self.logged_by} → {self.member} ({self.get_method_display()}) on {self.contacted_on}"