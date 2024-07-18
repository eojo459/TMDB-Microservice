# Chargebee api util
# https://apidocs.chargebee.com/docs/api

import chargebee
from decouple import config

# setup chargebee instance
chargebee.configure(config('CHARGEBEE_SITE_API_KEY_TEST'), config('CHARGEBEE_SITE_TEST'))

# create new hosted checkout url for new customer
def generate_checkout_new_url(request):
    result = chargebee.HostedPage.checkout_new_for_items({
        "subscription_items": [{
            "item_price_id": request["item_id"],
            "quantity": 1
        }],
        "customer": {
            "first_name": request["first_name"],
            "last_name": request["last_name"],
            "phone": request["phone"],
            "email": request["email"]
        }
    })
    hosted_page = result._response['hosted_page']
    return hosted_page

# get hosted page checkout url to see payment status
def get_hosted_page(hosted_page):
    result = chargebee.HostedPage.retrieve(hosted_page)
    hosted_page_result = result.hosted_page
    return hosted_page_result

# get a subscription by id
def get_subscription(subscription_id):
    result = chargebee.Subscription.retrieve(subscription_id)
    return result.subscription

# cancel a subscription by id
def cancel_subscription(request):
    result = chargebee.Subscription.cancel_for_items(request['subscription_id'],{
        "end_of_term" : request['cancellation_time']
    })
    return result.subscription
  
# create new hosted checkout url for customer to update a subscription
def generate_update_subscription_checkout_new_url(subscription_id):
    result = chargebee.HostedPage.checkout_existing_for_items({
        "subscription": {
            "id": subscription_id
        },
    })
    hosted_page = result._response['hosted_page']
    return hosted_page

# create new hosted checkout url for customer to manage payment methods
def generate_update_payment_method_checkout_new_url(customer_id):
    result = chargebee.HostedPage.manage_payment_sources({
        "customer": {
            "id": customer_id
        },
    })
    hosted_page = result._response['hosted_page']
    return hosted_page

# get invoice data
def get_invoice_data(invoice_id):
    result = chargebee.Invoice.retrieve(invoice_id)
    return result.invoice

# get invoice data as PDF
def get_invoice_data_pdf(invoice_id):
    result = chargebee.Invoice.pdf(invoice_id)
    return result.download