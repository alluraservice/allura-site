import dash
from dash import html

import site_ui as ui
from database.db_handler import get_categories_by_type

dash.register_page(__name__, path='/products')


def _category_cards():
    try:
        categories = get_categories_by_type("Products") or []
    except Exception as e:
        print(f"Error loading product categories: {e}")
        categories = []
    if not categories:
        return html.P("There are no existing categories.", className="catalog-empty")
    return html.Div([
        html.Div([
            html.A([
                html.Div([
                    html.Div([
                        html.H3(cat["name"], className="category-title"),
                        html.P(cat.get("description") or "Explore advanced diagnostic solutions and clinical essentials.",
                               className="category-desc"),
                    ], className="category-text-group"),
                    html.Span("view products", className="category-link-btn")
                ], className="category-content")
            ], href=ui.catalog_href('category', cat['id']), className="category-card",
               style={"backgroundImage": f"url('/{str(cat.get('image_url') or '').lstrip('/')}')", "width": "100%"})
        ], className="col-lg-4 col-md-6 mb-4 category-col")
        for cat in categories
    ], className="row")


def layout(*args, **kwargs):
    return html.Div([
        ui.page_header(
            "Products",
            "Diagnostic imaging, clinical equipment, and hospital supplies from trusted global manufacturers.",
            crumbs=[("Home", "/home"), ("Products", None)],
            actions=[html.A("View all products", href="/products/all", className="a-btn a-btn-light")],
        ),
        html.Div([
            # Intro card
            html.Div([
                html.Div([
                    html.H3("Empowering Clinical Excellence with Advanced Medical Solutions", className="card-title"),
                    html.P(
                        "Equipping healthcare facilities with cutting-edge diagnostic imaging systems, dependable clinical devices, "
                        "and essential supplies engineered for superior patient care.",
                        className="card-text"
                    ),
                    html.A("View All Products", href="/products/all", className="btn-white")
                ], className="section-card-content")
            ], className="section-card", style={
                "backgroundImage": "linear-gradient(rgba(0,0,0,0.5), rgba(0,0,0,0.5)), url('/assets/pictures/products/radiology/ct_scan/ct_5300.png')",
                "maxWidth": "none", "margin": "0"}),

            # Categories
            html.Div([
                ui.section_head("Browse", "Search by Category",
                                "Pick a category to see every product in it, or use the full list to search by name."),
                _category_cards(),
            ], className="site-section"),

            # Service cross-link: Allura sells and services
            html.Div([
                html.Div([
                    html.Div([
                        html.P("After the sale", className="site-eyebrow"),
                        html.H4("Installation, maintenance and power protection, from the same team",
                                style={"fontSize": "1.1rem", "margin": 0}),
                    ]),
                    html.A("See our services", href="/services", className="a-btn a-btn-primary"),
                ], className="d-flex flex-wrap justify-content-between align-items-center gap-3"),
            ], className="a-card site-card-pad mt-2"),
        ], className="site-container"),
    ], className="site-shell")
