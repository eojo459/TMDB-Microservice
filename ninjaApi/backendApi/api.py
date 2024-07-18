from datetime import date, datetime, timedelta, timezone
import json
from typing import List
from urllib import response
from uuid import UUID
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from ninja import Router, Schema
from backendApi.models import Cookies, InviteCodes, OtpTokenVerify
from backendApi.utils.helper import generate_magic_token, generate_random_invite_code, set_cookies, auth_session_user
from user.models import User
from decouple import config
from supabase import create_client, Client

router = Router()

# create supabase instances
supabase: Client = create_client(config("SUPABASE_URL"), config("SUPABASE_KEY"))
supabase_admin = create_client(config("SUPABASE_URL"), config("SUPABASE_SERVICE_KEY"))

################
# MODEL SCHEMAS
################
class CookieIn(Schema):
    user_uid: UUID
    name: str
    value: str
    expires_at: datetime

class CookieOut(Schema):
    id: UUID
    user_uid: UUID
    name: str
    value: str
    expires_at: datetime

class EmailContactSupportIn(Schema):
    from_email: str
    name: str
    company: str
    subject: str
    body: str

class UserOut(Schema):
    id: str
    uid: str
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


## seeding ##
@router.get("/seeding")
def initial_seeding(request):
    return {"success": True}

# create new cookie
@router.post("/cookies/users/uid/{user_uid}")
def create_cookie(request, user_uid: str, payload: CookieIn):
    # cookie fields
    cookie_name = payload.name
    cookie_value = payload.value

    expires_at = request.data['expires_at']
    user_uid = request.data['user_uid']

    cookies = request.COOKIES

    # check if cookie already exists and is not expired
    current_time = datetime.now()
    existing_cookies = Cookies.objects.filter(user_uid=user_uid, name=cookie_name, expires_at__gt=current_time.replace(tzinfo=timezone.utc))
    if len(existing_cookies) > 0:
        for existing_cookie in existing_cookies:
            if existing_cookie.expires_at <= current_time.replace(tzinfo=timezone.utc):
                # delete old cookies
                old_cookies = Cookies.objects.filter(user_uid=user_uid, name=cookie_name)
                for cookie in old_cookies:
                    cookie.delete()

                if cookie_name == "":
                    # delete other cookies
                    cookies_to_delete_1 = Cookies.objects.filter(user_uid=user_uid, name="")
                    cookies_to_delete_2 = Cookies.objects.filter(user_uid=user_uid, name="")
                    cookies_to_delete = cookies_to_delete_1 | cookies_to_delete_2

                for cookie in cookies_to_delete:
                    cookie.delete()

    # create new cookie 
    # date_format = "%a, %d %b %Y %H:%M:%S GMT"
    # expires_at_datetime = datetime.strptime(expires_at, date_format)

    # new_cookie = {
    #     'name': cookie_name,
    #     'value': cookie_value,
    #     'user_uid': user_uid,
    #     'expires_at': expires_at_datetime,
    # }
    cookie = Cookies.objects.create(**payload.dict())
                
    return {"id": cookie.id}

# get cookies
@router.get("/cookies/users/uid/{user_uid}")
def get_cookies(request, user_uid: str, httponly: bool = False):
    # get all cookies for user
    response = HttpResponse()

    response = set_cookies(response, user_uid, httponly)

    #return JsonResponse({"success": True})
    return {"success": True}

# update exitsing cookie
@router.put("/cookies/update/users/uid/{user_uid}")
def update_cookie(request, user_uid: str, payload: CookieIn):
     # cookie fields
    cookie_name = payload.name
    user_uid = request.data['user_uid']

    # check if cookie already exists and is not expired
    current_time = datetime.now()
    existing_cookies = Cookies.objects.filter(user_uid=user_uid, name=cookie_name, expires_at__gt=current_time.replace(tzinfo=timezone.utc))
    if len(existing_cookies) > 1:
        for existing_cookie in existing_cookies:
            if existing_cookie.expires_at <= current_time.replace(tzinfo=timezone.utc):
                # delete old cookies
                old_cookies = Cookies.objects.filter(user_uid=user_uid, name=cookie_name)
                for cookie in old_cookies:
                    cookie.delete()
            
        cookie = Cookies.objects.create(**payload.dict())

    elif len(existing_cookies) == 1:
        existing_cookies[0].name = payload.name
        existing_cookies[0].value = payload.value
        existing_cookies[0].expires_at = payload.expires_at
        existing_cookies[0].save()
    else:
        cookie = Cookies.objects.create(**payload.dict())

    return {"success": True}

