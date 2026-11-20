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
import threading

import dash_bootstrap_components as dbc
from dash import Input, Output, clientside_callback, html

from database.db_handler import create_inquiry
from utils.mailer import is_configured as email_is_configured, send_inquiry_acknowledgement
from utils.site_content import settings as site_settings

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _clean(v):
    return (v or '').strip()


PHONE_RE = re.compile(r"^[0-9+()\-.\s/]{7,}$")


def check_inquiry(customer, person, phone, email, inquiry):
    """The reasons an inquiry can't be sent yet, in plain words (empty list = OK)."""
    problems = []
    if not customer:
        problems.append(("Customer / Hospital Name", "This is empty. Type the name of your hospital, clinic or company."))
    if not person:
        problems.append(("Contact Person", "This is empty. Type the name of the person we should talk to."))
    if phone and not PHONE_RE.match(phone):
        problems.append(("Contact No.", f"“{phone}” doesn't look like a phone number. Use digits only, "
                                        "for example 0917 123 4567."))
    if not email:
        problems.append(("Email Address", "This is empty. We need it to send you our reply."))
    elif not EMAIL_RE.match(email):
        problems.append(("Email Address", f"“{email}” is not a complete email address. "
                                          "It should look like name@hospital.com."))
    if not inquiry:
        problems.append(("Inquiry details", "This is empty. Tell us which equipment or service you need."))
    return problems


def submit_inquiry(source, customer, address, person, dept, phone, email, inquiry, remarks, source_detail=None):
    """
    Validates and saves one inquiry, then emails the customer an acknowledgement in the background.
    Returns (ok, message_component, reference_no, window_body):
      message_component  short note shown under the form
      window_body        content for the pop-up window: the confirmation, or why it couldn't be sent
    """
    customer, address, person, dept = map(_clean, (customer, address, person, dept))
    phone, email, inquiry, remarks = map(_clean, (phone, email, inquiry, remarks))

    problems = check_inquiry(customer, person, phone, email, inquiry)
    if problems:
        note = html.Div("Your inquiry was not sent yet: please check the "
                        + ", ".join(f for f, _ in problems) + ".", className="a-alert a-alert-warn")
        return False, note, None, problem_body(problems)

    saved = create_inquiry(customer, address, person, dept, phone, email, inquiry, remarks or None,
                           source=source, source_detail=source_detail)
    if not saved:
        phone_no = site_settings()['phone']
        note = html.Div("Sorry, we couldn't send your inquiry right now. Please try again, or call us at "
                        f"{phone_no}.", className="a-alert a-alert-err")
        return False, note, None, problem_body(
            [("Connection problem", "Our system couldn't save your inquiry just now. Your details are still in "
                                    f"the form: please press Submit again in a minute, or call us at {phone_no}.")],
            title="Inquiry not sent")

    ref = saved.get('reference_no') or f"#{saved.get('id')}"
    emailing = email_is_configured()
    if emailing and not saved.get('duplicate'):
        # Sent in the background: the visitor sees the confirmation right away instead of waiting
        # for the mail server (UAT D-01).
        threading.Thread(target=_send_ack, args=(email, person, ref, source, inquiry), daemon=True).start()
    return True, confirmation(ref, email if emailing else None), ref, confirm_for(ref, email)


def _send_ack(email, person, ref, source, inquiry):
    try:
        send_inquiry_acknowledgement(email, person, ref, source, inquiry)
    except Exception as e:
        print(f"[inquiry_forms] acknowledgement email for {ref} failed: {e}")


def confirmation(reference_no, emailed_to=None):
    return html.Div([
        html.Span("✓", className="tick"),
        html.Div([
            html.B("Thank you! Your inquiry was sent to our team."),
            html.Div(["Your reference number is ", html.Span(reference_no, className="ref"), "."]),
            html.Div((f"A copy will be emailed to {emailed_to}. " if emailed_to else "") +
                     "Please mention this number if you call or email us about this request.",
                     className="small text-muted mt-1"),
        ]),
    ], className="a-alert a-alert-ok inquiry-confirm")


# ---------------------------------------------------------------------------------------------
# Confirmation window (UAT: "a confirmation window may help after submitting any inquiry")
# ---------------------------------------------------------------------------------------------
def confirm_window(prefix):
    """A pop-up shown after Submit: the confirmation when the inquiry is saved, or the reasons it
    wasn't sent (problem_body). Put it in the page layout."""
    return dbc.Modal(dbc.ModalBody([
        html.Div(id=f'{prefix}-done-body'),
        html.Div(html.Button("OK", id=f'{prefix}-done-ok', n_clicks=0, className="a-btn a-btn-primary a-btn-lg"),
                 className="modal-actions justify-content-center"),
    ]), id=f'{prefix}-done-modal', is_open=False, centered=True, className="a-modal inquiry-done-modal")


def confirm_body(reference_no, emailed_to=None):
    return html.Div([
        html.Div("✓", className="done-tick"),
        html.H4("Inquiry sent", className="fw-bold mb-2"),
        html.P("Thank you! Our team has received your inquiry and will get back to you.", className="mb-3"),
        html.Div("Your reference number", className="done-ref-label"),
        html.Div(reference_no, className="done-ref"),
        html.P((f"A copy will be emailed to {emailed_to}. " if emailed_to else "") +
               "Please keep this number and mention it if you call or email us about this request.",
               className="small text-muted mt-3 mb-0"),
    ], className="inquiry-done text-center")


def problem_body(problems, title="Please check your inquiry"):
    """Pop-up content listing why the inquiry wasn't sent: [(field, reason), ...]."""
    return html.Div([
        html.Div("!", className="done-tick done-tick-warn"),
        html.H4(title, className="fw-bold mb-2"),
        html.P("Your inquiry has not been sent yet. Please fix the following, then press Submit again:",
               className="mb-3"),
        html.Ul([html.Li([html.B(field + ": "), reason]) for field, reason in problems],
                className="problem-list text-start"),
    ], className="inquiry-done text-center")


def confirm_for(reference_no, email):
    """confirm_body() with the email line only when website email is switched on."""
    return confirm_body(reference_no, (email or '').strip() if email_is_configured() else None)


def register_confirm_close(prefix):
    """Closes the pop-up window when OK is pressed (runs in the browser)."""
    clientside_callback(
        "function(n) { if (!n) { return window.dash_clientside.no_update; } return false; }",
        Output(f'{prefix}-done-modal', 'is_open', allow_duplicate=True),
        Input(f'{prefix}-done-ok', 'n_clicks'),
        prevent_initial_call=True,
    )


def sending_state(button_id, label="Submit"):
    """While an inquiry is being saved, the Submit button is greyed out and reads "Sending…",
    so it can't be pressed twice (UAT D-01)."""
    return [(Output(button_id, 'disabled'), True, False), (Output(button_id, 'children'), "Sending…", label)]
