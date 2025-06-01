from rest_framework import serializers
from .models import Movie


class MovieSerializer(serializers.ModelSerializer):
    directors_list = serializers.SerializerMethodField(
        help_text="List of directors parsed from comma-separated string"
    )
    cast_list = serializers.SerializerMethodField(
        help_text="List of cast members parsed from comma-separated string"
    )

    class Meta:
        model = Movie
        fields = [
            'id', 'title', 'release_year', 'imdb_rating',
            'directors', 'directors_list', 'cast', 'cast_list',
            'plot_summary', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
        extra_kwargs = {
            'title': {
                'help_text': 'Movie title'
            },
            'release_year': {
                'help_text': 'Year the movie was released'
            },
            'imdb_rating': {
                'help_text': 'IMDB rating (0.0-10.0)'
            },
            'directors': {
                'help_text': 'Directors as comma-separated string'
            },
            'cast': {
                'help_text': 'Cast members as comma-separated string'
            },
            'plot_summary': {
                'help_text': 'Plot summary of the movie'
            }
        }

    def get_directors_list(self, obj):
        """Return directors as a list."""
        return obj.get_directors_list()

    def get_cast_list(self, obj):
        """Return cast as a list."""
        return obj.get_cast_list()


class ScrapeRequestSerializer(serializers.Serializer):
    """Serializer for movie scraping requests."""
    genre_or_keyword = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text=(
            "Search term: genre (e.g., 'action', 'comedy') or movie title (optional)"
        )
    )
    max_pages = serializers.IntegerField(
        required=False,
        default=3,
        min_value=1,
        max_value=10,
        help_text="Number of pages to scrape from IMDB (1-10, default: 3)"
    )
    title = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=200,
        help_text="Filter by movie title (optional)"
    )
    release_year = serializers.IntegerField(
        required=False,
        min_value=1888,  # First movie year
        max_value=2024,  # Current year
        help_text="Filter by release year (optional)"
    )
    min_rating = serializers.FloatField(
        required=False,
        min_value=0.0,
        max_value=10.0,
        help_text="Minimum IMDB rating (0.0-10.0, optional)"
    )
    max_rating = serializers.FloatField(
        required=False,
        min_value=0.0,
        max_value=10.0,
        help_text="Maximum IMDB rating (0.0-10.0, optional)"
    )
    directors = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Filter by directors (comma-separated, optional)"
    )
    cast = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Filter by cast members (comma-separated, optional)"
    )
    include_plot = serializers.BooleanField(
        required=False,
        default=True,
        help_text="Whether to include plot summary in the results"
    )

    def validate(self, data):
        """Validate the combined data."""
        # Check if at least one search parameter is provided
        search_params = [
            'genre_or_keyword', 'title', 'release_year',
            'directors', 'cast'
        ]
        if not any(data.get(param) for param in search_params):
            raise serializers.ValidationError(
                "At least one search parameter must be provided: "
                "genre_or_keyword, title, release_year, directors, or cast"
            )

        # Validate rating range
        if 'min_rating' in data and 'max_rating' in data:
            if data['min_rating'] > data['max_rating']:
                raise serializers.ValidationError(
                    "min_rating cannot be greater than max_rating"
                )
        return data 