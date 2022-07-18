import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, callback, dcc, html

import callbacks
from layouts import index_page, pathway_page, url_bar_and_content_div

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
# app = dash.Dash(__name__, external_stylesheets=['https://codepen.io/chriddyp/pen/bWLwgP.css', dbc.themes.BOOTSTRAP])

server = app.server

app.layout = url_bar_and_content_div

app.validation_layout = html.Div([url_bar_and_content_div, index_page, pathway_page])


@callback(Output("page-content", "children"), Input("url", "pathname"))
def display_page(pathname):
    """
    Display page content based on the URL.
    """
    if pathname == "/":
        return index_page
    else:
        return pathway_page


if __name__ == "__main__":
    app.run_server(debug=True)
