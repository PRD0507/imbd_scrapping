import logging
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from .models import Movie
import time
import random

logger = logging.getLogger(__name__)


class IMDbScraper:
    BASE_URL = "https://www.imdb.com"
    SEARCH_URL = f"{BASE_URL}/search/title/"
    HEADERS = {
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/120.0.0.0 Safari/537.36'
        ),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }

    def __init__(self, max_pages=3):
        self.max_pages = max_pages
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            self.session.close()

    def search_movies(self, genre_or_keyword=None, filters=None):
        """
        Search for movies by genre or keyword with additional filters.
        
        Args:
            genre_or_keyword (str, optional): The search term
            filters (dict, optional): Optional filters including:
                - title (str): Filter by movie title
                - release_year (int): Filter by release year
                - min_rating (float): Minimum IMDB rating
                - max_rating (float): Maximum IMDB rating
                - directors (str): Filter by directors
                - cast (str): Filter by cast members
                - include_plot (bool): Whether to include plot summary
        """
        filters = filters or {}
        movies = []
        
        # Build base URL
        if genre_or_keyword:
            search_term = quote_plus(genre_or_keyword)
            base_url = f"{self.SEARCH_URL}?genres={search_term}"
        elif filters.get('title'):
            # If searching by title, use the title search endpoint
            search_term = quote_plus(filters['title'])
            base_url = f"{self.BASE_URL}/search/title/?title={search_term}"
        else:
            # If no genre/keyword, use advanced search
            base_url = f"{self.BASE_URL}/search/title/"
        
        # Add common parameters
        base_url += "&sort=popularity,asc&title_type=feature"
        
        logger.info(f"Searching with URL: {base_url}")
        
        for page in range(1, self.max_pages + 1):
            # Build URL with filters
            url = f"{base_url}&start={(page-1)*50+1}"
            
            # Add year filter if specified
            if filters.get('release_year'):
                url += f"&release_date={filters['release_year']}"
            
            logger.info(f"Fetching page {page} with URL: {url}")
            page_movies = self._fetch_page(url, page)
            
            # Apply additional filters
            filtered_movies = self._apply_filters(page_movies, filters)
            movies.extend(filtered_movies)
            
            # Add delay to avoid being blocked
            if page < self.max_pages:
                time.sleep(random.uniform(1, 3))
        
        logger.info(f"Total movies found: {len(movies)}")
        return movies

    def _apply_filters(self, movies, filters):
        """Apply additional filters to the movie list."""
        filtered_movies = []
        
        for movie in movies:
            # Skip if any filter doesn't match
            if not self._matches_filters(movie, filters):
                continue
                
            # Fetch detailed information if needed
            if filters.get('include_plot', True):
                details = self._fetch_movie_details(movie.imdb_url, movie.title)
                if details:
                    movie.directors = details['directors']
                    movie.cast = details['cast']
                    movie.plot_summary = details['plot']
            
            filtered_movies.append(movie)
        
        return filtered_movies

    def _matches_filters(self, movie, filters):
        """Check if a movie matches all specified filters."""
        # Title filter
        if filters.get('title'):
            if not movie.title or filters['title'].lower() not in movie.title.lower():
                return False
        
        # Release year filter
        if filters.get('release_year'):
            if movie.release_year != filters['release_year']:
                return False
        
        # Rating filters
        if movie.imdb_rating is not None:
            if filters.get('min_rating') and movie.imdb_rating < filters['min_rating']:
                return False
            if filters.get('max_rating') and movie.imdb_rating > filters['max_rating']:
                return False
        
        # Directors filter
        if filters.get('directors'):
            if not movie.directors:
                return False
            director_list = [d.strip().lower() for d in filters['directors'].split(',')]
            movie_directors = [d.strip().lower() for d in movie.directors.split(',')]
            if not any(d in movie_directors for d in director_list):
                return False
        
        # Cast filter
        if filters.get('cast'):
            if not movie.cast:
                return False
            cast_list = [c.strip().lower() for c in filters['cast'].split(',')]
            movie_cast = [c.strip().lower() for c in movie.cast.split(',')]
            if not any(c in movie_cast for c in cast_list):
                return False
        
        return True

    def _fetch_page(self, url, page_num):
        """Fetch and parse a single page of search results."""
        try:
            response = self.session.get(url)
            if response.status_code != 200:
                msg = f"Failed to fetch page {page_num}: Status {response.status_code}"
                logger.error(msg)
                return []
            
            logger.info(f"Successfully fetched page {page_num}")
            return self._parse_search_results(response.text, page_num)
        except Exception as e:
            logger.error(f"Error fetching page {page_num}: {str(e)}")
            return []

    def _parse_search_results(self, html, page_num):
        """Parse movie information from search results page."""
        soup = BeautifulSoup(html, 'lxml')
        movies = []
        
        # Use the new IMDB structure
        movie_items = soup.select('.dli-parent')
        logger.info(f"Found {len(movie_items)} movie items on page {page_num}")
        
        for movie_div in movie_items:
            try:
                # Find title using new structure
                title_elem = movie_div.select_one('.ipc-title-link-wrapper h3.ipc-title__text')
                if not title_elem:
                    title_elem = movie_div.select_one('.titleColumn a')
                if not title_elem:
                    title_elem = movie_div.select_one('h3.ipc-title__text')
                
                if not title_elem:
                    logger.warning("Could not find title element")
                    continue
                
                title = title_elem.text.strip()
                # Remove numbering (like "1. The Shawshank Redemption")
                if '. ' in title and title.split('.')[0].isdigit():
                    title = '. '.join(title.split('.')[1:]).strip()
                
                logger.info(f"Found movie: {title}")
                
                # Extract year
                year = None
                year_elem = movie_div.select_one('.dli-title-metadata-item')
                if year_elem:
                    year_text = year_elem.text.strip()
                    try:
                        year = int(year_text)
                    except (ValueError, TypeError):
                        year = None
                
                # Extract rating
                rating = None
                rating_elem = movie_div.select_one('.ipc-rating-star')
                if rating_elem:
                    rating_text = rating_elem.select_one('.ipc-rating-star__rating')
                    if rating_text:
                        try:
                            rating = float(rating_text.text.strip())
                        except (ValueError, TypeError):
                            rating = None
                
                # Get movie URL
                movie_url = None
                url_elem = movie_div.select_one('a.ipc-title-link-wrapper')
                if url_elem and 'href' in url_elem.attrs:
                    movie_url = self.BASE_URL + url_elem['href']
                    logger.info(f"Found movie URL: {movie_url}")
                
                # Create basic movie object
                if title and year:
                    movie = Movie(
                        title=title,
                        release_year=year,
                        imdb_rating=rating,
                        imdb_url=movie_url,
                        # Leave directors, cast, and plot_summary as None/empty if not found
                        directors=None,
                        cast=None,
                        plot_summary=None
                    )
                    movies.append(movie)
                    logger.info(f"Parsed movie: {title} ({year})")
                else:
                    logger.warning(f"Missing required fields for movie: {title}")
                
            except Exception as e:
                logger.error(f"Error parsing movie on page {page_num}: {str(e)}")
                continue
        
        logger.info(f"Parsed {len(movies)} movies from page {page_num}")
        return movies

    def _fetch_movie_details(self, url, title):
        """Fetch detailed information for a specific movie."""
        try:
            # Add delay to avoid being blocked
            time.sleep(random.uniform(0.5, 1.5))
            
            response = self.session.get(url)
            if response.status_code != 200:
                msg = f"Failed to fetch details for '{title}': Status {response.status_code}"
                logger.error(msg)
                return None
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Extract directors
            directors = []
            # Try new structure first
            director_section = soup.select_one('[data-testid="title-pc-principal-credit"]:has(span:contains("Director"))')
            if director_section:
                director_links = director_section.select('a')
                directors = [a.text.strip() for a in director_links]
            
            # Extract cast
            cast = []
            cast_section = soup.select_one('[data-testid="title-pc-principal-credit"]:has(span:contains("Stars"))')
            if cast_section:
                cast_links = cast_section.select('a')
                cast = [a.text.strip() for a in cast_links]
            
            # Extract plot
            plot = ""
            plot_section = soup.select_one('[data-testid="plot-xl"]')
            if plot_section:
                plot = plot_section.text.strip()
            
            # Extract year and rating from title page
            year = None
            year_elem = soup.select_one('.sc-afe43def-4')  # Updated selector for year
            if year_elem:
                year_text = year_elem.text.strip()
                try:
                    year = int(year_text)
                except (ValueError, TypeError):
                    year = None
            
            rating = None
            rating_elem = soup.select_one('[data-testid="hero-rating-bar__aggregate-rating__score"]')
            if rating_elem:
                try:
                    rating = float(rating_elem.text.strip().split('/')[0])
                except (ValueError, TypeError):
                    rating = None
            
            logger.info(f"Retrieved details for '{title}'")
            return {
                'year': year,
                'rating': rating,
                'directors': ', '.join(directors) if directors else 'Unknown',
                'cast': ', '.join(cast) if cast else 'Unknown',
                'plot': plot if plot else 'No plot summary available'
            }
        except Exception as e:
            logger.error(f"Error fetching details for '{title}': {str(e)}")
            return None 