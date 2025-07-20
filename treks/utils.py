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

def columnar_decrypt(cipher_text, key="TREK"):
    """Decrypt text using columnar transposition cipher"""
    try:
        num_columns = len(key)
        num_rows = len(cipher_text) // num_columns
        
        # Get column order based on key
        order = sorted(range(len(key)), key=lambda k: key[k])
        
        # Create empty grid
        grid = [['' for _ in range(num_columns)] for _ in range(num_rows)]
        
        # Fill grid column by column in the correct order
        pos = 0
        for col_index in order:
            for row in range(num_rows):
                grid[row][col_index] = cipher_text[pos]
                pos += 1
        
        # Read grid row by row to get original text
        decrypted_text = ''
        for i in range(num_rows):
            for j in range(num_columns):
                decrypted_text += grid[i][j]
        
        # Remove padding 'X' characters from the end
        decrypted_text = decrypted_text.rstrip('X')
        
        return decrypted_text
        
    except Exception as e:
        raise Exception(f"Decryption failed: {e}")

google_places_service = GooglePlacesService()