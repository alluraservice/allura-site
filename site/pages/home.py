"""
Home - works for everyone: hospitals that already know Allura and those meeting us for the first time.

  1. Hero + short introduction
  2. What we do                         (equipment, service, consultation)
  3. Imaging & radiology carousel       (live from the database)
  4. Why hospitals work with us         (credentials and capabilities)
  5. How working with us works          (how a request is handled, with a reference number)
  6. Contact, social and AlluBot cards
Every section title uses ui.section_head, so headings, subtitles and body text share one type scale (40_site.css).
"""
import dash
from dash import html
import dash_bootstrap_components as dbc

import site_ui as ui
from database.db_handler import get_categories_by_type, get_modalities

dash.register_page(__name__, path='/home')

RECAP = [
    {
        "tag": "Equipment",
        "title": "Imaging & clinical equipment",
        "image": "/assets/pictures/products/radiology/radiology_cover.jpg",
        "text": "Diagnostic imaging and clinical systems for every department, from CT, MRI and ultrasound to X-ray, C-arm and cath lab.",
        "points": ["Models sourced from trusted global manufacturers", "Configured to your room, volume and budget",
                   "Formal quotation with lead time and warranty"],
        "link": ("Browse the catalog", "/products"),
    },
    {
        "tag": "Service",
        "title": "Installation & lifecycle care",
        "image": "/assets/pictures/services/equipment_services/medical_equipment_service_cover.webp",
        "text": "The same team that supplies your equipment installs it and keeps it running afterwards.",
        "points": ["Installation & commissioning", "Preventive maintenance & calibration", "Repairs by trained engineers"],
        "link": ("See our services", "/services"),
    },
    {
        "tag": "Consultation",
        "title": "Consultation & project planning",
        "image": "/assets/pictures/intensive_care_unit.jpg",
        "text": "Not sure yet what your department needs? We help you plan the right equipment, site and budget before you commit.",
        "points": ["Needs assessment & product recommendations", "Site visit & room planning",
                   "Proposals for private and government procurement"],
        "link": ("Talk to our team", "/contact_us"),
    },
]

STATS = [
    ("Since 2014", "10+ years", "working with hospitals"),
    ("PhilGEPS", "Platinum", "registered supplier"),
    ("FDA", "LTO", "licensed to operate"),
    ("Footprint", "Nationwide", "Luzon & Visayas"),
]

LESSER_KNOWN = [
    ("We can join public procurement",
     "Our PhilGEPS Platinum registration and FDA License to Operate mean government hospitals and LGUs can buy "
     "from us through bidding, with the documents ready when you need them."),
    ("We prepare the site, not just the machine",
     "Room assessment, electrical works, power distribution and shielding support are handled by our own team, "
     "so a new system arrives to a room that is ready for it."),
    ("Power quality is where we started",
     "Allura began with UPS solutions for CT systems. That background shapes how we plan every installation "
     "around stable, protected power."),
    ("One partner from proposal to after-sales",
     "Sales, installation and maintenance stay with one accountable team, so you never have to explain your "
     "setup to a new supplier."),
]

NEXT_STEPS = [
    ("Send your request", "Use Contact Sales on a product, the Services form, or Contact Us. You get a reference "
                          "number right away."),
    ("We reply within a business day", "Our team follows up by email or phone, quoting your reference number."),
    ("Assessment & proposal", "Where needed we visit the site, then send a clear scope, quotation and schedule."),
    ("Delivery & after-sales", "Installation, handover and maintenance plans, with the same team from start to finish."),
]


def _modality_cards():
    """Only the Radiology sub-groups belong in the "Imaging & Radiology Systems" carousel,
    so Clinic Equipment and Supplies groups (e.g. Patient Monitoring Accessories) stay out of it."""
    try:
        radiology_ids = {c['id'] for c in (get_categories_by_type("Products") or [])
                         if 'radiolog' in str(c.get('name', '')).lower()}
        modalities = [m for m in (get_modalities() or [])
                      if not radiology_ids or m.get('category_id') in radiology_ids]
    except Exception as e:
        print(f"Error loading modalities for home: {e}")
        modalities = []
    return [
        html.A([
            html.H4(mod["name"], className="modality-title"),
            html.Span("view products", className="modality-link")
        ], href=ui.catalog_href('modality', mod['id']), className="modality-card",
           style={"backgroundImage": f"linear-gradient(rgba(0,0,0,0.3), rgba(0,0,0,0.3)), url('/{str(mod.get('image_url') or '').lstrip('/')}')"})
        for mod in modalities
    ]


def _section_card(title, text, button, image, position="center"):
    """The shared home-page card: dark image card with a white pill button.
    position = CSS background-position (e.g. "center top" keeps faces in view)."""
    return html.Div([
        html.Div([
            html.Div([
                html.H3(title, className="card-title"),
                html.P(text, className="card-text"),
                button,
            ], className="section-card-content")
        ], className="section-card container",
           style={"backgroundImage": f"linear-gradient(rgba(0,0,0,0.5), rgba(0,0,0,0.5)), url('{image}')",
                  "backgroundPosition": position})
    ], className="py-4")


