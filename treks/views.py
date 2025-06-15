from rest_framework import generics
from .models import *
from .serializers import *

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from .serializers import UserSignupSerializer

class SignupView(APIView):
    def post(self, request):
        serializer = UserSignupSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user)

            # Get the user profile
            profile = UserProfile.objects.get(user=user)
            profile_data = UserProfileSerializer(profile).data

            return Response({
                'token': token.key,
                'user': profile_data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        user = authenticate(username=username, password=password)
        
        if user:
            token, created = Token.objects.get_or_create(user=user)

            # Get the user profile
            try:
                profile = UserProfile.objects.get(user=user)
                profile_data = UserProfileSerializer(profile).data
            except UserProfile.DoesNotExist:
                profile_data = {}

            return Response({
                'token': token.key,
                'user': profile_data
            }, status=status.HTTP_200_OK)

        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)


# --- USER PROFILE ---
class UserProfileListCreateView(generics.ListCreateAPIView):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer


class UserProfileDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    lookup_field = 'id'


# --- TREK ---
class TrekListCreateView(generics.ListCreateAPIView):
    queryset = Trek.objects.all()
    serializer_class = TrekSerializer


class TrekDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Trek.objects.all()
    serializer_class = TrekSerializer
    lookup_field = 'id'


# --- TIMS ---
class TimsApplicationListCreateView(generics.ListCreateAPIView):
    queryset = TimsApplication.objects.all()
    serializer_class = TimsApplicationSerializer


class TimsApplicationDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = TimsApplication.objects.all()
    serializer_class = TimsApplicationSerializer
    lookup_field = 'id'


# --- SOCIAL: POST ---
class PostListCreateView(generics.ListCreateAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer


class PostDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer


# --- SOCIAL: COMMENT ---
class CommentListCreateView(generics.ListCreateAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer


class CommentDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer


# --- LIKE ---
class LikeListCreateView(generics.ListCreateAPIView):
    queryset = Like.objects.all()
    serializer_class = LikeSerializer


class LikeDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Like.objects.all()
    serializer_class = LikeSerializer


# --- FAVORITE ---
class FavoriteListCreateView(generics.ListCreateAPIView):
    queryset = Favorite.objects.all()
    serializer_class = FavoriteSerializer


class FavoriteDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Favorite.objects.all()
    serializer_class = FavoriteSerializer


# --- USER-TREK INTERACTION ---
class UserTrekInteractionView(generics.ListCreateAPIView):
    queryset = UserTrekInteraction.objects.all()
    serializer_class = UserTrekInteractionSerializer


# --- TRANSIT PASS ---
class TransitPassListCreateView(generics.ListCreateAPIView):
    queryset = TransitPass.objects.all()
    serializer_class = TransitPassSerializer


class TransitPassDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = TransitPass.objects.all()
    serializer_class = TransitPassSerializer
