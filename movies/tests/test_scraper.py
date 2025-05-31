import pytest
from unittest.mock import Mock, patch
from movies.scraper import IMDbScraper
from movies.models import Movie


@pytest.fixture
def mock_response():
    """Fixture to create a mock response with sample HTML."""
    html = """
    <div class="dli-parent">
        <div class="ipc-title-link-wrapper">
            <h3 class="ipc-title__text">1. The Shawshank Redemption</h3>
        </div>
        <div class="dli-title-metadata-item">1994</div>
        <div class="ipc-rating-star">
            <span class="ipc-rating-star__rating">9.3</span>
        </div>
        <a class="ipc-title-link-wrapper" href="/title/tt0111161/"></a>
    </div>
    """
    mock = Mock()
    mock.text = html
    mock.status_code = 200
    return mock


@pytest.fixture
def scraper():
    """Fixture to create an IMDbScraper instance."""
    return IMDbScraper(max_pages=1)


def test_scraper_initialization(scraper):
    """Test scraper initialization with default parameters."""
    assert scraper.max_pages == 1
    assert scraper.session is not None
    assert scraper.session.headers['User-Agent'] is not None


def test_search_movies_with_title(scraper, mock_response):
    """Test searching movies by title."""
    with patch('requests.Session.get', return_value=mock_response):
        movies = scraper.search_movies(filters={'title': 'Shawshank'})
        assert len(movies) > 0
        assert isinstance(movies[0], Movie)
        assert 'Shawshank' in movies[0].title
        assert movies[0].release_year == 1994


def test_search_movies_with_genre(scraper, mock_response):
    """Test searching movies by genre."""
    with patch('requests.Session.get', return_value=mock_response):
        movies = scraper.search_movies(genre_or_keyword='drama')
        assert len(movies) > 0
        assert isinstance(movies[0], Movie)


def test_parse_search_results(scraper, mock_response):
    """Test parsing search results from HTML."""
    movies = scraper._parse_search_results(mock_response.text, 1)
    assert len(movies) > 0
    movie = movies[0]
    assert movie.title == 'The Shawshank Redemption'
    assert movie.release_year == 1994
    assert movie.imdb_rating == 9.3
    assert movie.imdb_url == 'https://www.imdb.com/title/tt0111161/'


def test_apply_filters(scraper):
    """Test applying filters to movie list."""
    movies = [
        Movie(
            title='The Shawshank Redemption',
            release_year=1994,
            imdb_rating=9.3,
            directors='Frank Darabont',
            cast='Tim Robbins, Morgan Freeman',
            imdb_url='https://example.com/1'
        ),
        Movie(
            title='The Godfather',
            release_year=1972,
            imdb_rating=9.2,
            directors='Francis Ford Coppola',
            cast='Marlon Brando, Al Pacino',
            imdb_url='https://example.com/2'
        )
    ]
    
    # Mock _fetch_movie_details to avoid real HTTP requests
    def mock_details(url, title):
        if 'Shawshank' in title:
            return {
                'directors': 'Frank Darabont',
                'cast': 'Tim Robbins, Morgan Freeman',
                'plot': 'Two imprisoned men bond over a number of years.'
            }
        elif 'Godfather' in title:
            return {
                'directors': 'Francis Ford Coppola',
                'cast': 'Marlon Brando, Al Pacino',
                'plot': 'The aging patriarch of an organized crime dynasty transfers control.'
            }
        return {}
    
    with patch.object(scraper, '_fetch_movie_details', side_effect=mock_details):
        # Test title filter
        filtered = scraper._apply_filters(movies, {'title': 'Shawshank', 'include_plot': True})
        assert len(filtered) == 1
        assert filtered[0].title == 'The Shawshank Redemption'
        assert filtered[0].plot_summary == 'Two imprisoned men bond over a number of years.'
        
        # Test year filter
        filtered = scraper._apply_filters(movies, {'release_year': 1972, 'include_plot': True})
        assert len(filtered) == 1
        assert filtered[0].title == 'The Godfather'
        assert filtered[0].plot_summary == 'The aging patriarch of an organized crime dynasty transfers control.'
        
        # Test rating filter
        filtered = scraper._apply_filters(movies, {'min_rating': 9.3, 'include_plot': True})
        assert len(filtered) == 1
        assert filtered[0].title == 'The Shawshank Redemption'
        assert filtered[0].plot_summary == 'Two imprisoned men bond over a number of years.'
        
        # Test directors filter
        filtered = scraper._apply_filters(movies, {'directors': 'Francis Ford Coppola', 'include_plot': True})
        assert len(filtered) == 1
        assert filtered[0].title == 'The Godfather'
        assert filtered[0].plot_summary == 'The aging patriarch of an organized crime dynasty transfers control.'
        
        # Test cast filter
        filtered = scraper._apply_filters(movies, {'cast': 'Morgan Freeman', 'include_plot': True})
        assert len(filtered) == 1
        assert filtered[0].title == 'The Shawshank Redemption'
        assert filtered[0].plot_summary == 'Two imprisoned men bond over a number of years.'


def test_fetch_movie_details(scraper):
    """Test fetching detailed movie information."""
    mock_html = """
    <div data-testid="title-pc-principal-credit">
        <span>Director</span>
        <a>Frank Darabont</a>
    </div>
    <div data-testid="title-pc-principal-credit">
        <span>Stars</span>
        <a>Tim Robbins</a>
        <a>Morgan Freeman</a>
    </div>
    <div data-testid="plot-xl">
        Two imprisoned men bond over a number of years.
    </div>
    """
    
    with patch('requests.Session.get') as mock_get:
        mock_get.return_value.text = mock_html
        mock_get.return_value.status_code = 200
        
        details = scraper._fetch_movie_details('https://www.imdb.com/title/tt0111161/', 'The Shawshank Redemption')
        
        assert details is not None
        assert details['directors'] == 'Frank Darabont'
        assert 'Tim Robbins' in details['cast']
        assert 'Morgan Freeman' in details['cast']
        assert 'Two imprisoned men bond' in details['plot']


def test_error_handling(scraper):
    """Test error handling in scraper methods."""
    # Test network error
    with patch('requests.Session.get', side_effect=Exception('Network error')):
        movies = scraper.search_movies(filters={'title': 'Shawshank'})
        assert len(movies) == 0
    
    # Test invalid HTML
    with patch('requests.Session.get') as mock_get:
        mock_get.return_value.text = '<invalid>html'
        mock_get.return_value.status_code = 200
        movies = scraper._parse_search_results('<invalid>html', 1)
        assert len(movies) == 0


def test_context_manager(scraper):
    """Test scraper as context manager."""
    with IMDbScraper() as s:
        assert isinstance(s, IMDbScraper)
        assert s.session is not None 