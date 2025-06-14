from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    UserProfile, Trek, TimsApplication,
    Post, Comment, Like, Favorite,
    UserTrekInteraction, TransitPass
)

# ✅ Define a basic UserSerializer
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

# ✅ Updated UserProfileSerializer using nested UserSerializer
class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = UserProfile
        fields = ['user', 'display_name', 'photo_url', 'role', 'is_active', 'created_at']


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
    class Meta:
        model = Favorite
        fields = '__all__'


class UserTrekInteractionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserTrekInteraction
        fields = '__all__'


class TransitPassSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransitPass
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
