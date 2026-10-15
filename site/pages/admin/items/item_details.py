"""
Admin item details — the public product page layout (product_details.py), plus an admin bar:
visibility status, Edit, Hide/Show, View on website, Delete.
The visitor-only "Contact Sales" button is shown greyed out so the page still looks like the public one.
The admin bar uses the same `.detail-bar` style as the public page's breadcrumb bar.
"""
from urllib.parse import parse_qs

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, dcc, html, no_update

import admin_ui as ui
from database.db_handler import delete_item, get_item_by_id, set_item_active

dash.register_page(__name__, path='/admin/item-details', title='Allura Enterprise - Admin Item Details')


def layout(id=None, **kwargs):
    return html.Div([
        dcc.Location(id='admin-item-detail-url', refresh=False),
        dcc.Location(id='admin-item-detail-redirect', refresh=True),
        dcc.Store(id='admin-item-detail-refresh', data=0),
        ui.page_header("Item details", "This is how the product page looks to visitors.", crumbs="Admin  /  Items  /  Details"),
        html.Div([
            dbc.Alert(id='admin-item-detail-toast', is_open=False, duration=5000, dismissable=True,
                      className="a-alert a-alert-ok mb-3"),
            html.Div(id='admin-item-detail-content'),
        ], className="admin-container"),
    ], className="admin-shell")


def _item_id(search):
    q = parse_qs((search or '').lstrip('?'))
    try:
        return int(q.get('id', [None])[0])
    except (TypeError, ValueError):
        return None


@callback(
    Output('admin-item-detail-content', 'children'),
    Input('admin-item-detail-url', 'search'),
    Input('admin-item-detail-refresh', 'data'),
)
def update_admin_item_detail_page(search, _refresh):
    item_id = _item_id(search)
    item = get_item_by_id(item_id) if item_id else None

    if not item:
        return html.Div([
            html.H3("Item Not Found", className="text-center text-muted py-5"),
            html.Div(dcc.Link("Back to Items", href="/admin/items", className="a-btn a-btn-primary"), className="text-center"),
        ], className="a-card a-card-body py-5")

    item_name = item.get("name") or "Item Details"
    short_desc = item.get("description") or "No description available."
    category_name = item.get("category_name", "Products")
    modality_name = item.get("modality_name", "General")
    image_path = ui.item_image_src(item.get("image_url"))
    is_fallback = "product_icon" in image_path
    img_class = "img-fluid rounded-4 shadow-sm product-icon" if is_fallback else "img-fluid rounded-4 shadow-sm"
    active = item.get('is_active', True) is not False

    cat_href = f"/admin/items?type=category&id={item['category_id']}" if item.get('category_id') else "/admin/items"
    mod_href = f"/admin/items?type=modality&id={item['modality_id']}" if item.get('modality_id') else "/admin/items"

    admin_bar = html.Div([
        html.Span("On website" if active else "Hidden from website", className="chip " + ("chip-active" if active else "chip-inactive")),
        html.Span("Featured", className="chip chip-pending plain") if item.get('is_featured') else None,
        html.Span("No photo yet" if is_fallback else "", className="text-muted", style={'fontSize': '.8rem'}),
        html.Div(className="grow"),
        html.A("View on website ↗", href=f"/product-details?id={item['id']}", target="_blank",
               className="a-btn a-btn-outline a-btn-sm") if active else None,
        html.Button("Show on website" if not active else "Hide from website", id='admin-item-toggle', n_clicks=0,
                    className="a-btn a-btn-outline a-btn-sm"),
        dcc.Link("Edit item", href=f"/admin/items/add?id={item['id']}", className="a-btn a-btn-primary a-btn-sm"),
        dcc.ConfirmDialogProvider(html.Button("Delete", className="a-btn a-btn-danger a-btn-sm"), id='admin-item-delete',
                                  message=f"Delete “{item_name}” permanently? This can't be undone."),
    ], className="detail-bar")

    # ---- below: same structure as the public product_details.py ----
    navigation_header = html.Div([
        dcc.Link("← Back to Items", href="/admin/items",
                 className="btn btn-outline-secondary rounded-pill btn-sm px-3 mb-3 fw-semibold text-decoration-none"),
        html.P([
            dcc.Link("Items", href="/admin/items", className="text-decoration-none text-muted"), " / ",
            dcc.Link(category_name, href=cat_href, className="text-decoration-none text-muted"), " / ",
            dcc.Link(modality_name, href=mod_href, className="text-decoration-none text-muted"), " / ",
            html.Span(item_name, className="fw-semibold text-dark"),
        ], className="text-muted mb-4 fs-6"),
    ])

    details_body = html.Div([
        html.Div([
            html.Div([
                html.Div([html.Img(src=image_path, alt=item_name, className=img_class)],
                         className="p-3 bg-white rounded-4 border text-center")
            ], className="col-lg-5 col-md-6 mb-4 mb-md-0"),
            html.Div([
                html.H2(item_name, className="fw-bold mb-3 text-dark"),
                html.P(short_desc, className="text-muted mb-4 fs-6", style={"lineHeight": "1.6"}),
                html.Div([
                    html.P([html.Strong("Category: "), dcc.Link(category_name, href=cat_href, className="text-decoration-none text-secondary")],
                           className="mb-1 text-secondary"),
                    html.P([html.Strong("Modality: "), dcc.Link(modality_name, href=mod_href, className="text-decoration-none text-secondary")],
                           className="mb-4 text-secondary"),
                ]),
                html.Button("Contact Sales", disabled=True, title="Visitors see this button on the public page",
                            className="btn btn-green rounded-pill fw-semibold px-4 py-2 text-white btn-preview-only"),
                html.Div("Visitors use this button to send a quote request (it appears in Inquiries under Product Page).",
                         className="a-help mt-2"),
            ], className="col-lg-7 col-md-6 ps-lg-5"),
        ], className="row align-items-center"),
    ])

    return html.Div([admin_bar, html.Div([navigation_header, details_body], className="a-card a-card-body p-4 p-lg-5")])


@callback(
    Output('admin-item-detail-toast', 'children'),
    Output('admin-item-detail-toast', 'is_open'),
    Input('admin-item-detail-url', 'search'),
)
def saved_toast(search):
    if 'saved=1' in (search or ''):
        return "Item saved.", True
    return no_update, False


@callback(
    Output('admin-item-detail-refresh', 'data'),
    Output('admin-item-detail-toast', 'children', allow_duplicate=True),
    Output('admin-item-detail-toast', 'is_open', allow_duplicate=True),
    Input('admin-item-toggle', 'n_clicks'),
    State('admin-item-detail-url', 'search'),
    State('admin-item-detail-refresh', 'data'),
    prevent_initial_call=True,
)
def toggle_visibility(n, search, refresh):
    if not n:
        raise dash.exceptions.PreventUpdate
    item = get_item_by_id(_item_id(search))
    if not item:
        raise dash.exceptions.PreventUpdate
    now_active = item.get('is_active') is False
    set_item_active(item['id'], now_active)
    return (refresh or 0) + 1, ("Back on the website." if now_active else "Hidden from the website."), True


@callback(
    Output('admin-item-detail-redirect', 'href'),
    Input('admin-item-delete', 'submit_n_clicks'),
    State('admin-item-detail-url', 'search'),
    prevent_initial_call=True,
)
def delete_this_item(n, search):
    if not n:
        raise dash.exceptions.PreventUpdate
    item_id = _item_id(search)
    if item_id:
        delete_item(item_id)
    return "/admin/items?deleted=1"
