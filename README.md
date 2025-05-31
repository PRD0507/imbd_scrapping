# IMDB Scraper

This project is a Django-based web application that scrapes movie data from IMDB and provides a RESTful API to search, filter, and manage movies.

## Project Setup

### Prerequisites
- Python 3.11 or higher
- pip (Python package manager)
- virtualenv (recommended)

### Installation Steps
1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd imbd_scrapping
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run migrations:
   ```bash
   python manage.py migrate
   ```

5. Start the development server:
   ```bash
   python manage.py runserver
   ```

## API Endpoints

### Movies API

#### GET /api/movies/
- **Description:** Lists all active movies.
- **Logic:** Uses the `MovieManager` to filter out inactive movies.

#### GET /api/movies/{id}/
- **Description:** Retrieves a specific movie by ID.
- **Logic:** Returns a 404 if the movie is not found or is inactive.

#### POST /api/movies/
- **Description:** Creates a new movie.
- **Logic:** Validates input data and saves the movie to the database.

#### PUT /api/movies/{id}/
- **Description:** Updates an existing movie.
- **Logic:** Validates input data and updates the movie in the database.

#### DELETE /api/movies/{id}/
- **Description:** Soft deletes a movie (sets `is_active` to `False`).
- **Logic:** Updates the movie's `is_active` field and sets `updated_by` to the current user.

### Scraper API

#### GET /api/scrape/
- **Description:** Triggers the IMDB scraper to fetch and store movie data.
- **Logic:** Uses the `IMDbScraper` class to search IMDB, parse results, and save movies to the database.

## Project Structure

- `movies/models.py`: Defines the `Movie` model and custom manager.
- `movies/views.py`: Contains the `MovieViewSet` for handling API requests.
- `movies/scraper.py`: Implements the `IMDbScraper` class for fetching and parsing IMDB data.
- `movies/tests/`: Contains test cases for models, views, and the scraper.

## Testing

Run tests with:
```bash
pytest
```

Check coverage with:
```bash
coverage run -m pytest
coverage report -m
```

## License

This project is licensed under the MIT License. 