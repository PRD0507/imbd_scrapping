from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Movie

class MovieModelTest(TestCase):
    def setUp(self):
        self.movie = Movie.objects.create(
            title="Test Movie",
            release_year=2024,
            imdb_rating=8.5,
            directors="John Doe, Jane Smith",
            cast="Actor 1, Actor 2",
            plot_summary="A test movie plot"
        )

    def test_movie_creation(self):
        self.assertEqual(self.movie.title, "Test Movie")
        self.assertEqual(self.movie.release_year, 2024)
        self.assertEqual(self.movie.imdb_rating, 8.5)
        self.assertEqual(self.movie.get_directors_list(), ["John Doe", "Jane Smith"])
        self.assertEqual(self.movie.get_cast_list(), ["Actor 1", "Actor 2"])

class MovieAPITest(APITestCase):
    def setUp(self):
        self.movie = Movie.objects.create(
            title="Test Movie",
            release_year=2024,
            imdb_rating=8.5,
            directors="John Doe",
            cast="Actor 1",
            plot_summary="A test movie plot"
        )
        self.url = reverse('movie-list')

    def test_get_movies(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_get_movie_detail(self):
        url = reverse('movie-detail', args=[self.movie.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], "Test Movie")

    def test_scrape_endpoint(self):
        url = reverse('movie-scrape')
        data = {'genre_or_keyword': 'comedy', 'max_pages': 1}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
