"""
Home - works for everyone: hospitals that already know Allura and those meeting us for the first time.

  1. Hero + short introduction
  2. What we do                         (equipment, service, consultation)
  3. Imaging & radiology carousel       (live from the database, one icon per modality)
  4. Why hospitals work with us         (credentials and capabilities)
  5. How working with us works          (how a request is handled, with a reference number)
  6. Contact, social and Allura Bot cards
Every section title uses ui.section_head, so headings, subtitles and body text share one type scale (40_site.css).
"""
import dash
from dash import html
import dash_bootstrap_components as dbc

import site_ui as ui
from database.db_handler import get_categories_by_type, get_modalities
from utils.site_content import get_content, lines, settings as site_settings

dash.register_page(__name__, path='/home')

# Text comes from Admin › Website Content › Home (defaults in utils/site_content.py).
# The three "What we do" cards keep their icons, photos and links here; only their words are editable.
RECAP_FIXED = [
    {"icon": "product_icon.svg", "image": "/assets/pictures/products/radiology/radiology_cover.jpg",
     "link": ("Browse the catalog", "/products")},
    {"icon": "service_icon.svg", "image": "/assets/pictures/services/equipment_services/medical_equipment_service_cover.webp",
     "link": ("See our services", "/services")},
    {"icon": "contact_us.svg", "image": "/assets/pictures/intensive_care_unit.jpg",
     "link": ("Talk to our team", "/contact_us")},
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
            html.Span(ui.icon_img(ui.catalog_icon(mod["name"], 'radiology.svg')), className="modality-icon"),
            html.H4(mod["name"], className="modality-title"),
            html.Span("view products  ›", className="modality-link")
        ], href=ui.catalog_href('modality', mod['id']), className="modality-card")
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
    c = get_content('home')
    s = site_settings()
    cards = [dict(RECAP_FIXED[i], **c['recap'][i]) for i in range(min(len(RECAP_FIXED), len(c['recap'])))]
    recap = html.Div([
        ui.section_head("What we do", c['recap_title'], c['recap_text'], center=True),
        html.Div([
            html.Div([
                html.Div(className="img", style={"backgroundImage": f"url('{r['image']}')"}),
                html.Div([
                    html.Span(ui.icon_img(f"/assets/icons/{r['icon']}"), className="feature-icon"),
                    html.Span(r["tag"], className="home-tag"),
                    html.H4(r["title"]),
                    html.P(r["text"]),
                    html.Ul([html.Li(p) for p in lines(r["points"])], className="tick-list"),
                    html.A(r["link"][0] + "  ›", href=r["link"][1], className="home-card-link"),
                ], className="body"),
            ], className="a-card feature-card")
            for r in cards
        ], className="feature-grid"),
    ], className="home-section")

    lesser_known = html.Div([
        ui.section_head("Why Allura", c['why_title'], c['why_text'], center=True),
        html.Div([
            html.Div([html.Div(x.get('k'), className="k"), html.Div(x.get('v'), className="v"),
                      html.Div(x.get('s'), className="s")], className="stat")
            for x in c['stats']
        ], className="stat-row mb-3"),
        html.Div([
            html.Div([
                html.Span(str(i), className="num"),
                html.Div([html.B(w.get('title')), html.P(w.get('text'))]),
            ], className="know-item")
            for i, w in enumerate(c['why'], start=1)
        ], className="a-card know-grid"),
        html.Div(html.A("Read our story", href="/about_us", className="a-btn a-btn-outline"), className="text-center mt-3"),
    ], className="home-section")

    next_steps = html.Div([
        ui.section_head("Getting started", c['steps_title'], c['steps_text'], center=True),
        html.Div([
            html.Div([html.Span(str(i), className="num"), html.H5(st.get('title')), html.P(st.get('text'))], className="step")
            for i, st in enumerate(c['steps'], start=1)
        ], className="a-card steps"),
    ], className="home-section")

    return html.Div([

        # 1. Hero
        html.Div([
            html.Div([
                html.Div(c['hero_eyebrow'], className="hero-subtitle"),
                html.H1(c['hero_title'], className="hero-title"),
                html.P(c['hero_lead'], className="hero-lead"),
                html.Div([
                    html.A("Browse our catalog", href="/products", className="btn-white"),
                    html.A("Talk to our team", href="/contact_us", className="a-btn a-btn-light a-btn-lg"),
                ], className="hero-actions"),
            ], className="hero-content text-center")
        ], className="hero-section", style={"backgroundImage": "linear-gradient(rgba(0,0,0,0.4), rgba(0,0,0,0.4)), url('/assets/pictures/home/cover_photo.jpg')"}),

        # 1b. Introduction
        html.Div(ui.section_head(
            "About Allura", c['intro_title'], c['intro_text'], center=True), className="home-section home-intro"),

        # 2. What we do
        recap,

        # 3. Imaging & radiology
        html.Div([
            ui.section_head(
                "Featured", c['featured_title'], c['featured_text'], center=True),
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
            c['contact_title'],
            c['contact_text'],
            html.A([ui.icon_img("/assets/icons/contact_us.svg", class_name="btn-ico"), "Connect with Us"],
                   href="/contact_us", className="btn-white"),
            "/assets/pictures/home/home_contact_card.jpg",   # cropped from home_photo_1.jpeg (no logos)
            "center top",
        ),

        # 7. Follow us
        _section_card(
            c['follow_title'],
            c['follow_text'],
            html.Div([
                html.A(html.Img(src='/assets/icons/facebook.svg', alt="Facebook"), href=s['facebook_url'], rel="noopener noreferrer",
                       target="_blank", title="Facebook", className="social-btn"),
                html.A(html.Img(src='/assets/icons/linkedin.svg', alt="LinkedIn"), href=s['linkedin_url'], rel="noopener noreferrer",
                       target="_blank", title="LinkedIn", className="social-btn"),
            ], className="d-flex align-items-center gap-3 mt-3"),
            "/assets/pictures/home/home_follow_card.jpg",    # cropped from home_photo_2.jpeg (no logos)
            "center top",
        ),

        # 8. Meet Allura Bot
        html.Div([
            html.Div([
                dbc.Row([
                    dbc.Col([
                        html.Div([
                            html.H3(c['allubot_title'], className="card-title text-white"),
                            html.P(c['allubot_text'], className="card-text text-white"),
                            html.Button([ui.icon_img("/assets/icons/allubot1.svg", class_name="btn-ico"), "Chat with Allura Bot"],
                                        id="home_open_chatbot_btn",
                                        className="btn-white mt-3 d-inline-flex align-items-center")
                        ], className="p-5 d-flex flex-column justify-content-center h-100")
                    ], md=7),
                    dbc.Col([
                        html.Div([
                            html.Img(src='/assets/icons/allubot2.svg', alt="Allura Bot Avatar")
                        ], className="meet-allubot-img d-flex justify-content-center align-items-center h-100 p-3")
                    ], md=5, className="d-flex align-items-center justify-content-center")
                ], className="g-0 h-100 align-items-center")
            ], className="section-card-allubot container p-0 overflow-hidden", style={"backgroundColor": "var(--dark-green)"})
        ], className="py-4 pb-5"),

    ], className="site-shell home-shell")
