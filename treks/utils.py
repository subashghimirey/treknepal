import os
import math
import requests
from django.conf import settings
from io import BytesIO
import base64
import qrcode

def columnar_encrypt(text, key="TREK"):

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

# NEW: matching decrypt for the above encrypt
def columnar_decrypt(cipher_text: str, key: str = "TREK") -> str:
    """
    Decrypt text encrypted by columnar_encrypt using the same key.
    Assumes padding with 'X' was used to fill the grid.
    """
    if not cipher_text or not key:
        return cipher_text or ""
    
    num_columns = len(key)
  
    if len(cipher_text) % num_columns != 0:
        return cipher_text
    
    num_rows = len(cipher_text) // num_columns

    # Column order used during encryption (stable sort on key)
    order = sorted(range(num_columns), key=lambda i: key[i])

    # Split ciphertext into equal columns in the sorted order
    cols = []
    idx = 0
    for _ in range(num_columns):
        cols.append(cipher_text[idx: idx + num_rows])
        idx += num_rows

    # Map columns back to their original positions
    columns_by_original_index = [""] * num_columns
    for sorted_pos, original_col_index in enumerate(order):
        columns_by_original_index[original_col_index] = cols[sorted_pos]

    # Reconstruct plaintext row-wise in original column order
    plaintext_chars = []
    for r in range(num_rows):
        for c in range(num_columns):
            plaintext_chars.append(columns_by_original_index[c][r])
    plaintext = "".join(plaintext_chars)

    # Strip padding X from the end (safe for TIMS numbers)
    return plaintext.rstrip("X")

def generate_qr_and_upload(text, upload_preset='timsqr'): 
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

class GeoapifyPlacesService:
    def __init__(self):
        self.api_key = getattr(settings, "GEOAPIFY_API_KEY", None) or os.getenv("GEOAPIFY_API_KEY")
        self.base_url = "https://api.geoapify.com/v2"

    def _distance_km(self, lat1, lon1, lat2, lon2):
        R = 6371
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat/2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2) ** 2
        return round(R * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))), 2)

    def _details(self, place_id: str) -> dict:
        if not place_id or not self.api_key:
            return {}
        try:
            r = requests.get(f"{self.base_url}/place-details", params={"id": place_id, "apiKey": self.api_key}, timeout=10)
            data = r.json() if r.ok else {}
            feat = (data.get("features") or [None])[0]
            return feat.get("properties") if feat else {}
        except Exception:
            return {}

    def search_nearby_places(self, latitude: float, longitude: float, place_type: str, radius: int = 5000) -> list:
        if not self.api_key:
            return []

        type_map = {
            "hospital": "healthcare.hospital",
            "pharmacy": "healthcare.pharmacy",
            "clinic": "healthcare.clinic",
            "police": "service.police",
            "hotel": "accommodation.hotel",
            "guest_house": "accommodation.guest_house",
            "lodge": "accommodation.lodge",
            "teahouse": "accommodation.guest_house",
            "tea_house": "accommodation.guest_house",
        }
        category = type_map.get((place_type or "").lower(), place_type or "healthcare.hospital")
        try:
            r = requests.get(
                f"{self.base_url}/places",
                params={
                    "categories": category,
                    "filter": f"circle:{longitude},{latitude},{radius}",
                    "limit": 10,
                    "apiKey": self.api_key,
                },
                timeout=12,
            )
            data = r.json() if r.ok else {}
            feats = data.get("features") or []
            items = []
            for f in feats:
                props = f.get("properties", {})
                coords = (f.get("geometry", {}).get("coordinates") or [None, None])
                lng, lat = coords[0], coords[1]
                if lat is None or lng is None:
                    continue
                dist = self._distance_km(latitude, longitude, lat, lng)
                items.append((dist, props, lat, lng))
            items.sort(key=lambda x: x[0])
            items = items[:10]

            out = []
            for i, (dist, props, lat, lng) in enumerate(items, start=1):
                details = self._details(props.get("place_id")) if i <= 5 else {}
                contact = details.get("contact", {}) if details else {}
                out.append({
                    "place_id": props.get("place_id"),
                    "name": details.get("name") or props.get("name") or "Unnamed",
                    "address": details.get("formatted") or props.get("formatted") or props.get("address_line1") or "",
                    "vicinity": props.get("address_line2") or "",
                    "rating": props.get("rating") or 0,
                    "user_ratings_total": props.get("rank") or 0,
                    "latitude": lat,
                    "longitude": lng,
                    "distance_km": dist,
                    "phone": contact.get("phone") or "",
                    "website": contact.get("website") or "",
                    "type": place_type or "",
                    "business_status": "OPERATIONAL",
                })
            return out[:5]
        except Exception:
            return []

# Backward-compatible alias
GooglePlacesService = GeoapifyPlacesService
google_places_service = GeoapifyPlacesService()