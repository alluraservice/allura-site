"""
Admin items — the same layout as the public product list (sidebar + item cards), plus admin tools:
add item, hover actions on every card (edit / hide-show / delete), hidden-item badges and a
visibility filter. Component ids are prefixed 'adm-items-' so they never clash with the public
product_list.py callbacks. Uses the same `.catalog` styles as the public list (30_cards.css).
"""
from urllib.parse import parse_qs

import dash
import dash_bootstrap_components as dbc
from dash import ALL, Input, Output, State, callback, ctx, dcc, html, no_update

import admin_ui as ui
from database.db_handler import (delete_item, get_all_items, get_categories_with_types, get_item_by_id,
                                 get_item_counts, get_items_by_category, get_items_by_modality, set_item_active)

dash.register_page(__name__, path='/admin/items')


def _product_categories():
    cats = [c for c in (get_categories_with_types() or []) if 'service' not in str(c.get('name', '')).lower()]
    for c in cats:
        c['types'] = [t for t in (c.get('types') or []) if 'service' not in str(t.get('name', '')).lower()]
    return cats


def layout(*args, **kwargs):
    sidebar_children = [
        html.Button("ALL PRODUCTS", id={'type': 'adm-items-filter', 'filter_type': 'all', 'target_id': 'none'},
                    className="sidebar-row sidebar-all-products btn bg-transparent text-start w-100 active")
    ]
    for cat in _product_categories():
        sidebar_children.append(html.Button(
            cat["name"], id={'type': 'adm-items-filter', 'filter_type': 'category', 'target_id': str(cat['id'])},
            className="sidebar-row sidebar-category-title btn bg-transparent text-start w-100"))
        for t in cat['types']:
            sidebar_children.append(html.Button(
                t["name"], id={'type': 'adm-items-filter', 'filter_type': 'modality', 'target_id': str(t['id'])},
                className="sidebar-row sidebar-modality-link btn bg-transparent text-start w-100"))

    toolbar = html.Div([
        dbc.Input(type='text', placeholder='Search product', id='adm-items-search', className='search-box', debounce=False),
        html.Div(dbc.Select(id='adm-items-visibility', value='all', className="a-input",
                            options=[{'label': 'All items', 'value': 'all'},
                                     {'label': 'On website', 'value': 'visible'},
                                     {'label': 'Hidden', 'value': 'hidden'}]), style={'width': '160px'}),
        html.Span(id='adm-items-count', className="count"),
    ], className="item-toolbar")

    delete_modal = dbc.Modal(dbc.ModalBody([
        html.H4("Delete item?"),
        html.P(id='adm-items-delete-text', className="modal-sub"),
        html.Div([
            html.Button("Cancel", id='adm-items-delete-cancel', n_clicks=0, className="a-btn a-btn-outline"),
            html.Button("Delete permanently", id='adm-items-delete-confirm', n_clicks=0, className="a-btn a-btn-danger"),
        ], className="modal-actions"),
    ]), id='adm-items-delete-modal', centered=True, is_open=False, className="a-modal")

    return html.Div([
        dcc.Location(id='adm-items-url', refresh=False),
        dcc.Store(id='adm-items-filter-store', data={'type': 'all', 'id': 'none'}),
        dcc.Store(id='adm-items-refresh', data=0),
        dcc.Store(id='adm-items-delete-id'),

        ui.page_header("Items", "The product catalog exactly as visitors see it, with tools to add, edit, hide and remove items.",
                       crumbs="Admin  /  Items",
                       actions=[dcc.Link("+  Add item", id='adm-items-add-link', href='/admin/items/add', className="a-btn a-btn-light")]),
        html.Div([
            dbc.Alert(id='adm-items-toast', is_open=False, duration=5000, dismissable=True, className="a-alert a-alert-ok mb-3"),
            html.Div([
                html.Div(sidebar_children, className="col-lg-3 d-none d-lg-block sidebar-container"),
                html.Div([toolbar, html.Div(id='adm-items-grid', className="row")], className="col-lg-9 col-md-12"),
            ], className="row g-4"),
        ], className="admin-container catalog"),
        delete_modal,
    ], className="admin-shell")


