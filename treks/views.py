from rest_framework import generics, permissions
from .models import *
from .serializers import *
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from .serializers import UserSignupSerializer

from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .recommend import recommend_treks
from .serializers import TrekSerializer

from django.core.mail import send_mail
from rest_framework.decorators import api_view
from rest_framework.response import Response


class TimsApplicationListCreateView(generics.ListCreateAPIView):
    queryset = TimsApplication.objects.all()
    serializer_class = TimsApplicationSerializer
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        user = self.request.user
        return TimsApplication.objects.filter(user=user)


class TimsApplicationDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = TransitPass.objects.all()
    serializer_class = TransitPassSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        user = self.request.user
        return TimsApplication.objects.filter(user=user)
from rest_framework import status

from .models import EmergencyContactPoint
from .utils import google_places_service
from django.utils import timezone
from .models import SOSAlert

# @api_view(['POST'])
# def send_sos(request):
#     try:
#         user_lat = float(request.data.get('latitude'))
#         user_lon = float(request.data.get('longitude'))
#         selected_types = request.data.get('selected_types', [])  # e.g. ["police", "hospital"]

#         # Get user info from profile (assuming request.user is authenticated)
#         user_profile = request.user.profile  # or however your UserProfile is related
#         user_name = user_profile.display_name or request.user.username
        

#         nearest_contacts = find_nearest_contacts(user_lat, user_lon, selected_types)

#         # Prepare email
#         subject = f"SOS Alert from {user_name}"
#         message = (
#             f"User {user_name} triggered an SOS.\n"
            
#             f"Location: https://maps.google.com/?q={user_lat},{user_lon}\n"
#             "Please respond immediately."
#         )
#         recipient_list = [cp.email for cp in nearest_contacts if cp.email]

#         if recipient_list:
#             send_mail(subject, message, 'codewithme.noworries@gmail.com', recipient_list)

#         # Prepare call numbers
#         call_numbers = [cp.phone for cp in nearest_contacts if cp.phone]

#         return Response({
#             "message": "SOS sent successfully",
#             "notified_emails": recipient_list,
#             "call_numbers": call_numbers,
#         }, status=status.HTTP_200_OK)

#     except Exception as e:
#         return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)






@api_view(['GET'])
@permission_classes([IsAuthenticated])
def recommended_treks_api(request):
    profile = request.user.profile
    print(f"Fetching recommendations for user: {profile.user.username} with interests: {profile.interests}")
    recommended = recommend_treks(profile)
    serializer = TrekSerializer(recommended, many=True)
    return Response(serializer.data)


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

            try:
                profile = UserProfile.objects.get(user=user)
                profile_data = UserProfileSerializer(profile).data
                
                # Send login notification email
                self.send_login_notification(user, profile)
                
            except UserProfile.DoesNotExist:
                profile_data = {}

            return Response({
                'token': token.key,
                'user': profile_data,
                'message': 'Login successful, notification sent'
            }, status=status.HTTP_200_OK)

        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
    
    def send_login_notification(self, user, profile):
        """Send email notification on successful login"""
        try:
            subject = "Login Alert - Trek Nepal App"
            message = (
                f"Hello,\n\n"
                f"User {profile.display_name or user.username} has successfully logged into Trek Nepal app.\n"
                f"Login time: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"Username: {user.username}\n\n"
                f"Trek Nepal Team"
            )

            print("sending email to")

            # Send email notification
            send_mail(
                subject=subject,
                message=message,
                from_email='codewithme.noworries@gmail.com',
                recipient_list=['sudeepkarki74@gmail.com'],
                fail_silently=True,  # Don't fail login if email fails
            )

            print(send_mail(
                subject=subject,
                message=message,
                from_email='codewithme.noworries@gmail.com',
                recipient_list=['sudeepkarki74@gmail.com'],
                fail_silently=True,  # Don't fail login if email fai
            ))
            
        except Exception as e:
            # Log the error but don't fail the login
            print(f"Failed to send login notification: {str(e)}")


# --- USER PROFILE ---
class UserProfileListCreateView(generics.ListCreateAPIView):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer


class UserProfileDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
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
    serializer_class = TimsApplicationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Check if user is authenticated and has a profile
        if self.request.user.is_authenticated:
            try:
                return TimsApplication.objects.filter(user=self.request.user.profile)
            except AttributeError:
                # User doesn't have a profile yet
                return TimsApplication.objects.none()
        return TimsApplication.objects.none()

    def perform_create(self, serializer):
        # Ensure user has a profile
        if self.request.user.is_authenticated:
            try:
                user_profile = self.request.user.profile
            except AttributeError:
                # Create profile if it doesn't exist
                from .models import UserProfile
                user_profile = UserProfile.objects.create(
                    user=self.request.user,
                    display_name=self.request.user.username
                )
            serializer.save(user=user_profile)
        else:
            raise PermissionError("Authentication required")

class TimsApplicationDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TimsApplicationSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        return TimsApplication.objects.filter(user=self.request.user.profile)

class PostListCreateView(generics.ListCreateAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer


class PostDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer



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
    serializer_class = FavoriteSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user.profile)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user.profile)


class FavoriteDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = FavoriteSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user.profile)


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


@api_view(['POST'])
def test_qr_generation(request):
    """Test endpoint for QR code generation"""
    try:
        from .utils import columnar_encrypt, generate_qr_and_upload
        
        test_text = request.data.get('text', 'TIMS-2025-000001')
        
        # Encrypt the text
        encrypted_data = columnar_encrypt(test_text)
        print(f"Test - Original text: {test_text}")
        print(f"Test - Encrypted data: {encrypted_data}")
        
        # Generate QR code and upload
        cloudinary_url = f"https://api.cloudinary.com/v1_1/ddykuhurr/image/upload"
        qr_url = generate_qr_and_upload(
            encrypted_data,
            cloudinary_url,
            'finalProject'
        )
        
        return Response({
            "success": True,
            "original_text": test_text,
            "encrypted_data": encrypted_data,
            "qr_url": qr_url
        })
        
    except Exception as e:
        return Response({
            "success": False,
            "error": str(e)
        }, status=400)


