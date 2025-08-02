from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'jobs', views.PrintJobViewSet)
router.register(r'history', views.PrintJobHistoryViewSet, basename='printjobhistory')
router.register(r'servers', views.PrintServerViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
    
    # Convenience endpoints
    path('api/queue-job/', views.PrintJobViewSet.as_view({'post': 'create'}), name='queue-print-job'),
    path('api/fetch-pending-job/', views.PrintJobViewSet.as_view({'get': 'fetch_pending_job'}), name='fetch-pending-job'),
    path('api/stats/', views.PrintJobViewSet.as_view({'get': 'stats'}), name='print-stats'),
]