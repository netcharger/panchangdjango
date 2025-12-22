"""
URL configuration for panchang app
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FestivalViewSet, ImportantDayViewSet, PanchangAPIView, AmavasyaAPIView

router = DefaultRouter()
router.register(r'festivals', FestivalViewSet, basename='festival')
router.register(r'important-days', ImportantDayViewSet, basename='importantday')

urlpatterns = [
    path('', include(router.urls)),
    path('panchang/', PanchangAPIView.as_view(), name='panchang'),  # GET endpoint: ?date=YYYY-MM-DD&language=en
    path('panchang/today/', PanchangAPIView.as_view(), name='panchang-today'),  # GET endpoint for today's panchang
    path('panchang/calculate/', PanchangAPIView.as_view(), name='panchang-calculate'),  # POST endpoint
    path('panchang/amavasya/', AmavasyaAPIView.as_view(), name='amavasya-list'),
]

