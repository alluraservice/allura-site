import dash
from dash import Output, Input, State, html, dcc
from app import app
from database.dbconnect import get_categories_by_type, get_modalities_by_category
import json

# 1. Handle clicking "Products" or "Services" -> Show Categories Row
@app.callback(
    [Output('category-row-container', 'children'),
     Output('category-row-container', 'style'),
     Output('selected-type-store', 'data'),
     Output('modality-row-container', 'style')],
    [Input('nav-products-btn', 'n_clicks'),
     Input('nav-services-btn', 'n_clicks')]
)
def display_categories(prod_clicks, serv_clicks):
    prod_clicks = prod_clicks or 0
    serv_clicks = serv_clicks or 0
    
    if prod_clicks == 0 and serv_clicks == 0:
        raise dash.exceptions.PreventUpdate
    
    ctx = dash.callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    item_type = 'Products' if button_id == 'nav-products-btn' else 'Services'
    
    # Fetch categories from your database
    categories = get_categories_by_type(item_type)
    
    # Render categories horizontally using consistent classing
    category_links = [
        html.Button(cat, id={'type': 'cat-btn', 'index': cat}, className='btn-nav fw-bold border-0 bg-transparent') 
        for cat in categories
    ]
    
    row_content = html.Div(category_links, className='d-flex justify-content-center align-items-center gap-4 py-2')
    
    return row_content, {'display': 'flex'}, item_type, {'display': 'none'}

# 2. Handle clicking a Category -> Show Modalities Row
@app.callback(
    [Output('modality-row-container', 'children'),
     Output('modality-row-container', 'style'),
     Output('selected-category-store', 'data')],
    [Input({'type': 'cat-btn', 'index': dash.ALL}, 'n_clicks')],
    [State('selected-type-store', 'data')],
    prevent_initial_call=True
)
def display_modalities(n_clicks, item_type):
    ctx = dash.callback_context
    if not ctx.triggered or not any(n_clicks):
        raise dash.exceptions.PreventUpdate
    
    triggered_prop = ctx.triggered[0]['prop_id']
    eval_dict = json.loads(triggered_prop.split('.')[0])
    selected_category = eval_dict['index']
    
    # Fetch modalities from your database using your item_type and category
    modalities = get_modalities_by_category(item_type, selected_category)
    
    # Render modalities horizontally
    modality_links = [
        dcc.Link(mod, href=f"/{item_type.lower()}?category={selected_category}&modality={mod}", className='btn-nav text-success text-decoration-none fw-semibold') 
        for mod in modalities
    ]
    
    row_content = html.Div(modality_links, className='d-flex justify-content-center align-items-center gap-4 py-2')
    
    return row_content, {'display': 'flex'}, selected_category