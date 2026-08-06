import dash
from dash import html, dcc, callback, Input, Output
import pandas as pd
from database import db_handler

dash.register_page(__name__, path='/product-categories', title='Allura Enterprise - Products')


def get_featured_products():
    """Queries featured products from PostgreSQL via db_handler."""
    query = """
        SELECT 
            i.id,
            LOWER(REPLACE(REPLACE(i.name, ' ', '-'), '/', '-')) AS slug,
            i.name AS title,
            i.short_description AS description,
            i.image_url AS image
        FROM items i
        JOIN categories c ON i.category_id = c.id
        JOIN types t ON c.type_id = t.id
        WHERE LOWER(t.name) = 'product' AND i.is_featured = TRUE AND i.is_active = TRUE;
    """
    df = db_handler.fetch_data_df(query)
    if df.empty:
        return []
    
    # Fallback to SVG icon if photo is missing or empty
    df['image'] = df['image'].apply(
        lambda x: x if pd.notna(x) and str(x).strip() != "" else "/assets/icons/product_icon.svg"
    )
    
    return df.to_dict('records')


def layout():
    # Fetch categories directly with image_path from DB
    categories_data = db_handler.get_category_cards_by_type('Product')

    return html.Div(
        className="categories-page-wrapper",
        children=[
            # 1. HERO TITLE BANNER
            html.Div(
                className="cat-hero-banner",
                children=[
                    html.Div(
                        className="cat-hero-overlay",
                        children=[
                            html.H1("PRODUCTS", className="cat-hero-title"),
                            html.P(
                                "Allura Enterprise offers advanced healthcare equipment, from critical care and radiology to industrial power protection.",
                                className="cat-hero-subtitle"
                            )
                        ]
                    )
                ]
            ),

            # 2. SEARCH & ALLUBOT BAR
            html.Div(
                className="cat-search-section",
                children=[
                    html.Div(
                        className="cat-search-box-wrapper",
                        children=[
                            html.Img(src="/assets/icons/search.svg", className="cat-search-icon"),
                            dcc.Input(
                                id="category-search-input",
                                type="text",
                                placeholder="Search product...",
                                className="cat-search-input"
                            )
                        ]
                    ),
                    html.Button(
                        children=[
                            html.Img(src="/assets/icons/allubot1.svg", className="cat-allubot-icon-white"),
                            "Not sure what you need? Ask AlluBot"
                        ],
                        id="allubot-trigger-product-categories", n_clicks=0,
                        className="cat-allubot-btn"
                    )
                ]
            ),

            # 3. DYNAMIC CAROUSEL CATEGORY CARDS
            html.Div(
                className="carousel-container-relative",
                children=[
                    html.Button(
                        "‹",
                        id="cat-scroll-left-btn",
                        className="carousel-nav-btn nav-left hidden",
                        n_clicks=0
                    ),
                    html.Div(
                        id="cat-carousel-container",
                        className="cards-scroll-container hide-scrollbar",
                        children=[
                            html.A(
                                href=f"/product-list?category={cat['id']}",
                                className="category-card square-card",
                                children=[
                                    html.Img(
                                        src=cat["img"], 
                                        className="category-card-bg product-icon" if "product_icon" in str(cat["img"]) else "category-card-bg", 
                                        alt=cat["title"]
                                    ),
                                    html.Div(className="category-card-overlay"),
                                    html.Div(
                                        className="category-card-content",
                                        children=[
                                            html.H3(cat["title"], className="category-card-title"),
                                            html.Span("view products", className="category-card-subtext")
                                        ]
                                    )
                                ]
                            ) for cat in categories_data
                        ] if categories_data else [html.P("No product categories available.", className="no-data-text")]
                    ),
                    html.Button(
                        "›",
                        id="cat-scroll-right-btn",
                        className="carousel-nav-btn nav-right",
                        n_clicks=0
                    )
                ]
            ),

            # 4. DYNAMIC FEATURED PRODUCT SHOWCASE (Rotates every 10s)
            dcc.Interval(
                id='featured-product-interval',
                interval=10 * 1000,
                n_intervals=0
            ),
            
            html.Div(
                className="featured-product-section",
                children=[
                    html.Div(
                        id="featured-product-card",
                        className="featured-product-card",
                        children=[]
                    )
                ]
            )
        ]
    )


# Clientside Callback for Horizontal Carousel Scroll
dash.clientside_callback(
    """
    function(leftClicks, rightClicks) {
        const container = document.getElementById('cat-carousel-container');
        const prevBtn = document.getElementById('cat-scroll-left-btn');
        const nextBtn = document.getElementById('cat-scroll-right-btn');
        
        if (!container || !prevBtn || !nextBtn) return "";

        function updateNavVisibility() {
            const scrollLeft = container.scrollLeft;
            const maxScrollLeft = container.scrollWidth - container.clientWidth;

            if (scrollLeft <= 1) {
                prevBtn.classList.add('hidden');
            } else {
                prevBtn.classList.remove('hidden');
            }

            if (scrollLeft >= maxScrollLeft - 1) {
                nextBtn.classList.add('hidden');
            } else {
                nextBtn.classList.remove('hidden');
            }
        }

        if (!container.dataset.scrollListenerAttached) {
            container.dataset.scrollListenerAttached = "true";
            container.addEventListener('scroll', updateNavVisibility);
            window.addEventListener('resize', updateNavVisibility);
        }

        const ctx = dash_clientside.callback_context;
        if (ctx.triggered.length) {
            const triggerId = ctx.triggered[0].prop_id.split('.')[0];
            const scrollAmount = 320;
            
            if (triggerId === 'cat-scroll-left-btn') {
                container.scrollBy({ left: -scrollAmount, behavior: 'smooth' });
            } else if (triggerId === 'cat-scroll-right-btn') {
                container.scrollBy({ left: scrollAmount, behavior: 'smooth' });
            }
            
            setTimeout(updateNavVisibility, 350);
        }

        return "";
    }
    """,
    Output("cat-carousel-container", "data-scroll"),
    Input("cat-scroll-left-btn", "n_clicks"),
    Input("cat-scroll-right-btn", "n_clicks"),
    prevent_initial_call=True
)


@callback(
    Output("featured-product-card", "children"),
    Input("featured-product-interval", "n_intervals")
)
def update_featured_product(n):
    featured_list = get_featured_products()
    
    if not featured_list:
        return html.P("No featured products currently available.", className="featured-desc")

    selected = featured_list[n % len(featured_list)]
    
    # Returning a wrapper Div with a dynamic key forces Dash to re-render 
    # and trigger the CSS fade animation on each rotation.
    return html.Div(
        key=f"feat-prod-{selected.get('id')}",
        className="featured-card-inner",
        style={"display": "flex", "alignItems": "center", "width": "100%", "gap": "40px"},
        children=[
            html.Div(
                className="featured-img-container",
                children=[html.Img(src=selected.get("image"), className="featured-img")]
            ),
            html.Div(
                className="featured-info-container",
                children=[
                    html.H2(selected.get("title"), className="featured-title"),
                    html.P(selected.get("description", ""), className="featured-desc"),
                    dcc.Link(
                        "View product",
                        href=f"/product-details?id={selected.get('id')}",
                        className="featured-view-btn"
                    )
                ]
            )
        ]
    )