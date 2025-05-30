# IMDb Movie Scraper

A Django-based web scraper that extracts movie information from IMDb, with REST API support and data persistence.

## Features

- Search movies by genre or keyword
- Extract detailed movie information including:
  - Title
  - Release Year
  - IMDb Rating
  - Director(s)
  - Cast
  - Plot Summary
- Pagination support for multiple search result pages
- REST API endpoints for accessing scraped data
- Asynchronous scraping for better performance
- Error handling and logging
- Unit tests

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd imdb-scraper
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up the database:
```bash
python manage.py migrate
```

5. Create a superuser (optional):
```bash
python manage.py createsuperuser
```

## Usage

1. Start the development server:
```bash
python manage.py runserver
```

2. Access the API endpoints:
- API Root: http://localhost:8000/api/
- Admin Interface: http://localhost:8000/admin/

3. Run the scraper:
```bash
python manage.py scrape_movies --genre "comedy" --pages 3
```

## API Endpoints

- `GET /api/movies/` - List all movies
- `GET /api/movies/{id}/` - Get movie details
- `POST /api/movies/scrape/` - Trigger scraping for specific genre/keyword

## Running Tests

```bash
pytest
```

## Project Structure

```
imdb_scraper/
├── movies/              # Main app directory
│   ├── models.py       # Database models
│   ├── views.py        # API views
│   ├── serializers.py  # API serializers
│   ├── urls.py         # URL routing
│   └── scraper.py      # Scraping logic
├── imdb_scraper/       # Project settings
├── tests/              # Test directory
└── manage.py           # Django management script
```

## Error Handling

The scraper includes comprehensive error handling for:
- Network issues
- Invalid responses
- Rate limiting
- Missing data
- Database errors

All errors are logged with appropriate severity levels.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 