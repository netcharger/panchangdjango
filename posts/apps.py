from django.apps import AppConfig


class PostsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'

    def ready(self):
        import posts.signals
    name = 'posts'
