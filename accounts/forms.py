# accounts/forms.py  — updated StaffCreateForm and StaffEditForm

from django import forms
from django.contrib.auth.models import User
from .models import UserProfile


class LoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'input-field', 'placeholder': 'Username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'input-field', 'placeholder': 'Password'}))


class ProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['phone', 'bio', 'department', 'photo']
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'input-field'}),
            'bio': forms.Textarea(attrs={'class': 'input-field', 'rows': 3}),
            'department': forms.TextInput(attrs={'class': 'input-field'}),
        }


class StaffCreateForm(forms.Form):
    first_name  = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'input-field'}))
    last_name   = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'input-field'}))
    username    = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'input-field'}))
    email       = forms.EmailField(required=False, widget=forms.EmailInput(attrs={'class': 'input-field'}))
    phone       = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={'class': 'input-field'}))
    department  = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'input-field'}))
    bio         = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'input-field', 'rows': 2}))

    role = forms.ChoiceField(
        choices=UserProfile.ROLE_CHOICES,
        widget=forms.Select(attrs={'class': 'input-field'})
    )
    section = forms.ChoiceField(
        choices=UserProfile.SECTION_CHOICES,
        widget=forms.Select(attrs={'class': 'input-field'}),
        help_text="Which section does this staff member belong to?"
    )

    password1 = forms.CharField(label='Password', widget=forms.PasswordInput(attrs={'class': 'input-field'}))
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput(attrs={'class': 'input-field'}))

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('This username is already taken.')
        return username

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('password1')
        p2 = cleaned.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('Passwords do not match.')
        return cleaned

    def save(self):
        d = self.cleaned_data
        user = User.objects.create_user(
            username=d['username'],
            password=d['password1'],
            first_name=d['first_name'],
            last_name=d['last_name'],
            email=d.get('email', ''),
        )
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.role       = d['role']
        profile.section    = d['section']
        profile.phone      = d.get('phone', '')
        profile.department = d.get('department', '')
        profile.bio        = d.get('bio', '')
        profile.save()
        return user


class StaffEditForm(forms.Form):
    first_name  = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'input-field'}))
    last_name   = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'input-field'}))
    email       = forms.EmailField(required=False, widget=forms.EmailInput(attrs={'class': 'input-field'}))
    phone       = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={'class': 'input-field'}))
    department  = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'input-field'}))
    bio         = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'input-field', 'rows': 2}))
    is_active   = forms.BooleanField(required=False)

    role = forms.ChoiceField(
        choices=UserProfile.ROLE_CHOICES,
        widget=forms.Select(attrs={'class': 'input-field'})
    )
    section = forms.ChoiceField(
        choices=UserProfile.SECTION_CHOICES,
        widget=forms.Select(attrs={'class': 'input-field'})
    )


class ResetPasswordForm(forms.Form):
    new_password1 = forms.CharField(label='New Password', widget=forms.PasswordInput(attrs={'class': 'input-field'}))
    new_password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput(attrs={'class': 'input-field'}))

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('new_password1')
        p2 = cleaned.get('new_password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('Passwords do not match.')
        return cleaned