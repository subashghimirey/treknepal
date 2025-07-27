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

class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=False)
    
    class Meta:
        model = UserProfile
        fields = ['user', 'display_name', 'photo_url', 'interests', 'role', 'is_active', 'created_at']

    def update(self, instance, validated_data):
        # Handle nested user data
        user_data = validated_data.pop('user', None)
        if user_data:
            user = instance.user
            for attr, value in user_data.items():
                setattr(user, attr, value)
            user.save()

        # Update UserProfile fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance
    

class UserProfileMiniSerializer(serializers.ModelSerializer):
   
    class Meta:
        model = UserProfile
        fields = ['id', 'display_name', 'photo_url']


class TrekSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trek
        fields = '__all__'


class TimsApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimsApplication
        fields = '__all__'


class PostSerializer(serializers.ModelSerializer):
    """Serializer for posts with nested relationships"""
    user = UserProfileMiniSerializer(read_only=True)
    comments = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    trek_name = serializers.CharField(source='trek.name', read_only=True)

    class Meta:
        model = Post
        fields = [
            'id', 'trek', 'trek_name', 'user', 'content',
            'images', 'location', 'likes_count', 'comments_count',
            'status', 'created_at', 'updated_at', 'comments',
            'is_liked'
        ]
        read_only_fields = [
            'likes_count', 'comments_count', 'status'
        ]

    def get_comments(self, obj):
        """Get top-level comments only"""
        return CommentSerializer(
            obj.comments.filter(parent=None, status='active'),
            many=True,
            context=self.context
        ).data

    def get_is_liked(self, obj):
        """Check if current user has liked this post"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.likes.filter(user=request.user.profile).exists()
        return False

    def validate_images(self, value):
        """Validate image URLs"""
        if not isinstance(value, list):
            raise serializers.ValidationError("Images must be a list")
        for url in value:
            if not isinstance(url, str):
                raise serializers.ValidationError("Each image must be a URL string")
        return value

class CommentSerializer(serializers.ModelSerializer):
    """Serializer for comments with nested user info and reply support"""
    user = UserProfileMiniSerializer(read_only=True)
    replies = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = [
            'id', 'post', 'user', 'content', 'parent',
            'likes_count', 'status', 'created_at',
            'updated_at', 'replies', 'is_liked'
        ]
        read_only_fields = ['likes_count', 'status']

    def get_replies(self, obj):
        """Get replies for this comment"""
        if hasattr(obj, 'replies'):
            return CommentSerializer(obj.replies.filter(status='active'), many=True).data
        return []

    def get_is_liked(self, obj):
        """Check if current user has liked this comment"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.likes.filter(user=request.user.profile).exists()
        return False

class LikeSerializer(serializers.ModelSerializer):
    """Serializer for likes"""
    user = UserProfileMiniSerializer(read_only=True)

    class Meta:
        model = Like
        fields = ['id', 'post', 'comment', 'user', 'created_at']
        read_only_fields = ['user']

    def validate(self, attrs):
        """Ensure either post or comment is provided, not both"""
        if attrs.get('post') and attrs.get('comment'):
            raise serializers.ValidationError(
                "Cannot like both post and comment simultaneously"
            )
        if not attrs.get('post') and not attrs.get('comment'):
            raise serializers.ValidationError(
                "Must like either a post or comment"
            )
        return attrs

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


class TimsApplicationSerializer(serializers.ModelSerializer):
    trek_details = TrekSerializer(source='trek', read_only=True)
    trek_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = TimsApplication
        fields = [
            'id', 'user', 'trek_id', 'trek_details', 'tims_card_no', 
            'encrypted_qr_code', 'transaction_id', 'issue_date', 'image',
            'full_name', 'nationality', 'passport_number', 'gender',
            'date_of_birth', 'trekker_area', 'route', 'entry_date',
            'exit_date', 'nepal_contact_name', 'nepal_organization',
            'nepal_designation', 'nepal_mobile', 'nepal_office_number',
            'nepal_address', 'home_contact_name', 'home_city',
            'home_mobile', 'home_office_number', 'home_address',
            'status', 'payment_status', 'transit_pass_cost',
            'permit_cost', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'tims_card_no', 'encrypted_qr_code', 
                           'created_at', 'updated_at']
    
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

class ChangePasswordSerializer(serializers.Serializer):
   
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)

    def validate_new_password(self, value):
        
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long")
        if not any(char.isdigit() for char in value):
            raise serializers.ValidationError("Password must contain at least one number")
        if not any(char.isupper() for char in value):
            raise serializers.ValidationError("Password must contain at least one uppercase letter")
        return value

class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

class OTPVerificationSerializer(serializers.Serializer):
    otp = serializers.CharField(min_length=6, max_length=6)

class SetNewPasswordSerializer(serializers.Serializer):
    otp = serializers.CharField(min_length=6, max_length=6)
    new_password = serializers.CharField(min_length=8)

    def validate_new_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long")
        if not any(char.isdigit() for char in value):
            raise serializers.ValidationError("Password must contain at least one number")
        if not any(char.isupper() for char in value):
            raise serializers.ValidationError("Password must contain at least one uppercase letter")
        return value
