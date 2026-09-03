import dash
from dash import html
import dash_bootstrap_components as dbc

dash.register_page(__name__, path='/about-us', title='About Us - Allura Enterprise')

# ==========================================
# PAGE LAYOUT
# ==========================================
layout = html.Div([

    # 1. HERO SECTION (With Image & Pure White Text)
html.Div([
        html.Div([
            html.Div([
                html.H1("From Regional Pioneer to National Healthcare Partner", className="fw-bold mb-3 display-5 text-white mx-auto",
                        style={'maxWidth': '550px', 'lineHeight': '1.3'}),
                html.P(
                    "Established in 2014, Allura Enterprise delivers reliable radiology, medical imaging, "
                    "power infrastructure, and specialized technical services to hospitals nationwide.",
                    className="text-white fs-5 mx-auto",
                    style={'maxWidth': '450px'}
                )
            ], className="container text-center pb-4", style={'paddingTop': '80px'})  # Added paddingTop to shift content down
        ], className="about-hero-card mb-5 shadow-sm")
    ], className="container py-3"),

    # 2. STATS OVERVIEW
    html.Div([
        html.Div([
            html.Div([
                html.Div([
                    html.Div("10+", className="stat-number"),
                    html.Div("Years of Excellence", className="fw-semibold text-muted text-uppercase fs-7 mt-1")
                ], className="stat-box text-center shadow-sm h-100")
            ], className="col-md-3 col-6 mb-4"),

            html.Div([
                html.Div([
                    html.Div("₱128.9M+", className="stat-number"),
                    html.Div("Largest Single Project (MRI 1.5T)", className="fw-semibold text-muted text-uppercase fs-7 mt-1")
                ], className="stat-box text-center shadow-sm h-100")
            ], className="col-md-3 col-6 mb-4"),

            html.Div([
                html.Div([
                    html.Div("Platinum", className="stat-number"),
                    html.Div("PhilGEPS & FDA LTO Certified", className="fw-semibold text-muted text-uppercase fs-7 mt-1")
                ], className="stat-box text-center shadow-sm h-100")
            ], className="col-md-3 col-6 mb-4"),

            html.Div([
                html.Div([
                    html.Div("Nationwide", className="stat-number"),
                    html.Div("Luzon & Visayas Footprint", className="fw-semibold text-muted text-uppercase fs-7 mt-1")
                ], className="stat-box text-center shadow-sm h-100")
            ], className="col-md-3 col-6 mb-4"),
        ], className="row")
    ], className="container mb-5"),

    # 3. WHO WE ARE & CAPABILITIES
    html.Div([
        html.Div([
            html.Div([
                html.H6("WHO WE ARE", className="fw-bold text-uppercase mb-2", style={'color': 'var(--dark-green)'}),
                html.H2("Complete Technical & Solutions Care for Hospitals", className="fw-bold text-dark mb-4"),
                html.P(
                    "Allura Enterprise is a trusted medical device distributor and service provider. "
                    "Over a decade of organic growth has elevated us from a regional trading firm into a full-scale channel partner "
                    "capable of managing turn-key medical installations, power conditioning, and after-sales maintenance.",
                    className="text-muted fs-6 mb-4",
                    style={'lineHeight': '1.8'}
                ),
                html.P(
                    "We solve the hospital sector's critical challenge: providing a single accountable, compliant, and "
                    "technically proficient partner that bridges global medical technology directly to local clinical operations.",
                    className="text-muted fs-6",
                    style={'lineHeight': '1.8'}
                )
            ], className="col-lg-6 mb-4 mb-lg-0"),

            html.Div([
                html.Div([
                    html.H4("Our Strategic Capabilities", className="fw-bold mb-4", style={'color': 'var(--dark-green)'}),
                    
                    html.Div([
                        html.H6("Direct Sales & Distribution", className="fw-bold text-dark mb-1"),
                        html.P("Radiology, MRI, CT Scans, Ultrasound, OR Equipment, and Hospital IT.", className="text-muted small mb-3")
                    ]),
                    html.Div([
                        html.H6("Power Quality Solutions", className="fw-bold text-dark mb-1"),
                        html.P("Medical-grade UPS and voltage stabilization for sensitive diagnostic gear.", className="text-muted small mb-3")
                    ]),
                    html.Div([
                        html.H6("Lifecycle Support & Repairs", className="fw-bold text-dark mb-1"),
                        html.P("Preventative maintenance, system calibration, site shielding, and repairs.", className="text-muted small")
                    ])
                ], className="section-card-content p-4 p-md-5 rounded-4 shadow-sm border-0 bg-light")
            ], className="col-lg-6")
        ], className="row align-items-center")
    ], className="container mb-5 py-4"),

    # 4. THE ALLURA SUCCESS STORY (TIMELINE)
    html.Div([
        html.Div([
            html.H6("OUR HISTORY", className="fw-bold text-uppercase mb-2 text-center", style={'color': 'var(--dark-green)'}),
            html.H2("The Allura Growth Story", className="fw-bold text-dark mb-5 text-center"),

            html.Div([
                # Phase 1
                html.Div([
                    html.Div([
                        html.Span("2014 – 2017", className="badge mb-2 px-3 py-2 fs-7 rounded-pill text-white", style={'backgroundColor': 'var(--green)'}),
                        html.H4("Phase 1: Foundation & Trust", className="fw-bold text-dark mb-2"),
                        html.P(
                            "Registered as a regional trading business. Built foundational trust and long-term hospital "
                            "relationships through relentless focus on customer satisfaction despite limited early resources.",
                            className="text-muted fs-6 mb-0"
                        )
                    ], className="timeline-content")
                ], className="timeline-item col-md-10 mx-auto"),

                # Phase 2
                html.Div([
                    html.Div([
                        html.Span("2018 – 2020", className="badge mb-2 px-3 py-2 fs-7 rounded-pill text-white", style={'backgroundColor': 'var(--green)'}),
                        html.H4("Phase 2: Capability & Compliance", className="fw-bold text-dark mb-2"),
                        html.P(
                            "Transitioned to VAT-registered operations, focused on UPS power solutions for CT systems, "
                            "and secured key certifications including PhilGEPS Platinum and FDA LTO. Appointed Fujifilm distributor.",
                            className="text-muted fs-6 mb-0"
                        )
                    ], className="timeline-content")
                ], className="timeline-item col-md-10 mx-auto"),

                # Phase 3
                html.Div([
                    html.Div([
                        html.Span("2021 – 2023", className="badge mb-2 px-3 py-2 fs-7 rounded-pill text-white", style={'backgroundColor': 'var(--green)'}),
                        html.H4("Phase 3: Solutions Provider Transition", className="fw-bold text-dark mb-2"),
                        html.P(
                            "Expanded into big-ticket equipment sales and technical services (preventative maintenance, calibration, repairs). "
                            "Delivered major projects including 32-slice CT Scans and Cardio-Vascular Ultrasound systems.",
                            className="text-muted fs-6 mb-0"
                        )
                    ], className="timeline-content")
                ], className="timeline-item col-md-10 mx-auto"),

                # Phase 4
                html.Div([
                    html.Div([
                        html.Span("2024 – 2026+", className="badge mb-2 px-3 py-2 fs-7 rounded-pill text-white", style={'backgroundColor': 'var(--green)'}),
                        html.H4("Phase 4: National Scale & Expansion", className="fw-bold text-dark mb-2"),
                        html.P(
                            "Executed major advanced systems deliveries (including ₱128.9M MRI 1.5T project). "
                            "Transitioned into a national medical channel partner establishing a Metro Manila National HQ.",
                            className="text-muted fs-6 mb-0"
                        )
                    ], className="timeline-content")
                ], className="timeline-item col-md-10 mx-auto"),
            ], className="timeline")
        ], className="py-4")
    ], className="container mb-5"),

    # 5. GOVERNANCE & LEADERSHIP
    html.Div([
        html.Div([
            html.H6("LEADERSHIP", className="fw-bold text-uppercase mb-2 text-center", style={'color': 'var(--dark-green)'}),
            html.H2("Governance & Leadership", className="fw-bold text-dark mb-5 text-center"),

            html.Div([
                html.Div([
                    html.Div([
                        html.H5("Ceceli B. Cellona", className="fw-bold text-dark mb-1"),
                        html.P("President", className="text-muted fw-semibold small mb-0")
                    ], className="leader-card text-center h-100")
                ], className="col-md-4 mb-4"),

                html.Div([
                    html.Div([
                        html.H5("Eric Vincent C. Cellona", className="fw-bold text-dark mb-1"),
                        html.P("Vice President / CEO", className="text-muted fw-semibold small mb-0")
                    ], className="leader-card text-center h-100")
                ], className="col-md-4 mb-4"),

                html.Div([
                    html.Div([
                        html.H5("John Philip C. Cellona", className="fw-bold text-dark mb-1"),
                        html.P("Operations Head", className="text-muted fw-semibold small mb-0")
                    ], className="leader-card text-center h-100")
                ], className="col-md-4 mb-4"),
            ], className="row justify-content-center")
        ], className="py-4")
    ], className="container mb-5")

])