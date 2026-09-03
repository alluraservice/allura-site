from dash import html, dcc
import dash_bootstrap_components as dbc

layout = html.Div([
    # ==========================================
    # SECTION 1: Hero Section (hero-section-2)
    # ==========================================
    html.Div([
     html.Div([
        html.Div([
            html.H1("CONTACT US", className="hero-title text-white"),
        ], className="hero-content text-start ps-5")
    ], className="hero-section-2")
]),

    # ==========================================
    # SECTION 2: Inquiry Form & Contact Info Grid
    # ==========================================
    html.Div([
        dbc.Row([
            # Left Column: Inquiry Form Only
            dbc.Col([
                html.H3("INQUIRY FORM", className="section-heading mb-4", style={"color": "var(--dark-green)"}),
                
                html.Div([
                    dbc.Row([
                        dbc.Col([
                            html.Label("Costumer/Hospital Name:", className="form-label fw-semibold", style={"color": "var(--dark-green)"}),
                            dbc.Input(type="text", id="contact-customer-name", placeholder="Enter your customer/hospital name here", className="input-box mb-3"),
                            
                            html.Label("Contact Person:", className="form-label fw-semibold", style={"color": "var(--dark-green)"}),
                            dbc.Input(type="text", id="contact-person", placeholder="Enter your contact person here", className="input-box mb-3"),
                            
                            html.Label("Contact No.:", className="form-label fw-semibold", style={"color": "var(--dark-green)"}),
                            dbc.Input(type="text", id="contact-no", placeholder="Enter your contact no. here", className="input-box mb-3"),
                            
                            html.Label("Machine Inquiry:", className="form-label fw-semibold", style={"color": "var(--dark-green)"}),
                            dbc.Textarea(id="contact-machine-inquiry", placeholder="Enter your machine inquiry here", className="input-box mb-3", style={"height": "140px"}),
                        ], md=6),

                        dbc.Col([
                            html.Label("Office Address:", className="form-label fw-semibold", style={"color": "var(--dark-green)"}),
                            dbc.Input(type="text", id="contact-office-address", placeholder="Enter your address here", className="input-box mb-3"),
                            
                            html.Label("Department and title:", className="form-label fw-semibold", style={"color": "var(--dark-green)"}),
                            dbc.Input(type="text", id="contact-department-title", placeholder="Enter your department and title here", className="input-box mb-3"),
                            
                            html.Label("Email address:", className="form-label fw-semibold", style={"color": "var(--dark-green)"}),
                            dbc.Input(type="email", id="contact-email", placeholder="Enter your email address here", className="input-box mb-3"),
                            
                            html.Label("Remarks (Optional):", className="form-label fw-semibold", style={"color": "var(--dark-green)"}),
                            dbc.Textarea(id="contact-remarks", placeholder="Enter your remarks here", className="input-box mb-3", style={"height": "140px"}),
                        ], md=6),
                    ]),
                    
                    dbc.Button("Submit", id="contact-submit-btn", className="btn-green mb-3 mt-2")
                ], className="p-4 bg-light rounded-4 mb-4"),

                html.P([
                    "By submitting this form, you hereby accept our Privacy Policy."
                ], className="mb-2"),
                
                html.A("Privacy Policy", href="/privacy-policy", className="btn-green mb-3 mt-2"),
            ], md=7, className="px-lg-3"),

            # Right Column: Contact Info Cards Only
            dbc.Col([
                html.Div([
                    html.H3("CONTACT INFO", className="section-heading mb-4", style={"color": "var(--dark-green, #008000)"}),
                    
                    html.Div([
                        html.Img(src='/assets/icons/office.svg', className="contact-icon"),
                        html.Div([
                            html.H3("MAIN OFFICE", className="fw-bold mb-1"),
                            html.P("Doña Paz Village, Cruzada, Legazpi City", className="mb-0")
                        ])
                    ], className="contact-info-card"),

                    html.Div([
                        html.Img(src='/assets/icons/satellite.svg', className="contact-icon"),
                        html.Div([
                            html.H3("SATELLITE OFFICE", className="fw-bold mb-1"),
                            html.P("Villa Angelina Phase 1, Mambog 4, Bacoor Cavite", className="mb-0")
                        ])
                    ], className="contact-info-card"),

                    html.Div([
                        html.Img(src='/assets/icons/call.svg', className="contact-icon"),
                        html.Div([
                            html.H3("CONTACT NO.", className="fw-bold mb-1"),
                            html.P("+63 917 770 1820", className="mb-0")
                        ])
                    ], className="contact-info-card"),

                    html.Div([
                        html.Img(src='/assets/icons/email.svg', className="contact-icon"),
                        html.Div([
                            html.H3("EMAIL", className="fw-bold mb-1"),
                            html.P("info@alluraenterpriseph.com", className="mb-0")
                        ])
                    ], className="contact-info-card"),

                    html.H5("Follow us", className="fw-bold mb-3 mt-4"),
                    html.Div([
                        html.A(html.Img(src='/assets/icons/facebook.svg', className="social-svg"), href="https://facebook.com", target="_blank", className="social-icon"),
                        html.A(html.Img(src='/assets/icons/linkedin.svg', className="social-svg"), href="https://linkedin.com", target="_blank", className="social-icon"),
                    ], className="social-links-container")
                ], className="contact-info")
            ], md=5, className="px-lg-3 mt-5 mt-md-0")
        ], className="row justify-content-end container-fluid my-5 px-4")
    ]),

    # ==========================================
    # SECTION 3: Main Office Address & Map
    # ==========================================
    html.Div([
        dbc.Row([
            dbc.Col([
                html.H3("MAIN OFFICE ADDRESS", className="section-heading mb-3", style={"color": "var(--dark-green, #008000)"}),
                html.Iframe(
                    src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3880.799757751662!2d123.7385!3d13.1391!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x0%3A0x0!2zRGHDusOZIFBheiBTdWJkaXZpc2lvbiwgQ3J1emFkYSwgTGVnYXpwaSBDaXR5!5e0!3m2!1sen!2sph!4v1620000000000!5m2!1sen!2sph",
                    width="100%",
                    height="300",
                    style={"border": "0", "borderRadius": "16px"},
                    className="shadow-sm"
                ),
            ], md=12, className="px-lg-3")
        ], className="row justify-content-center container my-5 px-4")
    ]),

    # ==========================================
    # SECTION 4: Satellite Office Address & Map
    # ==========================================
    html.Div([
        dbc.Row([
            dbc.Col([
                html.H3("SATELLITE OFFICE ADDRESS", className="section-heading mb-3", style={"color": "var(--dark-green, #008000)"}),
                html.Iframe(
                    src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3863.3121542122!2d120.9542!3d14.4445!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x0%3A0x0!2zVmlsbGEgQW5nZWxpYSBQaGFzZSAxLCBNYW1ib2cgNCwgQmFjb29yLCBDYXZpdGU!5e0!3m2!1sen!2sph!4v1620000000000!5m2!1sen!2sph",
                    width="100%",
                    height="300",
                    style={"border": "0", "borderRadius": "16px"},
                    className="shadow-sm"
                ),
            ], md=12, className="px-lg-3")
        ], className="row justify-content-center container my-5 px-4")
    ])
])