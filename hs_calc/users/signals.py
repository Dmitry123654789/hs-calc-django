from users.models import Profile


def create_user_profile(sender, instance, created, **kwargs):
    if kwargs.get("raw"):
        return

    if created:
        Profile.objects.create(user=instance)
