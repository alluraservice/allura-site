import dash
from dash import Input, Output, State, callback, html, no_update
import dash_bootstrap_components as dbc

import site_ui as ui
from database.db_handler import SOURCE_CONTACT
from inquiry_forms import submit_inquiry

MAIN_MAP = ("https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3880.799757751662!2d123.7385!3d13.1391!2m3!1f0!2f0!3f0"
            "!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x0%3A0x0!2zRGHDusOZIFBheiBTdWJkaXZpc2lvbiwgQ3J1emFkYSwgTGVnYXpwaSBDaXR5"
            "!5e0!3m2!1sen!2sph!4v1620000000000!5m2!1sen!2sph")
SATELLITE_MAP = ("https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3863.3121542122!2d120.9542!3d14.4445!2m3!1f0!2f0!3f0"
                 "!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x0%3A0x0!2zVmlsbGEgQW5nZWxpYSBQaGFzZSAxLCBNYW1ib2cgNCwgQmFjb29yLCBDYXZpdGU"
                 "!5e0!3m2!1sen!2sph!4v1620000000000!5m2!1sen!2sph")

FIELD_IDS = ['contact-customer-name', 'contact-office-address', 'contact-person', 'contact-department-title',
             'contact-no', 'contact-email', 'contact-machine-inquiry', 'contact-remarks']


def _field(label, component, full=False):
    return html.Div([html.Label(label, className="a-label"), component], className="full" if full else None)


def _info(icon, key, value):
    return html.Div([
        html.Span(html.Img(src=f'/assets/icons/{icon}'), className="ico"),
        html.Div([html.Div(key, className="k"), html.Div(value, className="v")]),
    ], className="info-row")


def layout(*args, **kwargs):
    form_card = html.Div([
        html.Div([
            html.H6("Inquiry form"),
            html.Span("We usually reply within one business day", className="text-muted small"),
        ], className="a-card-head"),
        html.Div([
            html.Div([
                _field("Customer / Hospital Name", dbc.Input(type="text", id="contact-customer-name", placeholder="Enter your customer/hospital name here", className="input-box")),
                _field("Office Address", dbc.Input(type="text", id="contact-office-address", placeholder="Enter your address here", className="input-box")),
                _field("Contact Person", dbc.Input(type="text", id="contact-person", placeholder="Enter your contact person here", className="input-box")),
                _field("Department and Title", dbc.Input(type="text", id="contact-department-title", placeholder="Enter your department and title here", className="input-box")),
                _field("Contact No.", dbc.Input(type="text", id="contact-no", placeholder="Enter your contact no. here", className="input-box")),
                _field("Email Address", dbc.Input(type="email", id="contact-email", placeholder="Enter your email address here", className="input-box")),
                _field("Machine Inquiry", dbc.Textarea(id="contact-machine-inquiry", placeholder="Enter your machine inquiry here", className="input-box", style={"height": "130px"})),
                _field("Remarks (Optional)", dbc.Textarea(id="contact-remarks", placeholder="Enter your remarks here", className="input-box", style={"height": "130px"})),
            ], className="form-row"),
            html.Div(id="contact-feedback", className="mt-3"),
            html.Div([
                html.Span(["By submitting this form, you accept our ",
                           html.A("Privacy Policy", href="/privacy-policy", style={"color": "var(--green)"}), "."],
                          className="text-muted small"),
                dbc.Button("Submit", id="contact-submit-btn", n_clicks=0, className="a-btn a-btn-primary a-btn-lg"),
            ], className="d-flex flex-wrap justify-content-between align-items-center gap-3 mt-4"),
        ], className="a-card-body", style={"padding": "20px 22px 22px"}),
    ], className="a-card")

    info_card = html.Div([
        html.Div(html.H6("Contact info"), className="a-card-head"),
        html.Div([
            _info("office.svg", "Main office", "Doña Paz Village, Cruzada, Legazpi City"),
            _info("satellite.svg", "Satellite office", "Villa Angelina Phase 1, Mambog 4, Bacoor Cavite"),
            _info("call.svg", "Contact no.", html.A("+63 917 770 1820", href="tel:+639177701820")),
            _info("email.svg", "Email", html.A("info@alluraenterpriseph.com", href="mailto:info@alluraenterpriseph.com")),
            html.Div([
                html.Div("Follow us", className="a-section-title mt-3"),
                html.Div([
                    html.A(html.Img(src='/assets/icons/facebook.svg'), href="https://facebook.com", target="_blank", title="Facebook"),
                    html.A(html.Img(src='/assets/icons/linkedin.svg'), href="https://linkedin.com", target="_blank", title="LinkedIn"),
                ], className="social-row"),
            ]),
        ], className="a-card-body"),
    ], className="a-card")

    def map_card(title, src):
        return html.Div([
            html.Div(html.H6(title), className="a-card-head"),
            html.Iframe(src=src),
        ], className="a-card map-card")

    return html.Div([
        ui.page_header(
            "Contact Us",
            "Product proposals, equipment demos, service requests or technical questions: our team is ready to help.",
            crumbs=[("Home", "/home"), ("Contact Us", None)],
        ),
        html.Div([
            html.Div([form_card, info_card], className="contact-grid"),
            html.Div([
                ui.section_head("Visit us", "Our offices"),
                html.Div([
                    map_card("Main office · Legazpi City", MAIN_MAP),
                    map_card("Satellite office · Bacoor, Cavite", SATELLITE_MAP),
                ], className="map-grid"),
            ], className="site-section"),
        ], className="site-container"),
    ], className="site-shell")


# ==========================================
# CALLBACK: SAVE THE INQUIRY (channel = Contact Us)
# ==========================================
@callback(
    Output('contact-feedback', 'children'),
    *[Output(i, 'value') for i in FIELD_IDS],
    Input('contact-submit-btn', 'n_clicks'),
    *[State(i, 'value') for i in FIELD_IDS],
    prevent_initial_call=True,
)
def submit_contact_inquiry(n, customer, address, person, dept, phone, email, inquiry, remarks):
    if not n:
        raise dash.exceptions.PreventUpdate
    ok, message, _ref = submit_inquiry(SOURCE_CONTACT, customer, address, person, dept, phone, email, inquiry, remarks)
    if ok:
        return (message,) + ('',) * len(FIELD_IDS)       # clear the form
    return (message,) + (no_update,) * len(FIELD_IDS)