# delete cookie
@router.delete("/cookies/users/uid/{user_uid}")
def delete_cookie(request, cookie_name: str, user_uid: str):
    existing_cookies = Cookies.objects.filter(user_uid=user_uid, name=cookie_name)

    # delete old cookies
    for existing_cookie in existing_cookies:
        existing_cookie.delete()

    return {"success": True}

# create otp verify token
@router.get("/otp/generate/token/")
def generate_otp_token(request):
    # get user
    user_uid_str = str(request.auth['user'].uid)
    user = User.objects.get(uid=user_uid_str)

    # clean old tokens
    old_tokens = OtpTokenVerify.objects.filter(user_uid=user_uid_str)
    for old_token in old_tokens:
        old_token.delete()

    # generate a new token
    token = generate_magic_token()

    expires_at = datetime.now() + timedelta(hours=1)

    otp_verify_token = {
        'token': token,
        'user_uid': user,
        'expires_at': expires_at,
    }

    new_otp_verify_token = OtpTokenVerify.objects.create(**otp_verify_token)

    return {"id": new_otp_verify_token.id}

# validate otp token
@router.post("/otp/verify/token/{otp_token}")
def validate_otp_token(request, otp_token: str):
    # get user uid
    user_uid_str = str(request.auth['user'].uid)

    # check if token exists and belongs to this user
    existing_token = OtpTokenVerify.objects.filter(token=otp_token, user_uid=user_uid_str).first()
    if existing_token is None:
        return {"success": False}
    
    # token is valid, delete it and return true
    existing_token.delete()

    return {"success": True}

# send new contact email to support via contact us form
@router.post("/email/contact/support/", auth=None)
def send_email_contact_support(request, payload: EmailContactSupportIn):

    email_info = {
        'from_email': payload.from_email,
        'name': payload.name,
        'company': payload.company,
        'subject': payload.subject,
        'body': payload.body,
    }

    # TODO: send email to support

    return {"success": True}

# generate invite code
@router.get("/invite/generate/code/")
def generate_invite_code(request):
    # generate a new invite code
    code = generate_random_invite_code()

    #expires_at = datetime.now() + timedelta(hours=1)

    invite_code = {
        'code': code,
        'enabled': True,
        #'expires': expires_at,
        'uses': 0,
    }

    new_invite_code = InviteCodes.objects.create(**invite_code)

    return {"id": new_invite_code.id}

# validate invite code
@router.post("/invite/verify/code/{invite_code}")
def validate_invite_code(request, invite_code: str):

    # check if code exists and is enabled
    existing_code = InviteCodes.objects.filter(code=invite_code, enabled=True).first()
    if existing_code is None:
        return {"success": False}
    
    # code is valid, increment usage and return true
    existing_code.uses += 1
    existing_code.save()

    return {"success": True}


# TODO: subscriptions & billing
# chargebee new checkout url
# get chargebee checkout url
# get user subscription
# get user payment
# update subscription
# update payment
# cancel subscription
# get invoice data
# get invoice pdf
# webhook listener
# verify subscription



### EXAMPLES ###
# @router.post("/item")
# def create(request, payload: UserIn):
#     employee = User.objects.create(**payload.dict())
#     return {"id": employee.id}

# @router.get("/item/{id}", response=UserOut)
# def get_by_id(request, id: str):
#     user = get_object_or_404(User, id=id)
#     return user

# @router.get("/item", response=List[UserOut])
# def list_all(request):
#     users_list = User.objects.all()
#     return users_list

# @router.put("/item/{id}")
# def update_by_id(request, user_id: str, payload: UserIn):
#     user = get_object_or_404(User, id=id)
#     for attr, value in payload.dict().items():
#         setattr(user, attr, value)
#     user.save()
#     return {"success": True}

# @router.delete("/item/{id}")
# def delete_by_id(request, id: str):
#     user = get_object_or_404(User, id=id)
#     user.delete()
#     return {"success": True}