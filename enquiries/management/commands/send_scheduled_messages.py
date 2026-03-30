# enquiries/management/commands/send_scheduled_messages.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from enquiries.models import Message, Member
from enquiries.views import send_sms
from django.core.mail import send_mail
from django.conf import settings

class Command(BaseCommand):
    help = "Send scheduled messages that are due"

    def handle(self, *args, **kwargs):
        now = timezone.now()
        messages_to_send = Message.objects.filter(status='scheduled', scheduled_at__lte=now)

        for msg in messages_to_send:
            members = Member.objects.filter(is_active=True) if msg.send_to_all else msg.recipients.all()
            total_sent = 0

            for member in members:
                if msg.message_type in ["email", "both"] and member.email:
                    send_mail(
                        msg.title,
                        msg.body,
                        settings.DEFAULT_FROM_EMAIL,
                        [member.email],
                        fail_silently=False,
                    )
                if msg.message_type in ["sms", "both"] and member.phone:
                    send_sms(member.phone, msg.body)
                total_sent += 1

            msg.total_sent = total_sent
            msg.status = 'sent'
            msg.sent_at = now
            msg.save()

        self.stdout.write(self.style.SUCCESS(f'Sent {messages_to_send.count()} scheduled messages'))