from django.http import Http404
from django.shortcuts import render

from .services import TMDBError, TMDBService

CATEGORIES = [
    {"key": "popular", "label": "Popular", "icon": "trending-up"},
    {"key": "top_rated", "label": "Top Rated", "icon": "star"},
    {"key": "now_playing", "label": "Now Playing", "icon": "film"},
    {"key": "upcoming", "label": "Upcoming", "icon": "calendar"},
]


def home(request):
    query = request.GET.get("q", "").strip()
    category = request.GET.get("category", "popular").strip().lower()
    page = request.GET.get("page", "1")
    page = int(page) if page.isdigit() else 1

    valid_keys = {c["key"] for c in CATEGORIES}
    if category not in valid_keys:
        category = "popular"

    service = TMDBService()
    error = None
    data = {"results": [], "total_pages": 1, "total_results": 0}
    featured_movie = None

    try:
        if query:
            data = service.search_movies(query, page)
        elif category == "top_rated":
            data = service.get_top_rated_movies(page)
        elif category == "now_playing":
            data = service.get_now_playing_movies(page)
        elif category == "upcoming":
            data = service.get_upcoming_movies(page)
        else:
            data = service.get_popular_movies(page)

        # On the first page of browsing (without active search query),
        # pick the first movie with a backdrop as the featured hero movie.
        if not query and page == 1 and data.get("results"):
            for m in data["results"]:
                if m.get("backdrop_url"):
                    featured_movie = m
                    break
            if not featured_movie and data["results"]:
                featured_movie = data["results"][0]

    except TMDBError:
        error = "We couldn't connect to TMDB right now. Please verify your connection or try again shortly."

    total_pages = min(data.get("total_pages", 1), 500)  # TMDB caps pagination at 500
    page = min(max(page, 1), total_pages if total_pages > 0 else 1)

    # Compute numeric page numbers for pagination
    start_page = max(1, page - 2)
    end_page = min(total_pages, page + 2)
    page_numbers = list(range(start_page, end_page + 1))

    # Active category label
    category_label = next((c["label"] for c in CATEGORIES if c["key"] == category), "Popular")

    context = {
        "movies": data.get("results", []),
        "featured_movie": featured_movie,
        "query": query,
        "category": category,
        "category_label": category_label,
        "categories": CATEGORIES,
        "page": page,
        "page_numbers": page_numbers,
        "total_pages": total_pages,
        "total_results": data.get("total_results", 0),
        "has_next": page < total_pages,
        "has_prev": page > 1,
        "next_page": page + 1,
        "prev_page": page - 1,
        "error": error,
    }
    return render(request, "movies/home.html", context)


def movie_detail(request, movie_id):
    try:
        movie = TMDBService().get_movie_details(movie_id)
    except TMDBError:
        raise Http404("Movie not found.")
    return render(request, "movies/movie_detail.html", {"movie": movie})