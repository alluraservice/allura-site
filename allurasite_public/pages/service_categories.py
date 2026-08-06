import dash
from dash import html, dcc, callback, Input, Output
import pandas as pd
from database import db_handler

dash.register_page(__name__, path='/service-categories', title='Allura Enterprise - Services')


def get_featured_services():
    """Queries featured services from PostgreSQL via db_handler."""
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
        WHERE LOWER(t.name) = 'service' AND i.is_featured = TRUE AND i.is_active = TRUE;
    """
    df = db_handler.fetch_data_df(query)
    if df.empty:
        return []
    
    # Fallback to SVG icon if photo is missing or empty
    df['image'] = df['image'].apply(
        lambda x: x if pd.notna(x) and str(x).strip() != "" else "/assets/icons/service_icon.svg"
    )
    
    return df.to_dict('records')


def layout():
    # Fetch categories directly with image_path from DB
    services_data = db_handler.get_category_cards_by_type('Service')

    return html.Div(
        className="categories-page-wrapper services-theme",
        children=[
            # 1. HERO TITLE BANNER
            html.Div(
                className="cat-hero-banner service-hero-bg",
                children=[
                    html.Div(
                        className="cat-hero-overlay",
                        children=[
                            html.H1("SERVICES", className="cat-hero-title"),
                            html.P(
                                "Comprehensive maintenance, power integration, and technical solutions for healthcare facilities.",
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
                                id="service-search-input",
                                type="text",
                                placeholder="Search service...",
                                className="cat-search-input"
                            )
                        ]
                    ),
                    html.Button(
                        children=[
                            html.Img(src="/assets/icons/allubot1.svg", className="cat-allubot-icon-white"),
                            "Not sure what you need? Ask AlluBot"
                        ],
                        id="allubot-trigger-service-categories", n_clicks=0,
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
                        id="srv-scroll-left-btn",
                        className="carousel-nav-btn nav-left hidden",
                        n_clicks=0
                    ),
                    html.Div(
                        id="srv-carousel-container",
                        className="cards-scroll-container hide-scrollbar",
                        children=[
                            html.A(
                                href=f"/service-list?category={s['id']}",
                                className="category-card square-card",
                                children=[
                                    html.Img(
                                        src=s["img"], 
                                        className="category-card-bg service-icon" if "service_icon" in str(s["img"]) else "category-card-bg", 
                                        alt=s["title"]
                                    ),
                                    html.Div(className="category-card-overlay"),
                                    html.Div(
                                        className="category-card-content",
                                        children=[
                                            html.H3(s["title"], className="category-card-title"),
                                            html.Span("view services", className="category-card-subtext")
                                        ]
                                    )
                                ]
                            ) for s in services_data
                        ] if services_data else [html.P("No service categories available.", className="no-data-text")]
                    ),
                    html.Button(
                        "›",
                        id="srv-scroll-right-btn",
                        className="carousel-nav-btn nav-right",
                        n_clicks=0
                    )
                ]
            ),

            # 4. DYNAMIC FEATURED SERVICE SHOWCASE (Rotates every 10s)
            dcc.Interval(
                id='featured-service-interval',
                interval=10 * 1000,
                n_intervals=0
            ),
            
            html.Div(
                className="featured-product-section",
                children=[
                    html.Div(
                        id="featured-service-card",
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
        const container = document.getElementById('srv-carousel-container');
        const prevBtn = document.getElementById('srv-scroll-left-btn');
        const nextBtn = document.getElementById('srv-scroll-right-btn');
        
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
            
            if (triggerId === 'srv-scroll-left-btn') {
                container.scrollBy({ left: -scrollAmount, behavior: 'smooth' });
            } else if (triggerId === 'srv-scroll-right-btn') {
                container.scrollBy({ left: scrollAmount, behavior: 'smooth' });
            }
            
            setTimeout(updateNavVisibility, 350);
        }

        return "";
    }
    """,
    Output("srv-carousel-container", "data-scroll"),
    Input("srv-scroll-left-btn", "n_clicks"),
    Input("srv-scroll-right-btn", "n_clicks"),
    prevent_initial_call=True
)


@callback(
    Output("featured-service-card", "children"),
    Input("featured-service-interval", "n_intervals")
)
def update_featured_service(n):
    featured_list = get_featured_services()

    if not featured_list:
        return html.P("No featured services currently available.", className="featured-desc")

    selected = featured_list[n % len(featured_list)]

    # Returning a wrapper Div with a dynamic key forces Dash to re-render 
    # and trigger the CSS fade animation on each rotation.
    return html.Div(
        key=f"feat-srv-{selected.get('id')}",
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
                        "View service",
                        href=f"/service-details?id={selected.get('id')}",
                        className="featured-view-btn"
                    )
                ]
            )
        ]
    )