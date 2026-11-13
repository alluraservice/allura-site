import dash
from dash import Input, Output, State, callback, html, no_update
import dash_bootstrap_components as dbc

import site_ui as ui
from database.db_handler import SOURCE_CONTACT
from inquiry_forms import submit_inquiry
from utils.site_content import settings as site_settings, tel_href

# Offices, phone, email, maps and social links come from Admin › Website Content › Site settings
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
    s = site_settings()
    form_card = html.Div([
        html.Div(html.H6("Inquiry form"), className="a-card-head"),
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
            html.Div(
                dbc.Button("Submit", id="contact-submit-btn", n_clicks=0, className="a-btn a-btn-primary a-btn-lg"),
                className="d-flex justify-content-end mt-4"),
        ], className="a-card-body", style={"padding": "20px 22px 22px"}),
    ], className="a-card")

    info_card = html.Div([
        html.Div(html.H6("Contact info"), className="a-card-head"),
        html.Div([
            _info("office.svg", "Main office", s['main_office']),
            _info("satellite.svg", "Satellite office", s['satellite_office']) if s['satellite_office'] else None,
            _info("call.svg", "Contact no.", html.A(s['phone'], href=tel_href(s['phone']))),
            _info("email.svg", "Email", html.A(s['email'], href=f"mailto:{s['email']}")),
            html.Div([
                html.Div("Follow us", className="a-section-title mt-3"),
                html.Div([
                    html.A(html.Img(src='/assets/icons/facebook.svg'), href=s['facebook_url'], target="_blank", rel="noopener noreferrer", title="Facebook"),
                    html.A(html.Img(src='/assets/icons/linkedin.svg'), href=s['linkedin_url'], target="_blank", rel="noopener noreferrer", title="LinkedIn"),
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
                    map_card(f"Main office · {s['main_office_label']}", s['main_map_url']) if s['main_map_url'] else None,
                    map_card(f"Satellite office · {s['satellite_office_label']}", s['satellite_map_url'])
                    if s['satellite_office'] and s['satellite_map_url'] else None,
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
