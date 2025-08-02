from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class PrintJob(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    # Core job information
    label_data = models.JSONField(help_text="All data required for printing the label")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    
    # User tracking
    requested_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Error handling
    error_message = models.TextField(blank=True, null=True)
    retry_count = models.PositiveIntegerField(default=0)
    max_retries = models.PositiveIntegerField(default=3)
    
    # Print server information
    print_server_id = models.CharField(max_length=100, blank=True, null=True, 
                                      help_text="ID of the print server that processed this job")

    class Meta:
        ordering = ['-priority', 'created_at']
        indexes = [
            models.Index(fields=['status', 'priority', 'created_at']),
            models.Index(fields=['requested_by', 'created_at']),
        ]

    def __str__(self):
        return f"Print Job {self.id} - {self.status} ({self.priority})"

    @property
    def can_retry(self):
        """Check if this job can be retried"""
        return self.status == 'failed' and self.retry_count < self.max_retries

    def mark_processing(self, print_server_id=None):
        """Mark job as processing"""
        self.status = 'processing'
        self.started_at = timezone.now()
        if print_server_id:
            self.print_server_id = print_server_id
        self.save(update_fields=['status', 'started_at', 'print_server_id'])

    def mark_completed(self):
        """Mark job as completed"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'completed_at'])

    def mark_failed(self, error_message=None):
        """Mark job as failed and increment retry count"""
        self.status = 'failed'
        self.retry_count += 1
        if error_message:
            self.error_message = error_message
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'retry_count', 'error_message', 'completed_at'])


class PrintJobHistory(models.Model):
    """Track status changes for audit purposes"""
    
    print_job = models.ForeignKey(PrintJob, on_delete=models.CASCADE, related_name='history')
    status_from = models.CharField(max_length=20)
    status_to = models.CharField(max_length=20)
    changed_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-changed_at']
        verbose_name_plural = "Print job histories"

    def __str__(self):
        return f"Job {self.print_job.id}: {self.status_from} → {self.status_to}"


class PrintServer(models.Model):
    """Track print server instances"""
    
    server_id = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=200)
    location = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)
    last_heartbeat = models.DateTimeField(null=True, blank=True)
    
    # Printer information
    printer_name = models.CharField(max_length=200, blank=True)
    printer_status = models.CharField(max_length=100, blank=True)
    
    # Performance tracking
    total_jobs_processed = models.PositiveIntegerField(default=0)
    jobs_completed_today = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.server_id})"

    @property
    def is_online(self):
        """Check if server is online based on last heartbeat"""
        if not self.last_heartbeat:
            return False
        from django.utils import timezone
        import datetime
        return timezone.now() - self.last_heartbeat < datetime.timedelta(minutes=5)