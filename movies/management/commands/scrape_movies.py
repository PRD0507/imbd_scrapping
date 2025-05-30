import asyncio
from django.core.management.base import BaseCommand
from movies.scraper import IMDbScraper
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Scrape movies from IMDb based on genre or keyword'

    def add_arguments(self, parser):
        parser.add_argument('--genre', type=str, help='Genre or keyword to search for')
        parser.add_argument('--pages', type=int, default=3, help='Number of pages to scrape')

    async def handle_async(self, *args, **options):
        genre = options['genre']
        pages = options['pages']

        if not genre:
            self.stdout.write(self.style.ERROR('Please provide a genre or keyword'))
            return

        self.stdout.write(f"Starting to scrape movies for genre: {genre}")
        
        try:
            async with IMDbScraper(max_pages=pages) as scraper:
                movies = await scraper.search_movies(genre)
                
                for movie in movies:
                    try:
                        movie.save()
                        self.stdout.write(
                            self.style.SUCCESS(f"Successfully saved: {movie.title} ({movie.release_year})")
                        )
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f"Error saving movie {movie.title}: {str(e)}")
                        )
                        continue

                self.stdout.write(self.style.SUCCESS(f"Successfully scraped {len(movies)} movies"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error during scraping: {str(e)}"))

    def handle(self, *args, **options):
        asyncio.run(self.handle_async(*args, **options)) 