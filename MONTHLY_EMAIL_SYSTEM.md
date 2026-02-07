# Monthly MOU Email System - Django

## Overview

This system sends automated monthly reminder emails for all active MOUs. It includes:

- **Database-based locking** to prevent duplicate execution across multiple workers
- **No Redis or Celery required** - uses PostgreSQL/MySQL database locking
- **Email logging** for tracking and debugging
- **Safe for production** with multiple workers/servers

## Components

### 1. Models

**TaskLock Model** (`mou/models.py`)
- Provides distributed locking mechanism
- Prevents duplicate task execution across workers
- Automatically expires locks
- Uses database unique constraint for atomicity

**EmailLog Model** (`mou/models.py`)
- Logs all email attempts (success and failures)
- Tracks which MOUs were notified
- Useful for debugging and auditing

### 2. Management Command

**send_monthly_mou_emails** (`mou/management/commands/send_monthly_mou_emails.py`)

Features:
- Sends emails to MOU coordinators and staff coordinators
- Includes MOU status, event summary, and expiry warnings
- Protected by database lock (safe with multiple workers)
- Configurable lock timeout
- Dry-run mode for testing
- Force mode to override stuck locks

## Setup

### 1. Create Database Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 2. Test the Command

```bash
# Dry run (no emails sent)
python manage.py send_monthly_mou_emails --dry-run

# Send actual emails
python manage.py send_monthly_mou_emails

# Custom lock timeout (default is 30 minutes)
python manage.py send_monthly_mou_emails --lock-timeout 60

# Force execution (ignore existing lock - use with caution)
python manage.py send_monthly_mou_emails --force
```

### 3. Configure Email Settings

Ensure your `settings.py` has email configuration:

```python
# Example with Gmail
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
DEFAULT_FROM_EMAIL = 'your-email@gmail.com'

# Or for development (console backend)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

## Scheduling

### Option 1: Linux/Mac with Cron

Edit crontab:
```bash
crontab -e
```

Add line to run on 1st of every month at 9:00 AM:
```cron
0 9 1 * * cd /path/to/project && /path/to/venv/bin/python manage.py send_monthly_mou_emails >> /var/log/mou_emails.log 2>&1
```

Or using a shell script:

Create `scripts/send_monthly_emails.sh`:
```bash
#!/bin/bash
cd /path/to/project
source venv/bin/activate
python manage.py send_monthly_mou_emails
```

Make executable and add to cron:
```bash
chmod +x scripts/send_monthly_emails.sh
```

Crontab entry:
```cron
0 9 1 * * /path/to/project/scripts/send_monthly_emails.sh >> /var/log/mou_emails.log 2>&1
```

### Option 2: Windows Task Scheduler

**Method 1: Using Task Scheduler GUI**

1. Open Task Scheduler
2. Click "Create Basic Task"
3. Name: "Monthly MOU Emails"
4. Trigger: Monthly, 1st day, 9:00 AM
5. Action: Start a program
   - Program: `C:\path\to\venv\Scripts\python.exe`
   - Arguments: `manage.py send_monthly_mou_emails`
   - Start in: `C:\path\to\project`

**Method 2: Using PowerShell Script**

Create `scripts/send_monthly_emails.ps1`:
```powershell
$ErrorActionPreference = "Stop"
cd C:\path\to\project
& C:\path\to\venv\Scripts\python.exe manage.py send_monthly_mou_emails
```

Create scheduled task via PowerShell:
```powershell
$action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument '-File C:\path\to\project\scripts\send_monthly_emails.ps1'
$trigger = New-ScheduledTaskTrigger -Monthly -DaysOfMonth 1 -At 9am
$settings = New-ScheduledTaskSettingsSet -RunOnlyIfNetworkAvailable
Register-ScheduledTask -TaskName "Monthly MOU Emails" -Action $action -Trigger $trigger -Settings $settings
```

**Method 3: Using schtasks Command**

```cmd
schtasks /create /tn "Monthly MOU Emails" /tr "C:\path\to\venv\Scripts\python.exe C:\path\to\project\manage.py send_monthly_mou_emails" /sc monthly /d 1 /st 09:00
```

### Option 3: systemd Timer (Linux)

Create `/etc/systemd/system/mou-monthly-email.service`:
```ini
[Unit]
Description=Send Monthly MOU Emails
After=network.target

[Service]
Type=oneshot
User=www-data
WorkingDirectory=/path/to/project
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/python manage.py send_monthly_mou_emails
```

Create `/etc/systemd/system/mou-monthly-email.timer`:
```ini
[Unit]
Description=Monthly MOU Email Timer
Requires=mou-monthly-email.service

[Timer]
OnCalendar=monthly
Persistent=true

[Install]
WantedBy=timers.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable mou-monthly-email.timer
sudo systemctl start mou-monthly-email.timer

