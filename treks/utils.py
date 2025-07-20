import requests
import math
from django.conf import settings
import os
import qrcode
import base64
from io import BytesIO

def columnar_encrypt(text, key="TREK"):
    # Remove any spaces from the text
    text = text.replace(" ", "")
    
    # Calculate dimensions
    num_columns = len(key)
    num_rows = math.ceil(len(text) / num_columns)
    
    # Pad text if necessary
    padding = num_rows * num_columns - len(text)
    text += 'X' * padding
    
    # Create the grid
    grid = [['' for _ in range(num_columns)] for _ in range(num_rows)]
    
    # Fill the grid
    pos = 0
    for i in range(num_rows):
        for j in range(num_columns):
            grid[i][j] = text[pos]
            pos += 1
    
    # Get column order based on key
    order = sorted(range(len(key)), key=lambda k: key[k])
    
    # Read off the columns in the correct order
    cipher_text = ''
    for col in order:
        for row in range(num_rows):
            cipher_text += grid[row][col]
    
    return cipher_text

def generate_qr_and_upload_v2(text, upload_preset='finalProject'):
    """Alternative QR generation using the same method as your register page"""
    try:
        # Create QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(text)
        qr.make(fit=True)
        
        # Create image
        qr_image = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64 (same as register page)
        buffered = BytesIO()
        qr_image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue())
        base64_img = f"data:image/png;base64,{img_str.decode()}"
        
        # Use exact same upload method as register page
        cloud_name = "ddykuhurr"
        upload_url = f"https://api.cloudinary.com/v1_1/{cloud_name}/image/upload"
        
        # Create form data exactly like register page
        import requests
        
        # Try with files parameter instead of data (like multipart form)
        files = {
            'file': (None, base64_img),
            'upload_preset': (None, upload_preset)
        }
        
        response = requests.post(upload_url, files=files)
        
        if response.ok:
            json_response = response.json()
            return json_response['secure_url']
        else:
            print(f"Upload failed: {response.status_code} - {response.text}")
            raise Exception(f"Upload failed: {response.text}")
            
    except Exception as e:
        print(f"QR generation error: {e}")
        raise
    try:
        # Create QR code
        print(f"Creating QR code for text: {text}")
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(text)
        qr.make(fit=True)
        
        # Create image
        qr_image = qr.make_image(fill_color="black", back_color="white")
        print("QR code image created successfully")
        
        # Convert to base64
        buffered = BytesIO()
        qr_image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue())
        base64_img = f"data:image/png;base64,{img_str.decode()}"
        print(f"Base64 conversion successful, length: {len(base64_img)}")
        
        # Prepare form data (similar to your register page)
        import requests
        
        formData = {
            'file': base64_img, 
            'upload_preset': upload_preset
        }
        
        print(f"Uploading to: {cloudinary_url}")
        print(f"Upload preset: {upload_preset}")
        print(f"Data keys: {list(formData.keys())}")
        
        # Use the same method as your register page
        response = requests.post(cloudinary_url, data=formData)
        
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        print(f"Response text: {response.text}")
        
        if response.ok:
            response_data = response.json()
            print(f"Upload successful: {response_data.get('secure_url')}")
            return response_data['secure_url']
        else:
            # Try to parse error response
            try:
                error_data = response.json()
                error_message = f"Cloudinary error: {error_data}"
            except:
                error_message = f"HTTP error: {response.status_code} - {response.text}"
            
            print(f"Upload failed: {error_message}")
            raise Exception(error_message)
            
    except Exception as e:
        print(f"Exception in generate_qr_and_upload: {str(e)}")
        import traceback
        traceback.print_exc()
        raise



class GooglePlacesService:

    def __init__(self):
        api = os.getenv('GOOGLE_API_KEY', None)
        self.api_key = api
        self.base_url = f'https://maps.googleapis.com/maps/api/place'
    
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