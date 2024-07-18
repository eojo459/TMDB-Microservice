from datetime import datetime
import os
import jinja2
from django.template.loader import render_to_string 
from django.core.mail import EmailMessage, send_mail
from django.template import Context
from decouple import config
from django.utils.html import strip_tags

# send email to confirm & verify email
def confirm_verify_email(to_email, token, redirect_url):
    env = config('ENV')
    if env == "prod":
        email_template_path = config('EMAIL_TEMPLATE_PATH')
        base_url = "https://website.com/"
    elif env == "dev":
        email_template_path = config('EMAIL_TEMPLATE_PATH_DEV')
        base_url = "http://dev.website.com/"
        to_email = config('EMAIL_TEST')
    elif env == "local":
        email_template_path = config('EMAIL_TEMPLATE_PATH_LOCAL')
        base_url = "http://localhost:3000/"
        to_email = config('EMAIL_TEST')
    else:
        return

    # context data for template
    context = {
        'token': token,
        'base_url': base_url,
        'url': base_url + "dashboard/?token=" + token + "&redirect=" + redirect_url,
    }

    # setup template loader 
    template_loader = jinja2.FileSystemLoader(email_template_path)
    template_env = jinja2.Environment(loader=template_loader)
    html_template = 'confirm_verify_email.html'
    template = template_env.get_template(html_template)

    # render and create html as string
    output_text = template.render(context)

    # setup email
    subject = 'Confirm and Verify Your Email'
    from_email = config('DEFAULT_FROM_EMAIL')
    message = EmailMessage(subject, output_text, from_email, [to_email])
    message.content_subtype = 'html'
    message.send()