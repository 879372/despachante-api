from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ClientViewSet, ProcessViewSet, DashboardViewSet

router = DefaultRouter()
router.register(r'clients', ClientViewSet)
router.register(r'processes', ProcessViewSet)
router.register(r'dashboard', DashboardViewSet, basename='dashboard')

urlpatterns = [
    path('', include(router.urls)),
]
