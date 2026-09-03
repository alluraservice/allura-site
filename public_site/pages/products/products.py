import dash
import psycopg2
from dash import html, dcc
import dash_bootstrap_components as dbc
from database.db_handler import get_categories_by_type
from app import app

dash.register_page(__name__, path='/products')

fetched_categories = get_categories_by_type("Products")

if fetched_categories:
    category_cards = [
        html.Div([
            html.A([
                html.Div([
                    html.Div([
                        html.H3(cat["name"], className="category-title"),
                        html.P(cat.get("description", "Explore advanced diagnostic solutions and clinical essentials."), className="category-desc"),
                    ], className="category-text-group"),
                    html.Span("view products", className="category-link-btn")
                ], className="category-content")
            ], href=f"/products/{cat['id']}", className="category-card", style={"backgroundImage": f"url('/{cat['image_url']}')", "width": "100%"})
        ], className="col-lg-4 col-md-6 mb-4 category-col")
        for cat in fetched_categories
    ]
    
    # Removed the 1000px max-width style so it matches the container above
    category_content = html.Div(category_cards, className="row justify-content-center")
else:
    category_content = html.Div(
        html.P("There are no existing categories.", className="text-center text-muted fs-5 py-4"),
        className="col-12"
    )

layout = html.Div([

    # ==========================================
    # SECTION 1: Hero Section
    # ==========================================
    html.Div([
        html.Div([
            html.H1("PRODUCTS", className="hero-title text-white"),
        ], className="hero-content text-start ps-5")
    ], className="hero-section-3"),

    # ==========================================
    # SECTION 3: Intro Card
    # ==========================================
    html.Div([
        html.Div([
            html.Div([
                html.H3("Empowering Clinical Excellence with Advanced Medical Solutions", className="card-title"),
                html.P(
                    "Equipping healthcare facilities with cutting-edge diagnostic imaging systems, dependable clinical devices, "
                    "and essential supplies engineered for superior patient care.",
                    className="card-text"
                ),
                html.A("View All Products", href="/products/all/none", className="btn-white")
            ], className="section-card-content")
        ], className="section-card container", style={"backgroundImage": "linear-gradient(rgba(0,0,0,0.5), rgba(0,0,0,0.5)), url('/assets/pictures/products/radiology/ct_scan/ct_5300.png')"})
    ], className="py-4", style={"marginTop":"30px"}),

# ==========================================
    # SECTION 4: Search by Category
    # ==========================================
    html.Div([
        html.Div([
            html.H2("Search by Category", className="section-heading text-center mb-5"),
            category_content
        ], className="container-fluid px-lg-5 py-5")
    ], className="section-no-border-2", style={"marginTop":"-60px"})

])