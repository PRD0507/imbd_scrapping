from django.shortcuts import render
import asyncio
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Movie
from .serializers import MovieSerializer
from .scraper import IMDbScraper
import logging

logger = logging.getLogger(__name__)


class MovieViewSet(viewsets.ModelViewSet):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer

    @action(detail=False, methods=['post'])
    async def scrape(self, request):
        """Scrape movies based on genre or keyword."""
        genre_or_keyword = request.data.get('genre_or_keyword')
        max_pages = int(request.data.get('max_pages', 3))

        if not genre_or_keyword:
            return Response(
                {'error': 'genre_or_keyword is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            async with IMDbScraper(max_pages=max_pages) as scraper:
                movies = await scraper.search_movies(genre_or_keyword)

                # Save movies to database
                saved_movies = []
                for movie in movies:
                    try:
                        movie.save()
                        saved_movies.append(movie)
                    except Exception as e:
                        logger.error(f"Error saving movie {movie.title}: {str(e)}")
                        continue

                serializer = self.get_serializer(saved_movies, many=True)
                return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Error during scraping: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    def details(self, request, pk=None):
        """Get detailed information about a specific movie."""
        movie = get_object_or_404(Movie, pk=pk)
        serializer = self.get_serializer(movie)
        return Response(serializer.data)
