import os
import math
import requests
import json
import re
import json
import time
import requests
from django.conf import settings
from io import BytesIO
import base64
import qrcode

# Model candidates (override with GEMINI_MODEL if you want to pin)
DEFAULT_GEMINI_MODELS = [
    os.getenv("GEMINI_MODEL"),
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "gemini-2.0-flash",
    "gemini-1.5-flash-latest",
    "gemini-1.5-flash-001",
    "gemini-1.5-pro-latest",
    "gemini-1.0-pro",
    "gemini-pro",
]
DEFAULT_GEMINI_MODELS = [m for m in DEFAULT_GEMINI_MODELS if m]

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

def _is_retryable_status(code: int) -> bool:
    return code in (429, 500, 503)

def _is_model_not_found(text: str) -> bool:
    s = (text or "").lower()
    return ("not found" in s) or ("not supported for generatecontent" in s) or ("model is not found" in s) or ("404" in s)

def _strip_markdown_fences(text: str) -> str:
    t = str(text or "")
    t = re.sub(r"```[a-zA-Z]*\n?", "", t)
    t = t.replace("```", "")
    return t.strip()

def _parse_json_from_text(raw: str):
    t = _strip_markdown_fences(raw)
    try:
        return json.loads(t)
    except Exception:
        pass
    first = t.find("{")
    last = t.rfind("}")
    if first != -1 and last != -1 and last > first:
        candidate = t[first:last + 1]
        try:
            return json.loads(candidate)
        except Exception:
            pass
    raise ValueError(f"Gemini response not JSON: {t[:300]}")

def _extract_gemini_text(resp_json: dict):
    """
    Return (text, error_reason). error_reason is None when text is found.
    """
    if not isinstance(resp_json, dict):
        return None, "Invalid AI response format"
    pf = resp_json.get("promptFeedback") or {}
    if pf.get("blockReason"):
        return None, f"Blocked by safety (prompt): {pf.get('blockReason')}"
    candidates = resp_json.get("candidates") or []
    blocked = []
    for c in candidates:
        fr = c.get("finishReason")
        if fr and fr != "STOP":
            blocked.append(fr)
        content = c.get("content") or {}
        parts = content.get("parts")
        if isinstance(parts, list) and parts:
            texts = [p.get("text") for p in parts if isinstance(p, dict) and p.get("text")]
            if texts:
                return "\n".join(texts).strip(), None
    if blocked:
        return None, f"All candidates blocked: {', '.join(set(blocked))}"
    if not candidates:
        return None, "No candidates in AI response"
    return None, "No candidate text in AI response"

# Use only categories supported by v1/v1beta
SAFE_SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
]

def _contains_safety_settings_error(s: str) -> bool:
    s = (s or "").lower()
    return "safety_settings" in s or "safetysettings" in s or "element predicate failed" in s

# Strict JSON schema for Gemini JSON mode
GEMINI_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "is_valid": {"type": "boolean"},
        "confidence": {"type": "number"},
        "reason": {"type": "string"},
    },
    "required": ["is_valid", "confidence", "reason"],
    # removed: "additionalProperties": False  # not supported by v1beta
}

def _contains_response_schema_error(s: str) -> bool:
    s = (s or "").lower()
    return ("response_schema" in s) or ("response schema" in s) or ("unknown name" in s and "schema" in s)

def _gemini_http_call(
    model: str,
    api_ver: str,
    api_key: str,
    prompt: str,
    temperature=0.1,
    max_tokens=256,
    use_safety=True,
    force_json=False,
    schema_dict=None,
):
    """
    Direct HTTP call to Gemini generateContent.
    Supports JSON mode via responseMimeType/responseSchema when force_json=True.
    """
    url = f"https://generativelanguage.googleapis.com/{api_ver}/models/{model}:generateContent"
    body = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
        },
    }
    if use_safety:
        body["safetySettings"] = SAFE_SAFETY_SETTINGS
    if force_json:
        # JSON mode (supported on 1.5/2.x models)
        body["generationConfig"]["responseMimeType"] = "application/json"
        if schema_dict:
            body["generationConfig"]["responseSchema"] = schema_dict
    return requests.post(url, params={"key": api_key}, json=body, timeout=20)

