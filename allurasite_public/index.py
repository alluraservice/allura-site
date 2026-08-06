import os
import sys
import webbrowser
import dash
from dash import html, dcc, Input, Output
from flask import send_from_directory

# ==============================================================================
# SECTION 1: DEFINE FILE PATHS
# ==============================================================================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
ASSETS_DIR = os.path.abspath(os.path.join(PARENT_DIR, "assets"))

# ==============================================================================
# SECTION 2: ADD PARENT DIR TO PYTHONPATH
# ==============================================================================
if PARENT_DIR not in sys.path:
    sys.path.append(PARENT_DIR)

# ==============================================================================
# SECTION 3: IMPORT APP COMPONENTS
# ==============================================================================
from database import db_handler
import allurasite_public.components as site_components
from allurasite_public.components import render_top_bar, render_footer, render_allubot_widget, register_allubot_widget_callback


def slugify_category(category):
    text = str(category or '').strip().lower()
    text = ''.join(ch if ch.isalnum() else '-' for ch in text)
    while '--' in text:
        text = text.replace('--', '-')
    return text.strip('-')


def get_category_page_href(category_type, category=None):
    if category:
        page_name = 'product-list' if category_type == 'Product' else 'service-list'
        return f'/{page_name}?category={slugify_category(category)}'

    return '/product-categories' if category_type == 'Product' else '/service-categories'


def render_header():
    product_categories = db_handler.get_categories_by_type('Product') or []
    service_categories = db_handler.get_categories_by_type('Service') or []

    return html.Header(className='main-header', children=[
        html.Div(className='container-fluid header-container', children=[
            html.Div(className='logo-area', children=[
                dcc.Link(
                    html.Img(src='/assets/logos/alluralogo1.png', className='logo-image', alt='ALLURA Logo'),
                    href='/'
                )
            ]),
            html.Div(className='header-left-group', children=[
                html.Nav(className='nav-links', children=[
                    dcc.Link('Home', href='/', className='nav-link'),
                    dcc.Link('About Us', href='/about-us', className='nav-link'),

                    html.Div(className='nav-dropdown', children=[
                        dcc.Link([
                            'Products',
                            html.Span(' ⌵', className='caret')
                        ], href=get_category_page_href('Product'), className='nav-link'),

                        html.Div(className='dropdown-menu', children=[
                            dcc.Link(
                                category,
                                href=get_category_page_href('Product', category),
                                className='dropdown-item'
                            ) for category in product_categories
                        ])
                    ]),

                    html.Div(className='nav-dropdown', children=[
                        dcc.Link([
                            'Services',
                            html.Span(' ⌵', className='caret')
                        ], href=get_category_page_href('Service'), className='nav-link'),

                        html.Div(className='dropdown-menu', children=[
                            dcc.Link(
                                category,
                                href=get_category_page_href('Service', category),
                                className='dropdown-item'
                            ) for category in service_categories
                        ])
                    ]),

                    dcc.Link('News/Blog', href='/news', className='nav-link'),
                    dcc.Link('Contact Us', href='/contact-us', className='nav-link')
                ]),

                html.Div(className='search-chat-actions', children=[
                    html.Div(className='search-container', children=[
                        html.Img(src='/assets/icons/search.svg', className='search-icon-svg', alt='Search'),
                        dcc.Input(
                            id='global-search',
                            type='text',
                            placeholder='Search...',
                            className='search-input',
                            debounce=True
                        )
                    ]),
                    html.Button([
                        html.Img(src='/assets/icons/allubot1.svg', className='allubot-icon-svg', alt='AlluBot'),
                        'Ask AlluBot'
                    ], id='allubot-trigger', className='btn-allubot')
                ])
            ])
        ])
    ])


site_components.render_header = render_header

# ==============================================================================
# SECTION 4: DASH APP CONFIGURATION
# ==============================================================================
app = dash.Dash(
    __name__,
    use_pages=True,
    pages_folder=os.path.join(CURRENT_DIR, "pages"),
    assets_folder=ASSETS_DIR,
    assets_url_path='/assets',
    suppress_callback_exceptions=True
)
server = app.server

# ==============================================================================
# SECTION 5: ASSET ROUTE HANDLER
# ==============================================================================
@server.route('/assets/<path:path>')
def serve_assets(path):
    return send_from_directory(ASSETS_DIR, path)

# ==============================================================================
# SECTION 6: SEARCH INPUT NAVIGATION CALLBACK
# ==============================================================================
@app.callback(
    Output('url', 'pathname'),
    Input('global-search', 'value')
)
def navigate_to_selected_item(search_value):
    if not search_value or not str(search_value).strip():
        return dash.no_update
    
    slug = str(search_value).strip().lower().replace(' ', '-')
    return f'/product-details?item={slug}'

# ==============================================================================
# SECTION 7: SHARED APP LAYOUT
# ==============================================================================
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),

    # TOP INFORMATION BAR
    render_top_bar(),

    # MAIN NAVIGATION HEADER
    render_header(),

    # DYNAMIC PAGE CONTENT
    html.Div(dash.page_container, style={'minHeight': '60vh'}),

    # SITE FOOTER
    render_footer(),

    # ALLUBOT CHAT WIDGET (persists across every page - see components.py)
    render_allubot_widget()
])

register_allubot_widget_callback()

# ==============================================================================
# SECTION 8: RUN APP
# ==============================================================================
if __name__ == '__main__':
    webbrowser.open('http://127.0.0.1:8050', autoraise=True)
    app.run()