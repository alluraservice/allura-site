"""
Public product list — same layout as the admin Items page (admin/items/items.py): page header,
sidebar card, search toolbar with a count, and item cards, without the admin controls.
Links like /products/all?type=category&id=3 or ?type=modality&id=7 open the list pre-filtered.
Hidden items (is_active = False) never show here.
"""
from urllib.parse import parse_qs

import dash
from dash import html, dcc, callback, Input, Output, State, ALL, ctx
import dash_bootstrap_components as dbc

import site_ui as ui
from database.db_handler import (
    get_all_items,
    get_items_by_category,
    get_items_by_modality,
    get_categories_with_types
)

dash.register_page(__name__, path='/products')


def _product_categories():
    cats = [c for c in (get_categories_with_types() or []) if 'service' not in str(c.get('name', '')).lower()]
    for c in cats:
        c['types'] = [t for t in (c.get('types') or []) if 'service' not in str(t.get('name', '')).lower()]
    return cats


# ==========================================
# PAGE LAYOUT
# ==========================================
def layout(*args, **kwargs):
    try:
        categories = _product_categories()
    except Exception as e:
        print(f"Error loading categories: {e}")
        categories = []

    sidebar_children = [
        html.Button("ALL PRODUCTS", id={'type': 'filter-btn', 'filter_type': 'all', 'target_id': 'none'},
                    className="sidebar-row sidebar-all-products btn bg-transparent text-start w-100 active")
    ]
    mobile_options = [{'label': 'All products', 'value': 'all|none'}]
    for cat in categories:
        sidebar_children.append(html.Button(
            cat["name"], id={'type': 'filter-btn', 'filter_type': 'category', 'target_id': str(cat['id'])},
            className="sidebar-row sidebar-category-title btn bg-transparent text-start w-100"))
        mobile_options.append({'label': cat["name"], 'value': f"category|{cat['id']}"})
        for t in cat['types']:
            sidebar_children.append(html.Button(
                t["name"], id={'type': 'filter-btn', 'filter_type': 'modality', 'target_id': str(t['id'])},
                className="sidebar-row sidebar-modality-link btn bg-transparent text-start w-100"))
            mobile_options.append({'label': f"   {t['name']}", 'value': f"modality|{t['id']}"})

    toolbar = html.Div([
        dbc.Input(type='text', placeholder='Search product', id='product_search_input', className='search-box', debounce=False),
        html.Span(id='product-list-count', className="count"),
    ], className="item-toolbar")

    # Small screens hide the sidebar, so offer the same filters as a dropdown
    mobile_filter = html.Div(
        dbc.Select(id='product-list-mobile-filter', options=mobile_options, value='all|none', className="a-input"),
        className="catalog-mobile-filter")

    return html.Div([
        dcc.Location(id='product-list-url', refresh=False),
        dcc.Store(id='active-filter-store', data={'type': 'all', 'id': 'none'}),

        ui.page_header("Products", "Browse our full catalog by category, or search by product name.",
                       crumbs=[("Home", "/home"), ("Products", "/products"), ("All products", None)]),
        html.Div([
            html.Div([
                html.Div(sidebar_children, className="col-lg-3 d-none d-lg-block sidebar-container"),
                html.Div([mobile_filter, toolbar, html.Div(id='items-grid-container', className="row")],
                         className="col-lg-9 col-md-12"),
            ], className="row g-4"),
        ], className="site-container catalog"),
    ], className="site-shell")


# ==========================================
# FILTERS: URL (?type=&id=), sidebar clicks, mobile dropdown
# ==========================================
@callback(
    Output('active-filter-store', 'data', allow_duplicate=True),
    Input('product-list-url', 'search'),
    prevent_initial_call='initial_duplicate'
)
def filter_from_url(search):
    q = parse_qs((search or '').lstrip('?'))
    if 'type' not in q:
        raise dash.exceptions.PreventUpdate
    return {'type': q.get('type', ['all'])[0], 'id': q.get('id', ['none'])[0]}


