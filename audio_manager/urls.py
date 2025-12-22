from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, AudioFileViewSet

router = DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'audio-files', AudioFileViewSet)

urlpatterns = router.urls



