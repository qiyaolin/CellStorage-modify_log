from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q, F
from django.db import transaction
from .models import PrintJob, PrintJobHistory, PrintServer
from .serializers import (
    PrintJobSerializer, PrintJobCreateSerializer, PrintJobStatusUpdateSerializer,
    PrintJobHistorySerializer, PrintServerSerializer, PrintServerHeartbeatSerializer
)


class PrintJobViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing print jobs
    """
    queryset = PrintJob.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return PrintJobCreateSerializer
        elif self.action == 'update_status':
            return PrintJobStatusUpdateSerializer
        return PrintJobSerializer

    def get_queryset(self):
        queryset = PrintJob.objects.all()
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by user (for regular users, only show their jobs)
        if not self.request.user.is_staff:
            queryset = queryset.filter(requested_by=self.request.user)
        
        return queryset

    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny])
    def fetch_pending_job(self, request):
        """
        Endpoint for print server to fetch the next pending job
        Returns the highest priority pending job
        """
        print_server_id = request.query_params.get('server_id')
        
        # Get the next pending job with highest priority
        with transaction.atomic():
            job = PrintJob.objects.filter(
                Q(status='pending') | Q(status='failed', retry_count__lt=F('max_retries'))
            ).order_by('-priority', 'created_at').first()
            
            if job:
                # Mark as processing
                old_status = job.status
                job.mark_processing(print_server_id)
                
                # Create history record
                PrintJobHistory.objects.create(
                    print_job=job,
                    status_from=old_status,
                    status_to='processing',
                    notes=f"Picked up by print server: {print_server_id}"
                )
                
                serializer = PrintJobSerializer(job)
                return Response(serializer.data)
            else:
                return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """
        Endpoint for print server to update job status
        """
        job = self.get_object()
        old_status = job.status
        
        serializer = PrintJobStatusUpdateSerializer(job, data=request.data, partial=True)
        if serializer.is_valid():
            with transaction.atomic():
                # Update the job
                if 'status' in serializer.validated_data:
                    new_status = serializer.validated_data['status']
                    if new_status == 'completed':
                        job.mark_completed()
                    elif new_status == 'failed':
                        error_message = serializer.validated_data.get('error_message')
                        job.mark_failed(error_message)
                    else:
                        serializer.save()
                else:
                    serializer.save()
                
                # Create history record
                PrintJobHistory.objects.create(
                    print_job=job,
                    status_from=old_status,
                    status_to=job.status,
                    notes=request.data.get('notes', '')
                )
                
                # Update print server stats if completed
                if job.status == 'completed' and job.print_server_id:
                    try:
                        server = PrintServer.objects.get(server_id=job.print_server_id)
                        server.total_jobs_processed += 1
                        server.jobs_completed_today += 1
                        server.save(update_fields=['total_jobs_processed', 'jobs_completed_today'])
                    except PrintServer.DoesNotExist:
                        pass
            
            return Response(PrintJobSerializer(job).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def retry(self, request, pk=None):
        """
        Retry a failed print job
        """
        job = self.get_object()
        
        if not job.can_retry:
            return Response(
                {'error': 'Job cannot be retried'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        old_status = job.status
        job.status = 'pending'
        job.error_message = None
        job.save(update_fields=['status', 'error_message'])
        
        # Create history record
        PrintJobHistory.objects.create(
            print_job=job,
            status_from=old_status,
            status_to='pending',
            notes=f"Retried by user: {request.user.username}"
        )
        
        return Response(PrintJobSerializer(job).data)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Get printing statistics
        """
        queryset = self.get_queryset()
        
        stats = {
            'total_jobs': queryset.count(),
            'pending_jobs': queryset.filter(status='pending').count(),
            'processing_jobs': queryset.filter(status='processing').count(),
            'completed_jobs': queryset.filter(status='completed').count(),
            'failed_jobs': queryset.filter(status='failed').count(),
        }
        
        # Add user-specific stats if not staff
        if not request.user.is_staff:
            stats['user_jobs'] = queryset.filter(requested_by=request.user).count()
        
        return Response(stats)


class PrintJobHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing print job history
    """
    serializer_class = PrintJobHistorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        print_job_id = self.request.query_params.get('job_id')
        if print_job_id:
            return PrintJobHistory.objects.filter(print_job_id=print_job_id)
        return PrintJobHistory.objects.all()


class PrintServerViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing print servers
    """
    queryset = PrintServer.objects.all()
    serializer_class = PrintServerSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['post'], permission_classes=[permissions.AllowAny])
    def heartbeat(self, request, pk=None):
        """
        Print server heartbeat endpoint
        """
        server = self.get_object()
        
        # Update last heartbeat
        server.last_heartbeat = timezone.now()
        
        # Update other fields if provided
        serializer = PrintServerHeartbeatSerializer(server, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(last_heartbeat=timezone.now())
            return Response({'status': 'heartbeat received'})
        
        server.save(update_fields=['last_heartbeat'])
        return Response({'status': 'heartbeat received'})

    @action(detail=False, methods=['get'])
    def online_servers(self, request):
        """
        Get list of online print servers
        """
        servers = PrintServer.objects.filter(is_active=True)
        online_servers = [server for server in servers if server.is_online]
        
        serializer = PrintServerSerializer(online_servers, many=True)
        return Response(serializer.data)