"""
Django management command to send monthly MOU reminder emails.
Protected against multiple workers using database locking.

Usage:
    python manage.py send_monthly_mou_emails
    
Schedule with cron (Linux/Mac):
    0 9 1 * * cd /path/to/project && /path/to/venv/bin/python manage.py send_monthly_mou_emails
    
Schedule with Task Scheduler (Windows):
    Create a scheduled task that runs monthly on the 1st at 9:00 AM
"""
from django.core.management.base import BaseCommand
from django.core.mail import send_mail, EmailMessage
from django.conf import settings
from django.utils import timezone
from django.db import transaction, IntegrityError
from mou.models import MOU, TaskLock, EmailLog
import socket
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Send monthly reminder emails for all active MOUs'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force execution even if lock exists (use with caution)',
        )
        parser.add_argument(
            '--lock-timeout',
            type=int,
            default=30,
            help='Lock timeout in minutes (default: 30)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simulate email sending without actually sending',
        )

    def handle(self, *args, **options):
        task_name = 'send_monthly_mou_emails'
        force = options['force']
        lock_timeout_minutes = options['lock_timeout']
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No emails will be sent'))
        
        # Try to acquire lock
        lock_acquired = self._acquire_lock(task_name, lock_timeout_minutes, force)
        
        if not lock_acquired:
            self.stdout.write(
                self.style.WARNING(
                    f'Task "{task_name}" is already running or locked. Skipping execution.'
                )
            )
            return
        
        try:
            self.stdout.write(f'Starting monthly MOU email task...')
            
            # Get active MOUs
            today = timezone.now().date()
            active_mous = MOU.objects.filter(
                end_date__gte=today
            ).prefetch_related('department', 'outcome', 'events')
            
            total_mous = active_mous.count()
            self.stdout.write(f'Found {total_mous} active MOUs')
            
            emails_sent = 0
            emails_failed = 0
            
            for mou in active_mous:
                try:
                    result = self._send_mou_email(mou, dry_run)
                    if result:
                        emails_sent += 1
                        self.stdout.write(
                            self.style.SUCCESS(f'✓ Sent email for MOU: {mou.title}')
                        )
                    else:
                        emails_failed += 1
                        self.stdout.write(
                            self.style.ERROR(f'✗ Failed to send email for MOU: {mou.title}')
                        )
                except Exception as e:
                    emails_failed += 1
                    logger.exception(f'Error sending email for MOU {mou.id}: {e}')
                    self.stdout.write(
                        self.style.ERROR(f'✗ Exception for MOU {mou.title}: {str(e)}')
                    )
            
            # Summary
            self.stdout.write(self.style.SUCCESS('\n' + '='*60))
            self.stdout.write(self.style.SUCCESS(f'Monthly MOU Email Summary:'))
            self.stdout.write(f'Total Active MOUs: {total_mous}')
            self.stdout.write(self.style.SUCCESS(f'Emails Sent: {emails_sent}'))
            if emails_failed > 0:
                self.stdout.write(self.style.ERROR(f'Emails Failed: {emails_failed}'))
            self.stdout.write(self.style.SUCCESS('='*60))
            
        finally:
            # Always release the lock
            self._release_lock(task_name)
            self.stdout.write('Lock released')

    def _acquire_lock(self, task_name, timeout_minutes, force=False):
        """
        Acquire a distributed lock using database.
        Returns True if lock acquired, False otherwise.
        """
        hostname = socket.gethostname()
        now = timezone.now()
        expires_at = now + timedelta(minutes=timeout_minutes)
        
        if force:
            # Force mode: delete existing lock
            TaskLock.objects.filter(task_name=task_name).delete()
            self.stdout.write(self.style.WARNING('Force mode: Existing lock removed'))
        
        # Clean up expired locks
        TaskLock.objects.filter(expires_at__lt=now).delete()
        
        # Try to create a new lock
        try:
            with transaction.atomic():
                lock = TaskLock.objects.create(
                    task_name=task_name,
                    locked_by=hostname,
                    expires_at=expires_at
                )
                self.stdout.write(
                    self.style.SUCCESS(f'Lock acquired by {hostname} (expires in {timeout_minutes} min)')
                )
                return True
        except IntegrityError:
            # Lock already exists and is not expired
            existing_lock = TaskLock.objects.filter(task_name=task_name).first()
            if existing_lock:
                self.stdout.write(
                    self.style.WARNING(
                        f'Lock held by {existing_lock.locked_by} since {existing_lock.locked_at}'
                    )
                )
            return False

    def _release_lock(self, task_name):
        """Release the lock for this task."""
        TaskLock.objects.filter(task_name=task_name).delete()

    def _send_mou_email(self, mou, dry_run=False):
        """
        Send email for a specific MOU.
        Returns True if successful, False otherwise.
        """
        # Collect recipients
        recipients = []
        if mou.mou_coordinator_email:
            recipients.append(mou.mou_coordinator_email)
        if mou.staff_coordinator_email and mou.staff_coordinator_email not in recipients:
            recipients.append(mou.staff_coordinator_email)
        
        if not recipients:
            self.stdout.write(
                self.style.WARNING(f'  No email addresses for MOU: {mou.title}')
            )
            return False
        
        # Prepare email content
        subject = f'Monthly MOU Update: {mou.title}'
        
        # Get event statistics
        total_events = mou.events.count()
        completed_events = mou.events.filter(status='Completed').count()
        pending_events = mou.events.filter(status='Pending').count()
        
        # Calculate days until expiry
        days_until_expiry = (mou.end_date - timezone.now().date()).days
        
        # Build email message
        message_lines = [
            f'Dear {mou.mou_coordinator_name or "Coordinator"},',
            '',
            f'This is your monthly update for the MOU: {mou.title}',
            '',
            'MOU Details:',
            f'  Organization: {mou.organization_name or "N/A"}',
            f'  Status: {mou.status.upper()}',
            f'  Valid Until: {mou.end_date}',
            f'  Days Remaining: {days_until_expiry} days',
            '',
            'Event Summary:',
            f'  Total Events: {total_events}',
            f'  Completed: {completed_events}',
            f'  Pending: {pending_events}',
            '',
        ]
        
        # Add warning if expiring soon
        if days_until_expiry <= 30:
            message_lines.extend([
                '⚠️ WARNING: This MOU will expire in less than 30 days!',
                'Please take necessary action to renew if needed.',
                '',
            ])
        
        # List pending events
        if pending_events > 0:
            message_lines.append('Pending Events:')
            for event in mou.events.filter(status='Pending')[:5]:  # Limit to 5
                message_lines.append(f'  - {event.title} (Due: {event.date})')
            if pending_events > 5:
                message_lines.append(f'  ... and {pending_events - 5} more')
            message_lines.append('')
        
        message_lines.extend([
            'For more details, please log in to the MOU Management System.',
            '',
            'Best regards,',
            'MOU Management System',
        ])
        
        message = '\n'.join(message_lines)
        
        # Send email
        if dry_run:
            self.stdout.write(f'  [DRY RUN] Would send to: {", ".join(recipients)}')
            self.stdout.write(f'  Subject: {subject}')
            return True
        
        try:
            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None) or getattr(settings, 'EMAIL_HOST_USER', None)
            
            email = EmailMessage(
                subject=subject,
                body=message,
                from_email=from_email,
                to=recipients,
            )
            email.send(fail_silently=False)
            
            # Log successful email
            for recipient in recipients:
                EmailLog.objects.create(
                    task_name='send_monthly_mou_emails',
                    recipient=recipient,
                    subject=subject,
                    success=True,
                    mou=mou
                )
            
            return True
            
        except Exception as e:
            logger.exception(f'Failed to send email for MOU {mou.id}')
            
            # Log failed email
            for recipient in recipients:
                EmailLog.objects.create(
                    task_name='send_monthly_mou_emails',
                    recipient=recipient,
                    subject=subject,
                    success=False,
                    error_message=str(e),
                    mou=mou
                )
            
            return False
