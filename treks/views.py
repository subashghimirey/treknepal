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
from django.contrib.auth import authenticate

from .recommend import recommend_treks
from .utils import google_places_service
from .email_service import EmailService



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def recommended_treks_api(request):
    profile = request.user.profile
    print(f"Fetching recommendations for user: {profile.user.username} with interests: {profile.interests}")
    recommended = recommend_treks(profile)
    serializer = TrekSerializer(recommended, many=True)
    return Response(serializer.data)


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

class UserProfileListCreateView(generics.ListCreateAPIView):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer


class UserProfileDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_field = 'id'


class TrekViewSet(viewsets.ModelViewSet):
    
    queryset = Trek.objects.all()
    serializer_class = TrekSerializer
    lookup_field = 'id'
    # permission_classes = [IsAuthenticated] 

    def get_queryset(self):
        queryset = Trek.objects.all()
        return queryset.order_by('id')


class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Post.objects.all().order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user.profile)


class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Comment.objects.all().order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user.profile)


class LikeViewSet(viewsets.ModelViewSet):
    queryset = Like.objects.all()
    serializer_class = LikeSerializer
    permission_classes = [IsAuthenticated]

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
                    "email": "sudeepkarki74@gmail.com",
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
            recipient_emails = ["nepalihoni226@gmail.com", "sudeepkarki74@gmail.com"]
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