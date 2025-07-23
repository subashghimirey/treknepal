from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    UserProfile, Trek, TimsApplication,
    Post, Comment, Like, Favorite,
    UserTrekInteraction, SOSAlert
)


class UserProfileInlineSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['display_name', 'photo_url', 'role', 'interests']

class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileInlineSerializer()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'profile']

    def update(self, instance, validated_data):
        # Extract profile data
        profile_data = validated_data.pop('profile', None)
        
        # Update User fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update profile if provided
        if profile_data:
            profile_instance = instance.profile
            for attr, value in profile_data.items():
                setattr(profile_instance, attr, value)
            profile_instance.save()
        
        return instance

class TimsApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimsApplication
        fields = [
            'id', 'tims_card_no', 'encrypted_qr_code', 'transaction_id', 
            'issue_date', 'image', 'full_name', 'nationality', 
            'passport_number', 'gender', 'date_of_birth',
            'trekker_area', 'route', 'entry_date', 'exit_date',
            'nepal_contact_name', 'nepal_organization', 'nepal_designation',
            'nepal_mobile', 'nepal_office_number', 'nepal_address',
            'home_contact_name', 'home_city', 'home_mobile',
            'home_office_number', 'home_address',
            'status', 'payment_status', 'transit_pass_cost', 'permit_cost',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'tims_card_no', 'issue_date', 'created_at', 'updated_at']
    
    def update(self, instance, validated_data):
        # Pop profile data from validated_data
        profile_data = validated_data.pop('profile', {})

        # Update User fields
        instance.username = validated_data.get('username', instance.username)
        instance.email = validated_data.get('email', instance.email)
        instance.save()

        # Update related UserProfile fields
        profile = instance.profile  # through OneToOneField

        for attr, value in profile_data.items():
            setattr(profile, attr, value)
        profile.save()

        return instance



class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    
    class Meta:
        model = UserProfile
        fields = ['user', 'display_name', 'photo_url', 'interests' , 'role', 'is_active', 'created_at']


class TrekSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trek
        fields = '__all__'


class TimsApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimsApplication
        fields = '__all__'


class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = '__all__'


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = '__all__'


class LikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Like
        fields = '__all__'


class FavoriteSerializer(serializers.ModelSerializer):
    trek = TrekSerializer(read_only=True)  
    trek_id = serializers.IntegerField(write_only=True)  
    
    class Meta:
        model = Favorite
        fields = ['id', 'created_at', 'user', 'trek', 'trek_id']
        read_only_fields = ['user']
    
    def create(self, validated_data):
        trek_id = validated_data.pop('trek_id')
        trek = Trek.objects.get(id=trek_id)
        validated_data['trek'] = trek
        return super().create(validated_data)
    
class UserTrekInteractionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserTrekInteraction
        fields = '__all__'



# ✅ Signup serializer handling user + user profile
class UserSignupSerializer(serializers.ModelSerializer):
    display_name = serializers.CharField()
    photo_url = serializers.URLField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'display_name', 'photo_url']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        display_name = validated_data.pop('display_name')
        photo_url = validated_data.pop('photo_url', '')
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        UserProfile.objects.create(
            user=user,
            display_name=display_name,
            photo_url=photo_url
        )
        return user

class SOSAlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = SOSAlert
        fields = [
            'id', 
            'latitude', 
            'longitude',
            'selected_types',
            'description',
            'emergency_type',
            'contacted_services',
            'google_places_data',
            'fallback_contacts',
            'status',
            'created_at',
            'resolved_at'
        ]
        read_only_fields = ['id', 'created_at', 'resolved_at', 'status']

    def to_representation(self, instance):
        """Customize the output format"""
        data = super().to_representation(instance)
        # Ensure empty lists instead of null
        data['selected_types'] = data.get('selected_types') or []
        data['contacted_services'] = data.get('contacted_services') or []
        data['google_places_data'] = data.get('google_places_data') or []
        data['fallback_contacts'] = data.get('fallback_contacts') or []
        return data
