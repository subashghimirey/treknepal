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

# Trek Nepal API Documentation

## Authentication Endpoints

### Sign Up
```http
POST /api/auth/signup/
```
**Request Body:**
```json
{
    "username": "johndoe",
    "password": "StrongPass123",
    "email": "john@example.com",
    "display_name": "John Doe",
    "interests": ["hiking", "photography"]
}
```

### Login
```http
POST /api/auth/login/
```
**Request Body:**
```json
{
    "username": "johndoe",
    "password": "StrongPass123"
}
```

### Change Password (Authenticated)
```http
POST /api/auth/change_password/
```
**Request Body:**
```json
{
    "old_password": "CurrentPass123",
    "new_password": "NewPass123"
}
```

### Password Reset Flow

1. Request OTP
```http
POST /api/auth/forgot_password/
```
**Request Body:**
```json
{
    "email": "john@example.com"
}
```

2. Verify OTP
```http
POST /api/auth/verify_otp/
```
**Request Body:**
```json
{
    "otp": "123456"
}
```

3. Set New Password
```http
POST /api/auth/set_new_password/
```
**Request Body:**
```json
{
    "otp": "123456",
    "new_password": "NewPass123"
}
```

## Trek Management

### List All Treks
```http
GET /api/treks/
```

### Get Trek Details
```http
GET /api/treks/{id}/
```

### Get Recommended Treks
```http
GET /api/recommendations/treks/
```

## TIMS Application

### Create TIMS Application
```http
POST /api/tims/
```
**Request Body:**
```json
{
    "trek_id": 1,
    "transaction_id": "TRX123456",
    "image": "https://example.com/photo.jpg",
    "full_name": "John Doe",
    "nationality": "USA",
    "passport_number": "123456789",
    "gender": "Male",
    "date_of_birth": "1990-01-01",
    "trekker_area": "Annapurna",
    "route": "ABC Trek",
    "entry_date": "2025-07-01",
    "exit_date": "2025-07-15",
    "nepal_contact_name": "Nepal Contact",
    "nepal_organization": "Trek Org",
    "nepal_designation": "Guide",
    "nepal_mobile": "9876543210",
    "nepal_office_number": "01-4321567",
    "nepal_address": "Thamel, Kathmandu",
    "home_contact_name": "Home Contact",
    "home_city": "New York",
    "home_mobile": "123-456-7890",
    "home_office_number": "098-765-4321",
    "home_address": "123 Main St, NY",
    "transit_pass_cost": 1500.00,
    "permit_cost": 2000.00
}
```

### List User's TIMS Applications
```http
GET /api/tims/
```

## Social Features

### Posts

#### Create Post
```http
POST /api/posts/
```
**Request Body:**
```json
{
    "trek": 1,
    "content": "Amazing trek experience!",
    "images": ["https://example.com/image1.jpg"],
    "location": {
        "latitude": 27.7172,
        "longitude": 85.3240,
        "place_name": "Annapurna Base Camp"
    }
}
```

#### Like/Unlike Post
```http
POST /api/posts/{id}/like/
```

#### Report Post
```http
POST /api/posts/{id}/report/
```

### Comments

#### Add Comment
```http
POST /api/comments/
```
**Request Body:**
```json
{
    "post": 1,
    "content": "Great views!",
    "parent": null
}
```

#### Like/Unlike Comment
```http
POST /api/comments/{id}/like/
```

## User Management

### List Users (Admin Only)
```http
GET /api/users/
```

### Update User Profile
```http
PATCH /api/users/{id}/
```
**Request Body:**
```json
{
    "display_name": "New Name",
    "photo_url": "https://example.com/photo.jpg",
    "interests": ["trekking", "camping"]
}
```

## SOS Alert

### Create SOS Alert
```http
POST /api/sos/
```
**Request Body:**
```json
{
    "latitude": 27.7172,
    "longitude": 85.3240,
    "selected_types": ["hospital", "police"],
    "emergency_type": "medical",
    "description": "Need immediate medical assistance"
}
```

### List User's SOS Alerts
```http
GET /api/sos/
```

## Authentication
All endpoints except signup, login, and password reset require authentication.
Add the following header to requests:
```http
Authorization: Token your_token_here
```

## Response Format
Most endpoints return responses in this format:
```json
{
    "success": true/false,
    "message": "Success/error message",
    "data": { ... }
}
```

## Error Handling
Errors are returned with appropriate HTTP status codes and messages:
```json
{
    "success": false,
    "error": "Error description"
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

- [Subash Ghimire]
