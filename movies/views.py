from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import Movie
from .serializers import MovieSerializer, ScrapeRequestSerializer
from .scraper import IMDbScraper
import logging

logger = logging.getLogger(__name__)


class MovieViewSet(viewsets.ModelViewSet):
    queryset = Movie.objects.all()  # Default queryset for URL resolution
    serializer_class = MovieSerializer

    def get_queryset(self):
        # By default, only return active movies
        return Movie.objects.all()

    @swagger_auto_schema(
        operation_description="Get all inactive (soft-deleted) movies",
        responses={200: MovieSerializer(many=True)}
    )
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

    @swagger_auto_schema(
        operation_description="Restore a soft-deleted movie",
        responses={
            200: MovieSerializer(),
            400: 'Movie is already active',
            404: 'Movie not found'
        }
    )
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

    @swagger_auto_schema(
        operation_description="Permanently delete a movie from the database",
        responses={
            204: 'Movie deleted successfully',
            404: 'Movie not found'
        }
    )
    @action(detail=True, methods=['delete'])
    def hard_delete(self, request, pk=None):
        """Permanently delete a movie from the database."""
        movie = get_object_or_404(Movie.all_objects, pk=pk)
        movie.hard_delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @swagger_auto_schema(
        operation_description="Scrape movies from IMDB by genre or keyword",
        request_body=ScrapeRequestSerializer,
        responses={
            201: openapi.Response(
                description="Movies scraped successfully",
                schema=MovieSerializer(many=True)
            ),
            400: openapi.Response(
                description="Bad request",
                examples={
                    "application/json": {
                        "error": "At least one search parameter must be provided"
                    }
                }
            ),
            500: openapi.Response(
                description="Internal server error",
                examples={
                    "application/json": {
                        "error": "Error message details"
                    }
                }
            )
        }
    )
    @action(detail=False, methods=['post'])
    def scrape(self, request):
        """Scrape movies based on genre or keyword."""
        serializer = ScrapeRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get all validated data
        validated_data = serializer.validated_data
        
        # Extract genre_or_keyword if provided
        genre_or_keyword = validated_data.get('genre_or_keyword')
        max_pages = validated_data.get('max_pages', 3)

        try:
            # Use synchronous scraper with context manager
            with IMDbScraper(max_pages=max_pages) as scraper:
                # Pass all filters to search_movies
                movies = scraper.search_movies(
                    genre_or_keyword=genre_or_keyword,
                    filters=validated_data
                )

            # Save movies to database
            saved_movies = []
            for movie in movies:
                try:
                    # Handle user assignment safely
                    if hasattr(request, 'user') and request.user.is_authenticated:
                        movie.created_by = request.user
                        movie.updated_by = request.user
                    else:
                        movie.created_by = None
                        movie.updated_by = None
                    
                    movie.save()
                    saved_movies.append(movie)
                    logger.info(f"Saved movie: {movie.title} ({movie.release_year})")
                except Exception as e:
                    msg = f"Error saving movie {movie.title}: {str(e)}"
                    logger.error(msg)
                    continue

            logger.info(f"Successfully scraped and saved {len(saved_movies)} movies")
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

    @swagger_auto_schema(
        operation_description="Get detailed information about a specific movie",
        responses={
            200: MovieSerializer(),
            404: 'Movie not found'
        }
    )
    @action(detail=True, methods=['get'])
    def details(self, request, pk=None):
        """Get detailed information about a specific movie."""
        movie = get_object_or_404(Movie.objects.all(), pk=pk)
        serializer = self.get_serializer(movie)
        return Response(serializer.data)
