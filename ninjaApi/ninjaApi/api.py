from ninja import NinjaAPI
from backendApi.utils.backend_auth import SupabaseTokenAuthentication
from user.api import router as users_router
from backendApi.api import router as backend_router

#api = NinjaAPI() # no auth
api = NinjaAPI(auth=SupabaseTokenAuthentication()) # global auth

# api routers
api.add_router("/", backend_router)
api.add_router("/users/", users_router)