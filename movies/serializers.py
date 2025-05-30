from rest_framework import serializers
from .models import Movie

class MovieSerializer(serializers.ModelSerializer):
    directors_list = serializers.SerializerMethodField()
    cast_list = serializers.SerializerMethodField()

    class Meta:
        model = Movie
        fields = [
            'id', 'title', 'release_year', 'imdb_rating',
            'directors', 'directors_list', 'cast', 'cast_list',
            'plot_summary', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_directors_list(self, obj):
        return obj.get_directors_list()

    def get_cast_list(self, obj):
        return obj.get_cast_list() 