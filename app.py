import base64
import datetime
import io
import plotly.graph_objs as go
import numpy as np

import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
import json
from calc import calc

# external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

# update_success = 'Update Completed!'
# update_fail = 'Update Failed!'
# reset_text = 'Reset Completed!'

# success_color = 'green'
# fail_color = 'red'
# reset_color = 'blue'

# success_style={'color': 'green'}
# fail_color={'color': 'red'}


# app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
# app = dash.Dash(__name__, external_stylesheets=['https://codepen.io/chriddyp/pen/bWLwgP.css', dbc.themes.BOOTSTRAP])

server = app.server


def calculate(df_lci):
    df = pd.merge(df_lci, lookup, left_on="Input", right_index=True)
    metrics = ["NOx", "GHG"]
    for metric in metrics:
        df[metric + "_Sum"] = df["Usage"] * df[metric]
    return df


# Read Data
lookup = pd.read_excel("Metric_table_sample.xlsx", index_col=0).transpose()
lci = pd.read_excel("upload_sample_LCI.xlsx")
res = calculate(lci)
res["Resource"] = res["Input"]
res["Input Amount"] = res["Usage"]

app.layout = dbc.Container(
    children=[
        dcc.Store(id="results"),
        html.H1(children="SCSA LCA Results", className="text-dark"),
        html.H3(
            children="""
        RD Production from Corn Stover via Biochem Pathway
    """,
            className="text-muted text-decoration-underline",
        ),
        html.Hr(),
        dbc.Alert(
            html.H4("Reset completed!", className="alert-heading"),
            id="reset_status",
            color="info",
            style={"textAlign": "center"},
            dismissable=True,
            is_open=False,
        ),
        dbc.Alert(
            html.H4("The results have been updated!", className="alert-heading"),
            id="update_status",
            color="success",
            style={"textAlign": "center"},
            dismissable=True,
            is_open=False,
        ),
        dcc.Upload(
            id="upload-data",
            children=html.Div(
                ["Drag and Drop or ", html.A("Select Files", className="link-primary")]
            ),
            style={
                "width": "100%",
                "height": "60px",
                "lineHeight": "60px",
                "borderWidth": "1px",
                "borderStyle": "dashed",
                "borderRadius": "5px",
                "textAlign": "center",
                "margin": "10px",
            },
            # Allow multiple files to be uploaded
            multiple=False,
        ),
        dbc.Button(
            "Reset", color="primary", className="me-1", id="reset-button", n_clicks=0
        ),
        dbc.Row(
            dbc.Col(
                [
                    html.H5("Renewable Electricity %"),
                    dcc.Slider(0, 1, 
                    step=None,
                    marks = {
                        val: '{:.0%}'.format(val) for val in np.linspace(0, 1, 11)
                    },
                    value=0,
                    id='renewable_elec'
                    )
                    ],
                    width={"size": 6, "offset": 3}
               )),
        dbc.Tabs(
            [
                dbc.Tab(
                    label="GHG", tab_id="GHG", activeTabClassName="fw-bold fst-italic"
                ),
                dbc.Tab(
                    label="NOx", tab_id="NOx", activeTabClassName="fw-bold fst-italic"
                ),
            ],
            id="tabs",
            active_tab="GHG",
        ),
        dbc.Row(
            [
                dbc.Col(dcc.Graph(id="graph1"), md=6),
                dbc.Col(dcc.Graph(id="graph2"), md=6),
            ]
        ),
        dbc.Row(
            [
                dbc.Col(dcc.Graph(id="graph3"), md=6),
                dbc.Col(dcc.Graph(id="graph4"), md=6),
            ]
        ),
    ]
)


def parse_contents(contents, filename, date):
    content_type, content_string = contents.split(",")

    decoded = base64.b64decode(content_string)
    try:
        if "csv" in filename:
            # Assume that the user uploaded a CSV file
            # df_upload = pd.read_csv(
            # io.StringIO(decoded.decode('utf-8')))
            lci_file = io.StringIO(decoded.decode("utf-8"))
        elif "xls" in filename:
            # Assume that the user uploaded an excel file
            # df_upload = pd.read_excel(io.BytesIO(decoded))
            lci_file = io.BytesIO(decoded)
    except Exception as e:
        print(e)
        return html.Div(["There was an error processing this file."])

    return lci_file