@callback(
    Output('active-filter-store', 'data'),
    Input({'type': 'filter-btn', 'filter_type': ALL, 'target_id': ALL}, 'n_clicks'),
    prevent_initial_call=True
)
def update_active_filter_store(n_clicks_list):
    if not ctx.triggered_id or not any(n_clicks_list or []):
        raise dash.exceptions.PreventUpdate
    return {'type': ctx.triggered_id['filter_type'], 'id': ctx.triggered_id['target_id']}


@callback(
    Output('active-filter-store', 'data', allow_duplicate=True),
    Input('product-list-mobile-filter', 'value'),
    State('active-filter-store', 'data'),
    prevent_initial_call=True
)
def filter_from_dropdown(value, current):
    if not value or '|' not in value:
        raise dash.exceptions.PreventUpdate
    kind, target = value.split('|', 1)
    current = current or {}
    # The grid callback writes this dropdown back to match the filter; don't loop on that echo
    if current.get('type') == kind and str(current.get('id')) == target:
        raise dash.exceptions.PreventUpdate
    return {'type': kind, 'id': target}


# ==========================================
# GRID
# ==========================================
def _tile(item):
    badges = [html.Span("Featured", className="chip chip-pending plain")] if item.get('is_featured') else []
    return html.Div(html.Div([
        dcc.Link([
            html.Div(html.Img(src=ui.item_image_src(item.get('image_url')), alt=item["name"], className="item-card-img"),
                     className="item-card-img-container"),
            html.P(item["name"], className="item-card-title"),
        ], href=f"/product-details?id={item['id']}", className="item-card"),
        html.Div(badges, className="tile-badges"),
    ], className="item-tile"), className="col-lg-4 col-md-6 mb-4 item-col")


@callback(
    Output('items-grid-container', 'children'),
    Output({'type': 'filter-btn', 'filter_type': ALL, 'target_id': ALL}, 'className'),
    Output('product-list-count', 'children'),
    Output('product-list-mobile-filter', 'value'),
    Input('active-filter-store', 'data'),
    Input('product_search_input', 'value'),
    State({'type': 'filter-btn', 'filter_type': ALL, 'target_id': ALL}, 'id'),
)
def render_filtered_grid(filter_data, search_term, button_ids):
    filter_type = (filter_data or {}).get('type', 'all')
    target_id = (filter_data or {}).get('id', 'none')

    try:
        if filter_type == 'category' and target_id != 'none':
            items = list(get_items_by_category(int(target_id)) or [])
        elif filter_type == 'modality' and target_id != 'none':
            items = list(get_items_by_modality(int(target_id)) or [])
        else:
            items = list(get_all_items() or [])
    except Exception as e:
        print(f"Error fetching filtered items: {e}")
        items = []

    # Visible items only, no duplicates
    seen, visible = set(), []
    for i in items:
        if ui.is_visible(i) and i['id'] not in seen:
            seen.add(i['id'])
            visible.append(i)
    total_in_view = len(visible)

    if search_term and str(search_term).strip():
        term = str(search_term).strip().lower()
        visible = [i for i in visible if term in str(i.get('name', '')).lower()]

    if visible:
        tiles = [_tile(i) for i in visible]
    else:
        tiles = [html.Div(html.Div([
            html.P("No products match this selection.", className="mb-2 fs-5"),
            html.P(["Can't find what you need? ", dcc.Link("Contact our sales team", href="/contact_us"), "."],
                   className="mb-0 small"),
        ], className="a-card catalog-empty"), className="col-12")]

    classes = []
    for b in button_ids:
        cls = "sidebar-row btn bg-transparent text-start w-100 " + {
            'all': 'sidebar-all-products', 'category': 'sidebar-category-title', 'modality': 'sidebar-modality-link'}[b['filter_type']]
        if b['filter_type'] == filter_type and str(b['target_id']) == str(target_id):
            cls += " active"
        classes.append(cls)

    if search_term and str(search_term).strip():
        count = f"{len(visible)} of {total_in_view} products"
    else:
        count = f"{total_in_view} product{'s' if total_in_view != 1 else ''}"

    return tiles, classes, count, f"{filter_type}|{target_id}"
