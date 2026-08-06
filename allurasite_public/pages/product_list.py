import dash
from dash import html, dcc, callback, Input, Output, State
from urllib.parse import parse_qs
import pandas as pd
from database import db_handler

dash.register_page(__name__, path='/product-list', title='Allura Enterprise - Products')


def get_category_details(category_param):
    """Fetches category info by ID or slug."""
    if not category_param:
        return None

    # FIXED: Replaced 'c.description' with 'NULL AS description' since the column doesn't exist
    query = """
        SELECT c.id, c.name, NULL AS description, c.image_path AS image_url
        FROM categories c
        JOIN types t ON c.type_id = t.id
        WHERE LOWER(t.name) = 'product'
          AND (
            c.id::text = %s
            OR LOWER(REGEXP_REPLACE(c.name, '[^a-zA-Z0-9]+', '-', 'g')) = LOWER(REGEXP_REPLACE(%s, '[^a-zA-Z0-9]+', '-', 'g'))
          );
    """
    df = db_handler.fetch_data_df(query, (str(category_param), str(category_param)))
    if df.empty:
        return None
    return df.to_dict('records')[0]


def get_category_items(category_id=None):
    """Queries product items for the specified category ID or all active products if none."""
    if category_id:
        query = """
            SELECT i.id, i.name AS title, i.image_url AS image
            FROM items i
            WHERE i.category_id = %s AND i.is_active = TRUE
            ORDER BY i.name ASC;
        """
        params = (category_id,)
    else:
        query = """
            SELECT i.id, i.name AS title, i.image_url AS image
            FROM items i
            JOIN categories c ON i.category_id = c.id
            JOIN types t ON c.type_id = t.id
            WHERE LOWER(t.name) = 'product' AND i.is_active = TRUE
            ORDER BY i.name ASC;
        """
        params = ()

    df = db_handler.fetch_data_df(query, params)
    if df.empty:
        return []

    df['image'] = df['image'].apply(
        lambda x: x if pd.notna(x) and str(x).strip() != "" else "/assets/icons/product_icon.svg"
    )
    return df.to_dict('records')


def layout(category=None, **kwargs):
    return html.Div([
        dcc.Location(id='product-list-url', refresh=False),
        html.Div(id='product-list-page-content')
    ])


@callback(
    Output('product-list-page-content', 'children'),
    Input('product-list-url', 'search'),
    Input('product-list-url', 'pathname')
)
def update_product_list_layout(search, pathname):
    category_param = None

    if search:
        raw_query = search.lstrip('?')
        if raw_query:
            query_params = parse_qs(raw_query)
            if 'category' in query_params:
                category_param = query_params['category'][0]

    if not category_param and pathname and pathname not in ["/product-list", "/product-list/"]:
        path_parts = [p for p in pathname.split("/") if p]
        if len(path_parts) > 1 and path_parts[0] == "product-list":
            category_param = path_parts[1]

    cat_info = get_category_details(category_param) if category_param else None

    cat_title = cat_info["name"].upper() if cat_info else "ALL PRODUCTS"
    
    # FIXED: Safely fetch description using .get() to avoid KeyError
    cat_desc = cat_info.get("description") if cat_info and cat_info.get("description") else "Allura Enterprise offers advanced healthcare equipment across the Philippines."

    raw_hero_bg = cat_info.get("image_url") if cat_info else None
    hero_bg = raw_hero_bg if raw_hero_bg and str(raw_hero_bg).strip() != "" else "/assets/pictures/radiology_department.jpg"

    cat_id = cat_info["id"] if cat_info else None
    items = get_category_items(cat_id)

    return html.Div(
        className="categories-page-wrapper",
        children=[
            dcc.Store(id="product-list-items-store", data=items),

            # 1. TITLE / HERO CARD
            html.Div(
                className="cat-hero-banner",
                style={"backgroundImage": f"url('{hero_bg}')"},
                children=[
                    html.Div(
                        className="cat-hero-overlay",
                        children=[
                            html.H1(cat_title, className="cat-hero-title"),
                            html.P(cat_desc, className="cat-hero-subtitle")
                        ]
                    )
                ]
            ),

            # 2. SEARCH BAR & ALLUBOT BUTTON
            html.Div(
                className="cat-search-section",
                children=[
                    html.Div(
                        className="cat-search-box-wrapper",
                        children=[
                            html.Img(src="/assets/icons/search.svg", className="cat-search-icon"),
                            dcc.Input(
                                id="product-list-search",
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
                        id="allubot-trigger-product-list", n_clicks=0,
                        className="cat-allubot-btn"
                    )
                ]
            ),

            # 3. PRODUCT GRID
            html.Div(
                className="product-grid-container",
                children=[
                    html.Div(
                        id="product-items-grid",
                        className="items-grid-wrapper",
                        children=render_item_cards(items, "/product-details?id=")
                    )
                ]
            )
        ]
    )


def render_item_cards(items, link_prefix):
    if not items:
        return [html.P("No products found in this category.", className="no-data-text")]

    cards = []
    for item in items:
        is_fallback = "product_icon" in str(item["image"])
        img_class = "item-card-img product-icon" if is_fallback else "item-card-img"

        cards.append(
            dcc.Link(
                href=f"{link_prefix}{item['id']}",
                className="item-grid-card",
                children=[
                    html.Div(
                        className="item-card-img-wrapper",
                        children=[html.Img(src=item["image"], className=img_class, alt=item["title"])]
                    ),
                    html.H4(item["title"], className="item-card-title")
                ]
            )
        )
    return cards


@callback(
    Output("product-items-grid", "children"),
    Input("product-list-search", "value"),
    State("product-list-items-store", "data")
)
def filter_products(search_term, items):
    if not items:
        return [html.P("No products available.", className="no-data-text")]

    if not search_term or search_term.strip() == "":
        return render_item_cards(items, "/product-details?id=")

    filtered = [
        item for item in items
        if search_term.lower() in item["title"].lower()
    ]
    return render_item_cards(filtered, "/product-details?id=")