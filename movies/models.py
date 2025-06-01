from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

# Create your models here.


class MovieManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)

    def with_inactive(self):
        return super().get_queryset()


class Movie(models.Model):
    title = models.CharField(max_length=200)
    release_year = models.IntegerField()
    imdb_rating = models.FloatField()
    directors = models.TextField()
    cast = models.TextField()
    plot_summary = models.TextField()
    imdb_url = models.URLField(max_length=500)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='movies_created'
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='movies_updated'
    )

    # Use the custom manager
    objects = MovieManager()
    # Keep a traditional manager to access all objects when needed
    all_objects = models.Manager()

    class Meta:
        ordering = ['-release_year', 'title']
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['release_year']),
            models.Index(fields=['imdb_rating']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.title} ({self.release_year})"

    def get_directors_list(self):
        if not self.directors:
            return []
        return [d.strip() for d in self.directors.split(',')]

    def get_cast_list(self):
        if not self.cast:
            return []
        return [c.strip() for c in self.cast.split(',')]

    def delete(self, using=None, keep_parents=False, updated_by=None):
        """
        Soft delete the movie by setting is_active to False
        """
        self.is_active = False
        self.updated_by = updated_by
        self.save(using=using)