def make_waterfall_plot(res, metric='GHG', n=4):

    df = res.copy()
    col = metric + '_Sum'

    df.loc[df[col]<0, 'Resource'] = df.loc[df[col]<0, 'Resource'].apply(lambda x: 'Disp. Credit of ' + x)
    dfp = df[df[col]>0].groupby('Resource', as_index=False)[col].sum()
    dfn = df[df[col]<0].groupby('Resource', as_index=False)[col].sum()
    df1 = dfp.nlargest(n, col)
    df2 = dfn.nsmallest(n, col)
    other = df[col].sum() - df1[col].sum() - df2[col].sum()
    
    for_plot = pd.concat([
        df1[['Resource', col]],
        pd.Series({'Resource': 'Other', col: other}).to_frame().T,
        df2[['Resource', col]],
    ])
    
    fig = go.Figure(go.Waterfall(
        # name = "20", 
        orientation = "v",
        measure = ["relative"] * len(for_plot) + ['total'],
        x = for_plot['Resource'].to_list() + ['Total'],
        y = for_plot[col].to_list() + [0],
        textposition = "outside",
        text = ["{:,.0f}".format(val) for val in for_plot[col].to_list() + [df[col].sum()]],
        connector = {"line":{"color":"rgb(63, 63, 63)"}},
    ))

    fig.update_layout(
            # title = col,
            showlegend = False
    )

    return fig

@app.callback(
    Output("results", "data"),
    Output("upload-data", "contents"),
    Output('renewable_elec', 'value'),
    Input("upload-data", "contents"),
    Input("reset-button", "n_clicks"),
    State("upload-data", "filename"),
    State("upload-data", "last_modified"),
)
def update_results(contents, n_clicks, filename, date):
    reset_status = False
    update_status = False

    ctx = dash.callback_context
    changed_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if changed_id == "reset-button":
        res_new = res.copy()
        reset_status = True
        # return res.to_json(date_format='iso', orient='split'), reset_status, update_status

    elif contents:
        lci_new = parse_contents(contents, filename, date)
        # df_new = pd.merge(lci_new, lookup, left_on='Input', right_index=True)

        res_new = calc(lci_new)
        update_status = True
    else:
        res_new = res.copy()

    # return res_new.to_json(date_format='iso', orient='split'), reset_status, update_status, None
    return {
        "pd": res_new.to_json(date_format="iso", orient="split"),
        "r_status": reset_status,
        "p_status": update_status,
    }, None, 0


@app.callback(
    Output("graph1", "figure"),
    Output("graph2", "figure"),
    Output("graph3", "figure"),
    Output("graph4", "figure"),
    Output("reset_status", "is_open"),
    Output("update_status", "is_open"),
    Input("results", "data"),
    Input("tabs", "active_tab"),
    Input('renewable_elec', 'value'),
    State("reset_status", "is_open"),
    State("update_status", "is_open"),
)
def update_figures(data, tab, re, rs, us):

    ctx = dash.callback_context
    changed_id = ctx.triggered[0]["prop_id"].split(".")[0]

    # print(ctx.triggered)
    if changed_id == "results":
        reset_status = data["r_status"]
        update_status = data["p_status"]
    else:
        reset_status = rs
        update_status = us

    res_new = pd.read_json(data["pd"], orient="split")
    res_new.loc[res_new['Resource']=='Electricity', tab + "_Sum"] = res_new.loc[res_new['Resource']=='Electricity', tab + "_Sum"] * (1 - re)
    fig1_new = px.bar(
        res_new, x="Process", y=tab + "_Sum", color="Category", custom_data=["Category"]
    )
    # fig1_new.update_layout(barmode="stack")
    fig1_new.update_traces(marker_line_width=0)
    fig2_new = make_waterfall_plot(res_new, tab)
    # fig2_new = px.bar(
    #     res_new,
    #     x="Resource",
    #     y="Input Amount",
    #     color="Process",
    #     custom_data=["Process"],
    # )
    fig3_new = px.pie(res_new, values=tab + "_Sum", names="Category")
    fig4_new = px.treemap(
        res_new,
        path=[px.Constant("all"), "Process", "Category", "Resource"],
        values=tab + "_Sum",
        color="Process",
    )

    return fig1_new, fig2_new, fig3_new, fig4_new, reset_status, update_status


if __name__ == "__main__":
    app.run_server(debug=True)
