import webbrowser

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import sys
import os

# Importing your app variable from app.py so we can use it
from app import app

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importing commonmodules and pages
import commonmodules as cm
from pages import home
from pages import about_us
from pages import contact_us
from pages.products import products
from pages.products import product_list
from pages.products import product_details
from pages.services import services
from pages.services import service_list
from pages.services import service_details

app.layout = html.Div(
    [
        dcc.Location(id='url', refresh=False),
        *cm.navbar,
        html.Div(
            dash.page_container, 
            id='page_content', 
            className='m-2 p-2'
        ),
        cm.get_footer(),
    ]
)

@app.callback(
    [Output('page_content', 'children')],
    [Input('url', 'pathname')]
)
def displaypage(pathname):
    ctx = dash.callback_context
    if ctx.triggered:
        eventid = ctx.triggered[0]['prop_id'].split('.')[0]   
    else:
        raise PreventUpdate

    if eventid == 'url':
        if pathname == '/' or pathname == '/home':
            returnlayout = home.layout() if callable(getattr(home, 'layout', None)) else home.layout

        elif pathname == '/about_us':
            returnlayout = about_us.layout() if callable(getattr(about_us, 'layout', None)) else about_us.layout
        elif pathname == '/contact_us':
            returnlayout = contact_us.layout() if callable(getattr(contact_us, 'layout', None)) else contact_us.layout

        elif pathname == '/products':
            returnlayout = products.layout() if callable(getattr(products, 'layout', None)) else products.layout
        
        # EXACT MATCHES MUST COME BEFORE startswith WILDCARDS
        elif pathname in ['/product-details', '/products/details', '/products/detail']:
            returnlayout = product_details.layout() if callable(getattr(product_details, 'layout', None)) else product_details.layout
        
        # Wildcard match for dynamic modality/type IDs (e.g., /products/1)
        elif pathname.startswith('/products/'):
            parts = pathname.strip('/').split('/')
            type_id = parts[1] if len(parts) > 1 else None
            returnlayout = product_list.layout(type_id)

        elif pathname == '/services':
            returnlayout = services.layout() if callable(getattr(services, 'layout', None)) else services.layout
        
        elif pathname in ['/service-details', '/services/details', '/services/detail']:
            returnlayout = service_details.layout() if callable(getattr(service_details, 'layout', None)) else service_details.layout
        
        elif pathname.startswith('/services/'):
            parts = pathname.strip('/').split('/')
            service_id = parts[1] if len(parts) > 1 else None
            returnlayout = service_list.layout(service_id)

        else:
            returnlayout = 'error404'
    
    return [returnlayout]


if __name__ == '__main__':
    webbrowser.open('http://127.0.0.1:8050/', new=0, autoraise=True)
    app.run(debug=False)