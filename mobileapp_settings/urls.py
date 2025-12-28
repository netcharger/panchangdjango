from rest_framework.routers import DefaultRouter
from .views import CarouselImageViewSet, SiteSettingViewSet, VersionCheckViewSet

router = DefaultRouter()
router.register(r'carousel-images', CarouselImageViewSet)
router.register(r'site-settings', SiteSettingViewSet)
router.register(r'version-check', VersionCheckViewSet, basename='version-check')

urlpatterns = router.urls















