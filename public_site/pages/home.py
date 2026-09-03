import dash
import psycopg2
from dash import html, dcc
import dash_bootstrap_components as dbc
from database.db_handler import get_modalities

dash.register_page(__name__, path='/home')

modality_cards = [
    html.A([
        html.H4(mod["name"], className="modality-title"),
        html.Span("view products", className="modality-link")
    ], href=f"/products/{mod['id']}", className="modality-card", style={"backgroundImage": f"linear-gradient(rgba(0,0,0,0.3), rgba(0,0,0,0.3)), url('/{mod['image_url']}')"})
    for mod in get_modalities()
]

layout = html.Div([
    
    # ==========================================
    # SECTION 1: Hero Card
    # ==========================================
    html.Div([
        html.Div([
            html.Div("Allura Enterprise", className="hero-subtitle"),
            html.H1("Your Trusted Partner in Advanced Healthcare Solutions.", className="hero-title"),
        ], className="hero-content text-center")
    ], className="hero-section", style={"backgroundImage": "linear-gradient(rgba(0,0,0,0.4), rgba(0,0,0,0.4)), url('/assets/pictures/home/cover_photo.jpg')"})
    ,

    # ==========================================
    # SECTION 2: About Us
    # ==========================================
    html.Div([
        html.H2("Building Lasting Partnerships in Healthcare.", className="section-heading text-center"),
        html.P(
            "Creating real trust through open conversations, dependable technical support, "
            "and a genuine dedication to helping your hospital succeed every step of the way.",
            className="section-subtext text-center"
        ),
        html.Div([
            html.A("Get to Know Us More", href="/about_us", className="btn-green")
        ], className="text-center mt-4")
    ], className="section-no-border-1"),

    # ==========================================
    # SECTION 3: Solutions
    # ==========================================
    html.Div([
        html.Div([
            html.Div([
                html.H3("Bringing Medical Solutions to Your Hospital", className="card-title"),
                html.P(
                    "We source trusted medical technology from global manufacturers, tailoring each solution "
                    "and providing local care so your hospital always has a partner it can count on.",
                    className="card-text"
                ),
                html.A("Explore our Solutions", href="/products", className="btn-white")
            ], className="section-card-content")
        ], className="section-card container", style={"backgroundImage": "linear-gradient(rgba(0,0,0,0.5), rgba(0,0,0,0.5)), url('/assets/pictures/products/radiology/cath_lab/azurion_5_m12.png')"})
    ], className="py-4"),

    # ==========================================
    # SECTION 4: Imaging & Radiology
    # ==========================================
    html.Div([
        html.H2("Featuring our Imaging & Radiology Systems", className="section-heading text-center"),
        html.P(
            "Backed by deep technical expertise and a consultative approach, our core imaging and radiology portfolio "
            "delivers precision, reliability, and end-to-end support for modern healthcare institutions.",
            className="card-text"
        ),
        
        # Carousel / Scrollable Cards Row Preview
        html.Div([
            html.Button("‹", className="carousel-btn carousel-btn-left hidden"),
            html.Div([
                html.A([
                    html.H4(mod["name"], className="modality-title"),
                    html.Span("view products", className="modality-link")
                ], href=f"/products/{mod['id']}", className="modality-card", style={"backgroundImage": f"linear-gradient(rgba(0,0,0,0.3), rgba(0,0,0,0.3)), url('/{mod['image_url']}')"})
                for mod in get_modalities()
            ], className="cards-scroll-container d-flex gap-3 overflow-hidden"),
            html.Button("›", className="carousel-btn carousel-btn-right"),
        ], className="carousel-wrapper position-relative align-items-center d-flex justify-content-center container")
    ], className="section-no-border-2"),

    # ==========================================
    # SECTION 5: Contact Us
    # ==========================================
    html.Div([
        html.Div([
            html.Div([
                html.H3("Let's Discuss Your Institution's Next Project", className="card-title"),
                html.P(
                    "Whether you need a product proposal, equipment demonstration, or technical consultation, "
                    "our team is ready to assist you.",
                    className="card-text"
                ),
                html.A("Connect with Us", href="/contact_us", className="btn-white")
            ], className="section-card-content")
        ], className="section-card container", style={"backgroundImage": "linear-gradient(rgba(0,0,0,0.5), rgba(0,0,0,0.5)), url('/assets/pictures/home/contact_us.jpeg')"})
    ], className="py-4"),

    # ==========================================
    # SECTION 6: Follow Us
    # ==========================================
html.Div([
        html.Div([
            html.Div([
                html.H3("Stay Connected With Allura", className="card-title text-white"),
                html.P(
                    "Follow our journey, catch our latest industry updates, and connect with our team on social media.",
                    className="card-text text-white"
                ),
                html.Div([
                    html.A(html.Img(src='/assets/icons/facebook.svg'), href="https://facebook.com", target="_blank", className="me-3"),
                    html.A(html.Img(src='/assets/icons/linkedin.svg'), href="https://linkedin.com", target="_blank"),
                ], className="d-flex align-items-center mt-3")
            ], className="section-card-content")
        ], className="section-card container", style={"backgroundImage": "linear-gradient(rgba(0,0,0,0.5), rgba(0,0,0,0.5)), url('/assets/pictures/home/follow_us.jpg')"})
    ], className="py-4"),

    # ==========================================
    # SECTION 7: Meet AlluBot
    # ==========================================
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
                        html.Button([
                            "Chat with AlluBot"
                        ], id="home_open_chatbot_btn", className="btn-white mt-3 d-inline-flex align-items-center")
                    ], className="p-5 d-flex flex-column justify-content-center h-100")
                ], md=7),
                dbc.Col([
                    html.Div([
                        html.Img(src='/assets/icons/allubot2.svg', alt="AlluBot Avatar")
                    ], className="meet-allubot-img d-flex justify-content-center align-items-center h-100 p-3")
                ], md=5, className="d-flex align-items-center justify-content-center")
            ], className="g-0 h-100 align-items-center")
        ], className="section-card-allubot container p-0 overflow-hidden", style={"backgroundColor": "var(--dark-green)"})
    ], className="py-4 mb-5")

])