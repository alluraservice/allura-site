import dash
from dash import html

import site_ui as ui

dash.register_page(__name__, path='/about-us', title='About Us - Allura Enterprise')

STATS = [
    ("Since 2014", "10+ years", "of serving hospitals"),
    ("Certified", "Platinum", "PhilGEPS & FDA LTO"),
    ("Footprint", "Nationwide", "Luzon & Visayas"),
    ("Growth", "800%+", "sales revenue growth"),
]

CAPABILITIES = [
    ("Direct Sales & Distribution", "Radiology, MRI, CT Scans, Ultrasound, OR Equipment, and Hospital IT."),
    ("Power Quality Solutions", "Medical-grade UPS and voltage stabilization for sensitive diagnostic gear."),
    ("Lifecycle Support & Repairs", "Preventive maintenance, system calibration, site shielding, and repairs."),
]

TIMELINE = [
    ("2014 – 2017", "Phase 1: Foundation & Trust",
     "Registered as a regional trading business. Built foundational trust and long-term hospital relationships "
     "through relentless focus on customer satisfaction despite limited early resources."),
    ("2018 – 2020", "Phase 2: Capability & Compliance",
     "Transitioned to VAT-registered operations, focused on UPS power solutions for CT systems, and secured key "
     "certifications including PhilGEPS Platinum and FDA LTO. Appointed Fujifilm distributor."),
    ("2021 – 2023", "Phase 3: Solutions Provider Transition",
     "Expanded into big-ticket equipment sales and technical services (preventive maintenance, calibration, repairs). "
     "Delivered major projects including 32-slice CT Scans and Cardio-Vascular Ultrasound systems."),
    ("2024 – 2026+", "Phase 4: National Scale & Expansion",
     "Achieved a sales revenue growth of more than 800%. Transitioned into a national medical channel partner "
     "establishing a Metro Manila National HQ."),
]

LEADERS = [
    ("Ceceli B. Cellona", "President", "/assets/pictures/about/leader_ceceli.jpg"),
    ("Eric Vincent C. Cellona", "Vice President / CEO", "/assets/pictures/about/leader_eric.jpg"),
    ("John Philip C. Cellona", "Operations Head", "/assets/pictures/about/leader_john.jpg"),
]


def _initials(name):
    parts = [p for p in name.replace('.', '').split() if len(p) > 1]
    return (parts[0][0] + parts[-1][0]).upper() if parts else "A"


# ==========================================
# PAGE LAYOUT
# ==========================================
def layout(*args, **kwargs):
    return html.Div([
        # Larger, centred banner (variant='feature'); every other inner page uses the standard hero
        ui.page_header(
            "From Regional Pioneer to National Healthcare Partner",
            "Established in 2014, Allura Enterprise delivers reliable radiology, medical imaging, power infrastructure, "
            "and specialized technical services to hospitals nationwide.",
            crumbs=[("Home", "/home"), ("About Us", None)],
            variant='feature',
        ),
        html.Div([
            # Stats
            html.Div([
                html.Div([html.Div(k, className="k"), html.Div(v, className="v"), html.Div(s, className="s")], className="stat")
                for k, v, s in STATS
            ], className="stat-row"),

            # Who we are + capabilities
            html.Div([
                html.Div([
                    html.Div([
                        ui.section_head("Who we are", "Complete Technical & Solutions Care for Hospitals"),
                        html.P(
                            "Allura Enterprise is a trusted medical device distributor and service provider. Over a decade of "
                            "organic growth has elevated us from a regional trading firm into a full-scale channel partner capable "
                            "of managing turn-key medical installations, power conditioning, and after-sales maintenance.",
                            className="site-lead mb-3"),
                        html.P(
                            "We solve the hospital sector's critical challenge: providing a single accountable, compliant, and "
                            "technically proficient partner that bridges global medical technology directly to local clinical operations.",
                            className="site-lead"),
                    ], className="col-lg-6 mb-4 mb-lg-0"),
                    html.Div([
                        html.Div([
                            html.Div(html.H6("Our Strategic Capabilities"), className="a-card-head"),
                            html.Div([
                                html.Div([html.B(t, className="d-block"), html.Span(d, className="text-muted small")],
                                         className="py-2" + (" border-bottom" if i < len(CAPABILITIES) - 1 else ""))
                                for i, (t, d) in enumerate(CAPABILITIES)
                            ], className="a-card-body"),
                            html.Div([
                                html.A("Our Products", href="/products", className="a-btn a-btn-primary a-btn-sm"),
                                html.A("Our Services", href="/services", className="a-btn a-btn-outline a-btn-sm"),
                            ], className="a-card-body pt-0 d-flex gap-2"),
                        ], className="a-card"),
                    ], className="col-lg-6"),
                ], className="row align-items-center"),
            ], className="site-section"),

            # Timeline
            html.Div([
                ui.section_head("Our history", "The Allura Growth Story"),
                html.Div(html.Div([
                    html.Div([
                        html.Span(years, className="chip chip-active plain"),
                        html.H5(title),
                        html.P(text),
                    ], className="tl-item")
                    for years, title, text in TIMELINE
                ], className="tl"), className="a-card site-card-pad"),
            ], className="site-section"),

            # Leadership
            html.Div([
                ui.section_head("Leadership", "Governance & Leadership"),
                html.Div([
                    html.Div([
                        html.Img(src=photo, alt=name, className="leader-photo") if photo
                        else html.Div(_initials(name), className="avatar lg"),
                        html.H5(name),
                        html.Span(role),
                    ], className="a-card leader")
                    for name, role, photo in LEADERS
                ], className="leader-grid"),
            ], className="site-section"),
        ], className="site-container narrow"),
    ], className="site-shell")
