# Trek Nepal API

A comprehensive trekking application backend providing trek management, TIMS permit verification, SOS alerts, and social features.

## Features 🚀

- Trek Management & Discovery
- TIMS Permit System with QR Verification
- Emergency SOS Alert System
- User Authentication & Profiles
- Social Interactions (Posts, Comments, Likes)
- Trek Favorites & Recommendations
- Admin Dashboard for TIMS Verification

## Tech Stack 💻

- Python 3.8+
- Django 5.2.2
- Django REST Framework 3.16.0
- PostgreSQL
- Google Places API

## Installation 🛠️

1. Clone the repository
```bash
git clone <your-repository-url>
cd treknepal
```

2. Create and activate virtual environment
```bash
python -m venv myenv
myenv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Configure environment variables
```bash
cp .env.example .env
# Update .env with your settings
```

5. Run migrations
```bash
python manage.py migrate
```

6. Start development server
```bash
python manage.py runserver
```

## API Documentation 📚

### Authentication Endpoints

```http
POST /api/auth/signup/
POST /api/auth/login/
```

### Trek Management

```http
GET /api/treks/
POST /api/treks/
GET /api/treks/{id}/
PUT /api/treks/{id}/
DELETE /api/treks/{id}/
```

### TIMS Applications

```http
GET /api/tims/
POST /api/tims/
GET /api/tims/{id}/
PATCH /api/tims/{id}/
DELETE /api/tims/{id}/
```

### SOS Alerts

```http
GET /api/sos/
POST /api/sos/
GET /api/sos/{id}/
PATCH /api/sos/{id}/
```

### Social Features

```http
# Posts
GET /api/posts/
POST /api/posts/

# Comments
GET /api/comments/
POST /api/comments/

# Likes
GET /api/likes/
POST /api/likes/
```

### QR Verification

```http
POST /api/verify/verify-qr/
GET /api/verify/check-role/
```

## Data Models 📊

### UserProfile
- User authentication and profile data
- Role-based access (user, admin, superadmin)
- Interest tracking for recommendations

### Trek
- Trek details (difficulty, duration, elevation)
- Location and route information
- Seasonal recommendations
- Itinerary and packing lists

### TimsApplication
- TIMS permit management
- Status tracking
- QR code integration

### SOSAlert
- Emergency alert system
- Location tracking
- Service contact management

## Environment Variables 🔐

```env
SECRET_KEY=your_secret_key
DEBUG=True
DATABASE_URL=your_database_url
GOOGLE_PLACES_API_KEY=your_api_key
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your_email
EMAIL_HOST_PASSWORD=your_app_password
```

## API Authentication 🔑

Use Token Authentication:
```http
Authorization: Token your_token_here
```

## Example Requests 📝

### Create TIMS Application
```json
POST /api/tims/
{
    "full_name": "John Doe",
    "nationality": "USA",
    "passport_number": "123456789",
    "gender": "male",
    "trekker_area": "Annapurna",
    "route": "ABC Trek"
}
```

### Send SOS Alert
```json
POST /api/sos/
{
    "latitude": 27.7172,
    "longitude": 85.3240,
    "selected_types": ["hospital", "police"],
    "emergency_type": ["medical"],
    "description": "Medical emergency"
}
```

## Response Formats 📨

Success Response:
```json
{
    "success": true,
    "data": {},
    "message": "Operation successful"
}
```

Error Response:
```json
{
    "success": false,
    "error": "Error message",
    "details": {}
}
```

## Contributing 🤝

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License 📄

[MIT License](LICENSE)

## Support 💬

For support, email contact@treknepal.com or join our Slack channel.

## Authors ✨

- [Your Name]
- [Team Members]