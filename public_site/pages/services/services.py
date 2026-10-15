import dash
from dash import html, callback, Input, Output, State, no_update
import dash_bootstrap_components as dbc

import site_ui as ui
from database.db_handler import SOURCE_SERVICE
from inquiry_forms import submit_inquiry

SERVICE_AREAS = [
    {
        "title": "Medical Equipment Services",
        "image": "/assets/pictures/services/equipment_services/medical_equipment_service_cover.webp",
        "text": "Installation and lifecycle care for imaging and clinical equipment, handled by trained engineers.",
        "points": ["Installation & commissioning", "Preventive maintenance programs", "Calibration & repairs"],
    },
    {
        "title": "Electrical Services",
        "image": "/assets/pictures/services/electrical_services/electrical_service_cover.webp",
        "text": "Facility electrical work planned around the needs of sensitive diagnostic and clinical areas.",
        "points": ["Site preparation for new equipment", "Power distribution works", "Room shielding support"],
    },
    {
        "title": "Power Supply Services",
        "image": "/assets/pictures/services/power_supply_services/power_supply_service_cover.jpg",
        "text": "Medical-grade power protection so CT, MRI and other critical systems stay online.",
        "points": ["Medical-grade UPS systems", "Voltage stabilization", "UPS maintenance & battery care"],
    },
]

STEPS = [
    ("Send a service inquiry", "Tell us about your facility, the equipment involved, and what you need, using the form on this page."),
    ("Technical assessment", "Our engineers review the request and, where needed, visit the site to check the equipment and conditions."),
    ("Proposal & schedule", "You receive a clear scope and quotation, then we agree on a schedule that works around your operations."),
    ("Service & handover", "The work is carried out and documented, with follow-up support and maintenance plans if you need them."),
]

FIELD_IDS = ['service-inquiry-customer', 'service-inquiry-address', 'service-inquiry-person', 'service-inquiry-dept',
             'service-inquiry-phone', 'service-inquiry-email', 'service-inquiry-details', 'service-inquiry-remarks']


def _label(text):
    return html.Label(text, className="a-label")


def _field(label, component, full=False):
    return html.Div([_label(label), component], className="full" if full else None)


def layout(*args, **kwargs):
    header = ui.page_header(
        "Services",
        "Installation, maintenance, and the electrical and power systems behind your equipment.",
        crumbs=[("Home", "/home"), ("Services", None)],
    )

    # 1. Service inquiry card (kept near the top of the page)
    inquiry_card = html.Div([
        html.Div(id='service-inquiry-toast'),
        html.Div([
            html.Div([
                html.H3("Complete Healthcare Infrastructure & Equipment Solutions", className="card-title"),
                html.P(
                    "From medical equipment installation to specialized electrical and uninterrupted power supply systems, "
                    "we deliver end-to-end technical support to keep your facility operational, safe, and efficient.",
                    className="card-text"
                ),
                html.Button("Service Inquiry", id="btn-open-service-modal", n_clicks=0, className="btn-white"),
            ], className="section-card-content")
        ], className="section-card", style={
            "backgroundImage": "linear-gradient(rgba(0,0,0,0.5), rgba(0,0,0,0.5)), "
                               "url('/assets/pictures/services/equipment_services/medical_equipment_service_cover.webp')",
            "maxWidth": "none", "margin": "0"}),
    ])

    # 2. What we service
    areas = html.Div([
        ui.section_head(
            "What we service",
            "One team for your equipment and the facility around it",
            "Allura supplies medical equipment and services it too. The same engineers who know the machines also handle "
            "the power and electrical work they depend on, so you deal with a single accountable partner.",
        ),
        html.Div([
            html.Div([
                html.Div(className="img", style={"backgroundImage": f"url('{a['image']}')"}),
                html.Div([
                    html.H4(a["title"]),
                    html.P(a["text"]),
                    html.Ul([html.Li(p) for p in a["points"]], className="tick-list"),
                ], className="body"),
            ], className="a-card feature-card")
            for a in SERVICE_AREAS
        ], className="feature-grid"),
    ], className="site-section")

    # 3. How service works
    steps = html.Div([
        ui.section_head("How it works", "From request to handover in four steps"),
        html.Div([
            html.Div([html.Span(str(i), className="num"), html.H5(title), html.P(text)], className="step")
            for i, (title, text) in enumerate(STEPS, start=1)
        ], className="a-card steps"),
    ], className="site-section")

    # 4. Sales + service across the equipment lifecycle
    lifecycle = html.Div([
        html.Div([
            html.Div([
                html.P("Sales & service", className="site-eyebrow", style={"color": "rgba(255,255,255,.75)"}),
                html.H3("A partner before, during, and after the purchase"),
                html.P("Buy the equipment and keep it running with the same company. Tell us what you need and our team "
                       "will get back to you with the right engineer."),
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