def _gemini_generate_json(prompt: str, schema_hint: str = None, preferred_model: str = None):
    """
    Try multiple models and API versions with retries.
    Returns dict: {ok, data, error, model, api, raw_text}
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {"ok": False, "error": "GEMINI_API_KEY not set", "data": None, "model": None, "api": None, "raw_text": None}

    models = [preferred_model] + [m for m in DEFAULT_GEMINI_MODELS if m != preferred_model] if preferred_model else DEFAULT_GEMINI_MODELS
    last_err = None

    for model in models:
        for api_ver in ("v1", "v1beta"):
            for attempt in range(1, 4):
                try:
                    if attempt > 1:
                        time.sleep(min(2 ** (attempt - 1), 8))
                    # First try: JSON mode with schema
                    resp = _gemini_http_call(
                        model, api_ver, api_key, prompt,
                        temperature=0.1, max_tokens=128,
                        use_safety=True, force_json=True, schema_dict=GEMINI_JSON_SCHEMA
                    )
                    if not resp.ok:
                        short = ""
                        try:
                            jj = resp.json()
                            short = json.dumps(jj.get("error") or jj)[:300]
                        except Exception:
                            short = (resp.text or "")[:300]

                        # If response_schema not accepted, retry JSON mode without schema
                        if resp.status_code == 400 and _contains_response_schema_error(short):
                            r2 = _gemini_http_call(
                                model, api_ver, api_key, prompt,
                                temperature=0.1, max_tokens=128,
                                use_safety=True, force_json=True, schema_dict=None
                            )
                            if r2.ok:
                                resp = r2
                            else:
                                try:
                                    jj2 = r2.json()
                                    short2 = json.dumps(jj2.get("error") or jj2)[:300]
                                except Exception:
                                    short2 = (r2.text or "")[:300]
                                # Also try without safety if schema still fails
                                if r2.status_code == 400 and _contains_response_schema_error(short2):
                                    r3 = _gemini_http_call(
                                        model, api_ver, api_key, prompt,
                                        temperature=0.1, max_tokens=128,
                                        use_safety=False, force_json=True, schema_dict=None
                                    )
                                    if r3.ok:
                                        resp = r3
                                    else:
                                        try:
                                            jj3 = r3.json()
                                            short3 = json.dumps(jj3.get("error") or jj3)[:300]
                                        except Exception:
                                            short3 = (r3.text or "")[:300]
                                        last_err = f"{api_ver} error 400 (responseSchema): {short3}"
                                        break

                        # If safety settings invalid, retry once without them (still JSON mode)
                        if resp.status_code == 400 and _contains_safety_settings_error(short):
                            r2 = _gemini_http_call(
                                model, api_ver, api_key, prompt,
                                temperature=0.1, max_tokens=128,
                                use_safety=False, force_json=True, schema_dict=GEMINI_JSON_SCHEMA
                            )
                            if r2.ok:
                                resp = r2
                            else:
                                try:
                                    jj2 = r2.json()
                                    short2 = json.dumps(jj2.get("error") or jj2)[:300]
                                except Exception:
                                    short2 = (r2.text or "")[:300]
                                last_err = f"{api_ver} error 400 (safetySettings): {short2}"
                                break

                        if not resp.ok:
                            if resp.status_code == 404 or _is_model_not_found(short):
                                last_err = f"{api_ver} 404/not found for {model}: {short}"
                                break
                            if _is_retryable_status(resp.status_code) and attempt < 3:
                                last_err = f"{api_ver} retryable {resp.status_code}: {short}"
                                continue
                            last_err = f"{api_ver} error {resp.status_code}: {short}"
                            break

                    data = resp.json()
                    text, parse_reason = _extract_gemini_text(data)
                    if not text:
                        # If MAX_TOKENS, do one focused retry with higher cap and no safety
                        if parse_reason and "MAX_TOKENS" in parse_reason:
                            r3 = _gemini_http_call(
                                model, api_ver, api_key, prompt,
                                temperature=0.0, max_tokens=512,
                                use_safety=False, force_json=True, schema_dict=GEMINI_JSON_SCHEMA
                            )
                            if r3.ok:
                                j3 = r3.json()
                                t3, pr3 = _extract_gemini_text(j3)
                                if t3:
                                    try:
                                        parsed3 = _parse_json_from_text(t3)
                                        return {"ok": True, "data": parsed3, "error": None, "model": model, "api": api_ver, "raw_text": t3}
                                    except Exception as e3:
                                        # Fall through to repair path below
                                        text = t3
                                        parse_reason = None
                                else:
                                    return {"ok": False, "error": pr3 or parse_reason or "No text", "data": None, "model": model, "api": api_ver, "raw_text": None}
                        else:
                            return {"ok": False, "error": parse_reason or "No text", "data": None, "model": model, "api": api_ver, "raw_text": None}

                    # Parse JSON
                    try:
                        parsed = _parse_json_from_text(text)
                        return {"ok": True, "data": parsed, "error": None, "model": model, "api": api_ver, "raw_text": text}
                    except Exception as e:
                        if not schema_hint:
                            return {"ok": False, "error": f"Parse failed: {e}", "data": None, "model": model, "api": api_ver, "raw_text": text}
                        # One repair pass (still JSON mode)
                        repair_prompt = (
                            "The following text was intended to be valid minified JSON with the schema below, "
                            "but it may include markdown fences or be malformed. Output ONLY valid minified JSON conforming to the schema. "
                            "Do NOT include markdown fences or comments.\n\n"
                            f"Schema:\n{schema_hint}\n\nText:\n{text}"
                        )
                        r2 = _gemini_http_call(
                            model, api_ver, api_key, repair_prompt,
                            temperature=0.2, max_tokens=256,
                            use_safety=False, force_json=True, schema_dict=GEMINI_JSON_SCHEMA
                        )
                        if not r2.ok:
                            try:
                                ej = r2.json()
                                es = json.dumps(ej.get("error") or ej)[:300]
                            except Exception:
                                es = (r2.text or "")[:300]
                            return {"ok": False, "error": f"Repair HTTP {r2.status_code}: {es}", "data": None, "model": model, "api": api_ver, "raw_text": text}
                        j2 = r2.json()
                        t2, _ = _extract_gemini_text(j2)
                        try:
                            parsed2 = _parse_json_from_text(t2 or "")
                            return {"ok": True, "data": parsed2, "error": None, "model": model, "api": api_ver, "raw_text": t2}
                        except Exception as e2:
                            return {"ok": False, "error": f"Repair parse failed: {e2}", "data": None, "model": model, "api": api_ver, "raw_text": t2}

                except requests.exceptions.Timeout:
                    last_err = f"{api_ver} timeout for {model}"
                    if attempt >= 3:
                        break
                    continue
                except Exception as ex:
                    last_err = f"{api_ver} exception for {model}: {type(ex).__name__}: {ex}"
                    break

    return {"ok": False, "error": last_err or "No compatible Gemini model found", "data": None, "model": None, "api": None, "raw_text": None}

def validate_sos_with_gemini(description: str, emergency_type: str):
    """
    Returns {is_valid, confidence, reason, validation_method, model, api}
    """
    desc = (description or "").strip()
    if len(desc) < 5:
        return {
            "is_valid": False,
            "confidence": 0.0,
            "reason": "Description too short (min 5 chars)",
            "validation_method": "pre_check",
            "model": None,
            "api": None,
        }
    # Cap extremely long descriptions to avoid hitting token limits
    if len(desc) > 1000:
        desc = desc[:1000]

    schema = '{"is_valid": boolean, "confidence": number, "reason": string}'
    prompt = f"""You validate SOS alerts for a trekking safety app.