# ---------------------------------------------------------------------
# Filters (sidebar clicks and ?type=&id= links from item details)
# ---------------------------------------------------------------------
@callback(
    Output('adm-items-filter-store', 'data', allow_duplicate=True),
    Output('adm-items-toast', 'children', allow_duplicate=True),
    Output('adm-items-toast', 'is_open', allow_duplicate=True),
    Input('adm-items-url', 'search'),
    prevent_initial_call='initial_duplicate',
)
def filter_from_url(search):
    q = parse_qs((search or '').lstrip('?'))
    toast = ("Item deleted.", True) if 'deleted' in q else (no_update, no_update)
    if 'type' not in q:
        if toast[1] is True:
            return no_update, *toast
        raise dash.exceptions.PreventUpdate
    return {'type': q.get('type', ['all'])[0], 'id': q.get('id', ['none'])[0]}, *toast


@callback(
    Output('adm-items-filter-store', 'data'),
    Input({'type': 'adm-items-filter', 'filter_type': ALL, 'target_id': ALL}, 'n_clicks'),
    prevent_initial_call=True,
)
def filter_from_sidebar(n_clicks_list):
    if not ctx.triggered_id or not any(n_clicks_list or []):
        raise dash.exceptions.PreventUpdate
    return {'type': ctx.triggered_id['filter_type'], 'id': ctx.triggered_id['target_id']}


# ---------------------------------------------------------------------
# Grid
# ---------------------------------------------------------------------
def _tile(item):
    hidden = not (item.get('is_active') if item.get('is_active') is not None else True)
    badges = []
    if hidden:
        badges.append(html.Span("Hidden", className="chip chip-inactive"))
    if item.get('is_featured'):
        badges.append(html.Span("Featured", className="chip chip-pending plain"))
    return html.Div(html.Div([
        dcc.Link([
            html.Div(html.Img(src=ui.item_image_src(item.get('image_url')), alt=item["name"], className="item-card-img"),
                     className="item-card-img-container"),
            html.P(item["name"], className="item-card-title"),
        ], href=f"/admin/item-details?id={item['id']}", className="item-card"),
        html.Div(badges, className="tile-badges"),
        html.Div([
            dcc.Link("Edit", href=f"/admin/items/add?id={item['id']}", className="tile-btn", title="Edit"),
            html.Button("Show" if hidden else "Hide", id={'type': 'adm-items-toggle', 'index': item['id']}, n_clicks=0,
                        className="tile-btn", title="Show on website" if hidden else "Hide from website"),
            html.Button("Delete", id={'type': 'adm-items-delete', 'index': item['id']}, n_clicks=0,
                        className="tile-btn danger", title="Delete"),
        ], className="tile-actions"),
    ], className="item-tile" + (" is-hidden" if hidden else "")), className="col-lg-4 col-md-6 mb-4 item-col")


@callback(
    Output('adm-items-grid', 'children'),
    Output({'type': 'adm-items-filter', 'filter_type': ALL, 'target_id': ALL}, 'className'),
    Output('adm-items-count', 'children'),
    Output('adm-items-add-link', 'href'),
    Input('adm-items-filter-store', 'data'),
    Input('adm-items-search', 'value'),
    Input('adm-items-visibility', 'value'),
    Input('adm-items-refresh', 'data'),
    State({'type': 'adm-items-filter', 'filter_type': ALL, 'target_id': ALL}, 'id'),
)
def render_grid(filter_data, search, visibility, _refresh, button_ids):
    filter_type = (filter_data or {}).get('type', 'all')
    target_id = (filter_data or {}).get('id', 'none')

    try:
        if filter_type == 'category' and target_id != 'none':
            items = list(get_items_by_category(int(target_id), include_hidden=True) or [])
        elif filter_type == 'modality' and target_id != 'none':
            items = list(get_items_by_modality(int(target_id), include_hidden=True) or [])
        else:
            items = list(get_all_items(include_hidden=True) or [])
    except Exception as e:
        print(f"Error fetching admin items: {e}")
        items = []

    if search and str(search).strip():
        term = str(search).strip().lower()
        items = [i for i in items if term in str(i.get('name', '')).lower()]
    if visibility == 'visible':
        items = [i for i in items if i.get('is_active') is not False]
    elif visibility == 'hidden':
        items = [i for i in items if i.get('is_active') is False]

    # "Add item" tile pre-selects the category/modality being browsed
    add_href = '/admin/items/add'
    if filter_type == 'modality' and target_id != 'none':
        add_href += f'?modality={target_id}'
    elif filter_type == 'category' and target_id != 'none':
        add_href += f'?category={target_id}'

    add_tile = html.Div(dcc.Link([html.Span("+", className="plus"), "Add item",
                                  html.Small("Upload a photo and details")], href=add_href, className="item-add-card"),
                        className="col-lg-4 col-md-6 mb-4 item-col")
    tiles = [add_tile] + [_tile(i) for i in items]
    if not items:
        tiles.append(html.Div(html.P("No items in this selection.", className="text-center text-muted fs-5 py-5"),
                              className="col-lg-8 col-md-6"))

    classes = []
    for b in button_ids:
        cls = "sidebar-row btn bg-transparent text-start w-100 " + {
            'all': 'sidebar-all-products', 'category': 'sidebar-category-title', 'modality': 'sidebar-modality-link'}[b['filter_type']]
        if b['filter_type'] == filter_type and str(b['target_id']) == str(target_id):
            cls += " active"
        classes.append(cls)

    c = get_item_counts()
    count = f"Showing {len(items)}  ·  {c['visible']} on website" + (f", {c['hidden']} hidden" if c['hidden'] else "")
    return tiles, classes, count, add_href


