import os
import jinja2
import pdfkit
from datetime import datetime
from decouple import config

# create overall report for a whole business
def create_overall_report(filename, business_info, report_info, header, rows):
    env = config('ENV')
    if env == "prod":
        report_template_path = config('REPORT_TEMPLATE_PATH')
        report_css_path = config('REPORT_CSS_PATH')
    elif env == "dev":
        report_template_path = config('REPORT_TEMPLATE_PATH_DEV')
        report_css_path = config('REPORT_CSS_PATH_DEV')
    elif env == "local":
        report_template_path = config('REPORT_TEMPLATE_PATH_LOCAL')
        report_css_path = config('REPORT_CSS_PATH_LOCAL')
    else:
        return

    # setup variables for pdf
    business_name = business_info.name
    street = business_info.street
    street2 = business_info.city + " " + business_info.province + " " + business_info.postal_code
    report_start_date = report_info['report_start_date']
    report_end_date = report_info['report_end_date']
    day_count = report_info['day_count']
    current_day = report_info['start_day']
    report_id = report_info['report_id']
    email = business_info.email
    today_date = datetime.today().strftime("%Y-%m-%d")

    # fill in variables with data
    context = {
        'business_name': business_name,
        'street': street, 
        'street2': street2, 
        'report_start_date': report_start_date,
        'report_end_date': report_end_date,
        'report_id': report_id,
        'email': email,
        'today_date': today_date,
        'day_count': day_count,
        'current_day': current_day,
        'header': header,
        'people': rows,
    }

    # setup template loader 
    template_loader = jinja2.FileSystemLoader(report_template_path)
    template_env = jinja2.Environment(loader=template_loader)
    html_template = 'report_overall_template.html'
    template = template_env.get_template(html_template)

    # render and create pdf
    output_text = template.render(context)
    options = {
        'encoding': 'UTF-8',
        'javascript-delay':'10', #Optional
        'enable-local-file-access': None, #To be able to access CSS
        'orientation': 'Landscape',
        'page-size': 'Letter',
        'custom-header' : [
            ('Accept-Encoding', 'gzip')
        ],
    }
    pdfkit.from_string(output_text, filename, options=options, css=report_css_path)

# create timesheet report for a person
def create_timesheet_report(filename, person_info, timesheet_info, header, rows, depth):
    env = config('ENV')
    if env == "prod":
        report_template_path = config('REPORT_TEMPLATE_PATH')
        report_css_path = config('REPORT_CSS_PATH')
    elif env == "dev":
        report_template_path = config('REPORT_TEMPLATE_PATH_DEV')
        report_css_path = config('REPORT_CSS_PATH_DEV')
    elif env == "local":
        report_template_path = config('REPORT_TEMPLATE_PATH_LOCAL')
        report_css_path = config('REPORT_CSS_PATH_LOCAL')
    else:
        return

    # setup variables for pdf
    person_name = person_info['name']
    street = person_info['street']
    street_2 = person_info['street_2']
    timesheet_start_date = timesheet_info['start_date']
    timesheet_end_date = timesheet_info['end_date']
    timesheet_id = timesheet_info['id']
    email = person_info['email']
    today_date = datetime.today().strftime("%Y-%m-%d")

    # fill in variables with data
    context = {
        'name': person_name,
        'street': street, 
        'street2': street_2, 
        'timesheet_start_date': timesheet_start_date,
        'timesheet_end_date': timesheet_end_date,
        'timesheet_id': timesheet_id,
        'email': email,
        'today_date': today_date,
        'header': header,
        'day_rows': rows,
        'depth': depth,
    }

    # setup template loader 
    template_loader = jinja2.FileSystemLoader(report_template_path)
    template_env = jinja2.Environment(loader=template_loader)
    html_template = 'timesheet_template.html'
    template = template_env.get_template(html_template)

    # render and create pdf
    output_text = template.render(context)
    options = {
        'encoding': 'UTF-8',
        'javascript-delay':'10', #Optional
        'enable-local-file-access': None, #To be able to access CSS
        'orientation': 'Landscape',
        'page-size': 'Letter',
        'custom-header' : [
            ('Accept-Encoding', 'gzip')
        ],
    }
    pdfkit.from_string(output_text, filename, options=options, css=report_css_path)