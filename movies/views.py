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
    queryset = Movie.objects.all()  # Default queryset for URL resolution
    serializer_class = MovieSerializer

    def get_queryset(self):
        # By default, only return active movies
        return Movie.objects.all()

    @action(detail=False, methods=['get'])
    def inactive(self, request):
        """Get all inactive (soft-deleted) movies."""
        queryset = Movie.all_objects.filter(is_active=False)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def perform_destroy(self, instance):
        # Override destroy to perform soft deletion
        instance.delete(updated_by=self.request.user)

    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        """Restore a soft-deleted movie."""
        movie = get_object_or_404(Movie.all_objects, pk=pk)
        if movie.is_active:
            return Response(
                {'error': 'Movie is already active'},
                status=status.HTTP_400_BAD_REQUEST
            )
        movie.is_active = True
        movie.updated_by = request.user
        movie.save()
        serializer = self.get_serializer(movie)
        return Response(serializer.data)

    @action(detail=True, methods=['delete'])
    def hard_delete(self, request, pk=None):
        """Permanently delete a movie from the database."""
        movie = get_object_or_404(Movie.all_objects, pk=pk)
        movie.hard_delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

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
                        movie.created_by = request.user
                        movie.updated_by = request.user
                        movie.save()
                        saved_movies.append(movie)
                    except Exception as e:
                        msg = f"Error saving movie {movie.title}: {str(e)}"
                        logger.error(msg)
                        continue

                serializer = self.get_serializer(saved_movies, many=True)
                return Response(
                    serializer.data,
                    status=status.HTTP_201_CREATED
                )

        except Exception as e:
            logger.error(f"Error during scraping: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    def details(self, request, pk=None):
        """Get detailed information about a specific movie."""
        movie = get_object_or_404(Movie.objects.all(), pk=pk)
        serializer = self.get_serializer(movie)
        return Response(serializer.data)
