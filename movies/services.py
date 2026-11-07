import hashlib
import requests

from django.conf import settings
from django.core.cache import cache


class TMDBError(Exception):
    """Raised when the TMDB API cannot be reached or returns an error."""


class TMDBService:
    BASE_URL = "https://api.themoviedb.org/3"
    IMAGE_BASE_URL = "https://image.tmdb.org/t/p"
    CACHE_TIMEOUT = 60 * 15  # 15 minutes

    def __init__(self):
        self.api_key = settings.TMDB_API_KEY
        if not self.api_key:
            raise ValueError("TMDB API key is missing.")
        self.session = requests.Session()  # reuses connections

    def get(self, endpoint, params=None):
        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"
        request_params = {"api_key": self.api_key, **(params or {})}

        try:
            response = self.session.get(url, params=request_params, timeout=10)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise TMDBError(f"TMDB request failed: {exc}") from exc

        return response.json()

    def cached_get(self, endpoint, params=None):
        params_signature = repr(sorted((params or {}).items()))
        param_hash = hashlib.md5(params_signature.encode("utf-8")).hexdigest()
        clean_endpoint = endpoint.strip("/").replace("/", "_")
        key = f"tmdb_{clean_endpoint}_{param_hash}"

        data = cache.get(key)
        if data is None:
            data = self.get(endpoint, params)
            cache.set(key, data, self.CACHE_TIMEOUT)
        return data

    @classmethod
    def image_url(cls, path, size="w500"):
        return f"{cls.IMAGE_BASE_URL}/{size}{path}" if path else None

    def _add_posters(self, movie):
        movie["poster_url"] = self.image_url(movie.get("poster_path"))
        movie["backdrop_url"] = self.image_url(movie.get("backdrop_path"), "w1280")
        release_date = movie.get("release_date") or ""
        movie["release_year"] = release_date[:4] if len(release_date) >= 4 else ""
        return movie

    def get_popular_movies(self, page=1):
        data = self.cached_get("movie/popular", {"page": page})
        data["results"] = [self._add_posters(m) for m in data.get("results", [])]
        return data

    def get_top_rated_movies(self, page=1):
        data = self.cached_get("movie/top_rated", {"page": page})
        data["results"] = [self._add_posters(m) for m in data.get("results", [])]
        return data

    def get_now_playing_movies(self, page=1):
        data = self.cached_get("movie/now_playing", {"page": page})
        data["results"] = [self._add_posters(m) for m in data.get("results", [])]
        return data

    def get_upcoming_movies(self, page=1):
        data = self.cached_get("movie/upcoming", {"page": page})
        data["results"] = [self._add_posters(m) for m in data.get("results", [])]
        return data

    def search_movies(self, query, page=1):
        data = self.cached_get("search/movie", {"query": query, "page": page})
        data["results"] = [self._add_posters(m) for m in data.get("results", [])]
        return data

    def get_movie_details(self, movie_id):
        raw = self.cached_get(
            f"movie/{movie_id}",
            {"append_to_response": "credits,videos,recommendations"}
        )
        movie = self._add_posters(raw)

        # Format runtime
        runtime = movie.get("runtime")
        if runtime:
            hours, minutes = divmod(runtime, 60)
            movie["formatted_runtime"] = f"{hours}h {minutes}m" if hours else f"{minutes}m"
        else:
            movie["formatted_runtime"] = None

        # Format budget & revenue
        budget = movie.get("budget", 0)
        revenue = movie.get("revenue", 0)
        movie["formatted_budget"] = f"${budget:,}" if budget > 0 else "N/A"
        movie["formatted_revenue"] = f"${revenue:,}" if revenue > 0 else "N/A"

        # Find YouTube trailer
        trailer_key = None
        videos = movie.get("videos", {}).get("results", [])
        # Prefer official Trailer first
        for vid in videos:
            if vid.get("site") == "YouTube" and vid.get("type") == "Trailer" and vid.get("official"):
                trailer_key = vid.get("key")
                break
        # Fallback to any YouTube Trailer
        if not trailer_key:
            for vid in videos:
                if vid.get("site") == "YouTube" and vid.get("type") == "Trailer":
                    trailer_key = vid.get("key")
                    break
        # Fallback to any YouTube video (Teaser, Clip)
        if not trailer_key:
            for vid in videos:
                if vid.get("site") == "YouTube" and vid.get("key"):
                    trailer_key = vid.get("key")
                    break
        movie["trailer_key"] = trailer_key

        # Extract top cast
        cast = movie.get("credits", {}).get("cast", [])[:10]
        for person in cast:
            person["profile_url"] = self.image_url(person.get("profile_path"), "w185")
        movie["top_cast"] = cast

        # Extract directors & writers
        crew = movie.get("credits", {}).get("crew", [])
        movie["directors"] = [c["name"] for c in crew if c.get("job") == "Director"]
        movie["writers"] = [c["name"] for c in crew if c.get("job") in ["Screenplay", "Writer"]][:3]

        # Extract recommendations
        recommendations = movie.get("recommendations", {}).get("results", [])[:8]
        movie["top_recommendations"] = [self._add_posters(r) for r in recommendations]

        return movie
