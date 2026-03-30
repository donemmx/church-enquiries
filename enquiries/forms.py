from django import forms
from .models import Member, FollowUp, Event, Message, PrayerRequest, Attendance, Note, Ministry, Integration, ContactLog
from django.contrib.auth.models import User


class MemberForm(forms.ModelForm):
    class Meta:
        model = Member
        fields = [
            'first_name', 'last_name', 'email', 'phone', 'whatsapp',
            'gender', 'date_of_birth', 'age_bracket',
            'marital_status', 'address', 'vocation_address',
            'occupation',

            'status', 'first_visit_date',
            'how_did_you_hear', 'previous_church',

            'invitee',                 # ✅ ADD
            'is_born_again',           # ✅ ADD
            'joining_church',          # ✅ ADD
            'preferred_visit_time',    # ✅ ADD

            'prayer_requests', 'observation',

            'interests',
            'assigned_to',
            'notes',
            'is_baptized',
            'profile_photo',
        ]

        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'input-field'}),
            'last_name': forms.TextInput(attrs={'class': 'input-field'}),
            'email': forms.EmailInput(attrs={'class': 'input-field'}),
            'phone': forms.TextInput(attrs={'class': 'input-field'}),
            'whatsapp': forms.TextInput(attrs={'class': 'input-field'}),

            'gender': forms.Select(attrs={'class': 'input-field'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'input-field', 'type': 'date'}),
            'age_bracket': forms.Select(attrs={'class': 'input-field'}),

            'marital_status': forms.Select(attrs={'class': 'input-field'}),
            'address': forms.Textarea(attrs={'class': 'input-field', 'rows': 2}),
            'vocation_address': forms.Textarea(attrs={'class': 'input-field', 'rows': 2}),

            'occupation': forms.TextInput(attrs={'class': 'input-field'}),

            'status': forms.Select(attrs={'class': 'input-field'}),
            'first_visit_date': forms.DateInput(attrs={'class': 'input-field', 'type': 'date'}),

            'how_did_you_hear': forms.TextInput(attrs={'class': 'input-field'}),
            'previous_church': forms.TextInput(attrs={'class': 'input-field'}),

            'invitee': forms.TextInput(attrs={'class': 'input-field'}),

            'is_born_again': forms.Select(attrs={'class': 'input-field'}),
            'joining_church': forms.Select(attrs={'class': 'input-field'}),
            'preferred_visit_time': forms.Select(attrs={'class': 'input-field'}),

            'prayer_requests': forms.Textarea(attrs={'class': 'input-field', 'rows': 3}),
            'observation': forms.Textarea(attrs={'class': 'input-field', 'rows': 3}),

            'interests': forms.CheckboxSelectMultiple(),

            'assigned_to': forms.Select(attrs={'class': 'input-field'}),
            'notes': forms.Textarea(attrs={'class': 'input-field', 'rows': 2}),

            'profile_photo': forms.FileInput(attrs={'class': 'form-file'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['assigned_to'].queryset = User.objects.filter(is_active=True)
        self.fields['assigned_to'].required = False
        self.fields['status'].initial = 'new'

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        # Remove spaces, dashes, parentheses
        phone = ''.join(filter(str.isdigit, phone))
        if phone.startswith('0'):
            phone = '+234' + phone[1:]
        elif not phone.startswith('+'):
            phone = '+' + phone
        return phone


class FollowUpForm(forms.ModelForm):
    class Meta:
        model = FollowUp
        fields = ['member', 'assigned_to', 'follow_up_type', 'due_date', 'notes', 'outcome', 'priority']
        widgets = {
            'member': forms.Select(attrs={'class': 'input-field'}),
            'assigned_to': forms.Select(attrs={'class': 'input-field'}),
            'follow_up_type': forms.Select(attrs={'class': 'input-field'}),
            'status': forms.Select(attrs={'class': 'input-field'}),
            'due_date': forms.DateInput(attrs={'class': 'input-field', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'input-field', 'rows': 3, 'placeholder': 'Notes about this follow-up...'}),
            'outcome': forms.Textarea(attrs={'class': 'input-field', 'rows': 3, 'placeholder': 'Outcome after completion...'}),
            'priority': forms.Select(attrs={'class': 'input-field'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['assigned_to'].queryset = User.objects.filter(is_active=True)


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = [
            'title','description','event_type',
            'start_date','end_date','venue','max_attendees',
            'banner','send_notifications','target_audience'
        ]

        widgets = {
            'start_date': forms.DateTimeInput(
                attrs={'class': 'input-field', 'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M'
            ),
            'end_date': forms.DateTimeInput(
                attrs={'class': 'input-field', 'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M'
            ),
        }

    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.fields['start_date'].input_formats = ['%Y-%m-%dT%H:%M']
        self.fields['end_date'].input_formats = ['%Y-%m-%dT%H:%M']


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['title', 'message_type', 'subject', 'body', 'send_to_all', 'recipients', 'scheduled_at', 'related_event']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'input-field', 'placeholder': 'Message Title'}),
            'message_type': forms.Select(attrs={'class': 'input-field'}),
            'subject': forms.TextInput(attrs={'class': 'input-field', 'placeholder': 'Email Subject'}),
            'body': forms.Textarea(attrs={'class': 'input-field', 'rows': 8, 'placeholder': 'Message content...'}),
            'recipients': forms.CheckboxSelectMultiple(),
            'scheduled_at': forms.DateTimeInput(attrs={'class': 'input-field', 'type': 'datetime-local'}),
            'related_event': forms.Select(attrs={'class': 'input-field'}),
        }


class PrayerRequestForm(forms.ModelForm):
    class Meta:
        model = PrayerRequest
        fields = ['member', 'request', 'status', 'is_anonymous', 'testimony', 'handled_by']
        widgets = {
            'member': forms.Select(attrs={'class': 'input-field'}),
            'request': forms.Textarea(attrs={'class': 'input-field', 'rows': 4, 'placeholder': 'Prayer request...'}),
            'status': forms.Select(attrs={'class': 'input-field'}),
            'testimony': forms.Textarea(attrs={'class': 'input-field', 'rows': 3, 'placeholder': 'Testimony (if answered)...'}),
            'handled_by': forms.Select(attrs={'class': 'input-field'}),
        }


class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ['member', 'date', 'service_type', 'notes']
        widgets = {
            'member': forms.Select(attrs={'class': 'input-field'}),
            'date': forms.DateInput(attrs={'class': 'input-field', 'type': 'date'}),
            'service_type': forms.TextInput(attrs={'class': 'input-field', 'placeholder': 'e.g., Sunday Service'}),
            'notes': forms.TextInput(attrs={'class': 'input-field', 'placeholder': 'Notes'}),
        }


class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ['content', 'is_private']
        widgets = {
            'content': forms.Textarea(attrs={'class': 'input-field', 'rows': 3, 'placeholder': 'Add a note...'}),
        }


class MinistryForm(forms.ModelForm):
    class Meta:
        model = Ministry
        fields = ['name', 'description', 'leader', 'icon', 'color', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'input-field', 'placeholder': 'Ministry Name'}),
            'description': forms.Textarea(attrs={'class': 'input-field', 'rows': 3}),
            'leader': forms.Select(attrs={'class': 'input-field'}),
            'icon': forms.TextInput(attrs={'class': 'input-field', 'placeholder': 'Icon class name'}),
            'color': forms.TextInput(attrs={'class': 'input-field', 'placeholder': 'Color (e.g., gold, blue)'}),
        }




class IntegrationForm(forms.ModelForm):
    class Meta:
        model  = Integration
        fields = ['member', 'integrated_on', 'pathway', 'notes']
        widgets = {
            'integrated_on': forms.DateInput(attrs={'type': 'date'}),
            'notes':         forms.Textarea(attrs={'rows': 3}),
        }


class ContactLogForm(forms.ModelForm):
    class Meta:
        model  = ContactLog
        fields = ['method', 'outcome', 'contacted_on', 'notes']
        widgets = {
            'contacted_on': forms.DateInput(attrs={'type': 'date'}),
            'notes':        forms.Textarea(attrs={'rows': 2, 'placeholder': 'Brief notes on the interaction…'}),
        }