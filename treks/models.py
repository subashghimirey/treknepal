from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.utils import timezone


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    display_name = models.CharField(max_length=255)
    photo_url = models.URLField(blank=True, null=True)
    role = models.CharField(max_length=20, default='user')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.display_name or self.user.username


class Trek(models.Model):
    name = models.TextField()
    district = models.TextField()
    region = models.TextField()
    difficulty = models.TextField()
    duration = models.TextField()
    best_seasons = models.JSONField(null=True, blank=True)
    elevation_profile = models.JSONField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    historical_significance = models.TextField(null=True, blank=True)
    itinerary = models.JSONField(null=True, blank=True)
    cost_breakdown = models.JSONField(null=True, blank=True)
    transportation = models.TextField(null=True, blank=True)
    nearby_attractions = models.JSONField(null=True, blank=True)
    required_permits = models.JSONField(null=True, blank=True)
    recommended_gear = models.JSONField(null=True, blank=True)
    safety_info = models.JSONField(null=True, blank=True)
    photos = models.JSONField(null=True, blank=True)
    itinerary_points = models.JSONField(null=True, blank=True)
    transit_card_cost = models.IntegerField(null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    cluster_label = models.IntegerField(null=True, blank=True)
    tags = models.JSONField(null=True, blank=True)

    def __str__(self):
        return self.name


class TimsApplication(models.Model):
    tims_card_no = models.CharField(max_length=255, unique=True)
    transaction_id = models.CharField(max_length=255, unique=True)
    issue_date = models.DateTimeField()
    full_name = models.CharField(max_length=255)
    nationality = models.CharField(max_length=255)
    passport_number = models.CharField(max_length=255)
    gender = models.CharField(max_length=10)
    date_of_birth = models.DateField()
    trekker_area = models.CharField(max_length=255)
    route = models.CharField(max_length=255)
    entry_date = models.DateField()
    exit_date = models.DateField()

    # Nepal contact
    nepal_contact_name = models.CharField(max_length=255)
    nepal_organization = models.CharField(max_length=255)
    nepal_designation = models.CharField(max_length=255, null=True, blank=True)
    nepal_mobile = models.CharField(max_length=20)
    nepal_office_number = models.CharField(max_length=20, null=True, blank=True)
    nepal_address = models.TextField()

    # Home contact
    home_contact_name = models.CharField(max_length=255)
    home_city = models.CharField(max_length=255)
    home_mobile = models.CharField(max_length=20)
    home_office_number = models.CharField(max_length=20, null=True, blank=True)
    home_address = models.TextField()

    status = models.CharField(max_length=50, default='pending')
    payment_status = models.CharField(max_length=50, default='pending')
    permit_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.tims_card_no


class Post(models.Model):
    trek = models.ForeignKey(Trek, on_delete=models.CASCADE)
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)


class Like(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('post', 'user')




class Favorite(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    trek = models.ForeignKey(Trek, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('user', 'trek')



class UserTrekInteraction(models.Model):
    INTERACTIONS = (
        ('view', 'View'),
        ('like', 'Like'),
        ('favorite', 'Favorite'),
        ('comment', 'Comment'),
        ('post', 'Post')
    )
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    trek = models.ForeignKey(Trek, on_delete=models.CASCADE)
    interaction_type = models.CharField(max_length=20, choices=INTERACTIONS)
    interaction_weight = models.IntegerField(default=1)
    created_at = models.DateTimeField(default=timezone.now)


class TransitPass(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    trek = models.ForeignKey(Trek, on_delete=models.CASCADE)
    encrypted_qr = models.TextField()
    issued_at = models.DateTimeField(default=timezone.now)
    validated_at = models.DateTimeField(null=True, blank=True)
