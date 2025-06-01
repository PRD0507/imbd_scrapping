from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, BasePermission
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import Movie
from .serializers import (
    MovieSerializer,
    ScrapeRequestSerializer,
    MovieSearchInputSerializer,
    MovieSearchOutputSerializer,
)
from .scraper import IMDbScraper
from .permissions import IsAdminOrReadOnly
import logging
from django.db.models import Q

logger = logging.getLogger(__name__)


class CanSearchMovies(BasePermission):
    """
    Custom permission to only allow users with movies_search permission to use search.
    """
    def has_permission(self, request, view):
        return request.user and request.user.has_perm('movies.movies_search')


class MovieViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet
):
    """
    ViewSet for viewing and editing movies.
    """
    serializer_class = MovieSerializer
    queryset = Movie.objects.all()
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action == 'search':
            permission_classes = [IsAuthenticated, CanSearchMovies]
        else:
            permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """
        Returns all active movies.
        """
        return Movie.objects.all()

    def perform_update(self, serializer):
        """
        Update a movie and set the updated_by field.
        """
        if hasattr(self.request, 'user') and self.request.user.is_authenticated:
            serializer.save(updated_by=self.request.user)
        else:
            serializer.save()

    @swagger_auto_schema(
        operation_description="List all movies with pagination",
        manual_parameters=[
            openapi.Parameter(
                'page',
                openapi.IN_QUERY,
                description="Page number for pagination",
                type=openapi.TYPE_INTEGER,
                default=1
            ),
            openapi.Parameter(
                'page_size',
                openapi.IN_QUERY,
                description="Number of items per page",
                type=openapi.TYPE_INTEGER,
                default=10
            )
        ],
        responses={
            200: openapi.Response(
                description="Paginated list of movies",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'count': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'next': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                        'previous': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                        'results': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Items(type=openapi.TYPE_OBJECT)
                        )
                    }
                )
            ),
            401: "Authentication credentials were not provided",
            403: "You do not have permission to perform this action"
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Create a new movie",
        request_body=MovieSerializer,
        responses={
            201: MovieSerializer,
            400: "Bad Request",
            401: "Unauthorized"
        }
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Update a movie",
        request_body=MovieSerializer,
        responses={
            200: MovieSerializer,
            400: "Bad Request",
            401: "Unauthorized",
            404: "Not Found"
        }
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Partially update a movie",
        request_body=MovieSerializer,
        responses={
            200: MovieSerializer,
            400: "Bad Request",
            401: "Unauthorized",
            404: "Not Found"
        }
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Search movies by various parameters",
        query_serializer=MovieSearchInputSerializer(),
        responses={
            200: MovieSearchOutputSerializer(many=True),
            400: "Invalid parameters",
            401: "Unauthorized",
            403: "Permission denied"
        }
    )
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Search movies by various parameters."""
        # Validate input using the serializer
        input_serializer = MovieSearchInputSerializer(data=request.query_params)
        if not input_serializer.is_valid():
            return Response(
                input_serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )       

        # Get validated data
        validated_data = input_serializer.validated_data
        queryset = Movie.objects.all()

        # Build query using validated data
        if validated_data.get('id'):
            queryset = queryset.filter(pk=validated_data['id'])

        if validated_data.get('title'):
            queryset = queryset.filter(title__icontains=validated_data['title'])

        if validated_data.get('release_year'):
            queryset = queryset.filter(release_year=validated_data['release_year'])

        if validated_data.get('min_rating'):
            queryset = queryset.filter(imdb_rating__gte=validated_data['min_rating'])

        if validated_data.get('max_rating'):
            queryset = queryset.filter(imdb_rating__lte=validated_data['max_rating'])

        if validated_data.get('directors'):
            queryset = queryset.filter(directors__icontains=validated_data['directors'])

        if validated_data.get('cast'):
            queryset = queryset.filter(cast__icontains=validated_data['cast'])

        # Paginate the results
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = MovieSearchOutputSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = MovieSearchOutputSerializer(queryset, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Scrape movies from IMDB by genre or keyword",
        request_body=ScrapeRequestSerializer,
        responses={
            201: MovieSerializer(many=True),
            400: "Bad Request",
            401: "Unauthorized",
            500: "Internal Server Error"
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
        operation_description="Delete movies by parameters",
        request_body=MovieSearchInputSerializer,
        responses={
            200: openapi.Response(
                description="Movies deleted successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'deleted_count': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'message': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            400: "Invalid parameters",
            401: "Unauthorized",
            403: "Permission denied"
        }
    )
    @action(detail=False, methods=['post'])
    def delete_by_params(self, request):
        """Delete movies by parameters."""
        serializer = MovieSearchInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        filters = serializer.validated_data
        query = Q()

        if filters.get("title"):
            query &= Q(title__icontains=filters["title"])
        if filters.get("release_year"):
            query &= Q(release_year=filters["release_year"])
        if filters.get("min_rating"):
            query &= Q(imdb_rating__gte=filters["min_rating"])
        if filters.get("max_rating"):
            query &= Q(imdb_rating__lte=filters["max_rating"])
        if filters.get("directors"):
            query &= Q(directors__icontains=filters["directors"])
        if filters.get("cast"):
            query &= Q(cast__icontains=filters["cast"])

        deleted_count, _ = Movie.objects.filter(query).delete()
        return Response(
            {"message": f"Successfully deleted {deleted_count} movies"},
            status=status.HTTP_200_OK,
        )