# --- SOS ALERT ---
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_sos_alert(request):
    try:
        user_lat = float(request.data.get('latitude'))
        user_lon = float(request.data.get('longitude'))
        selected_types = request.data.get('selected_types', [])  
        emergency_type = request.data.get('emergency_type', []) 
        description = request.data.get('description')  
        
        user_profile = request.user.profile
        user_name = user_profile.display_name or request.user.username
        
        fallback_contacts = [
            # {
            #     "name": "Nepal Police",
            #     "email": "police@helpnepal.gov.np",
            #     "phone": "100",
            #     "type": "police",
            #     "fallback": True
            # },
            # {
            #     "name": "Rescue Association", 
            #     "email": "rescue@himalayarescue.org",
            #     "phone": "+9779801234567",
            #     "type": "rescue",
            #     "fallback": True
            # },
            # {
            #     "name": "Emergency Medical Services",
            #     "email": "emergency@health.gov.np", 
            #     "phone": "102",
            #     "type": "hospital",
            #     "fallback": True
            # },
            {
                "name": "Local Guide",
                "email": "sudeepkarki2022@gmail.com",   
                "phone": "+9779801234567",
                "type": "police",
                "fallback": True
            },
            {
                "name": "Emergency Medical Services",
                "email": "nepalihoni226@gmail.com   ", 
                "phone": "102",
                "type": "hospital",
                "fallback": True
            },
        ]
        
        # Search Google Places for each selected type
        all_nearby_places = []  
        contacted_services = []
        
        for place_type in selected_types:
            nearby_places = google_places_service.search_nearby_places(
                user_lat, user_lon, place_type
            )
            all_nearby_places.extend(nearby_places)
            
            # Add places with contact info to contacted services
            for place in nearby_places:
                if place.get('phone') or place.get('email'):
                    contacted_services.append({
                        'name': place['name'],
                        'phone': place.get('phone', ''),
                        'email': place.get('email', ''),
                        'type': place_type,
                        'distance_km': place['distance_km'],
                        'source': 'google_places'
                    })
        
        # Add fallback contacts for types that didn't find enough nearby places
        for contact in fallback_contacts:
            if contact['type'] in selected_types:
                contacted_services.append(contact)
        
        # Prepare email recipients
        recipient_emails = []
        call_numbers = []
        
        for service in contacted_services:
            if service.get('email'):
                recipient_emails.append(service['email'])
            if service.get('phone'):
                call_numbers.append({
                    'name': service['name'],
                    'phone': service['phone'],
                    'type': service.get('type', 'unknown')
                })
        
        # Create SOS Alert record
        sos_alert = SOSAlert.objects.create(
            user=user_profile,
            latitude=user_lat,
            longitude=user_lon,
            description=description,
            emergency_type=emergency_type,
            selected_types=selected_types,
            contacted_services=contacted_services,
            google_places_data=all_nearby_places,
            fallback_contacts=fallback_contacts
        )
        
        # Send emails if we have recipients
        if recipient_emails:
            subject = f"Trek help application test {user_name}"
            message = (
                f"Test SOS Alert\n\n"
                f"User: {user_name}\n"
                f"Time: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"Location: https://maps.google.com/?q={user_lat},{user_lon}\n"
                f"Coordinates: {user_lat}, {user_lon}\n"
                f"Emergency Types: {', '.join(selected_types)}\n\n"
                f"{description}\n\n"
                f"⚠️ PLEASE RESPOND IMMEDIATELY ⚠️\n\n"
                f"This is an automated emergency alert from Trek Nepal App.\n"
                f"Alert ID: {sos_alert.id}"
            )
            
            try:
                send_mail(
                    subject=subject,
                    message=message,
                    from_email='emergency@treknepal.com',
                    recipient_list=recipient_emails,
                    fail_silently=False,
                )
            except Exception as e:
                print(f"Failed to send SOS email: {e}")
        
        return Response({
            "success": True,
            "message": "SOS alert sent successfully",
            "description" : description,
            "emergency_type": emergency_type,
            "alert_id": sos_alert.id,
            "contacted_services": len(contacted_services),
            "nearby_places_found": len(all_nearby_places),
            "emails_sent_to": recipient_emails,
            "call_numbers": call_numbers,
            "location": {
                "latitude": user_lat,
                "longitude": user_lon,
                "maps_url": f"https://maps.google.com/?q={user_lat},{user_lon}"
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            "success": False,
            "error": str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_sos_alerts(request):
    """Get SOS alerts for the current user"""
    alerts = SOSAlert.objects.filter(user=request.user.profile).order_by('-created_at')
    
    alerts_data = []
    for alert in alerts:
        alerts_data.append({
            "id": alert.id,
            "latitude": alert.latitude,
            "longitude": alert.longitude,
            "selected_types": alert.selected_types,
            "description": alert.description,
            "emergency_type": alert.emergency_type,
            "contacted_services": alert.contacted_services,
            "google_places_data": alert.google_places_data,
            "fallback_contacts": alert.fallback_contacts,
            "status": alert.status,
            "created_at": alert.created_at.isoformat(),
            "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None
        })
    
    return Response(alerts_data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def resolve_sos_alert(request, alert_id):
    """Mark an SOS alert as resolved"""
    try:
        alert = SOSAlert.objects.get(id=alert_id, user=request.user.profile)
        alert.status = 'resolved'
        alert.resolved_at = timezone.now()
        alert.save()
        
        return Response({
            "success": True,
            "message": "SOS alert marked as resolved"
        })
    except SOSAlert.DoesNotExist:
        return Response({
            "error": "SOS alert not found"
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sos_alert_detail(request, alert_id):
    """Get details of a specific SOS alert for the current user"""
    try:
        alert = SOSAlert.objects.get(id=alert_id, user=request.user.profile)
        alert_data = {
            "id": alert.id,
            "latitude": alert.latitude,
            "longitude": alert.longitude,
            "description": alert.description,
            "emergency_type": alert.emergency_type,
            "selected_types": alert.selected_types,
            "contacted_services": alert.contacted_services,
            "google_places_data": alert.google_places_data,
            "fallback_contacts": alert.fallback_contacts,
            "status": alert.status,
            "created_at": alert.created_at.isoformat(),
            "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None
        }
        return Response(alert_data)
    except SOSAlert.DoesNotExist:
        return Response({"error": "SOS alert not found"}, status=status.HTTP_404_NOT_FOUND)