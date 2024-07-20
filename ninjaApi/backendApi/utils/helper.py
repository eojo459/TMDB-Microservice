# generate random invite codes to be used to join the website
from datetime import datetime, timezone
from io import BytesIO
import secrets
import string
import qrcode
from backendApi.models import Cookies, OtpTokenVerify, InviteCodes
from decouple import config
from supabase import create_client, Client

# setup supabase instance
supabase: Client = create_client(config("SUPABASE_URL"), config("SUPABASE_KEY"))

# generate random invite codes to be used to join the website
def generate_invite_code():
    while True:
        code = ''.join(secrets.choice(string.ascii_letters + string.digits).upper() for _ in range(6))
        if not InviteCodes.objects.filter(code=code).exists():
            return code
        
# generate qr code for invite links   
def generate_qr_code(invite_code):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(f'https://website.com/invite/?code={invite_code}')
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")

    # Convert QR code image to binary data
    img_buffer = BytesIO()
    qr_img.save(img_buffer, format='PNG')
    img_binary = img_buffer.getvalue()

    # Save the QR code image to a file or database
    #file_path = f'qr_codes/{invite_code}.png'
    #qr_img.save(file_path)

    # formatted data
    formatted_data = {
        #'qr_code_url': file_path,
        'image_binary': img_binary,
    }

    # Return the file path or URL to qr code
    return formatted_data

# set the cookies
def set_cookies(response, user_uid, httponly):
    current_time = datetime.now()
    existing_cookies = Cookies.objects.filter(user_uid=user_uid)
    for cookie in existing_cookies:
        if cookie.expires_at < current_time.replace(tzinfo=timezone.utc):
            cookie.delete()
            continue

        http_only = httponly

        response.set_cookie(
            key=cookie.name,
            value=cookie.value,
            httponly=http_only,
            secure=False,
            samesite='lax',
            expires=cookie.expires_at
        )
    return response

# generate random magic tokens used to verify OTP requests
def generate_magic_token():
    length = 64
    while True:
        characters = string.ascii_letters + string.digits
        token = ''.join(secrets.choice(characters) for _ in range(length))
        if not OtpTokenVerify.objects.filter(token=token).exists():
            return token
        
# generate random invite code
def generate_random_invite_code():
    length = 6
    while True:
        characters = string.ascii_letters + string.digits
        code = ''.join(secrets.choice(characters) for _ in range(length))
        if not InviteCodes.objects.filter(code=code).exists():
            return code
        
# get auth session user via jwt token
def auth_session_user(jwt_token):
    res = supabase.auth.get_user(jwt_token)
    return res

# check if difference is >= certain amount of time
def calculate_day_difference(date_str, days_difference):
    given_date = datetime.strptime(date_str, '%Y-%m-%d')
    today_date = datetime.today()
    difference = today_date - given_date
    return difference.days >= days_difference