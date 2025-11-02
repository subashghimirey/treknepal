from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from .models import UserProfile

@receiver(post_save, sender=User)
def create_profile_and_token(sender, instance, created, **kwargs):
    # Only on first creation to avoid duplicates
    if created:
        UserProfile.objects.get_or_create(
            user=instance,
            defaults={"display_name": instance.username}
        )
        Token.objects.get_or_create(user=instance)