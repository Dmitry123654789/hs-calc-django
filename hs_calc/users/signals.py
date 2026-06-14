import users.models


def create_user_profile(sender, instance, created, **kwargs):
    if kwargs.get("raw"):
        return

    if created:
        users.models.Profile.objects.create(user=instance)
