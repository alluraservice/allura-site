import dash
from dash import html, dcc, callback, Input, Output
from urllib.parse import parse_qs
import pandas as pd
from database import db_handler
from allurasite_public.components import render_quote_modal, register_quote_modal_callback

dash.register_page(__name__, path='/service-details', title='Allura Enterprise - Service Details')

# Registered once at import time (NOT inside the page callback below) to avoid
# duplicate-callback-output errors. See components.register_quote_modal_callback.
_QUOTE_RECIPIENT_EMAIL = db_handler.get_site_settings().get('contact_email') or 'info@alluraenterpriseph.com'
register_quote_modal_callback('service', _QUOTE_RECIPIENT_EMAIL)


def get_item_details(item_id):
    """Fetches details for a specific service item."""
    if not item_id:
        return None
    query = """
        SELECT i.id, i.name, i.short_description, i.long_description, i.image_url, 
               c.name AS category_name, c.id AS category_id
        FROM items i
        LEFT JOIN categories c ON i.category_id = c.id
        WHERE i.id = %s AND i.is_active = TRUE
        LIMIT 1;
    """
    df = db_handler.fetch_data_df(query, (item_id,))
    if df.empty:
        return None
    return df.to_dict('records')[0]


def get_related_items(item_id, category_id):
    """Fetches related services based on the same category."""
    if not item_id or not category_id:
        return []
    query = """
        SELECT id, name AS title, image_url AS image
        FROM items
        WHERE category_id = %s AND id != %s AND is_active = TRUE
        LIMIT 4;
    """
    df = db_handler.fetch_data_df(query, (category_id, item_id))
    if df.empty:
        return []
    df['image'] = df['image'].apply(
        lambda x: x if pd.notna(x) and str(x).strip() != "" else "/assets/icons/service_icon.svg"
    )
    return df.to_dict('records')


def layout(id=None, **kwargs):
    return html.Div([
        dcc.Location(id='service-detail-url', refresh=False),
        html.Div(id='service-detail-content')
    ])


@callback(
    Output('service-detail-content', 'children'),
    Input('service-detail-url', 'search')
)
def update_service_detail_page(search):
    item_id = None
    if search:
        raw_query = search.lstrip('?')
        query_params = parse_qs(raw_query)
        if 'id' in query_params:
            try:
                item_id = int(query_params['id'][0])
            except ValueError:
                item_id = None

    item = get_item_details(item_id)
    if not item:
        return html.Div([
            html.H2("Service Not Found", className="no-data-text"),
            dcc.Link("Back to Services", href="/service-list", className="cat-allubot-btn")
        ], className="categories-page-wrapper services-theme", style={"textAlign": "center", "padding": "50px"})

    raw_img = item.get("image_url")
    image_src = raw_img if raw_img and str(raw_img).strip() != "" else "/assets/icons/service_icon.svg"
    is_fallback = "service_icon" in str(image_src)
    img_class = "item-large-img service-icon" if is_fallback else "item-large-img"

    related_services = get_related_items(item["id"], item.get("category_id"))

    return html.Div(
        className="categories-page-wrapper services-theme service-detail-theme",
        children=[
            # 1. SEARCH BAR & ALLUBOT BUTTON
            html.Div(
                className="cat-search-section",
                children=[
                    html.Div(
                        className="cat-search-box-wrapper",
                        children=[
                            html.Img(src="/assets/icons/search.svg", className="cat-search-icon"),
                            dcc.Input(
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
                        id="allubot-trigger-service-details", n_clicks=0,
                        className="cat-allubot-btn"
                    )
                ]
            ),

            # BREADCRUMB / NAV INFO
            html.Div(
                className="detail-breadcrumb",
                children=[
                    dcc.Link("Home", href="/"), " / ",
                    dcc.Link("Services", href="/service-list"), " / ",
                    html.Span(item.get("category_name", "Category"), style={"color": "#666"}), " / ",
                    html.Span(item["name"], style={"fontWeight": "bold"})
                ]
            ),

            # 2-6. MAIN ITEM SECTION (Photo, Name, Short Desc, Category, Button)
            html.Div(
                className="item-main-container",
                children=[
                    html.Div(
                        className="item-large-img-card",
                        children=[html.Img(src=image_src, className=img_class, alt=item["name"])]
                    ),
                    html.Div(
                        className="item-info-panel",
                        children=[
                            html.H1(item["name"], className="item-main-title"),
                            html.P(item.get("short_description", ""), className="item-main-short-desc"),
                            html.Div([
                                html.Strong("Category: "),
                                html.Span(item.get("category_name", "General"))
                            ], className="item-category-label"),
                            html.Button(
                                "Service Request",
                                id='service-quote-open-btn', n_clicks=0,
                                className="item-action-btn service-btn"
                            )
                        ]
                    )
                ]
            ),

            # 7. LONG DESCRIPTION SECTION
            html.Div(
                className="item-description-section",
                children=[
                    html.H2("Description", className="section-heading"),
                    html.Div(
                        dcc.Markdown(item.get("long_description", "No detailed description available."), mathjax=False),
                        className="item-long-desc-content"
                    )
                ]
            ),

            # 8. RELATED SERVICES SECTION (Conditional)
            html.Div(
                className="related-section",
                style={"display": "block" if related_services else "none"},
                children=[
                    html.H2("Related Services", className="section-heading"),
                    html.Div(
                        className="items-grid-wrapper",
                        children=[
                            dcc.Link(
                                href=f"/service-details?id={rel['id']}",
                                className="item-grid-card",
                                children=[
                                    html.Div(
                                        className="item-card-img-wrapper",
                                        children=[
                                            html.Img(
                                                src=rel["image"], 
                                                className="item-card-img service-icon" if "service_icon" in str(rel["image"]) else "item-card-img", 
                                                alt=rel["title"]
                                            )
                                        ]
                                    ),
                                    html.H4(rel["title"], className="item-card-title")
                                ]
                            ) for rel in related_services
                        ]
                    )
                ] if related_services else []
            ),

            # 9. SERVICE REQUEST MODAL (hidden until the button above is clicked)
            render_quote_modal(
                prefix='service',
                item_name=item["name"],
                item_image=image_src,
                item_subtitle=item.get("category_name"),
                theme='service'
            )
        ]
    )