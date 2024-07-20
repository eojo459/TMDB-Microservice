from ninja import NinjaAPI
from backendApi.utils.backend_auth import SupabaseTokenAuthentication
from user.api import router as users_router
from backendApi.api import router as backend_router
from movies.api import router as movies_router
from tvshows.api import router as tvshow_router
from genres.api import router as genres_router
from people.api import router as people_router
from trailers.api import router as trailers_router
from reviews.api import router as reviews_router

api = NinjaAPI() # no auth
#api = NinjaAPI(auth=SupabaseTokenAuthentication()) # global auth

# api routers
api.add_router("/", backend_router)
api.add_router("/users/", users_router)
api.add_router("/movies/", movies_router)
api.add_router("/tvshows/", tvshow_router)
api.add_router("/genres/", genres_router)
api.add_router("/reviews/", reviews_router)
api.add_router("/trailers/", trailers_router)
api.add_router("/people/", people_router)