def layout(*args, **kwargs):
    recap = html.Div([
        ui.section_head("What we do", "Equipment, service and guidance, from one team",
                        "Whether you're planning a new department or keeping existing systems running, "
                        "these are the three ways we support hospitals.",
                        center=True),
        html.Div([
            html.Div([
                html.Div(className="img", style={"backgroundImage": f"url('{r['image']}')"}),
                html.Div([
                    html.Span(r["tag"], className="home-tag"),
                    html.H4(r["title"]),
                    html.P(r["text"]),
                    html.Ul([html.Li(p) for p in r["points"]], className="tick-list"),
                    html.A(r["link"][0] + "  ›", href=r["link"][1], className="home-card-link"),
                ], className="body"),
            ], className="a-card feature-card")
            for r in RECAP
        ], className="feature-grid"),
    ], className="home-section")

    lesser_known = html.Div([
        ui.section_head("Why Allura", "Why hospitals work with us",
                        "Credentials and capabilities that make a difference once equipment is on site.",
                        center=True),
        html.Div([
            html.Div([html.Div(k, className="k"), html.Div(v, className="v"), html.Div(s, className="s")], className="stat")
            for k, v, s in STATS
        ], className="stat-row mb-3"),
        html.Div([
            html.Div([
                html.Span(str(i), className="num"),
                html.Div([html.B(title), html.P(text)]),
            ], className="know-item")
            for i, (title, text) in enumerate(LESSER_KNOWN, start=1)
        ], className="a-card know-grid"),
        html.Div(html.A("Read our story", href="/about_us", className="a-btn a-btn-outline"), className="text-center mt-3"),
    ], className="home-section")

    next_steps = html.Div([
        ui.section_head("Getting started", "How working with us works",
                        "Four simple steps, whether it's your first inquiry or your next project.", center=True),
        html.Div([
            html.Div([html.Span(str(i), className="num"), html.H5(title), html.P(text)], className="step")
            for i, (title, text) in enumerate(NEXT_STEPS, start=1)
        ], className="a-card steps"),
    ], className="home-section")

    return html.Div([

        # 1. Hero
        html.Div([
            html.Div([
                html.Div("Allura Enterprise", className="hero-subtitle"),
                html.H1("Your Trusted Partner in Advanced Healthcare Solutions.", className="hero-title"),
                html.P("Medical equipment, installation and lifecycle support for Philippine hospitals, "
                       "from one accountable team.", className="hero-lead"),
                html.Div([
                    html.A("Browse our catalog", href="/products", className="btn-white"),
                    html.A("Talk to our team", href="/contact_us", className="a-btn a-btn-light a-btn-lg"),
                ], className="hero-actions"),
            ], className="hero-content text-center")
        ], className="hero-section", style={"backgroundImage": "linear-gradient(rgba(0,0,0,0.4), rgba(0,0,0,0.4)), url('/assets/pictures/home/cover_photo.jpg')"}),

        # 1b. Introduction
        html.Div(ui.section_head(
            "About Allura",
            "A healthcare technology partner for Philippine hospitals",
            "Since 2014, Allura Enterprise has supplied, installed and maintained medical equipment for public and private "
            "hospitals. Whether we've worked together before or you're just getting to know us, here's how we can help.",
            center=True), className="home-section home-intro"),

        # 2. What we do
        recap,

        # 3. Imaging & radiology
        html.Div([
            ui.section_head(
                "Featured", "Imaging & Radiology Systems",
                "Backed by deep technical expertise and a consultative approach, our imaging and radiology portfolio "
                "delivers precision, reliability, and end-to-end support for modern healthcare institutions.",
                center=True),
            html.Div([
                html.Button("‹", className="carousel-btn carousel-btn-left hidden"),
                html.Div(_modality_cards(), className="cards-scroll-container d-flex gap-3 overflow-hidden"),
                html.Button("›", className="carousel-btn carousel-btn-right"),
            ], className="carousel-wrapper position-relative align-items-center d-flex justify-content-center container")
        ], className="home-section"),

        # 4. Why hospitals work with us
        lesser_known,

        # 5. How working with us works
        next_steps,

        # 6. Contact
        _section_card(
            "Let's Discuss Your Institution's Next Project",
            "Whether you need a product proposal, equipment demonstration, or technical consultation, "
            "our team is ready to assist you.",
            html.A("Connect with Us", href="/contact_us", className="btn-white"),
            "/assets/pictures/home/home_contact_card.jpg",   # cropped from home_photo_1.jpeg (no logos)
            "center top",
        ),

        # 7. Follow us
        _section_card(
            "Stay Connected With Allura",
            "Follow our journey, catch our latest industry updates, and connect with our team on social media.",
            html.Div([
                html.A(html.Img(src='/assets/icons/facebook.svg'), href="https://facebook.com", target="_blank", className="me-3"),
                html.A(html.Img(src='/assets/icons/linkedin.svg'), href="https://linkedin.com", target="_blank"),
            ], className="d-flex align-items-center mt-3"),
            "/assets/pictures/home/home_follow_card.jpg",    # cropped from home_photo_2.jpeg (no logos)
            "center top",
        ),

        # 8. Meet AlluBot
        html.Div([
            html.Div([
                dbc.Row([
                    dbc.Col([
                        html.Div([
                            html.H3("Meet AlluBot! Our AI Chatbot", className="card-title text-white"),
                            html.P(
                                "In case you're not sure what you need, let AlluBot guide you through our solutions "
                                "and instantly match your hospital with the right support.",
                                className="card-text text-white"
                            ),
                            html.Button(["Chat with AlluBot"], id="home_open_chatbot_btn",
                                        className="btn-white mt-3 d-inline-flex align-items-center")
                        ], className="p-5 d-flex flex-column justify-content-center h-100")
                    ], md=7),
                    dbc.Col([
                        html.Div([
                            html.Img(src='/assets/icons/allubot2.svg', alt="AlluBot Avatar")
                        ], className="meet-allubot-img d-flex justify-content-center align-items-center h-100 p-3")
                    ], md=5, className="d-flex align-items-center justify-content-center")
                ], className="g-0 h-100 align-items-center")
            ], className="section-card-allubot container p-0 overflow-hidden", style={"backgroundColor": "var(--dark-green)"})
        ], className="py-4 pb-5"),

    ], className="site-shell home-shell")