# ---------------------------------------------------------------------
# Hide / show
# ---------------------------------------------------------------------
@callback(
    Output('adm-items-refresh', 'data', allow_duplicate=True),
    Output('adm-items-toast', 'children', allow_duplicate=True),
    Output('adm-items-toast', 'is_open', allow_duplicate=True),
    Input({'type': 'adm-items-toggle', 'index': ALL}, 'n_clicks'),
    State('adm-items-refresh', 'data'),
    prevent_initial_call=True,
)
def toggle_visibility(_, refresh):
    if not ctx.triggered_id or not (ctx.triggered and ctx.triggered[0].get('value')):
        raise dash.exceptions.PreventUpdate
    item = get_item_by_id(ctx.triggered_id['index'])
    if not item:
        raise dash.exceptions.PreventUpdate
    now_active = not item.get('is_active', True)
    set_item_active(item['id'], now_active)
    msg = f"“{item['name']}” is {'back on the website' if now_active else 'hidden from the website'}."
    return (refresh or 0) + 1, msg, True


# ---------------------------------------------------------------------
# Delete (with confirmation)
# ---------------------------------------------------------------------
@callback(
    Output('adm-items-delete-modal', 'is_open'),
    Output('adm-items-delete-id', 'data'),
    Output('adm-items-delete-text', 'children'),
    Input({'type': 'adm-items-delete', 'index': ALL}, 'n_clicks'),
    Input('adm-items-delete-cancel', 'n_clicks'),
    prevent_initial_call=True,
)
def ask_delete(_, __):
    if ctx.triggered_id == 'adm-items-delete-cancel':
        return False, None, no_update
    if not ctx.triggered_id or not (ctx.triggered and ctx.triggered[0].get('value')):
        raise dash.exceptions.PreventUpdate
    item = get_item_by_id(ctx.triggered_id['index'])
    if not item:
        raise dash.exceptions.PreventUpdate
    return True, item['id'], [html.B(item['name']), " and its uploaded photo will be removed permanently. "
                              "To take it off the website for now, hide it instead."]


@callback(
    Output('adm-items-delete-modal', 'is_open', allow_duplicate=True),
    Output('adm-items-refresh', 'data', allow_duplicate=True),
    Output('adm-items-toast', 'children', allow_duplicate=True),
    Output('adm-items-toast', 'is_open', allow_duplicate=True),
    Input('adm-items-delete-confirm', 'n_clicks'),
    State('adm-items-delete-id', 'data'),
    State('adm-items-refresh', 'data'),
    prevent_initial_call=True,
)
def confirm_delete(n, item_id, refresh):
    if not n or not item_id:
        raise dash.exceptions.PreventUpdate
    item = get_item_by_id(item_id)
    delete_item(item_id)
    return False, (refresh or 0) + 1, f"Deleted “{item['name'] if item else 'item'}”.", True
