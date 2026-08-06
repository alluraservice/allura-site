import dash
from dash import html, dcc
from database import db_handler

dash.register_page(__name__, path='/', title='Allura Enterprise - Home')


def create_card(title, img_url, link_url, subtext="view products"):
    """Helper to render category cards consistently with fallback image logic."""
    # Fallback to cover_photo.jpg if image URL/path is empty or invalid
    final_img = img_url if img_url and str(img_url).strip() != "" else "/assets/pictures/cover_photo.jpg"

    return html.A(
        href=link_url,
        className="category-card square-card",
        children=[
            html.Img(src=final_img, className="category-card-bg", alt=title),
            html.Div(className="category-card-overlay"),
            html.Div(
                className="category-card-content",
                children=[
                    html.H3(title, className="category-card-title"),
                    html.Span(subtext, className="category-card-subtext")
                ]
            )
        ]
    )


def layout():
    # Fetch category cards metadata directly from PostgreSQL via db_handler
    product_categories = db_handler.get_category_cards_by_type('Product')
    service_categories = db_handler.get_category_cards_by_type('Service')

    # Build product cards using database metadata targeting /product-list
    product_cards = [
        create_card(
            cat["title"],
            cat.get("img"),
            f"/product-list?category={cat['id']}",
            "view products"
        )
        for cat in product_categories
    ]

    # Build service cards using database metadata targeting /service-list
    service_cards = [
        create_card(
            srv["title"],
            srv.get("img"),
            f"/service-list?category={srv['id']}",
            "view services"
        )
        for srv in service_categories
    ]

    return html.Div([
        # -------------------------------------------------------------
        # 1. Hero Cover Section
        # -------------------------------------------------------------
        html.Section(
            className="hero-section",
            children=[
                html.Div(className="hero-overlay"),
                html.Div(
                    className="hero-content",
                    children=[
                        html.H1([
                            "Precision Equipment.", html.Br(),
                            "Unfailing Power.", html.Br(),
                            "Protecting Lives."
                        ], className="hero-headline"),
                        html.P(
                            "Your trusted partner in Medical Distribution and Power Protection solutions across the Philippines.",
                            className="hero-subline"
                        )
                    ]
                )
            ]
        ),

        # -------------------------------------------------------------
        # 2. AlluBot Banner Section
        # -------------------------------------------------------------
        html.Section(
            className="allubot-banner",
            children=[
                html.Div(
                    className="allubot-container",
                    children=[
                        html.Img(src="/assets/icons/allubot2.svg", className="allubot-illustration", alt="AlluBot"),
                        html.Div(
                            className="allubot-text-content",
                            children=[
                                html.Span("Not sure what you need?", className="allubot-eyebrow"),
                                html.H2("Ask AlluBot!", className="allubot-headline"),
                                html.P(
                                    "Your 24/7 AI guide can help you find products by features or clinical needs, "
                                    "request technical datasheets and service details, match medical gear with the right "
                                    "UPS/Power solution, and many more!",
                                    className="allubot-description"
                                ),
                                html.Button(
                                    children=[
                                        html.Img(src="/assets/icons/allubot1.svg", className="allubot-btn-icon", alt=""),
                                        "Chat with AlluBot"
                                    ],
                                    id="allubot-trigger-home", n_clicks=0,
                                    className="allubot-cta-btn"
                                )
                            ]
                        )
                    ]
                )
            ]
        ),

        # -------------------------------------------------------------
        # 3. Explore Our Products (Dynamic Carousel)
        # -------------------------------------------------------------
        html.Section(
            className="explore-section products-section",
            children=[
                html.H2("Explore our Products", className="section-title"),
                html.Div(
                    className="carousel-container-relative",
                    children=[
                        html.Button(
                            "‹",
                            id="btn-scroll-left",
                            className="carousel-nav-btn nav-left hidden",
                            n_clicks=0
                        ),
                        html.Div(
                            id="products-scroll-wrapper",
                            className="cards-scroll-container hide-scrollbar",
                            children=product_cards if product_cards else [html.P("No product categories available.", className="no-data-text")]
                        ),
                        html.Button(
                            "›",
                            id="btn-scroll-right",
                            className="carousel-nav-btn nav-right",
                            n_clicks=0
                        ),
                    ]
                ),
                html.Div(
                    className="center-btn-wrapper",
                    children=[
                        dcc.Link("View all products", href="/product-categories", className="primary-pill-btn")
                    ]
                )
            ]
        ),

        # -------------------------------------------------------------
        # 4. Explore Our Services (Dynamic Centered Cards)
        # -------------------------------------------------------------
        html.Section(
            className="explore-section services-section",
            children=[
                html.H2("Explore our Services", className="section-title"),
                html.Div(
                    className="services-centered-container",
                    children=service_cards if service_cards else [html.P("No service categories available.", className="no-data-text")]
                ),
                html.Div(
                    className="center-btn-wrapper",
                    children=[
                        dcc.Link("View all services", href="/service-categories", className="primary-pill-btn")
                    ]
                )
            ]
        )
    ])


# Dash Clientside Callback for smooth scrolling & nav button visibility
dash.clientside_callback(
    """
    function(left_clicks, right_clicks) {
        const container = document.getElementById('products-scroll-wrapper');
        const prevBtn = document.getElementById('btn-scroll-left');
        const nextBtn = document.getElementById('btn-scroll-right');
        
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
            const button_id = ctx.triggered[0].prop_id.split('.')[0];
            const scrollAmount = 320;
            
            if (button_id === 'btn-scroll-left') {
                container.scrollBy({ left: -scrollAmount, behavior: 'smooth' });
            } else if (button_id === 'btn-scroll-right') {
                container.scrollBy({ left: scrollAmount, behavior: 'smooth' });
            }
            
            setTimeout(updateNavVisibility, 350);
        }

        return "";
    }
    """,
    dash.Output('products-scroll-wrapper', 'data-scroll'),
    [dash.Input('btn-scroll-left', 'n_clicks'), dash.Input('btn-scroll-right', 'n_clicks')],
    prevent_initial_call=True
)