# Check status
sudo systemctl status mou-monthly-email.timer
sudo systemctl list-timers
```

## Production Deployment with Multiple Workers

### How It Works

1. **Database Locking**: Uses a unique constraint on `task_name` in `TaskLock` table
2. **Atomic Operations**: Uses `transaction.atomic()` to ensure only one worker acquires lock
3. **Auto-Expiry**: Locks automatically expire after timeout (default 30 minutes)
4. **Cleanup**: Expired locks are automatically cleaned before each run

### Example: Multiple Gunicorn Workers

Your application can have multiple workers:

```bash
# gunicorn with 4 workers
gunicorn mou_manager.wsgi:application --workers 4 --bind 0.0.0.0:8000
```

Even if all 4 workers try to run the command simultaneously (e.g., via cron), only ONE will execute:

```bash
# This is safe - only one will actually run
0 9 1 * * cd /app && python manage.py send_monthly_mou_emails
```

### What Happens in Production?

**Scenario: 3 servers running the app, each with 4 workers**

1. Cron triggers on all 3 servers at 9:00 AM
2. Total of 12 workers try to acquire lock
3. **Only 1 worker** acquires the lock (database constraint)
4. Other 11 workers see lock exists and exit immediately
5. The winning worker sends all emails
6. Lock is released when done

### Monitoring

**Check Active Locks** (Django shell or admin):
```python
from mou.models import TaskLock
TaskLock.objects.all()
```

**Check Email Logs**:
```python
from mou.models import EmailLog
from django.utils import timezone
from datetime import timedelta

# Last 24 hours
recent = timezone.now() - timedelta(hours=24)
EmailLog.objects.filter(sent_at__gte=recent)

# Failed emails
EmailLog.objects.filter(success=False)

# By task
EmailLog.objects.filter(task_name='send_monthly_mou_emails')
```

**Via Admin**: Visit `/admin/mou/emaillog/` to see all email logs with filtering

### Troubleshooting

**Lock is stuck**:
```bash
# Force mode (removes existing lock)
python manage.py send_monthly_mou_emails --force
```

**Or manually via Django shell**:
```python
from mou.models import TaskLock
TaskLock.objects.filter(task_name='send_monthly_mou_emails').delete()
```

**Test without sending emails**:
```bash
python manage.py send_monthly_mou_emails --dry-run
```

**Check what would be sent**:
```python
from mou.models import MOU
from django.utils import timezone

# Active MOUs that would receive emails
active = MOU.objects.filter(end_date__gte=timezone.now().date())
for mou in active:
    print(f"{mou.title}: {mou.mou_coordinator_email}, {mou.staff_coordinator_email}")
```

## Email Content

Each email includes:
- MOU title and organization
- Status and expiry date
- Days until expiration
- Event summary (total, completed, pending)
- Warning if expiring within 30 days
- List of pending events

## Advanced Features

### Custom Lock Timeout

For tasks that might take longer:
```bash
python manage.py send_monthly_mou_emails --lock-timeout 120  # 2 hours
```

### Add More Email Tasks

You can create additional commands following the same pattern:

1. Create new command file in `mou/management/commands/`
2. Use `TaskLock` with a unique task name
3. Implement the same locking pattern

Example task names:
- `send_monthly_mou_emails` (already implemented)
- `send_expiry_warnings` (for MOUs expiring soon)
- `send_weekly_summary` (weekly digest)

## Performance

- **Lock acquisition**: Single database query (< 10ms)
- **Lock check**: If locked, exits immediately (< 10ms)
- **Email sending**: Depends on number of MOUs and email server
- **Recommended**: Run during low-traffic hours (e.g., early morning)

## Security

- Email logs are readonly in admin (prevents tampering)
- Locks cannot be created manually via admin
- All operations logged for auditing
- Failed email attempts logged with error messages

## Testing Checklist

- [ ] Migrations applied successfully
- [ ] Dry-run executes without errors
- [ ] Test email sends successfully
- [ ] Lock prevents duplicate execution
- [ ] Lock expires after timeout
- [ ] Email logs appear in admin
- [ ] Cron/scheduler job configured
- [ ] Email settings configured correctly
- [ ] Force mode works when needed

## FAQ

**Q: What if the server crashes during execution?**
A: Lock will automatically expire after the timeout period (default 30 minutes).

**Q: Can I run this manually while scheduled task is running?**
A: No, the lock will prevent duplicate execution. Use `--force` if absolutely necessary.

**Q: How do I change the email schedule?**
A: Modify your cron expression or Windows Task Scheduler settings.

**Q: What if I have thousands of MOUs?**
A: Consider batching emails or increasing the lock timeout. Monitor execution time and adjust accordingly.

**Q: Can I use this with Celery later?**
A: Yes! The same locking mechanism works with Celery. Just call the command from a Celery task.

## Next Steps

1. Apply migrations: `python manage.py migrate`
2. Test with dry-run: `python manage.py send_monthly_mou_emails --dry-run`
3. Send test email: `python manage.py send_monthly_mou_emails`
4. Set up scheduling (cron or Task Scheduler)
5. Monitor email logs in admin panel
