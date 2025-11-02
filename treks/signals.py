from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token

from .models import UserProfile

@receiver(post_save, sender=User)
def create_profile_and_token(sender, instance, created, **kwargs):
    # Ensure a profile exists for every user (superusers included)
    UserProfile.objects.get_or_create(
        user=instance,
        defaults={"display_name": instance.username}
    )
    # Ensure auth token exists
    Token.objects.get_or_create(user=instance)