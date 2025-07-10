import requests
import math
from django.conf import settings

class GooglePlacesService:
    def __init__(self):
        self.api_key = getattr(settings, 'GOOGLE_PLACES_API_KEY', 'AIzaSyBlDSuRXF3dOV3sbCK2uQP2zyauYibjXN4')
        self.base_url = 'https://maps.googleapis.com/maps/api/place'
    
    def calculate_distance(self, lat1, lon1, lat2, lon2):
        """Calculate distance between two points using Haversine formula"""
        R = 6371  # Earth's radius in km
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat/2) * math.sin(dlat/2) + 
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
             math.sin(dlon/2) * math.sin(dlon/2))
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c
    
    def get_place_details(self, place_id):
        """Get detailed information about a place"""
        try:
            url = f"{self.base_url}/details/json"
            params = {
                'place_id': place_id,
                'fields': 'formatted_phone_number,international_phone_number,website,email,formatted_address',
                'key': self.api_key
            }
            response = requests.get(url, params=params)
            data = response.json()
            
            if data.get('status') == 'OK' and data.get('result'):
                return data['result']
            return {}
        except Exception as e:
            print(f"Error fetching place details: {e}")
            return {}
    
    def search_nearby_places(self, latitude, longitude, place_type, radius=5000):
        """Search for nearby places of specified type"""
        try:
            # Map our types to Google Places types
            type_mapping = {
                'police': 'police',
                'hospital': 'hospital',
                'teahouse': 'lodging',
                'rescue': 'fire_station'  # Best approximation for rescue services
            }
            
            google_type = type_mapping.get(place_type, place_type)
            
            url = f"{self.base_url}/nearbysearch/json"
            params = {
                'location': f"{latitude},{longitude}",
                'radius': radius,
                'type': google_type,
                'key': self.api_key
            }
            
            # For teahouse, add specific keywords
            if place_type == 'teahouse':
                params['keyword'] = 'teahouse lodge hotel'
            
            response = requests.get(url, params=params)
            data = response.json()
            
            if data.get('status') == 'OK' and data.get('results'):
                places = []
                for place in data['results'][:3]:  # Limit to 3 nearest
                    place_lat = place['geometry']['location']['lat']
                    place_lng = place['geometry']['location']['lng']
                    distance = self.calculate_distance(latitude, longitude, place_lat, place_lng)
                    
                    # Get detailed contact information
                    details = self.get_place_details(place['place_id'])
                    
                    place_info = {
                        'place_id': place['place_id'],
                        'name': place['name'],
                        'vicinity': place.get('vicinity', ''),
                        'rating': place.get('rating'),
                        'distance_km': round(distance, 2),
                        'latitude': place_lat,
                        'longitude': place_lng,
                        'phone': details.get('formatted_phone_number', ''),
                        'website': details.get('website', ''),
                        'email': details.get('email', ''),
                        'address': details.get('formatted_address', place.get('vicinity', '')),
                        'type': place_type
                    }
                    places.append(place_info)
                
                # Sort by distance
                places.sort(key=lambda x: x['distance_km'])
                return places
            
            return []
        except Exception as e:
            print(f"Error searching nearby places: {e}")
            return []

google_places_service = GooglePlacesService()