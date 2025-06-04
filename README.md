# IMDB Movie Scraper API

A Django REST API for scraping and managing movie data from IMDB. This project provides endpoints to search, scrape, and manage movie information with features like pagination, filtering, and authentication.

## Features

- 🔍 Search movies by various parameters (title, year, rating, etc.)
- 📥 Scrape movies from IMDB by genre or keyword
- 🔐 Token-based authentication
- 📄 Pagination support
- 🎯 Advanced filtering capabilities
- 📚 Swagger/OpenAPI documentation
- 🛡️ Permission-based access control
- 📊 PostgreSQL database support
- 🔄 CORS support for frontend integration

## Prerequisites

- Python 3.8+
- PostgreSQL
- pip (Python package manager)
- virtualenv (recommended)

## Project Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/imbd_scrapping.git
   cd imbd_scrapping
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure PostgreSQL**
   - Create a database named `imdb_scraper_db`
   - Create a user `imdb_user` with password `admin`
   - Or update the database settings in `imdb_scraper/settings.py`

5. **Run migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create superuser (optional)**
   ```bash
   python manage.py createsuperuser
   ```

7. **Run the development server**
   ```bash
   python manage.py runserver
   ```

## Project Structure

```
imbd_scrapping/
├── imdb_scraper/          # Main project directory
│   ├── settings.py        # Project settings
│   ├── urls.py           # Main URL configuration
│   └── wsgi.py           # WSGI configuration
├── movies/               # Movies app
│   ├── models.py         # Movie model definition
│   ├── views.py          # API views and endpoints
│   ├── serializers.py    # Data serializers
│   ├── permissions.py    # Custom permissions
│   ├── scraper.py        # IMDB scraping logic
│   └── management/       # Custom management commands
├── requirements.txt      # Project dependencies
└── manage.py            # Django management script
```

## API Endpoints

### Authentication

- `POST /api/token/` - Get authentication token
  ```bash
  curl -X POST http://localhost:8000/api/token/ \
    -H "Content-Type: application/json" \
    -d '{"username": "your_username", "password": "your_password"}'
  ```

### Movies

- `GET /api/movies/` - List all movies (paginated)
  ```bash
  curl -X GET http://localhost:8000/api/movies/ \
    -H "Authorization: Token your_token_here"
  ```

- `POST /api/movies/` - Create a new movie
  ```bash
  curl -X POST http://localhost:8000/api/movies/ \
    -H "Authorization: Token your_token_here" \
    -H "Content-Type: application/json" \
    -d '{"title": "Movie Title", "release_year": 2024}'
  ```

- `GET /api/movies/search/` - Search movies
  ```bash
  curl -X GET "http://localhost:8000/api/movies/search/?title=inception&min_rating=8.0" \
    -H "Authorization: Token your_token_here"
  ```

- `POST /api/movies/scrape/` - Scrape movies from IMDB
  ```bash
  curl -X POST http://localhost:8000/api/movies/scrape/ \
    -H "Authorization: Token your_token_here" \
    -H "Content-Type: application/json" \
    -d '{"genre_or_keyword": "action", "max_pages": 3}'
  ```

## API Documentation

Access the Swagger documentation at:
- Swagger UI: `http://localhost:8000/swagger/`
- ReDoc: `http://localhost:8000/redoc/`

## Scraping Features

The scraper supports:
- Genre-based search
- Keyword-based search
- Year filtering
- Rating filtering
- Director filtering
- Cast member filtering
- Plot summary extraction

## Permissions

- **IsAdminOrReadOnly**: Only admin users can create/update/delete movies
- **CanSearchMovies**: Custom permission for search functionality
- **IsAuthenticated**: Required for all endpoints

## Database Schema

### Movie Model
```python
class Movie(models.Model):
    title = models.CharField(max_length=200)
    release_year = models.IntegerField()
    imdb_rating = models.FloatField(null=True)
    directors = models.TextField(null=True)
    cast = models.TextField(null=True)
    plot_summary = models.TextField(null=True)
    imdb_url = models.URLField(null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
```

## Error Handling

The API includes comprehensive error handling for:
- Authentication failures
- Invalid input data
- Scraping errors
- Database operations
- Permission violations

## Logging

Logs are stored in `debug.log` with the following levels:
- INFO: General operations
- WARNING: Non-critical issues
- ERROR: Critical issues

## Testing

Run tests using:
```bash
python manage.py test
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please open an issue in the GitHub repository or contact the maintainers. 