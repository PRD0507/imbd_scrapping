from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, BasePermission
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import Movie
from .serializers import MovieSerializer, ScrapeRequestSerializer
from .scraper import IMDbScraper
import logging

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
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action == 'search':
            permission_classes = [IsAuthenticated, CanSearchMovies]
        else:
            permission_classes = [IsAuthenticated]
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
        operation_description="Search movies by various parameters",
        manual_parameters=[
            openapi.Parameter(
                'id',
                openapi.IN_QUERY,
                description="Search by movie ID",
                type=openapi.TYPE_INTEGER,
                required=False
            ),
            openapi.Parameter(
                'title',
                openapi.IN_QUERY,
                description="Search by movie title (partial match)",
                type=openapi.TYPE_STRING,
                required=False
            ),
            openapi.Parameter(
                'release_year',
                openapi.IN_QUERY,
                description="Filter by release year",
                type=openapi.TYPE_INTEGER,
                required=False
            ),
            openapi.Parameter(
                'min_rating',
                openapi.IN_QUERY,
                description="Minimum IMDB rating (0.0-10.0)",
                type=openapi.TYPE_NUMBER,
                required=False
            ),
            openapi.Parameter(
                'max_rating',
                openapi.IN_QUERY,
                description="Maximum IMDB rating (0.0-10.0)",
                type=openapi.TYPE_NUMBER,
                required=False
            ),
            openapi.Parameter(
                'directors',
                openapi.IN_QUERY,
                description="Search by directors (comma-separated)",
                type=openapi.TYPE_STRING,
                required=False
            ),
            openapi.Parameter(
                'cast',
                openapi.IN_QUERY,
                description="Search by cast members (comma-separated)",
                type=openapi.TYPE_STRING,
                required=False
            ),
        ],
        responses={
            200: MovieSerializer(many=True),
            400: "Invalid parameters"
        }
    )
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Search movies by various parameters."""
        queryset = Movie.objects.all()
        
        # Get all search parameters
        movie_id = request.query_params.get('id')
        title = request.query_params.get('title')
        release_year = request.query_params.get('release_year')
        min_rating = request.query_params.get('min_rating')
        max_rating = request.query_params.get('max_rating')
        directors = request.query_params.get('directors')
        cast = request.query_params.get('cast')

        # Build query
        if movie_id:
            try:
                queryset = queryset.filter(pk=int(movie_id))
            except ValueError:
                return Response(
                    {'error': 'Invalid movie ID'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        if title:
            queryset = queryset.filter(title__icontains=title)
        
        if release_year:
            try:
                year = int(release_year)
                queryset = queryset.filter(release_year=year)
            except ValueError:
                return Response(
                    {'error': 'Invalid release year'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        if min_rating:
            try:
                min_rating = float(min_rating)
                queryset = queryset.filter(imdb_rating__gte=min_rating)
            except ValueError:
                return Response(
                    {'error': 'Invalid minimum rating'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        if max_rating:
            try:
                max_rating = float(max_rating)
                queryset = queryset.filter(imdb_rating__lte=max_rating)
            except ValueError:
                return Response(
                    {'error': 'Invalid maximum rating'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        if directors:
            queryset = queryset.filter(directors__icontains=directors)
        
        if cast:
            queryset = queryset.filter(cast__icontains=cast)

        # Paginate the results
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

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
                        "error": "Search parameter required"
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
        operation_description="Delete movies by various parameters",
        manual_parameters=[
            openapi.Parameter(
                'id',
                openapi.IN_QUERY,
                description="Delete by movie ID",
                type=openapi.TYPE_INTEGER,
                required=False
            ),
            openapi.Parameter(
                'title',
                openapi.IN_QUERY,
                description="Delete by movie title (partial match)",
                type=openapi.TYPE_STRING,
                required=False
            ),
            openapi.Parameter(
                'release_year',
                openapi.IN_QUERY,
                description="Delete by release year",
                type=openapi.TYPE_INTEGER,
                required=False
            ),
            openapi.Parameter(
                'min_rating',
                openapi.IN_QUERY,
                description="Delete movies with rating >= value",
                type=openapi.TYPE_NUMBER,
                required=False
            ),
            openapi.Parameter(
                'max_rating',
                openapi.IN_QUERY,
                description="Delete movies with rating <= value",
                type=openapi.TYPE_NUMBER,
                required=False
            ),
            openapi.Parameter(
                'directors',
                openapi.IN_QUERY,
                description="Delete by directors (comma-separated)",
                type=openapi.TYPE_STRING,
                required=False
            ),
            openapi.Parameter(
                'cast',
                openapi.IN_QUERY,
                description="Delete by cast members (comma-separated)",
                type=openapi.TYPE_STRING,
                required=False
            ),
        ],
        responses={
            200: openapi.Response(
                description="Movies deleted successfully",
                examples={
                    "application/json": {
                        "deleted_count": 5,
                        "message": "Successfully deleted 5 movies"
                    }
                }
            ),
            400: "Invalid parameters",
            403: "Permission denied"
        }
    )
    @action(detail=False, methods=['delete'])
    def delete_by_params(self, request):
        """Delete movies by various parameters."""
        queryset = Movie.objects.all()
        
        # Get all search parameters
        movie_id = request.query_params.get('id')
        title = request.query_params.get('title')
        release_year = request.query_params.get('release_year')
        min_rating = request.query_params.get('min_rating')
        max_rating = request.query_params.get('max_rating')
        directors = request.query_params.get('directors')
        cast = request.query_params.get('cast')

        # Build query
        if movie_id:
            try:
                queryset = queryset.filter(pk=int(movie_id))
            except ValueError:
                return Response(
                    {'error': 'Invalid movie ID'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        if title:
            queryset = queryset.filter(title__icontains=title)
        
        if release_year:
            try:
                year = int(release_year)
                queryset = queryset.filter(release_year=year)
            except ValueError:
                return Response(
                    {'error': 'Invalid release year'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        if min_rating:
            try:
                min_rating = float(min_rating)
                queryset = queryset.filter(imdb_rating__gte=min_rating)
            except ValueError:
                return Response(
                    {'error': 'Invalid minimum rating'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        if max_rating:
            try:
                max_rating = float(max_rating)
                queryset = queryset.filter(imdb_rating__lte=max_rating)
            except ValueError:
                return Response(
                    {'error': 'Invalid maximum rating'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        if directors:
            queryset = queryset.filter(directors__icontains=directors)
        
        if cast:
            queryset = queryset.filter(cast__icontains=cast)

        # Check if any parameters were provided
        if not any([movie_id, title, release_year, min_rating, max_rating, directors, cast]):
            return Response(
                {'error': 'At least one parameter must be provided'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get the count before deletion
        count = queryset.count()
        
        # Soft delete all matching movies
        for movie in queryset:
            movie.delete(updated_by=request.user)

        return Response({
            'deleted_count': count,
            'message': f'Successfully deleted {count} movies'
        })
