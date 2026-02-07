from django.contrib import admin
from .models import Department, Outcome, TaskLock, EmailLog

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('code', 'name')

@admin.register(Outcome)
class OutcomeAdmin(admin.ModelAdmin):
    list_display = ('code', 'name')


@admin.register(TaskLock)
class TaskLockAdmin(admin.ModelAdmin):
    list_display = ('task_name', 'locked_by', 'locked_at', 'expires_at')
    list_filter = ('task_name', 'locked_at')
    search_fields = ('task_name', 'locked_by')
    readonly_fields = ('locked_at',)
    
    def has_add_permission(self, request):
        # Prevent manual creation of locks via admin
        return False


@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = ('task_name', 'recipient', 'subject', 'sent_at', 'success', 'mou_link')
    list_filter = ('task_name', 'success', 'sent_at')
    search_fields = ('recipient', 'subject', 'error_message')
    readonly_fields = ('task_name', 'recipient', 'subject', 'sent_at', 'success', 'error_message', 'mou')
    date_hierarchy = 'sent_at'
    
    def has_add_permission(self, request):
        # Prevent manual creation of logs via admin
        return False
    
    def mou_link(self, obj):
        if obj.mou:
            from django.urls import reverse
            from django.utils.html import format_html
            url = reverse('admin:mou_mou_change', args=[obj.mou.id])
            return format_html('<a href="{}">{}</a>', url, obj.mou.title)
        return '-'
    mou_link.short_description = 'MOU'
