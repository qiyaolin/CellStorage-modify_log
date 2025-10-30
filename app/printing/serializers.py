from rest_framework import serializers
from django.contrib.auth.models import User
from .models import PrintJob, PrintJobHistory, PrintServer


class PrintJobSerializer(serializers.ModelSerializer):
    requested_by_username = serializers.CharField(source='requested_by.username', read_only=True)
    can_retry = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = PrintJob
        fields = [
            'id', 'label_data', 'status', 'priority',
            'requested_by', 'requested_by_username',
            'created_at', 'started_at', 'completed_at',
            'error_message', 'retry_count', 'max_retries', 'can_retry',
            'print_server_id'
        ]
        read_only_fields = [
            'id', 'status', 'created_at', 'started_at', 'completed_at',
            'error_message', 'retry_count', 'print_server_id'
        ]

    def validate_label_data(self, value):
        """Validate that label_data contains required fields"""
        required_fields = ['itemName', 'barcode']
        for field in required_fields:
            if field not in value:
                raise serializers.ValidationError(f"Missing required field: {field}")
        return value


class PrintJobCreateSerializer(serializers.ModelSerializer):
    """Simplified serializer for creating print jobs"""
    
    class Meta:
        model = PrintJob
        fields = ['label_data', 'priority']

    def validate_label_data(self, value):
        """Validate that label_data contains required fields"""
        required_fields = ['itemName', 'barcode']
        for field in required_fields:
            if field not in value:
                raise serializers.ValidationError(f"Missing required field: {field}")
        return value

    def create(self, validated_data):
        # Set the requesting user from the request context
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['requested_by'] = request.user
        return super().create(validated_data)


class PrintJobStatusUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating print job status (used by print server)"""
    
    class Meta:
        model = PrintJob
        fields = ['status', 'error_message', 'print_server_id']

    def validate_status(self, value):
        """Validate status transitions"""
        if self.instance:
            current_status = self.instance.status
            valid_transitions = {
                'pending': ['processing', 'failed'],
                'processing': ['completed', 'failed'],
                'failed': ['processing'],  # Allow retry
                'completed': []  # No transitions from completed
            }
            
            if value not in valid_transitions.get(current_status, []):
                raise serializers.ValidationError(
                    f"Invalid status transition from {current_status} to {value}"
                )
        return value


class PrintJobHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PrintJobHistory
        fields = ['id', 'status_from', 'status_to', 'changed_at', 'notes']


class PrintServerSerializer(serializers.ModelSerializer):
    is_online = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = PrintServer
        fields = [
            'id', 'server_id', 'name', 'location', 'is_active',
            'last_heartbeat', 'printer_name', 'printer_status',
            'total_jobs_processed', 'jobs_completed_today',
            'is_online', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'total_jobs_processed', 'jobs_completed_today',
            'created_at', 'updated_at'
        ]


class PrintServerHeartbeatSerializer(serializers.ModelSerializer):
    """Serializer for print server heartbeat updates"""
    
    class Meta:
        model = PrintServer
        fields = ['printer_name', 'printer_status', 'jobs_completed_today']