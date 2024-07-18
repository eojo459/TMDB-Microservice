import jwt
import os
from supabase import create_client, Client
from requests import Response
from user.models import User
from decouple import config
from ninja.security import HttpBearer, APIKeyHeader

# supabase setup
supabase: Client = create_client(config('SUPABASE_URL'), config('SUPABASE_KEY'))

# authentication middleware to validate access tokens
class SupabaseTokenAuthentication(APIKeyHeader):
    param_name = "X-JWT"

    def authenticate(self, request, access_token):
        # find user who owns the access token
        user = supabase.auth.get_user(access_token)
        if user.user is not None:
            if user.user.role == 'authenticated':
                # retrieve the user object from Django database
                try:
                    return {"user": User.objects.get(uid=user.user.id), "access_token": access_token} # Return the user
                except User.DoesNotExist:
                    return 404, {"message": "User not found"}
            
        return 404, {"message": "User not found"}