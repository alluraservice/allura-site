import logging
import os

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    assets_folder='../assets'
)

# Expose underlying Flask server for Gunicorn
server = app.server

app.config.suppress_callback_exceptions = True
app.css.config.serve_locally = True
app.scripts.config.serve_locally = True
app.title = "Allura Enterprise"

log = logging.getLogger("werkzeug")
log.setLevel(logging.ERROR)