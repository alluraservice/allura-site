"""
Saving inquiries from the three public forms (used by contact_us.py, services.py, product_details.py).

Each form records WHERE the inquiry came from, so the admin inbox can file it under its channel:
    Product Page  - "Contact Sales" on a product (source_detail = the product name)
    Service Page  - the Service Inquiry form on the Services page
    Contact Us    - the inquiry form on the Contact Us page
Every saved inquiry gets a reference number (e.g. ALR-2610-00042) that the customer sees on screen
and in their acknowledgement email, and that the admin sees in the inbox and in every reply.
"""
import re

from dash import html

from database.db_handler import create_inquiry
from utils.mailer import send_inquiry_acknowledgement

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _clean(v):
    return (v or '').strip()


def submit_inquiry(source, customer, address, person, dept, phone, email, inquiry, remarks, source_detail=None):
    """
    Validates and saves one inquiry, then emails the customer an acknowledgement.
    Returns (ok, message_component, reference_no).
    """
    customer, address, person, dept = map(_clean, (customer, address, person, dept))
    phone, email, inquiry, remarks = map(_clean, (phone, email, inquiry, remarks))

    missing = []
    if not customer:
        missing.append("customer / hospital name")
    if not person:
        missing.append("contact person")
    if not EMAIL_RE.match(email):
        missing.append("a valid email address")
    if not inquiry:
        missing.append("what you need")
    if missing:
        return False, html.Div("Please fill in " + ", ".join(missing) + ".", className="a-alert a-alert-warn"), None

    saved = create_inquiry(customer, address, person, dept, phone, email, inquiry, remarks or None,
                           source=source, source_detail=source_detail)
    if not saved:
        return False, html.Div("Sorry, we couldn't send your inquiry right now. Please try again, or call us at "
                               "+63 917 770 1820.", className="a-alert a-alert-err"), None

    ref = saved.get('reference_no') or f"#{saved.get('id')}"
    sent, _ = send_inquiry_acknowledgement(email, person, ref, source, inquiry)
    return True, confirmation(ref, email if sent else None), ref


def confirmation(reference_no, emailed_to=None):
    return html.Div([
        html.Span("✓", className="tick"),
        html.Div([
            html.B("Thank you! Your inquiry was sent to our team."),
            html.Div(["Your reference number is ", html.Span(reference_no, className="ref"), "."]),
            html.Div((f"A copy was emailed to {emailed_to}. " if emailed_to else "") +
                     "Please mention this number if you call or email us about this request.",
                     className="small text-muted mt-1"),
        ]),
    ], className="a-alert a-alert-ok inquiry-confirm")
