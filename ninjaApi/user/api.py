from datetime import date, datetime
from typing import List
from uuid import UUID
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from ninja import Router, Schema
from .models import User
from decouple import config
from supabase import create_client, Client

router = Router()

# setup supabase instance
supabase: Client = create_client(config("SUPABASE_URL"), config("SUPABASE_KEY"))

################
# MODEL SCHEMAS
################
class UserRegisterIn(Schema):
    username: str
    email: str
    password: str
    role: str

class UserSignIn(Schema):
    username: str
    email: str
    password: str

class PasswordUpdate(Schema):
    email: str
    password: str
    new_password: str

class UserIn(Schema):
    uid: str
    first_name: str
    last_name: str
    username: str
    email: str
    street: str
    street_2: str
    city: str
    province: str
    country: str
    country_code: str
    postal_code: str
    gender: str
    role: str
    cell_number: str
    work_number: str
    home_number: str
    pin_code: str
    password: str
    notes: str
    last_logged_in: datetime
    password_changed_at: datetime
    date_joined: date
    active: bool
    archived: bool
    confirm_email: bool
    pending_approval: bool
    date_of_birth: date

class UserOutFull(Schema):
    id: UUID
    uid: UUID
    first_name: str
    last_name: str
    username: str
    email: str
    street: str
    street_2: str
    city: str
    province: str
    country: str
    country_code: str
    postal_code: str
    gender: str
    role: str
    cell_number: str
    work_number: str
    home_number: str
    pin_code: str
    password: str
    notes: str
    last_logged_in: datetime
    password_changed_at: datetime
    date_joined: date
    active: bool
    archived: bool
    confirm_email: bool
    pending_approval: bool
    date_of_birth: date

class UserOut(Schema):
    id: UUID
    uid: UUID
    first_name: str
    last_name: str
    username: str
    email: str
    active: bool
    archived: bool
    confirm_email: bool
    role: str

################################
# API CONTROLLER METHODS
################################

# create new user
@router.post("/", auth=None)
def create_user(request, payload: UserRegisterIn):
    # create auth user in supabase
    signup_response = supabase.auth.sign_up(
        credentials={ 
            "email": payload.email, 
            "password": payload.password,
            "options": {"data": {"username": payload.username, "role": payload.role}}, 
        }
    )

    # create user in django database 
    new_user = {
        'uid': signup_response.user.id, # id from supabase is uid in django db
        'username': payload.username,
        'email': payload.email,
        'date_joined': signup_response.user.created_at,
        'role': payload.role,
    }
    user = User.objects.create(**new_user)
    return {"id": user.id}

# sign in auth user in supabase
@router.post("/login/", auth=None)
def sign_in_user(request, payload: UserSignIn):
    if payload.email is not None and payload.email != "":
        # sign in with email
        user = get_object_or_404(User, email=payload.email)
        signin_response = supabase.auth.sign_in_with_password(
            {
                "email": payload.email, 
                "password": payload.password,
            }
        )
    else:
        # sign in with username
        user = get_object_or_404(User, username=payload.username)
        signin_response = supabase.auth.sign_in_with_password(
            {
                "email": user.email, 
                "password": payload.password,
            }
        )

    # update last logged in timestamp
    user.last_logged_in = datetime.now()
    user.save()

    return {"token": signin_response.session.access_token}

# sign out auth user in supabase
@router.post("/logout/")
def sign_out_user(request):
    res = supabase.auth.sign_out()
    return res

# update/change password in auth user in supabase
@router.post("/update/password/")
def update_password(request, payload: PasswordUpdate):
    # sign in with email
    signin_response = supabase.auth.sign_in_with_password(
        {
            "email": payload.email, 
            "password": payload.password,
        }
    )

    # update password
    update_password_response = supabase.auth.update_user({ 'password': payload.new_password })

    # update password changed at timestamp
    user = get_object_or_404(User, email=payload.email)
    user.password_changed_at = datetime.now()
    user.save()

    return update_password_response

# TODO: password reset

# check if current user info/data exists
@router.get("/auth/check/")
def auth_check_users(request, username: str = None, email: str = None):
    username_count = 0
    email_count = 0

    if username is not None:
        # check if username already exists
        username_count = User.objects.filter(username=username).count()
    
    if email is not None:
        # check if email already exists
        email_count = User.objects.filter(email=email).count()

    return {'username_count': username_count, 'email_count': email_count}

# get current auth user session
@router.get("/auth/session/")
def auth_session(request):
    res = supabase.auth.get_session()
    return res

# get current auth user from the current session
@router.get("/auth/session/user/")
def auth_session_user(request):
    res = supabase.auth.get_user()
    return res

# get current auth user from the current session via jwt
@router.get("/auth/session/jwt/user/{jwt_token}")
def auth_jwt_session_user(request, jwt_token: str):
    res = supabase.auth.get_user(jwt_token)
    return res

# refresh the session 
@router.get("/auth/session/refresh/")
def auth_session_refresh(request):
    res = supabase.auth.refresh_session()
    return res

# get user by uid
@router.get("/uid/{user_uid}", response=UserOut)
def get_user_by_uid(request, user_uid: str):
    user = get_object_or_404(User, uid=user_uid)
    return user

# get user by id
@router.get("/id/{user_id}", response=UserOut)
def get_user_by_id(request, user_id: str):
    user = get_object_or_404(User, id=user_id)
    return user

# get all users
@router.get("/", response=List[UserOut])
def list_users(request):
    users_list = User.objects.all()
    return users_list

# update user by uid
@router.put("/uid/{user_uid}")
def update_user_by_uid(request, user_uid: str, payload: UserIn):
    user = get_object_or_404(User, uid=user_uid)
    for attr, value in payload.dict().items():
        setattr(user, attr, value)
    user.save()
    return {"success": True}

# update user by id
@router.put("/id/{user_id}")
def update_user_by_id(request, user_id: str, payload: UserIn):
    user = get_object_or_404(User, id=user_id)
    for attr, value in payload.dict().items():
        setattr(user, attr, value)
    user.save()
    return {"success": True}

# delete user by uid (archive and deactivate account)
@router.delete("/uid/{user_uid}")
def delete_user_by_uid(request, user_uid: str):
    user = get_object_or_404(User, uid=user_uid)
    user.active = False
    user.archived = True
    user.save()
    return {"success": True}