Emergency Type: {emergency_type or 'Not specified'}
Description: "{desc}"

Return ONLY minified JSON matching this schema:
{schema}

Rules:
- is_valid is true only for real emergencies (injury, illness, lost/stranded, danger, rescue).
- Mark tests/pranks/gibberish as invalid.
- confidence between 0 and 1.
- reason one short sentence."""

    res = _gemini_generate_json(prompt, schema_hint=schema, preferred_model=os.getenv("GEMINI_MODEL"))
    if res["ok"] and isinstance(res["data"], dict):
        d = res["data"]
        return {
            "is_valid": bool(d.get("is_valid", True)),
            "confidence": float(d.get("confidence", 0.5)),
            "reason": str(d.get("reason", "AI validation")),
            "validation_method": "gemini_ai",
            "model": res.get("model"),
            "api": res.get("api"),
        }
    return {
        "is_valid": True,
        "confidence": 0.5,
        "reason": res.get("error") or "AI validation unavailable",
        "validation_method": "ai_fallback",
        "model": res.get("model"),
        "api": res.get("api"),
    }

def validate_post_with_gemini(content: str, title: str = ""):
    """
    Classifies a post's text for abusive/inappropriate content.
    Returns {appropriate, confidence, reason, validation_method, model, api}
    """
    text = (content or "").strip()
    if len(text) < 3:
        return {
            "appropriate": False,
            "confidence": 0.9,
            "reason": "Content too short/meaningless",
            "validation_method": "pre_check",
            "model": None,
            "api": None,
        }
    if len(text) > 2000:
        text = text[:2000]

    schema = '{"appropriate": boolean, "confidence": number, "reason": string}'
    prompt = f"""You moderate user-generated posts. Determine if the content is appropriate.
Consider: hate speech, slurs, harassment, insults, threats, sexual content, graphic violence, profanity, doxxing.

Title: "{(title or '').strip()}"
Content: "{text}"

Respond ONLY with minified JSON matching this schema:
{schema}

Rules:
- appropriate=false for abusive/harassing/hate/sexual explicit/threatening content or excessive profanity.
- confidence in [0,1].
- reason one short sentence (no quotes from the content)."""

    res = _gemini_generate_json(prompt, schema_hint=schema, preferred_model=os.getenv("GEMINI_MODEL"))
    if res["ok"] and isinstance(res["data"], dict):
        d = res["data"]
        return {
            "appropriate": bool(d.get("appropriate", True)),
            "confidence": float(d.get("confidence", 0.5)),
            "reason": str(d.get("reason", "Moderation result")),
            "validation_method": "gemini_ai",
            "model": res.get("model"),
            "api": res.get("api"),
        }
    return {
        "appropriate": True,  # allow but low confidence on AI issues
        "confidence": 0.5,
        "reason": res.get("error") or "Moderation unavailable",
        "validation_method": "ai_fallback",
        "model": res.get("model"),
        "api": res.get("api"),
    }