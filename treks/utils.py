import requests
import math
import os
import qrcode
import base64
from io import BytesIO

def columnar_encrypt(text, key="TREK"):
    """Encrypt text using columnar transposition cipher"""
    text = text.replace(" ", "")
    
    num_columns = len(key)
    num_rows = math.ceil(len(text) / num_columns)
    
    # Pad text if necessary
    padding = num_rows * num_columns - len(text)
    text += 'X' * padding
    
    # Create grid and fill it
    grid = [['' for _ in range(num_columns)] for _ in range(num_rows)]
    pos = 0
    for i in range(num_rows):
        for j in range(num_columns):
            grid[i][j] = text[pos]
            pos += 1
    
    # Get column order based on key
    order = sorted(range(len(key)), key=lambda k: key[k])
    
    # Read columns in correct order
    cipher_text = ''
    for col in order:
        for row in range(num_rows):
            cipher_text += grid[row][col]
    
    return cipher_text

def generate_qr_and_upload(text, upload_preset='timsqr'):  # Change to 'timsqr'
    """Simple QR code generation and Cloudinary upload"""
    try:
        # Create QR code
        qr = qrcode.QRCode(
            version=1,
            box_size=10,
            border=5,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
        )
        qr.add_data(text)
        qr.make(fit=True)
        
        # Generate QR image
        qr_image = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffered = BytesIO()
        qr_image.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode()
        base64_string = f"data:image/png;base64,{img_base64}"
        
        # Upload to Cloudinary
        cloud_name = "dq8k8enle"
        upload_url = f"https://api.cloudinary.com/v1_1/{cloud_name}/image/upload"
        
        # Generate safe public_id
        import uuid
        import time
        safe_public_id = f"tims_qr_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        
        # Use the timsqr preset
        payload = {
            'file': base64_string,
            'upload_preset': 'timsqr',  # Use your new preset
            'public_id': safe_public_id,
            'resource_type': 'image'
        }
        
        response = requests.post(upload_url, data=payload)
        
        if response.status_code == 200:
            response_data = response.json()
            return response_data['secure_url']
        else:
            raise Exception(f"Upload failed: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"QR generation/upload error: {e}")
        raise e

class GooglePlacesService:
    def __init__(self):
        self.api_key = os.getenv('GOOGLE_API_KEY', None)
        self.base_url = 'https://maps.googleapis.com/maps/api/place'
        
        if not self.api_key:
            print("⚠️ WARNING: GOOGLE_API_KEY not found in environment variables!")
    
    def calculate_distance(self, lat1, lon1, lat2, lon2):
        """Calculate distance using Haversine formula"""
        R = 6371  # Earth's radius in km
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat/2) * math.sin(dlat/2) + 
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
             math.sin(dlon/2) * math.sin(dlon/2))
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return round(R * c, 2)  # Return rounded distance
    
    def get_place_details(self, place_id):
        """Get detailed information about a place"""
        if not self.api_key:
            return {}
            
        try:
            url = f"{self.base_url}/details/json"
            params = {
                'place_id': place_id,
                'fields': 'formatted_phone_number,international_phone_number,website,formatted_address,opening_hours',
                'key': self.api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if data.get('status') == 'OK' and data.get('result'):
                return data['result']
            else:
                print(f"⚠️ Place details fetch failed: {data.get('status')}")
                return {}
                
        except requests.exceptions.Timeout:
            print(f"⚠️ Timeout fetching details for place_id: {place_id}")
            return {}
        except Exception as e:
            print(f"❌ Error fetching place details: {e}")
            return {}
    
    def search_nearby_places(self, latitude, longitude, place_type, radius=5000):
        """Search for nearby places of specified type"""
        if not self.api_key:
            print("❌ Cannot search - GOOGLE_API_KEY not configured")
            return []
            
        try:
            # Map our types to Google Places types
            type_mapping = {
                'police': 'police',
                'hospital': 'hospital',
                'teahouse': 'lodging',
                'tea_house': 'lodging',
                'lodge': 'lodging',
                'rescue': 'fire_station',
                'pharmacy': 'pharmacy',
                'clinic': 'doctor'
            }
            
            google_type = type_mapping.get(place_type.lower(), place_type)
            
            url = f"{self.base_url}/nearbysearch/json"
            params = {
                'location': f"{latitude},{longitude}",
                'radius': radius,
                'type': google_type,
                'key': self.api_key
            }
            
            # Add specific keywords for teahouses
            if place_type.lower() in ['teahouse', 'tea_house']:
                params['keyword'] = 'teahouse lodge guest house hotel'
            
            print(f"🔍 Searching for {place_type} near ({latitude}, {longitude})")
            print(f"   Radius: {radius}m, Google Type: {google_type}")
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            print(f"   API Status: {data.get('status')}")
            
            if data.get('status') == 'ZERO_RESULTS':
                print(f"   ⚠️ No {place_type} found within {radius}m radius")
                return []
            
            if data.get('status') != 'OK':
                print(f"   ❌ API Error: {data.get('error_message', 'Unknown error')}")
                return []
            
            if not data.get('results'):
                print(f"   ⚠️ Empty results for {place_type}")
                return []
            
            places = []
            results = data['results'][:10]  # Get top 10 results
            
            print(f"   ✅ Found {len(results)} results, processing...")
            
            for idx, place in enumerate(results, 1):
                try:
                    place_lat = place['geometry']['location']['lat']
                    place_lng = place['geometry']['location']['lng']
                    distance = self.calculate_distance(latitude, longitude, place_lat, place_lng)
                    
                    # Basic info without details API call (faster)
                    place_info = {
                        'place_id': place['place_id'],
                        'name': place['name'],
                        'vicinity': place.get('vicinity', ''),
                        'rating': place.get('rating', 0),
                        'user_ratings_total': place.get('user_ratings_total', 0),
                        'distance_km': distance,
                        'latitude': place_lat,
                        'longitude': place_lng,
                        'phone': '',  # Will be filled if details fetched
                        'website': '',
                        'address': place.get('vicinity', ''),
                        'type': place_type,
                        'business_status': place.get('business_status', 'OPERATIONAL')
                    }
                    
                    # Only fetch details for the nearest 5 places (to save API calls)
                    if idx <= 5:
                        details = self.get_place_details(place['place_id'])
                        if details:
                            place_info['phone'] = details.get('formatted_phone_number', details.get('international_phone_number', ''))
                            place_info['website'] = details.get('website', '')
                            place_info['address'] = details.get('formatted_address', place.get('vicinity', ''))
                    
                    places.append(place_info)
                    print(f"      {idx}. {place['name']} - {distance} km")
                    
                except Exception as e:
                    print(f"      ⚠️ Error processing place {idx}: {e}")
                    continue
            
            # Sort by distance
            places.sort(key=lambda x: x['distance_km'])
            
            print(f"   📍 Returning {len(places)} places sorted by distance\n")
            print(f"   Top places: {[place['name'] for place in places[:5]]}")
            return places[:5]  # Return top 5 nearest
            
        except requests.exceptions.Timeout:
            print(f"❌ Request timeout for {place_type}")
            return []
        except Exception as e:
            print(f"❌ Error searching nearby places: {e}")
            import traceback
            traceback.print_exc()
            return []

# Initialize service
google_places_service = GooglePlacesService()