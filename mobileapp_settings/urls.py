from rest_framework.routers import DefaultRouter
from .views import CarouselImageViewSet, SiteSettingViewSet

router = DefaultRouter()
router.register(r'carousel-images', CarouselImageViewSet)
router.register(r'site-settings', SiteSettingViewSet)

urlpatterns = router.urls















