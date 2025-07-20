from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.utils import timezone
import qrcode
import base64
from io import BytesIO
import requests
import math


class UserProfile(models.Model):

    ROLE_CHOICES = [
        ('user', 'Regular User'),
        ('admin', 'Admin/Officer'),
        ('superadmin', 'Super Admin'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    display_name = models.CharField(max_length=255)
    photo_url = models.URLField(blank=True, null=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES,default='user')
    interests = models.JSONField(default=list, blank=True) 
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    def is_admin(self):
        return self.role in ['admin', 'superadmin']

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
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ]
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed')
    ]
    
    user = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True)
    tims_card_no = models.CharField(max_length=50, unique=True, blank=True, null=True)
    encrypted_qr_code = models.URLField(blank=True, null=True)
    transaction_id = models.CharField(max_length=100)
    issue_date = models.DateField(auto_now_add=True)
    image = models.URLField()
    full_name = models.CharField(max_length=200)
    nationality = models.CharField(max_length=100)
    passport_number = models.CharField(max_length=100)
    gender = models.CharField(max_length=10)
    date_of_birth = models.DateField(null=True, blank=True)
    trekker_area = models.CharField(max_length=200)
    route = models.CharField(max_length=200)
    entry_date = models.DateField(null=True, blank=True)
    exit_date = models.DateField(null=True, blank=True)
    
    # Nepal Contact Information
    nepal_contact_name = models.CharField(max_length=200)
    nepal_organization = models.CharField(max_length=200)
    nepal_designation = models.CharField(max_length=200, blank=True)
    nepal_mobile = models.CharField(max_length=20)
    nepal_office_number = models.CharField(max_length=20, blank=True)
    nepal_address = models.TextField()
    
    # Home Country Contact Information
    home_contact_name = models.CharField(max_length=200)
    home_city = models.CharField(max_length=200)
    home_mobile = models.CharField(max_length=20)
    home_office_number = models.CharField(max_length=20, blank=True)
    home_address = models.TextField()
    
    # Status and Cost Information
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    transit_pass_cost = models.JSONField()
    permit_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.pk:
            super().save(*args, **kwargs)
        
        if not self.tims_card_no:
            year = self.created_at.strftime('%Y')
            self.tims_card_no = f'TIMS{year}{str(self.id).zfill(6)}'
            
            try:
                from .utils import columnar_encrypt, generate_qr_and_upload
                
                encrypted_data = columnar_encrypt(self.tims_card_no)
                qr_url = generate_qr_and_upload(encrypted_data, 'timsqr')  # Use 'timsqr' preset
                self.encrypted_qr_code = qr_url
                
                super().save(update_fields=['tims_card_no', 'encrypted_qr_code'])
            except Exception as e:
                print(f"Error generating QR code: {e}")
                super().save(update_fields=['tims_card_no'])
        else:
            super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.full_name} - {self.tims_card_no or 'Pending'}"

    class Meta:
        ordering = ['-created_at']


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



class EmergencyContactPoint(models.Model):
    name = models.CharField(max_length=100)
    type = models.CharField(choices=[('police', 'Police'), ('hospital', 'Hospital'), ('teahouse', 'Teahouse / Lodge'), ('rescue', 'Rescue')], max_length=20)
    email = models.EmailField(null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    latitude = models.FloatField()
    longitude = models.FloatField()

    def __str__(self):
        return f"{self.name} ({self.type}) - {self.phone}"
    
    
class SOSAlert(models.Model):
    ALERT_TYPES = (
        ('police', 'Police'),
        ('hospital', 'Hospital'),
        ('teahouse', 'Teahouse'),
        ('rescue', 'Rescue'),
    )

    EMERGENCY_TYPES = (
        ('health_issues', 'Health Issues'),
        ('lost', 'Lost'),
        ('theft', 'Theft'),
        ('rescue', 'Rescue'),
    )


    
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    latitude = models.FloatField()
    longitude = models.FloatField()
    selected_types = models.JSONField()  # List of selected emergency types
    contacted_services = models.JSONField(default=list) 
    google_places_data = models.JSONField(default=list)  
    fallback_contacts = models.JSONField(default=list)  
    status = models.CharField(max_length=20 ,default='sent')
    emergency_type = models.CharField(max_length=20, choices=EMERGENCY_TYPES, default='health_issues')
    description = models.TextField(null=True, blank=True) 
    created_at = models.DateTimeField(default=timezone.now)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"SOS Alert by {self.user.display_name} at {self.created_at}"
