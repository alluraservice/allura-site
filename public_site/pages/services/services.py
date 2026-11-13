import dash
from dash import html, callback, Input, Output, State, no_update
import dash_bootstrap_components as dbc

import site_ui as ui
from database.db_handler import SOURCE_SERVICE
from inquiry_forms import submit_inquiry
from utils.site_content import get_content, lines

# Text and the three service-area photos come from Admin › Website Content › Services
# (defaults in utils/site_content.py). The icons stay fixed, in this order.
AREA_ICONS = ["equipment_services.svg", "electrical_services.svg", "power_supply_services.svg"]

FIELD_IDS = ['service-inquiry-customer', 'service-inquiry-address', 'service-inquiry-person', 'service-inquiry-dept',
             'service-inquiry-phone', 'service-inquiry-email', 'service-inquiry-details', 'service-inquiry-remarks']


def _label(text):
    return html.Label(text, className="a-label")


def _field(label, component, full=False):
    return html.Div([_label(label), component], className="full" if full else None)


def layout(*args, **kwargs):
    c = get_content('services')
    areas_data = [dict(a, icon=AREA_ICONS[i % len(AREA_ICONS)]) for i, a in enumerate(c['areas'])]
    banner_img = (areas_data[0].get('photo') if areas_data else None) or \
        "/assets/pictures/services/equipment_services/medical_equipment_service_cover.webp"
    header = ui.page_header(
        "Services",
        c['header_lead'],
        crumbs=[("Home", "/home"), ("Services", None)],
    )

    # 1. Service inquiry card (kept near the top of the page)
    inquiry_card = html.Div([
        html.Div(id='service-inquiry-toast'),
        html.Div([
            html.Div([
                html.H3(c['banner_title'], className="card-title"),
                html.P(c['banner_text'], className="card-text"),
                html.Button([ui.icon_img("/assets/icons/service_icon.svg", class_name="btn-ico"), "Service Inquiry"],
                            id="btn-open-service-modal", n_clicks=0, className="btn-white"),
            ], className="section-card-content")
        ], className="section-card", style={
            "backgroundImage": f"linear-gradient(rgba(0,0,0,0.5), rgba(0,0,0,0.5)), url('{banner_img}')",
            "maxWidth": "none", "margin": "0"}),
    ])

    # 2. What we service
    areas = html.Div([
        ui.section_head(
            "What we service", c['areas_title'], c['areas_text'],
        ),
        html.Div([
            html.Div([
                html.Div(className="img", style={"backgroundImage": f"url('{a.get('photo')}')"}),
                html.Div([
                    html.Span(ui.icon_img(f"/assets/icons/{a['icon']}"), className="feature-icon"),
                    html.H4(a["title"]),
                    html.P(a["text"]),
                    html.Ul([html.Li(p) for p in lines(a.get("points"))], className="tick-list"),
                ], className="body"),
            ], className="a-card feature-card")
            for a in areas_data
        ], className="feature-grid"),
    ], className="site-section")

    # 3. How service works
    steps = html.Div([
        ui.section_head("How it works", c['steps_title']),
        html.Div([
            html.Div([html.Span(str(i), className="num"), html.H5(st.get('title')), html.P(st.get('text'))], className="step")
            for i, st in enumerate(c['steps'], start=1)
        ], className="a-card steps"),
    ], className="site-section")

    # 4. Sales + service across the equipment lifecycle
    lifecycle = html.Div([
        html.Div([
            html.Div([
                html.P("Sales & service", className="site-eyebrow", style={"color": "rgba(255,255,255,.75)"}),
                html.H3(c['lifecycle_title']),
                html.P(c['lifecycle_text']),
                html.Div([
                    html.Button("Request a Service", id="btn-open-service-modal-2", n_clicks=0,
                                className="a-btn a-btn-white a-btn-lg"),
                    html.A("Browse Products", href="/products", className="a-btn a-btn-light a-btn-lg"),
                ], className="d-flex flex-wrap gap-2"),
            ], className="left"),
            html.Div([
                html.Div([html.Span("Before", className="tag"),
                          html.Div([html.B("Planning & site readiness"),
                                    html.Span("Equipment selection, site assessment, and power requirements.")])], className="phase"),
                html.Div([html.Span("Installation", className="tag"),
                          html.Div([html.B("Turn-key setup"),
                                    html.Span("Delivery, installation, power conditioning, and commissioning.")])], className="phase"),
                html.Div([html.Span("After-sales", className="tag"),
                          html.Div([html.B("Lifecycle support"),
                                    html.Span("Preventive maintenance, calibration, and repairs to reduce downtime.")])], className="phase"),
            ], className="right"),
        ], className="a-card split-band"),
    ], className="site-section")

    # Service inquiry modal (same ids as before)
    modal = dbc.Modal([
        dbc.ModalBody([
            html.Div([
                html.Div([
                    html.H4("Service Inquiry"),
                    html.P("Tell us what you need and our service team will get in touch.", className="modal-sub"),
                ]),
                html.Button(type="button", id="btn-close-service-modal", className="btn-close ms-auto",
                            **{"aria-label": "Close"}),
            ], className="d-flex align-items-start gap-3"),

            html.Div([
                _field("Customer / Hospital Name", dbc.Input(id='service-inquiry-customer', type='text', placeholder='Enter your customer/hospital name here', className='input-box')),
                _field("Office Address", dbc.Input(id='service-inquiry-address', type='text', placeholder='Enter your address here', className='input-box')),
                _field("Contact Person", dbc.Input(id='service-inquiry-person', type='text', placeholder='Enter your contact person here', className='input-box')),
                _field("Department and Title", dbc.Input(id='service-inquiry-dept', type='text', placeholder='Enter your department and title here', className='input-box')),
                _field("Contact No.", dbc.Input(id='service-inquiry-phone', type='text', placeholder='Enter your contact no. here', className='input-box')),
                _field("Email Address", dbc.Input(id='service-inquiry-email', type='email', placeholder='Enter your email address here', className='input-box')),
                _field("Service Inquiry Details", dbc.Textarea(id='service-inquiry-details', placeholder='Enter your service requirements here', className='input-box', style={'height': '110px'})),
                _field("Remarks (Optional)", dbc.Textarea(id='service-inquiry-remarks', placeholder='Enter your remarks here', className='input-box', style={'height': '110px'})),
            ], className="form-row"),

            html.Div(id='service-inquiry-feedback', className="mt-3"),
            html.Div([
                html.Button("Submit", id='btn-submit-service-inquiry', n_clicks=0, className='a-btn a-btn-primary a-btn-lg'),
            ], className="modal-actions"),
        ])
    ], id='service-inquiry-modal', size='lg', centered=True, is_open=False, className="a-modal")

    return html.Div([
        header,
        html.Div([inquiry_card, areas, steps, lifecycle], className="site-container"),
        modal,
    ], className="site-shell")


