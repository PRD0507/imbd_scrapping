from django.contrib import admin
from .models import Movie

@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ('title', 'release_year', 'imdb_rating', 'created_at')
    list_filter = ('release_year', 'imdb_rating')
    search_fields = ('title', 'directors', 'cast')
    readonly_fields = ('created_at', 'updated_at')
