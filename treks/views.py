from .models import *
from .serializers import *
from .serializers import UserSignupSerializer, SOSAlertSerializer

from rest_framework import generics, permissions, viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes, action

from django.utils import timezone
from datetime import timedelta
import random

class RecommendationViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def treks(self, request):
        try:
            profile = request.user.profile
            print(f"Fetching recommendations for user: {profile.user.username} with interests: {profile.interests}")
            recommended = recommend_treks(profile)
            serializer = TrekSerializer(recommended, many=True)
            return Response({
                "success": True,
                "recommended_treks": serializer.data
            })
        except AttributeError:
            return Response({
                "success": False,
                "error": "User profile not found"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "success": False,
                "error": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class AuthViewSet(viewsets.ViewSet):
    
    @action(detail=False, methods=['post'])
    def signup(self, request):
        serializer = UserSignupSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user)
            profile = UserProfile.objects.get(user=user)
            profile_data = UserProfileSerializer(profile).data
            return Response({
                'token': token.key,
                'user': profile_data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def login(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        user = authenticate(username=username, password=password)
        
        if user:
            token, created = Token.objects.get_or_create(user=user)
            try:
                profile = UserProfile.objects.get(user=user)
                profile_data = UserProfileSerializer(profile).data
            except UserProfile.DoesNotExist:
                profile_data = {}
            return Response({
                'token': token.key,
                'user': profile_data,
                'message': 'Login successful'
            })
        return Response({
            'error': 'Invalid credentials'
        }, status=status.HTTP_401_UNAUTHORIZED)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def change_password(self, request):
        """
        Change password for authenticated user
        """
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            if user.check_password(serializer.validated_data['old_password']):
                user.set_password(serializer.validated_data['new_password'])
                user.save()
                return Response({
                    'success': True,
                    'message': 'Password changed successfully'
                })
            return Response({
                'success': False,
                'error': 'Invalid old password'
            }, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def forgot_password(self, request):
        """Request password reset OTP"""
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            try:
                user = User.objects.get(email=email)
                
                # Generate 6 digit OTP
                otp = ''.join([str(random.randint(0, 9)) for _ in range(6)])
                
                # Save OTP with user reference
                PasswordResetOTP.objects.create(
                    user=user,
                    otp=otp
                )
                
                # Send email
                send_mail(
                    'Password Reset Code',
                    f'Your password reset code is: {otp}\nValid for 10 minutes.',
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=False,
                )
                
                return Response({
                    'success': True,
                    'message': 'Password reset code sent to your email'
                })
            except User.DoesNotExist:
                return Response({
                    'success': False,
                    'error': 'No user found with this email'
                }, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def reset_password_with_otp(self, request):
        """Reset password using OTP"""
        serializer = ResetPasswordWithOTPSerializer(data=request.data)
        if serializer.is_valid():
            otp = serializer.validated_data['otp']
            new_password = serializer.validated_data['new_password']
            
            try:
                # Get the latest unused OTP
                otp_obj = PasswordResetOTP.objects.filter(
                    otp=otp,
                    is_used=False
                ).latest('created_at')
                
                # Check if OTP is valid and not expired
                if otp_obj.is_valid():
                    user = otp_obj.user
                    # Update password
                    user.set_password(new_password)
                    user.save()
                    
                    # Mark OTP as used
                    otp_obj.is_used = True
                    otp_obj.save()
                    
                    return Response({
                        'success': True,
                        'message': 'Password reset successful'
                    })
                return Response({
                    'success': False,
                    'error': 'OTP has expired'
                }, status=status.HTTP_400_BAD_REQUEST)
                
            except PasswordResetOTP.DoesNotExist:
                return Response({
                    'success': False,
                    'error': 'Invalid OTP'
                }, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def verify_otp(self, request):
        """First step: Verify OTP"""
        serializer = OTPVerificationSerializer(data=request.data)
        if serializer.is_valid():
            otp = serializer.validated_data['otp']
            
            try:
                otp_obj = PasswordResetOTP.objects.filter(
                    otp=otp,
                    is_used=False
                ).latest('created_at')
                
                if otp_obj.is_valid():
                    # Mark as verified but not used
                    otp_obj.is_verified = True
                    otp_obj.save()
                    
                    return Response({
                        'success': True,
                        'message': 'OTP verified successfully. You can now reset your password.',
                        'verified': True
                    })
                return Response({
                    'success': False,
                    'error': 'OTP has expired'
                }, status=status.HTTP_400_BAD_REQUEST)
                
            except PasswordResetOTP.DoesNotExist:
                return Response({
                    'success': False,
                    'error': 'Invalid OTP'
                }, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def set_new_password(self, request):
        """Second step: Set new password after OTP verification"""
        serializer = SetNewPasswordSerializer(data=request.data)
        if serializer.is_valid():
            otp = serializer.validated_data['otp']
            new_password = serializer.validated_data['new_password']
            
            try:
                otp_obj = PasswordResetOTP.objects.filter(
                    otp=otp,
                    is_verified=True,
                    is_used=False
                ).latest('created_at')
                
                if otp_obj.is_valid():
                    user = otp_obj.user
                    user.set_password(new_password)
                    user.save()
                    
                    # Mark OTP as used
                    otp_obj.is_used = True
                    otp_obj.save()
                    
                    return Response({
                        'success': True,
                        'message': 'Password reset successful'
                    })
                return Response({
                    'success': False,
                    'error': 'OTP has expired'
                }, status=status.HTTP_400_BAD_REQUEST)
                
            except PasswordResetOTP.DoesNotExist:
                return Response({
                    'success': False,
                    'error': 'Invalid or unverified OTP'
                }, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class IsAdminUser(permissions.BasePermission):
    def has_permission(self, request, view):
        try:
            return request.user.profile.is_admin()
        except AttributeError:
            return False

class IsAdminOrSelf(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return True
        return False

    def has_object_permission(self, request, view, obj):
        if request.user.profile.is_admin():
            return True
            
        return obj.id == request.user.profile.id

class UserProfileListCreateView(generics.ListCreateAPIView):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]  

    def get_queryset(self):
        if self.request.user.profile.is_admin():
            return UserProfile.objects.all()
        return UserProfile.objects.none()

class UserProfileDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSelf]  
    lookup_field = 'id'

    def get_queryset(self):
        user = self.request.user
        if user.profile.is_admin():
            return UserProfile.objects.all()
        
        return UserProfile.objects.filter(id=user.profile.id)

class TrekViewSet(viewsets.ModelViewSet):
    
    queryset = Trek.objects.all()
    serializer_class = TrekSerializer
    lookup_field = 'id'
    

    def get_queryset(self):
        queryset = Trek.objects.all()
        return queryset.order_by('id')


class PostViewSet(viewsets.ModelViewSet):
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Post.objects.filter(status='active').order_by('-created_at')

    def create(self, request, *args, **kwargs):
        try:
            # Add user to request data
            data = request.data.copy()
            
            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            
            # Explicitly set the user before saving
            post = serializer.save(user=request.user.profile)
            
            return Response({
                "success": True,
                "message": "Post created successfully",
                "post": {
                    "id": post.id,
                    "content": post.content,
                    "images": post.images,
                    "location": post.location,
                    "likes_count": 0,
                    "comments_count": 0,
                    "created_at": post.created_at,
                    "user": {
                        "id": request.user.profile.id,
                        "display_name": request.user.profile.display_name,
                        "photo_url": request.user.profile.photo_url
                    },
                    "trek": {
                        "id": post.trek.id,
                        "name": post.trek.name
                    } if post.trek else None
                }
            }, status=status.HTTP_201_CREATED)

            

        except Exception as e:
            return Response({
                "success": False,
                "error": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        
        post = self.get_object()
        user_profile = request.user.profile
        
        try:
            like = Like.objects.get(post=post, user=user_profile)
            like.delete()
            return Response({'status': 'unliked'})
        except Like.DoesNotExist:
            Like.objects.create(post=post, user=user_profile)
            return Response({'status': 'liked'})

    @action(detail=True, methods=['post'])
    def report(self, request, pk=None):
       
        post = self.get_object()
        post.status = 'reported'
        post.save()
        return Response({'status': 'reported'})

class CommentViewSet(viewsets.ModelViewSet):
   
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Comment.objects.filter(status='active')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user.profile)
        # Update post's comment count
        post = serializer.validated_data['post']
        post.comments_count = post.comments.count()
        post.save()

    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
       
        comment = self.get_object()
        user_profile = request.user.profile
        
        try:
            like = Like.objects.get(comment=comment, user=user_profile)
            like.delete()
            return Response({'status': 'unliked'})
        except Like.DoesNotExist:
            Like.objects.create(comment=comment, user=user_profile)
            return Response({'status': 'liked'})

    @action(detail=True, methods=['post'])
    def report(self, request, pk=None):
        
        comment = self.get_object()
        comment.status = 'reported'
        comment.save()
        return Response({'status': 'reported'})

class LikeViewSet(viewsets.ModelViewSet):
   
    serializer_class = LikeSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'delete']  

    def get_queryset(self):
        return Like.objects.filter(user=self.request.user.profile)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user.profile)


class FavoriteViewSet(viewsets.ModelViewSet):
    serializer_class = FavoriteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user.profile).select_related('trek')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user.profile)


class UserTrekInteractionView(generics.ListCreateAPIView):
    queryset = UserTrekInteraction.objects.all()
    serializer_class = UserTrekInteractionSerializer


class TIMSViewSet(viewsets.ModelViewSet):
    queryset = TimsApplication.objects.all()
    serializer_class = TimsApplicationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        
        try:
            user_profile = user.profile
            return self.queryset.filter(user=user_profile).order_by('-created_at')
        except AttributeError:
            user_profile = UserProfile.objects.create(
                user=user,
                display_name=user.username
            )
            return self.queryset.filter(user=user_profile).order_by('-created_at')
        except Exception as e:
            return self.queryset.none()

    def perform_create(self, serializer):
        user = self.request.user
        try:
            user_profile = user.profile
        except AttributeError:
            
            user_profile = UserProfile.objects.create(
                user=user,
                display_name=user.username
            )
        serializer.save(user=user_profile)

class VerificationViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'])
    def verify_qr(self, request):
        try:
            user_profile = request.user.profile
            if not user_profile.is_admin():
                return Response({
                    "success": False,
                    "error": "Access denied. Only admin users can verify QR codes.",
                    "user_role": user_profile.role,
                    "message": "Contact administrator to get admin access."
                }, status=status.HTTP_403_FORBIDDEN)

            encrypted_data = request.data.get('qr_data')
            if not encrypted_data:
                return Response({
                    "success": False,
                    "error": "QR data is required"
                }, status=status.HTTP_400_BAD_REQUEST)

            from .utils import columnar_decrypt
            decrypted_tims_no = columnar_decrypt(encrypted_data)

            try:
                tims_app = TimsApplication.objects.get(tims_card_no=decrypted_tims_no)
                return Response({
                    "success": True,
                    "verified": True,
                    "verification_details": {
                        "verified_by": user_profile.display_name,
                        "officer_role": user_profile.role,
                        "verification_time": timezone.now().strftime('%Y-%m-%d %H:%M:%S')
                    },
                    "permit_details": {
                        "tims_card_no": tims_app.tims_card_no,
                        "full_name": tims_app.full_name,
                        "nationality": tims_app.nationality,
                        "passport_number": tims_app.passport_number,
                        "gender": tims_app.gender,
                        "trekker_area": tims_app.trekker_area,
                        "route": tims_app.route,
                        "entry_date": tims_app.entry_date.strftime('%Y-%m-%d') if tims_app.entry_date else None,
                        "exit_date": tims_app.exit_date.strftime('%Y-%m-%d') if tims_app.exit_date else None,
                        "status": tims_app.status,
                        "validity_status": "✅ VALID" if tims_app.status == 'approved' else "⚠️ PENDING/INVALID",
                        "applicant": tims_app.user.display_name,
                        "issued_date": tims_app.created_at.strftime('%Y-%m-%d')
                    }
                }, status.HTTP_200_OK)

            except TimsApplication.DoesNotExist:
                return Response({
                    "success": True,
                    "verified": False,
                    "error": "❌ INVALID PERMIT - Not found in database",
                    "message": "This permit may be fake or expired",
                    "verification_details": {
                        "verified_by": user_profile.display_name,
                        "verification_time": timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
                        "attempted_tims_no": decrypted_tims_no
                    }
                }, status.HTTP_404_NOT_FOUND)

        except AttributeError:
            return Response({
                "success": False,
                "error": "User profile not found. Please contact administrator.",
            }, status.HTTP_403_FORBIDDEN)

        except Exception as e:
            return Response({
                "success": False,
                "verified": False,
                "error": f"Verification failed: {str(e)}"
            }, status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def check_role(self, request):
        try:
            user_profile = request.user.profile
            return Response({
                "user_details": {
                    "username": request.user.username,
                    "display_name": user_profile.display_name,
                    "role": user_profile.role,
                    "is_admin": user_profile.is_admin(),
                    "can_verify_qr": user_profile.is_admin(),
                }
            })
        except AttributeError:
            return Response({
                "error": "User profile not found"
            }, status.HTTP_404_NOT_FOUND)

class SOSAlertViewSet(viewsets.ModelViewSet):

    serializer_class = SOSAlertSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        
        return SOSAlert.objects.filter(
            user=self.request.user.profile
        ).order_by('-created_at')

    def create(self, request, *args, **kwargs):
        
        try:
            
            user_lat = float(request.data.get('latitude'))
            user_lon = float(request.data.get('longitude'))
            selected_types = request.data.get('selected_types', [])
            emergency_type = request.data.get('emergency_type', [])
            description = request.data.get('description')

            user_profile = request.user.profile
            user_name = user_profile.display_name or request.user.username

            
            default_contacts = [
                {
                    "name": "Emergency Contact 1",
                    "email": "nepalihoni226@gmail.com",
                    "type": "emergency",
                    "source": "default"
                },
                {
                    "name": "Emergency Contact 2",
                    "email": "sudeepkarki75@gmail.com",
                    "type": "emergency",
                    "source": "default"
                }
            ]

            
            sos_alert = SOSAlert.objects.create(
                user=user_profile,
                latitude=user_lat,
                longitude=user_lon,
                description=description,
                emergency_type=emergency_type,
                selected_types=selected_types,
                contacted_services=default_contacts,
                google_places_data=[],
                status='sent'
            )

            
            nearby_places = []
            contacted_services = default_contacts.copy()
            recipient_emails = ["nepalihoni226@gmail.com", "sudeepkarki75@gmail.com"]
            call_numbers = []

            if selected_types:
                for place_type in selected_types:
                    places = google_places_service.search_nearby_places(
                        user_lat, user_lon, place_type
                    )
                    nearby_places.extend(places)

                   
                    for place in places:
                        if place.get('phone') or place.get('email'):
                            service = {
                                'name': place['name'],
                                'phone': place.get('phone', ''),
                                'email': place.get('email', ''),
                                'type': place_type,
                                'distance_km': place['distance_km'],
                                'source': 'google_places'
                            }
                            contacted_services.append(service)
                            
                            if service['email'] and service['email'] not in recipient_emails:
                                recipient_emails.append(service['email'])
                            if service['phone']:
                                call_numbers.append({
                                    'name': service['name'],
                                    'phone': service['phone'],
                                    'type': service['type']
                                })

            # Send emails
            if recipient_emails:
                EmailService.send_sos_alert(
                    user_name=user_name,
                    user_lat=user_lat,
                    user_lon=user_lon,
                    selected_types=selected_types,
                    description=description,
                    alert_id=sos_alert.id,
                    recipient_emails=recipient_emails
                )

            return Response({
                "success": True,
                "message": "SOS alert sent successfully",
                "description": description,
                "emergency_type": emergency_type,
                "alert_id": sos_alert.id,
                "contacted_services": len(contacted_services),
                "nearby_places_found": len(nearby_places),
                "emails_sent_to": recipient_emails,
                "call_numbers": call_numbers,
                "location": {
                    "latitude": user_lat,
                    "longitude": user_lon,
                    "maps_url": f"https://maps.google.com/?q={user_lat},{user_lon}"
                }
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                "success": False,
                "error": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)