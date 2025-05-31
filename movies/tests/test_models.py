import pytest
from movies.models import Movie
from django.contrib.auth import get_user_model


@pytest.mark.django_db
def test_movie_str():
    movie = Movie(title=None, release_year=2020)
    assert str(movie) == 'Untitled (2020)'
    movie.title = 'Test Movie'
    assert str(movie) == 'Test Movie (2020)'


@pytest.mark.django_db
def test_get_directors_list():
    movie = Movie(directors=None)
    assert movie.get_directors_list() == []
    movie.directors = 'John Doe, Jane Smith'
    assert movie.get_directors_list() == ['John Doe', 'Jane Smith']


@pytest.mark.django_db
def test_get_cast_list():
    movie = Movie(cast=None)
    assert movie.get_cast_list() == []
    movie.cast = 'Actor 1, Actor 2'
    assert movie.get_cast_list() == ['Actor 1', 'Actor 2']


@pytest.mark.django_db
def test_soft_delete_and_hard_delete():
    user = get_user_model().objects.create(username='deleter')
    movie = Movie.objects.create(title='Delete Me', release_year=2021)
    movie.delete(updated_by=user)
    movie.refresh_from_db()
    assert not movie.is_active
    assert movie.updated_by == user
    # Hard delete
    movie.hard_delete()
    assert not Movie.all_objects.filter(id=movie.id).exists() 