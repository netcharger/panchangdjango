from rest_framework.routers import DefaultRouter
from django.urls import path
from .views import CategoryViewSet, TagViewSet, PostViewSet, delete_category_image

app_name = 'posts'

router = DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'tags', TagViewSet)
router.register(r'posts', PostViewSet)

urlpatterns = [
    path('categories/<int:pk>/delete_image/', delete_category_image, name='posts_category_delete_image'),
] + router.urls



