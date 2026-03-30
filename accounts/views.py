# accounts/views.py  — full replacement

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from .models import UserProfile
from .forms import LoginForm, ProfileForm, StaffCreateForm, StaffEditForm, ResetPasswordForm


# ─────────────────────────────────────────────
#  SHARED HELPER  (import this in enquiries/views.py too)
# ─────────────────────────────────────────────

def get_profile(user):
    """Always returns a UserProfile, creating one if needed."""
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile


def get_section(user):
    """Returns the user's section string, e.g. 'greeters' / 'followup' / 'all'."""
    return get_profile(user).section


def can_see_all(user):
    """True only for Django superusers or role=admin + section=all."""
    if user.is_superuser:
        return True
    profile = get_profile(user)
    return profile.role == 'admin' and profile.section == 'all'


def is_section_admin(user):
    """True for section_admin and above within their section."""
    if user.is_superuser:
        return True
    return get_profile(user).role in ('admin', 'section_admin')


def section_staff_qs(user):
    """
    Returns a queryset of User objects who are in the same section as `user`.
    Superusers / all-section admins get all active users.
    """
    if can_see_all(user):
        return User.objects.filter(is_active=True)
    section = get_section(user)
    return User.objects.filter(
        is_active=True,
        profile__section__in=[section, 'all']
    )


# ─────────────────────────────────────────────
#  AUTH
# ─────────────────────────────────────────────

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(
                request,
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password'],
            )
            if user:
                login(request, user)
                UserProfile.objects.get_or_create(user=user)
                return redirect(request.GET.get('next', 'member_list'))
            messages.error(request, 'Invalid username or password.')
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


# ─────────────────────────────────────────────
#  PROFILE
# ─────────────────────────────────────────────

@login_required
def profile_view(request):
    profile = get_profile(request.user)
    if request.method == 'POST':
        request.user.first_name = request.POST.get('first_name', '')
        request.user.last_name  = request.POST.get('last_name', '')
        request.user.email      = request.POST.get('email', '')
        request.user.save()
        profile.phone = request.POST.get('phone', '')
        profile.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('profile')
    return render(request, 'accounts/profile.html', {'profile': profile})


# ─────────────────────────────────────────────
#  STAFF MANAGEMENT
# ─────────────────────────────────────────────

@login_required
def staff_list(request):
    if not is_section_admin(request.user):
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    # Each admin only sees staff in their own section
    if can_see_all(request.user):
        staff = User.objects.select_related('profile').order_by('first_name')
    else:
        section = get_section(request.user)
        staff = User.objects.filter(
            profile__section__in=[section, 'all']
        ).select_related('profile').order_by('first_name')

    return render(request, 'admin_panel/staff.html', {'staff': staff})


@login_required
def staff_create(request):
    if not is_section_admin(request.user):
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    if request.method == 'POST':
        form = StaffCreateForm(request.POST)

        # Non-superusers can only create staff within their own section
        if form.is_valid():
            if not can_see_all(request.user):
                # Force the section to match the creator's section
                form_section = form.cleaned_data.get('section')
                my_section   = get_section(request.user)
                if form_section != my_section:
                    form.add_error('section', 'You can only create staff in your own section.')

            # Also prevent section_admins from creating global admins
            if not can_see_all(request.user):
                if form.cleaned_data.get('role') == 'admin':
                    form.add_error('role', 'Only the superuser can create global administrators.')

            if form.is_valid():  # re-check after possible added errors
                user = form.save()
                messages.success(request, f'"{user.get_full_name()}" created. Username: {user.username}')
                return redirect('admin_staff')
    else:
        form = StaffCreateForm()

        # Pre-lock section for non-superusers
        if not can_see_all(request.user):
            form.fields['section'].initial  = get_section(request.user)
            form.fields['section'].disabled = True
            # Hide the global admin role option for section admins
            form.fields['role'].choices = [
                c for c in UserProfile.ROLE_CHOICES if c[0] != 'admin'
            ]

    return render(request, 'accounts/staff_form.html', {'form': form})


@login_required
def staff_edit(request, pk):
    if not is_section_admin(request.user):
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    staff_user = get_object_or_404(User, pk=pk)
    profile, _ = UserProfile.objects.get_or_create(user=staff_user)

    # Section admins cannot edit staff from other sections
    if not can_see_all(request.user) and profile.section != get_section(request.user):
        messages.error(request, 'You cannot edit staff from another section.')
        return redirect('admin_staff')

    if request.method == 'POST':
        form = StaffEditForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data

            # Prevent section_admin from moving a user to another section
            new_section = d.get('section', profile.section)
            if not can_see_all(request.user):
                new_section = get_section(request.user)   # force own section

            staff_user.first_name = d['first_name']
            staff_user.last_name  = d['last_name']
            staff_user.email      = d.get('email', '')
            staff_user.is_active  = d.get('is_active', True)
            staff_user.save()

            profile.role       = d['role'] if can_see_all(request.user) else d['role']
            profile.section    = new_section
            profile.phone      = d.get('phone', '')
            profile.department = d.get('department', '')
            profile.bio        = d.get('bio', '')
            profile.save()

            messages.success(request, f'{staff_user.get_full_name()} updated successfully!')
            return redirect('admin_staff')
    else:
        form = StaffEditForm(initial={
            'first_name': staff_user.first_name,
            'last_name':  staff_user.last_name,
            'email':      staff_user.email,
            'phone':      profile.phone,
            'role':       profile.role,
            'section':    profile.section,
            'department': profile.department,
            'bio':        profile.bio,
            'is_active':  staff_user.is_active,
        })

        # Lock section for section admins
        if not can_see_all(request.user):
            form.fields['section'].disabled = True
            form.fields['role'].choices = [
                c for c in UserProfile.ROLE_CHOICES if c[0] != 'admin'
            ]

    return render(request, 'accounts/staff_edit.html', {
        'staff_user': staff_user,
        'profile':    profile,
        'form':       form,
    })


@login_required
def staff_reset_password(request, pk):
    if not is_section_admin(request.user):
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    staff_user = get_object_or_404(User, pk=pk)
    profile    = get_profile(staff_user)

    # Section admins can only reset passwords for their own section
    if not can_see_all(request.user) and profile.section != get_section(request.user):
        messages.error(request, 'Access denied.')
        return redirect('admin_staff')

    if request.method == 'POST':
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            staff_user.set_password(form.cleaned_data['new_password1'])
            staff_user.save()
            messages.success(request, f'Password for {staff_user.get_full_name()} has been reset.')
            return redirect('admin_staff')
    else:
        form = ResetPasswordForm()

    return render(request, 'accounts/reset_password.html', {
        'form': form,
        'staff_user': staff_user,
    })


@login_required
def staff_deactivate(request, pk):
    if not is_section_admin(request.user):
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    staff_user = get_object_or_404(User, pk=pk)
    profile    = get_profile(staff_user)

    if not can_see_all(request.user) and profile.section != get_section(request.user):
        messages.error(request, 'Access denied.')
        return redirect('admin_staff')

    if request.method == 'POST':
        if staff_user == request.user:
            messages.error(request, 'You cannot deactivate your own account.')
            return redirect('admin_staff')
        staff_user.is_active = not staff_user.is_active
        staff_user.save()
        status = 'activated' if staff_user.is_active else 'deactivated'
        messages.success(request, f'{staff_user.get_full_name()} has been {status}.')
        return redirect('admin_staff')

    return render(request, 'accounts/confirm_deactivate.html', {'staff_user': staff_user})