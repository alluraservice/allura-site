import dash
from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc

layout = html.Div([
    # ==========================================
    # SECTION 1: Hero Section (hero-section-3)
    # ==========================================
    html.Div([
        html.Div([
            html.H1("SERVICES", className="hero-title text-white"),
        ], className="hero-content text-start ps-5")
    ], className="hero-section-3"),

    # ==========================================
    # SECTION 2: Service Card
    # ==========================================
    html.Div([
        html.Div([
            html.Div([
                html.H3("Complete Healthcare Infrastructure & Equipment Solutions", className="card-title"),
                html.P(
                    "From medical equipment installation to specialized electrical and uninterrupted power supply systems, we deliver end-to-end technical support to keep your facility operational, safe, and efficient.",
                    className="card-text"
                ),
                html.Button(
                    "Service Inquiry",
                    id="btn-open-service-modal",
                    n_clicks=0,
                    className="btn-white"
                )
            ], className="section-card-content")
        ], className="section-card container", style={"backgroundImage": "linear-gradient(rgba(0,0,0,0.5), rgba(0,0,0,0.5)), url('/assets/pictures/services/equipment_services/equipment_service_cover.webp')"}),
    ], className="py-4"),

    # ==========================================
    # MODAL: Service Inquiry Form
    # ==========================================
    dbc.Modal([
        dbc.ModalBody([
            # Close Button
            html.Div([
                html.Button(
                    type="button",
                    id="btn-close-service-modal",
                    className="btn-close ms-auto",
                    **{"aria-label": "Close"}
                )
            ], className="d-flex justify-content-end mb-2"),

            # Form Title
            html.H4("SERVICE INQUIRY FORM", className="fw-bold mb-4", style={'color': 'var(--dark-green)'}),

            # Form Fields Grid
            html.Div([
                # Row 1
                html.Div([
                    html.Div([
                        html.Label("Customer/Hospital Name:", className="fw-semibold mb-1", style={'color': 'var(--dark-green)'}),
                        dbc.Input(id='service-inquiry-customer', type='text', placeholder='Enter your customer/hospital name here', className='input-box')
                    ], className="col-md-6 mb-3"),
                    html.Div([
                        html.Label("Office Address:", className="fw-semibold mb-1", style={'color': 'var(--dark-green)'}),
                        dbc.Input(id='service-inquiry-address', type='text', placeholder='Enter your address here', className='input-box')
                    ], className="col-md-6 mb-3"),
                ], className="row"),

                # Row 2
                html.Div([
                    html.Div([
                        html.Label("Contact Person:", className="fw-semibold mb-1", style={'color': 'var(--dark-green)'}),
                        dbc.Input(id='service-inquiry-person', type='text', placeholder='Enter your contact person here', className='input-box')
                    ], className="col-md-6 mb-3"),
                    html.Div([
                        html.Label("Department and Title:", className="fw-semibold mb-1", style={'color': 'var(--dark-green)'}),
                        dbc.Input(id='service-inquiry-dept', type='text', placeholder='Enter your department and title here', className='input-box')
                    ], className="col-md-6 mb-3"),
                ], className="row"),

                # Row 3
                html.Div([
                    html.Div([
                        html.Label("Contact No.:", className="fw-semibold mb-1", style={'color': 'var(--dark-green)'}),
                        dbc.Input(id='service-inquiry-phone', type='text', placeholder='Enter your contact no. here', className='input-box')
                    ], className="col-md-6 mb-3"),
                    html.Div([
                        html.Label("Email Address:", className="fw-semibold mb-1", style={'color': 'var(--dark-green)'}),
                        dbc.Input(id='service-inquiry-email', type='email', placeholder='Enter your email address here', className='input-box')
                    ], className="col-md-6 mb-3"),
                ], className="row"),

                # Row 4 (Textareas)
                html.Div([
                    html.Div([
                        html.Label("Service Inquiry Details:", className="fw-semibold mb-1", style={'color': 'var(--dark-green)'}),
                        dbc.Textarea(id='service-inquiry-details', placeholder='Enter your service requirements here', className='input-box', style={'height': '110px'})
                    ], className="col-md-6 mb-3"),
                    html.Div([
                        html.Label("Remarks (Optional):", className="fw-semibold mb-1", style={'color': 'var(--dark-green)'}),
                        dbc.Textarea(id='service-inquiry-remarks', placeholder='Enter your remarks here', className='input-box', style={'height': '110px'})
                    ], className="col-md-6 mb-3"),
                ], className="row"),

                # Submit Button
                html.Div([
                    html.Button("Submit", id='btn-submit-service-inquiry', n_clicks=0, className='btn btn-green rounded-pill fw-semibold px-5 py-2 text-white shadow-sm')
                ], className="mt-2")
            ])
        ], className='p-4')
    ], id='service-inquiry-modal', size='lg', centered=True, is_open=False)
])


# ==========================================
# CALLBACK: TOGGLE SERVICE MODAL
# ==========================================
@callback(
    Output('service-inquiry-modal', 'is_open'),
    [
        Input('btn-open-service-modal', 'n_clicks'),
        Input('btn-submit-service-inquiry', 'n_clicks'),
        Input('btn-close-service-modal', 'n_clicks')
    ],
    [State('service-inquiry-modal', 'is_open')],
    prevent_initial_call=True
)
def toggle_service_modal(open_clicks, submit_clicks, close_clicks, is_open):
    ctx = dash.callback_context
    if not ctx.triggered:
        return False

    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if trigger_id == 'btn-open-service-modal' and (open_clicks or 0) > 0:
        return True

    if trigger_id in ['btn-submit-service-inquiry', 'btn-close-service-modal']:
        return False

    return is_open