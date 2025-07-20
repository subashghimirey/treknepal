from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    UserProfile, Trek, TimsApplication,
    Post, Comment, Like, Favorite,
    UserTrekInteraction
)


class UserProfileInlineSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['display_name', 'photo_url', 'role', 'interests']

class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileInlineSerializer()
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'profile', ]


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
    class Meta:
        model = Favorite
        fields = '__all__'


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
