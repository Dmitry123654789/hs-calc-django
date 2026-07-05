from django.apps import AppConfig
from django.db.models.signals import post_save


class UsersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "users"
    verbose_name = "Пользователи"

    def ready(self):
        from django.contrib.auth import get_user_model
        import users.signals

        user = get_user_model()
        post_save.connect(
            users.signals.create_user_profile,
            sender=user,
        )
