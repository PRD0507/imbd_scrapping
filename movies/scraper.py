import logging
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from .models import Movie

logger = logging.getLogger(__name__)

class IMDbScraper:
    BASE_URL = "https://www.imdb.com"
    SEARCH_URL = f"{BASE_URL}/search/title/"
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    def __init__(self, max_pages=3):
        self.max_pages = max_pages
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(headers=self.HEADERS)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def search_movies(self, genre_or_keyword):
        """Search for movies by genre or keyword."""
        search_term = quote_plus(genre_or_keyword)
        tasks = []
        
        for page in range(1, self.max_pages + 1):
            url = f"{self.SEARCH_URL}?genres={search_term}&start={(page-1)*50+1}"
            tasks.append(self._fetch_page(url))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        movies = []
        
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Error fetching page: {str(result)}")
                continue
            movies.extend(result)
        
        return movies

    async def _fetch_page(self, url):
        """Fetch and parse a single page of search results."""
        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    logger.error(f"Failed to fetch {url}: Status {response.status}")
                    return []
                
                html = await response.text()
                return await self._parse_search_results(html)
        except Exception as e:
            logger.error(f"Error fetching {url}: {str(e)}")
            return []

    async def _parse_search_results(self, html):
        """Parse movie information from search results page."""
        soup = BeautifulSoup(html, 'lxml')
        movies = []
        
        for movie_div in soup.select('.lister-item'):
            try:
                title = movie_div.select_one('.lister-item-header a').text.strip()
                year_text = movie_div.select_one('.lister-item-year').text.strip('()')
                year = int(year_text) if year_text.isdigit() else None
                
                rating_div = movie_div.select_one('.ratings-imdb-rating')
                rating = float(rating_div['data-value']) if rating_div else None
                
                # Get movie details
                movie_url = self.BASE_URL + movie_div.select_one('.lister-item-header a')['href']
                details = await self._fetch_movie_details(movie_url)
                
                if details:
                    movie = Movie(
                        title=title,
                        release_year=year or details['year'],
                        imdb_rating=rating or details['rating'],
                        directors=details['directors'],
                        cast=details['cast'],
                        plot_summary=details['plot']
                    )
                    movies.append(movie)
            except Exception as e:
                logger.error(f"Error parsing movie: {str(e)}")
                continue
        
        return movies

    async def _fetch_movie_details(self, url):
        """Fetch detailed information for a specific movie."""
        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    return None
                
                html = await response.text()
                soup = BeautifulSoup(html, 'lxml')
                
                # Extract directors
                directors = []
                director_section = soup.select_one('h4:contains("Director")')
                if director_section:
                    directors = [a.text.strip() for a in director_section.find_next_sibling().select('a')]
                
                # Extract cast
                cast = []
                cast_section = soup.select_one('h4:contains("Stars")')
                if cast_section:
                    cast = [a.text.strip() for a in cast_section.find_next_sibling().select('a')]
                
                # Extract plot
                plot = ""
                plot_section = soup.select_one('div[data-testid="plot-xl"]')
                if plot_section:
                    plot = plot_section.text.strip()
                
                # Extract year and rating
                year = None
                year_text = soup.select_one('a[href*="releaseinfo"]')
                if year_text:
                    year = int(year_text.text.strip()[:4])
                
                rating = None
                rating_div = soup.select_one('div[data-testid="hero-rating-bar__aggregate-rating__score"]')
                if rating_div:
                    rating = float(rating_div.text.strip().split('/')[0])
                
                return {
                    'year': year,
                    'rating': rating,
                    'directors': ', '.join(directors),
                    'cast': ', '.join(cast),
                    'plot': plot
                }
        except Exception as e:
            logger.error(f"Error fetching movie details from {url}: {str(e)}")
            return None 