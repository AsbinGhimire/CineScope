
import requests

from django.conf import settings


class TMDBService:

    BASE_URL = "https://api.themoviedb.org/3"

    def __init__(self):
        self.api_key = settings.TMDB_API_KEY

        if not self.api_key:
            raise ValueError("TMDB API key is missing.")

    def get(self, endpoint, params=None):

        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"

        request_params = {
            "api_key": self.api_key,
        }

        if params:
            request_params.update(params)

        response = requests.get(
            url,
            params=request_params,
            timeout=10,
        )

        response.raise_for_status()

        return response.json()

    def get_popular_movies(self):

        return self.get("movie/popular")

    def search_movies(self, query):

        return self.get(
            "search/movie",
            params={"query": query}
        )

    def get_movie_details(self, movie_id):

        return self.get(f"movie/{movie_id}")
