# DynaLinks - Dynamic Link Service

A Firebase Dynamic Links alternative - A powerful URL shortener with platform-specific redirects, analytics, and QR code generation.

## Features

- **Platform-Specific Redirects**: Automatically redirect users to different URLs based on their platform (iOS, Android, Desktop)
- **Short Link Generation**: Create short, memorable URLs with optional custom codes
- **Analytics & Tracking**: Comprehensive click analytics with device, platform, and location tracking
- **QR Code Generation**: Generate QR codes for your dynamic links
- **Expiration Support**: Set expiration dates for temporary links
- **Social Media Tags**: Meta tags support for better social media sharing
- **Rate Limiting**: Built-in rate limiting to prevent abuse
- **Caching**: Redis caching for better performance
- **REST API**: Full REST API with OpenAPI documentation

## Quick Start with Docker

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd dynalinks
   ```

2. **Start with Docker Compose**
   ```bash
   docker-compose up -d
   ```

3. **Access the application**
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

## Manual Setup

### Prerequisites
- Python 3.11+
- PostgreSQL 12+
- Redis 6+

### Installation

1. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Environment configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Database setup**
   ```bash
   # Create database
   createdb dynalinks
   
   # Create tables manually
   psql dynalinks < schema.sql
   ```

5. **Start the application**
   ```bash
   uvicorn app.main:app --reload
   ```

## Configuration

Key environment variables in `.env`:

```env
DATABASE_URL=postgresql://username:password@localhost:5432/dynalinks
REDIS_URL=redis://localhost:6379/0
BASE_DOMAIN=https://yourdomain.com
SHORT_DOMAIN=https://dl.yourdomain.com
SECRET_KEY=your-super-secret-key
```

## API Usage

### Create a Dynamic Link

```bash
curl -X POST "http://localhost:8000/api/v1/links/" \
  -H "Content-Type: application/json" \
  -d '{
    "ios_url": "https://apps.apple.com/app/myapp",
    "android_url": "https://play.google.com/store/apps/details?id=com.myapp",
    "fallback_url": "https://myapp.com",
    "title": "My Awesome App",
    "description": "Check out this awesome app!"
  }'
```

Response:
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "short_code": "abc123",
  "short_url": "https://dl.yourdomain.com/abc123",
  "ios_url": "https://apps.apple.com/app/myapp",
  "android_url": "https://play.google.com/store/apps/details?id=com.myapp",
  "fallback_url": "https://myapp.com",
  "title": "My Awesome App",
  "description": "Check out this awesome app!",
  "is_active": true,
  "created_at": "2025-01-09T10:00:00Z",
  "updated_at": "2025-01-09T10:00:00Z"
}
```

### Redirect Behavior

When someone clicks your short link:

- **iOS devices** → Redirected to `ios_url`
- **Android devices** → Redirected to `android_url`
- **Desktop/Other** → Redirected to `fallback_url` or `desktop_url` if provided
- **Missing platform URL** → Redirected to appropriate app store or fallback

### Get Analytics

```bash
curl "http://localhost:8000/api/v1/analytics/abc123"
```

Response:
```json
{
  "total_clicks": 150,
  "unique_clicks": 120,
  "clicks_by_platform": {
    "iOS": 60,
    "Android": 50,
    "Desktop": 40
  },
  "clicks_by_country": {
    "US": 80,
    "CA": 30,
    "GB": 25
  },
  "clicks_by_date": {
    "2025-01-08": 70,
    "2025-01-09": 80
  },
  "top_referrers": {
    "twitter.com": 45,
    "facebook.com": 30
  }
}
```

### Generate QR Code

```bash
curl "http://localhost:8000/api/v1/links/abc123/qr?size=300" -o qr_code.png
```

## Advanced Features

### Custom Short Codes
```bash
curl -X POST "http://localhost:8000/api/v1/links/?custom_code=myproduct" \
  -H "Content-Type: application/json" \
  -d '{"fallback_url": "https://myapp.com"}'
```

### Expiring Links
```json
{
  "fallback_url": "https://myapp.com",
  "expires_at": "2025-12-31T23:59:59Z"
}
```

### Social Media Optimization
```json
{
  "fallback_url": "https://myapp.com",
  "title": "My App",
  "description": "Amazing mobile app",
  "image_url": "https://myapp.com/image.jpg",
  "social_title": "Download My App Now!",
  "social_description": "The best app in the store",
  "social_image_url": "https://myapp.com/social.jpg"
}
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/links/` | Create dynamic link |
| GET | `/api/v1/links/` | List dynamic links |
| GET | `/api/v1/links/{short_code}` | Get specific link |
| PUT | `/api/v1/links/{short_code}` | Update link |
| DELETE | `/api/v1/links/{short_code}` | Deactivate link |
| GET | `/api/v1/links/{short_code}/qr` | Generate QR code |
| GET | `/api/v1/analytics/{short_code}` | Get analytics |
| GET | `/{short_code}` | Redirect endpoint |
| GET | `/health` | Health check |

## Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=app
```

## Production Deployment

### Docker (Recommended)

1. **Build and deploy**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

2. **Configure reverse proxy** (nginx/traefik)
   - Set up SSL certificates
   - Configure domain routing
   - Set up rate limiting

### Manual Deployment

1. **Install production dependencies**
   ```bash
   pip install gunicorn
   ```

2. **Run with Gunicorn**
   ```bash
   gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
   ```

3. **Set up systemd service** (optional)

## Security Considerations

- Use strong `SECRET_KEY` in production
- Configure CORS properly for your domains
- Set up rate limiting at reverse proxy level
- Use HTTPS for all domains
- Implement API authentication if needed
- Regular backup of PostgreSQL database
- Monitor for abuse and implement blocking

## Monitoring & Maintenance

- Monitor application logs
- Set up database backups
- Monitor Redis memory usage
- Track API response times
- Set up alerts for high error rates
- Regular security updates

## Similar to Firebase Dynamic Links

This service provides similar functionality to Firebase Dynamic Links:

✅ **Platform-specific redirects**
✅ **Analytics tracking**  
✅ **Custom domains**
✅ **Social media previews**
✅ **QR code generation**
✅ **Link expiration**
✅ **REST API**

## Contributing

1. Fork the repository
2. Create feature branch
3. Add tests for new features
4. Submit pull request

## License

MIT License - see LICENSE file for details.
