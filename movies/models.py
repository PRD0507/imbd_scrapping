from django.db import models

# Create your models here.

class Movie(models.Model):
    title = models.CharField(max_length=200)
    release_year = models.IntegerField()
    imdb_rating = models.FloatField(null=True, blank=True)
    directors = models.TextField()  # Stored as comma-separated values
    cast = models.TextField()  # Stored as comma-separated values
    plot_summary = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-release_year', 'title']
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['release_year']),
            models.Index(fields=['imdb_rating']),
        ]

    def __str__(self):
        return f"{self.title} ({self.release_year})"

    def get_directors_list(self):
        return [d.strip() for d in self.directors.split(',')]

    def get_cast_list(self):
        return [c.strip() for c in self.cast.split(',')]
