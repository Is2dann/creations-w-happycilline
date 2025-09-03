from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Profile

User = settings.AUTH_USER_MODEL


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_profile_for_new_user(sender, instance, created, **kwargs):
    """
    Create the user profile
    """
    if created:
        Profile.objects.get_or_create(user=instance)