# ==========================================
# CALLBACK: OPEN / CLOSE THE SERVICE MODAL
# (Submit no longer closes it blindly: the save callback below closes it only when the inquiry was saved.)
# ==========================================
@callback(
    Output('service-inquiry-modal', 'is_open'),
    Output('service-inquiry-feedback', 'children'),
    Input('btn-open-service-modal', 'n_clicks'),
    Input('btn-open-service-modal-2', 'n_clicks'),
    Input('btn-close-service-modal', 'n_clicks'),
    prevent_initial_call=True
)
def toggle_service_modal(_o1, _o2, _close):
    ctx = dash.callback_context
    if not ctx.triggered or not ctx.triggered[0].get('value'):
        raise dash.exceptions.PreventUpdate
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    return trigger_id != 'btn-close-service-modal', None


# ==========================================
# CALLBACK: SAVE THE INQUIRY (channel = Service Page)
# ==========================================
@callback(
    Output('service-inquiry-modal', 'is_open', allow_duplicate=True),
    Output('service-inquiry-feedback', 'children', allow_duplicate=True),
    Output('service-inquiry-toast', 'children'),
    *[Output(i, 'value') for i in FIELD_IDS],
    Input('btn-submit-service-inquiry', 'n_clicks'),
    *[State(i, 'value') for i in FIELD_IDS],
    prevent_initial_call=True,
)
def submit_service_inquiry(n, customer, address, person, dept, phone, email, details, remarks):
    if not n:
        raise dash.exceptions.PreventUpdate
    ok, message, _ref = submit_inquiry(SOURCE_SERVICE, customer, address, person, dept, phone, email, details, remarks)
    if ok:
        return (False, None, html.Div(message, className="mb-3")) + ('',) * len(FIELD_IDS)
    return (no_update, message, no_update) + (no_update,) * len(FIELD_IDS)
