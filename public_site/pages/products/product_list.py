import dash
from dash import html, dcc, callback, Input, Output, State, ALL, ctx
import dash_bootstrap_components as dbc
from database.db_handler import (
    get_all_items, 
    get_items_by_category, 
    get_items_by_modality, 
    get_categories_with_types
)

dash.register_page(__name__, path='/products')

# ==========================================
# PAGE LAYOUT (INITIAL SKELETON WITH STORES)
# ==========================================
def layout(*args, **kwargs):
    categories_data = get_categories_with_types() or []

    # Hero Section
    hero_section = html.Div([
        html.Div([
            html.H1("PRODUCTS", className="hero-title text-white"),
        ], className="hero-content text-start ps-5")
    ], className="hero-section-3")

    # Sidebar Construction using Pattern-Matching IDs
    sidebar_children = [
        html.Button(
            "ALL PRODUCTS",
            id={'type': 'filter-btn', 'filter_type': 'all', 'target_id': 'none'},
            className="sidebar-row sidebar-all-products btn bg-transparent text-start w-100 active"
        )
    ]

    for cat in categories_data:
        if "service" in str(cat.get("name", "")).lower():
            continue

        sidebar_children.append(
            html.Button(
                cat["name"],
                id={'type': 'filter-btn', 'filter_type': 'category', 'target_id': str(cat['id'])},
                className="sidebar-row sidebar-category-title btn bg-transparent text-start w-100"
            )
        )

        for t in cat.get("types", []):
            if "service" in str(t.get("name", "")).lower():
                continue

            sidebar_children.append(
                html.Button(
                    t["name"],
                    id={'type': 'filter-btn', 'filter_type': 'modality', 'target_id': str(t['id'])},
                    className="sidebar-row sidebar-modality-link btn bg-transparent text-start w-100"
                )
            )

    sidebar_column = html.Div(
        sidebar_children,
        className="col-lg-3 d-none d-lg-block sidebar-container"
    )

    # Search Bar
    search_bar_row = html.Div([
        html.Div([
            html.Div([
                dbc.Input(
                    type='text',
                    placeholder='Search product',
                    id='product_search_input',
                    className='search-box w-150'
                ),
            ], className="col-lg-5 col-md-6 mb-3 mb-md-0")
        ], className='row align-items-center mb-4')
    ])

    # Dynamic Container for Filtered Items
    items_grid_container = html.Div(id='items-grid-container', className="row")

    main_content_column = html.Div([
        search_bar_row,
        items_grid_container
    ], className="col-lg-9 col-md-12")

    return html.Div([
        # Client-Side Stores for Active Filter State
        dcc.Store(id='active-filter-store', data={'type': 'all', 'id': 'none'}),
        
        hero_section,
        html.Div([
            html.Div([
                html.Div([
                    sidebar_column,
                    main_content_column
                ], className="row g-4")
            ], className="container-fluid px-0 py-4")
        ], className="section-no-border-2")
    ])


# ==========================================
# CALLBACK 1: HANDLE PATTERN-MATCHING CLICKS
# ==========================================
@callback(
    Output('active-filter-store', 'data'),
    Input({'type': 'filter-btn', 'filter_type': ALL, 'target_id': ALL}, 'n_clicks'),
    prevent_initial_call=True
)
def update_active_filter_store(n_clicks_list):
    if not ctx.triggered_id or not any(n_clicks_list):
        raise dash.exceptions.PreventUpdate

    clicked_info = ctx.triggered_id
    return {
        'type': clicked_info['filter_type'],
        'id': clicked_info['target_id']
    }


# ==========================================
# CALLBACK 2: RENDER GRID & ACTIVE STYLES
# ==========================================
@callback(
    [
        Output('items-grid-container', 'children'),
        Output({'type': 'filter-btn', 'filter_type': ALL, 'target_id': ALL}, 'className')
    ],
    [
        Input('active-filter-store', 'data'),
        Input('product_search_input', 'value')
    ],
    [
        State({'type': 'filter-btn', 'filter_type': ALL, 'target_id': ALL}, 'id')
    ]
)
def render_filtered_grid(filter_data, search_term, button_ids):
    filter_type = filter_data.get('type', 'all')
    target_id = filter_data.get('id', 'none')

    fetched_items = []
    
    # 1. Database Query Execution
    try:
        if filter_type == 'category' and target_id != 'none':
            # 1a. Fetch items directly under category
            res = get_items_by_category(int(target_id)) or []
            fetched_items = list(res)

            # 1b. Collect child modality items if category has modalities
            categories_data = get_categories_with_types() or []
            target_cat = next((c for c in categories_data if str(c.get('id')) == str(target_id)), None)
            
            if target_cat and target_cat.get("types"):
                for t in target_cat["types"]:
                    mod_items = get_items_by_modality(int(t['id'])) or []
                    fetched_items.extend(mod_items)

            # Deduplicate items by ID
            seen_ids = set()
            unique_items = []
            for item in fetched_items:
                if item['id'] not in seen_ids:
                    seen_ids.add(item['id'])
                    unique_items.append(item)
            fetched_items = unique_items

        elif filter_type == 'modality' and target_id != 'none':
            res = get_items_by_modality(int(target_id))
            fetched_items = res if res is not None else []
        else:
            res = get_all_items()
            fetched_items = res if res is not None else []
    except Exception as e:
        print(f"Error fetching filtered items: {e}")
        fetched_items = []

    # 2. In-Memory Search Filtering
    if search_term and str(search_term).strip():
        term = str(search_term).strip().lower()
        fetched_items = [
            item for item in fetched_items 
            if term in str(item.get('name', '')).lower()
        ]

    # 3. Render Item Grid UI
    if fetched_items and len(fetched_items) > 0:
        grid_children = [
            html.Div([
                dcc.Link([
                    html.Div([
                        html.Img(
                            src=f"/{str(item['image_url']).lstrip('/')}",
                            alt=item["name"],
                            className="item-card-img"
                        )
                    ], className="item-card-img-container"),
                    html.P(item["name"], className="item-card-title")
                ], href=f"/product-details?id={item['id']}", className="item-card")
            ], className="col-lg-4 col-md-6 mb-4 item-col")
            for item in fetched_items
        ]
    else:
        grid_children = [
            html.Div([
                html.P("No items in this selection.", className="text-center text-muted fs-5 py-5")
            ], className="col-12")
        ]

    # 4. Update Active Classes across all Sidebar Buttons
    updated_class_names = []
    for btn_id in button_ids:
        base_class = "sidebar-row btn bg-transparent text-start w-100"
        
        if btn_id['filter_type'] == 'all':
            base_class += " sidebar-all-products"
        elif btn_id['filter_type'] == 'category':
            base_class += " sidebar-category-title"
        elif btn_id['filter_type'] == 'modality':
            base_class += " sidebar-modality-link"

        is_active = (
            btn_id['filter_type'] == filter_type and 
            str(btn_id['target_id']) == str(target_id)
        )
        if is_active:
            base_class += " active"

        updated_class_names.append(base_class)

    return grid_children, updated_class_names