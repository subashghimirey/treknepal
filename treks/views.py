from .models import *
from .serializers import *
from .serializers import UserSignupSerializer, SOSAlertSerializer, PasswordResetRequestSerializer, ResetPasswordWithOTPSerializer, OTPVerificationSerializer, SetNewPasswordSerializer, ChangePasswordSerializer

from rest_framework import generics, permissions, viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets
from .utils import google_places_service, validate_sos_with_gemini, validate_post_with_gemini
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes, action

from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import authenticate

from .recommend import recommend_treks 
from .email_service import EmailService


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
        serializer.is_valid(raise_exception=True)  # ensure 400 on validation errors
        user = serializer.save()

        # Ensure token + profile exist
        from rest_framework.authtoken.models import Token
        token, _ = Token.objects.get_or_create(user=user)
        profile = getattr(user, "profile", None)
        if profile is None:
            from .models import UserProfile
            profile, _ = UserProfile.objects.get_or_create(user=user, defaults={"display_name": user.username})

        return Response({
            "token": token.key,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
            },
            "profile": {
                "id": profile.id,
                "user_id": user.id,
                "display_name": profile.display_name,
                "photo_url": profile.photo_url,
                "role": profile.role,
                "interests": profile.interests or [],
                "is_active": profile.is_active,
                "created_at": profile.created_at,
            }
        }, status=status.HTTP_201_CREATED)

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
    queryset = Post.objects.all()
    permission_classes = [IsAuthenticated]  # uncomment if you require auth

    def create(self, request, *args, **kwargs):
        title = request.data.get("title") or ""
        content = (
            request.data.get("content")
            or request.data.get("description")
            or request.data.get("text")
            or ""
        )

        # Moderate content with Gemini
        moderation = validate_post_with_gemini(content, title)

        # Hard block clearly abusive content
        if not moderation["appropriate"] and moderation["confidence"] >= 0.7:
            return Response({
                "success": False,
                "error": "Please use appropriate content.",
                "message": moderation["reason"],
                "details": {
                    "confidence": moderation["confidence"],
                    "validation_method": moderation["validation_method"]
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        # Optionally pass moderation metadata to perform_create
        request._post_moderation = moderation
        return super().create(request, *args, **kwargs)

    # Optional: save moderation metadata if your Post model has these fields
    # def perform_create(self, serializer):
    #     m = getattr(self.request, "_post_moderation", {}) or {}
    #     flagged = (not m.get("appropriate", True)) and m.get("confidence", 0) >= 0.3
    #     serializer.save(
    #         moderation_appropriate=m.get("appropriate", True),
    #         moderation_confidence=m.get("confidence", 1.0),
    #         moderation_reason=m.get("reason", ""),
    #         moderation_method=m.get("validation_method", ""),
    #         flagged_for_review=flagged,
    #     )

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
            profile = user.profile
        except AttributeError:
            profile, _ = UserProfile.objects.get_or_create(
                user=user,
                defaults={"display_name": user.username}
            )

        qs = self.queryset.select_related("user").order_by("-created_at")

        try:
            if profile.is_admin():
                return qs
        except Exception:
            pass

        return qs.filter(user=profile)

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

            # Use same key as encrypt (default "TREK" or override via settings.TIMS_QR_KEY)
            from .utils import columnar_decrypt
            qr_key = getattr(settings, "TIMS_QR_KEY", "TREK")
            decrypted_tims_no = columnar_decrypt(encrypted_data, qr_key)

            # Try by decrypted TIMS number; also fall back to raw string just in case
            try:
                tims_app = TimsApplication.objects.get(tims_card_no=decrypted_tims_no)
            except TimsApplication.DoesNotExist:
                tims_app = TimsApplication.objects.filter(tims_card_no=encrypted_data).first()
                if not tims_app:
                    raise

            return Response({
                "success": True,
                "verified": True,
                "verification_details": {
                    "verified_by": user_profile.display_name,
                    "officer_role": user_profile.role,
                    "verification_time": timezone.now().strftime('%Y-%m-%d %H:%M:%S')
                },
                "permit_details": {
                    "id": tims_app.id,
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
                    "validity_status": "  VALID" if tims_app.status == 'approved' else "  PENDING/INVALID",
                    "applicant": tims_app.user.display_name,
                    "issued_date": tims_app.created_at.strftime('%Y-%m-%d')
                }
            }, status.HTTP_200_OK)

        except TimsApplication.DoesNotExist:
            return Response({
                "success": True,
                "verified": False,
                "error": "  INVALID PERMIT - Not found in database",
                "message": "This permit may be fake or expired",
                "verification_details": {
                    "verified_by": request.user.profile.display_name if hasattr(request.user, "profile") else request.user.username,
                    "verification_time": timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
                    "attempted_tims_no": decrypted_tims_no if 'decrypted_tims_no' in locals() else encrypted_data
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
        if self.request.user.profile.is_admin():
            return SOSAlert.objects.all().order_by('-created_at')
        return SOSAlert.objects.filter(
            user=self.request.user.profile
        ).order_by('-created_at')

    def create(self, request, *args, **kwargs):
        print("\n" + "="*80)
        print("SOS ALERT CREATION")
        print("="*80)
        
        try:
            user_lat = float(request.data.get('latitude'))
            user_lon = float(request.data.get('longitude'))
            selected_types = request.data.get('selected_types', [])
            emergency_type = request.data.get('emergency_type', '')
            description = request.data.get('description', '')

            user_profile = request.user.profile
            user_name = user_profile.display_name or request.user.username
            
            # VALIDATE WITH GEMINI AI
            print(f"🤖 Validating SOS description with Gemini AI...")
            print(f"Description: {description}")
            print(f"Type: {emergency_type}")
            
            validation = validate_sos_with_gemini(description, emergency_type)
            
            print(f"Validation result: {validation}")
            
            # Reject if clearly invalid (confidence > 0.7 that it's spam)
            if not validation['is_valid'] and validation['confidence'] > 0.7:
                print(f"❌ SOS REJECTED: {validation['reason']}")
                return Response({
                    "success": False,
                    "error": "Invalid SOS request",
                    "message": validation['reason'],
                    "details": {
                        "confidence": validation['confidence'],
                        "validation_method": validation['validation_method']
                    },
                    "help": "Please provide a clear emergency description. Test alerts and spam are not allowed."
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Flag uncertain cases (0.3 < confidence < 0.7 for invalid)
            flagged = not validation['is_valid'] and validation['confidence'] >= 0.3

            default_contacts = [
                {"name": "Emergency Contact 1", "email": "nepalihoni226@gmail.com", "type": "emergency", "source": "default"},
                {"name": "Emergency Contact 2", "email": "sudeepkarki75@gmail.com", "type": "emergency", "source": "default"}
            ]

            # Create SOS with validation data
            sos_alert = SOSAlert.objects.create(
                user=user_profile,
                latitude=user_lat,
                longitude=user_lon,
                description=description,
                emergency_type=emergency_type,
                selected_types=selected_types,
                contacted_services=default_contacts,
                google_places_data=[],
                status='sent',
                is_valid=validation['is_valid'],
                validation_confidence=validation['confidence'],
                validation_reason=validation['reason'],
                validation_method=validation['validation_method'],
                flagged_for_review=flagged
            )
            
            print(f"✅ SOS Alert created: ID={sos_alert.id}, Valid={validation['is_valid']}, Flagged={flagged}")

            # Initialize tracking
            nearby_places = []
            contacted_services = default_contacts.copy()
            recipient_emails = ["nepalihoni226@gmail.com", "sudeepkarki75@gmail.com"]
            call_numbers = []

            # CRITICAL SECTION - Search Google Places
            if selected_types:
                print(f"Searching for {len(selected_types)} service types...")
                for place_type in selected_types:
                    try:
                        places = google_places_service.search_nearby_places(
                            user_lat, user_lon, place_type, radius=5000
                        )
                        if places:
                            nearby_places.extend(places)
                            for place in places:
                                if place.get('phone') or place.get('email'):
                                    service = {
                                        'name': place['name'],
                                        'phone': place.get('phone', ''),
                                        'email': place.get('email', ''),
                                        'type': place_type,
                                        'distance_km': place['distance_km'],
                                        'source': 'geoapify'
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
                    except Exception as e:
                        print(f"Error searching {place_type}: {e}")

            # Send emails
            if recipient_emails:
                try:
                    EmailService.send_sos_alert(
                        user_name=user_name,
                        user_lat=user_lat,
                        user_lon=user_lon,
                        selected_types=selected_types,
                        description=description,
                        alert_id=sos_alert.id,
                        recipient_emails=recipient_emails
                    )
                    print(f"📧 Emails sent to {len(recipient_emails)} recipients")
                except Exception as e:
                    print(f"Email error: {e}")
            
            sos_alert.google_places_data = nearby_places
            sos_alert.contacted_services = contacted_services
            sos_alert.save()

            # Prepare response
            response_data = {
                "success": True,
                "message": "SOS alert sent successfully",
                "alert_id": sos_alert.id,
                "validation": {
                    "is_valid": validation['is_valid'],
                    "confidence": validation['confidence'],
                    "reason": validation['reason'],
                    "method": validation['validation_method']
                },
                "contacted_services": len(contacted_services),
                "nearby_places_found": len(nearby_places),
                "nearby_places": nearby_places,
                "emails_sent_to": recipient_emails,
                "call_numbers": call_numbers,
                "location": {
                    "latitude": user_lat,
                    "longitude": user_lon,
                    "maps_url": f"https://maps.google.com/?q={user_lat},{user_lon}"
                }
            }
            
            # Add warning if flagged
            if flagged:
                response_data["warning"] = f"Alert created but flagged for review: {validation['reason']}"
                response_data["alert_status"] = "flagged_for_review"
            
            print("SOS ALERT COMPLETED")
            print("="*80 + "\n")
            
            return Response(response_data, status=status.HTTP_201_CREATED)

        except Exception as e:
            print(f"CRITICAL ERROR: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return Response({
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['patch'], permission_classes=[IsAuthenticated])
    def review(self, request, pk=None):
        """Admin endpoint to review flagged SOS alerts"""
        if not request.user.profile.is_admin():
            return Response({"error": "Admin access required"}, status=status.HTTP_403_FORBIDDEN)
        
        sos_alert = self.get_object()
        action = request.data.get('action')
        
        if action == 'approve':
            sos_alert.is_valid = True
            sos_alert.flagged_for_review = False
            sos_alert.reviewed_by = request.user.profile
            sos_alert.reviewed_at = timezone.now()
            sos_alert.validation_reason = f"Manually approved by {request.user.username}"
            sos_alert.save()
            return Response({"message": "SOS alert approved", "alert_id": sos_alert.id})
        
        elif action == 'reject':
            sos_alert.is_valid = False
            sos_alert.status = 'cancelled'
            sos_alert.flagged_for_review = False
            sos_alert.reviewed_by = request.user.profile
            sos_alert.reviewed_at = timezone.now()
            sos_alert.save()
            return Response({"message": "SOS alert rejected as spam", "alert_id": sos_alert.id})
        
        return Response({"error": "Invalid action (use 'approve' or 'reject')"}, status=status.HTTP_400_BAD_REQUEST)

class NearbyPlacesView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        try:
            lat = float(request.query_params.get("lat"))
            lng = float(request.query_params.get("lng"))
        except (TypeError, ValueError):
            return Response({"error": "lat and lng are required floats"}, status=status.HTTP_400_BAD_REQUEST)

        place_type = request.query_params.get("type", "hospital")
        try:
            radius = int(request.query_params.get("radius", 5000))
        except ValueError:
            radius = 5000

        results = google_places_service.search_nearby_places(lat, lng, place_type, radius=radius)
        return Response({"count": len(results), "results": results}, status=status.HTTP_200_OK)

