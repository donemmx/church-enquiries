from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models import UserProfile
from enquiries.models import Ministry, Member, FollowUp, Event, PrayerRequest
from django.utils import timezone
from datetime import timedelta, date


class Command(BaseCommand):
    help = 'Create initial sample data for the church enquiries system'

    def handle(self, *args, **kwargs):
        # Create admin/head user
        if not User.objects.filter(username='admin').exists():
            admin_user = User.objects.create_superuser(
                username='admin',
                password='admin123',
                first_name='Pastor',
                last_name='Johnson',
                email='pastor@gracechapel.org'
            )
            UserProfile.objects.create(
                user=admin_user,
                role='head',
                phone='+234 800 000 0001',
                department='Enquiries Unit'
            )
            self.stdout.write(self.style.SUCCESS('Created admin user (admin/admin123)'))

        # Create assistant users
        assistants = [
            ('sister_grace', 'Grace', 'Okafor', 'grace@gracechapel.org'),
            ('brother_david', 'David', 'Adeyemi', 'david@gracechapel.org'),
        ]
        for username, first, last, email in assistants:
            if not User.objects.filter(username=username).exists():
                u = User.objects.create_user(
                    username=username, password='church123',
                    first_name=first, last_name=last, email=email
                )
                UserProfile.objects.create(user=u, role='assistant', department='Follow-up Team')
                self.stdout.write(self.style.SUCCESS(f'Created assistant: {username}/church123'))

        # Create ministries
        ministries_data = [
            ('Youth Ministry', 'Engaging and empowering the youth of our church'),
            ('Worship Team', 'Leading the congregation in worship and praise'),
            ('Evangelism', 'Reaching out to the community with the gospel'),
            ('Prayer Warriors', 'Dedicated intercessory prayer team'),
            ('Children\'s Church', 'Nurturing faith in children aged 0-12'),
            ('Women\'s Fellowship', 'Supporting and empowering women in the church'),
            ('Men\'s Fellowship', 'Brotherhood and accountability for men'),
            ('Hospitality', 'Welcoming visitors and managing church events'),
        ]
        for name, desc in ministries_data:
            Ministry.objects.get_or_create(name=name, defaults={'description': desc})
        self.stdout.write(self.style.SUCCESS(f'Created {len(ministries_data)} ministries'))

        # Create sample members
        members_data = [
            ('Adaeze', 'Okonkwo', 'adaeze@email.com', '+234 811 111 0001', 'new'),
            ('Chukwudi', 'Eze', 'chukwudi@email.com', '+234 811 111 0002', 'returning'),
            ('Blessing', 'Nwosu', 'blessing@email.com', '+234 811 111 0003', 'regular'),
            ('Emmanuel', 'Okeke', 'emma@email.com', '+234 811 111 0004', 'member'),
            ('Chioma', 'Ibe', 'chioma@email.com', '+234 811 111 0005', 'new'),
            ('Tunde', 'Fashola', 'tunde@email.com', '+234 811 111 0006', 'regular'),
        ]
        admin_user = User.objects.get(username='admin')
        assistant = User.objects.filter(username='sister_grace').first()

        for first, last, email, phone, status in members_data:
            member, created = Member.objects.get_or_create(
                email=email,
                defaults={
                    'first_name': first, 'last_name': last,
                    'phone': phone, 'status': status,
                    'first_visit_date': date.today() - timedelta(days=7),
                    'created_by': admin_user,
                    'assigned_to': assistant,
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created member: {first} {last}'))

        # Create sample events
        if not Event.objects.filter(title='Sunday Thanksgiving Service').exists():
            Event.objects.create(
                title='Sunday Thanksgiving Service',
                description='Join us for a special service of thanksgiving and worship.',
                event_type='service',
                start_date=timezone.now() + timedelta(days=3),
                end_date=timezone.now() + timedelta(days=3, hours=2),
                venue='Main Auditorium',
                organizer=admin_user,
                send_notifications=True
            )
            Event.objects.create(
                title='New Members Orientation',
                description='Welcome program for all new and returning visitors.',
                event_type='program',
                start_date=timezone.now() + timedelta(days=10),
                end_date=timezone.now() + timedelta(days=10, hours=3),
                venue='Conference Room A',
                organizer=admin_user,
                send_notifications=True,
                target_audience='New Visitors'
            )
            self.stdout.write(self.style.SUCCESS('Created sample events'))

        # Create sample follow-ups
        members = Member.objects.all()[:3]
        if assistant and not FollowUp.objects.filter(assigned_to=assistant).exists():
            for member in members:
                FollowUp.objects.create(
                    member=member,
                    assigned_to=assistant,
                    assigned_by=admin_user,
                    follow_up_type='call',
                    status='pending',
                    due_date=date.today() + timedelta(days=3),
                    priority=2,
                    notes=f'First contact with {member.get_full_name()}'
                )
            self.stdout.write(self.style.SUCCESS('Created sample follow-ups'))

        self.stdout.write(self.style.SUCCESS('\n✝ Initial data setup complete!'))
        self.stdout.write(self.style.WARNING('Login credentials:'))
        self.stdout.write('  Admin/Head: admin / admin123')
        self.stdout.write('  Assistant: sister_grace / church123')
        self.stdout.write('  Assistant: brother_david / church123')
