import base64
from distutils import core
import io
from typing import final
import plotly.graph_objs as go
import plotly.express as px
import numpy as np
import math

import dash
from dash import dcc, html, MATCH, ALL
from dash.dash_table import DataTable, FormatTemplate
from dash.dash_table.Format import Format, Scheme, Trim
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
import json
from calc import (
    generate_coproduct_lci,
    read_data,
    calc,
    generate_final_lci,
    generate_coproduct_lci,
    data_check,
    # calculate_allocation_ratio,
)
from utils import (
    display_units,
    # format_input,
    energy,
    biorefinery_units,
    biorefinery_conversion,
    metric_units,
    unit_conversion,
)
from allocation import format_input

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
# app = dash.Dash(__name__, external_stylesheets=['https://codepen.io/chriddyp/pen/bWLwgP.css', dbc.themes.BOOTSTRAP])

server = app.server

nav_item = dbc.Nav(
    [
        dbc.NavItem(html.Br(), className="d-none d-md-block"),
        dbc.NavItem(html.Br(), className="d-none d-md-block"),
        dbc.NavItem(html.H2("SOT Pathways"), className="d-none d-md-block"),
        # dbc.NavItem(dbc.NavLink("")),
        dbc.NavItem(html.Hr(), className="d-none d-md-block"),
        dbc.NavItem(html.Br()),
        # dbc.NavItem(dbc.NavLink("Test")),
        dbc.NavItem(
            dbc.NavLink(
                "Biochemical Conversion",
                # href="/Biochemical-Conversion",
                href="/",
                active="exact",
                external_link=True,
            )
        ),
        dbc.NavItem(
            dbc.NavLink(
                "Catalytic Fast Pyrolysis",
                href="/Catalytic-Fast-Pyrolysis",
                active="exact",
                external_link=True,
            )
        ),
        dbc.NavItem(
            dbc.NavLink(
                "Indirect Hydrothermal Liquefaction",
                href="/Indirect-Hydrothermal-Liquefaction",
                active="exact",
                external_link=True,
            )
        ),
        dbc.NavItem(
            dbc.NavLink(
                "Combined Algae Processing",
                href="/Combined-Algae-Processing",
                active="exact",
                external_link=True,
            )
        ),
        dbc.NavItem(
            dbc.NavLink(
                "Algae Hydrothermal Liquefaction",
                href="/Algae-Hydrothermal-Liquefaction",
                active="exact",
                external_link=True,
            )
        ),
        dbc.NavItem(
            dbc.NavLink(
                "WWT Sludge Hydrothermal Liquefaction",
                href="/WWT-Sludge-Hydrothermal-Liquefaction",
                active="exact",
                external_link=True,
            )
        ),
    ],
    vertical="md",
    pills=True,
)

navbar = dbc.Navbar(
    dbc.Container(
        [
            dbc.NavbarBrand(
                "SOT Pathways",
                id="navbar-brand",
                href="#",
                className="d-md-none",
                # style={'overflow': 'hidden'}
            ),
            dbc.NavbarToggler(id="navbar-toggler", n_clicks=0),
            dbc.Collapse(
                [
                    dbc.Nav(
                        [
                            nav_item,
                        ],
                        # className="ms-auto",
                        navbar=True,
                        # id='navbar-content',
                        # style={'width': '50%', 'margin-left': "50px", 'padding': "0px", 'clear': 'left'}
                    )
                ],
                id="navbar-collapse",
                navbar=True,
            ),
        ]
    ),
    # className="mb-5 border-bottom",
    color="white",
    # expand='lg',
    # style={'width':'100%'}
)

single_file_content = [
    html.Br(),
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
    dbc.Alert(
        [
            html.H5(
                "Results cannot be updated due to the following error in the LCI file: ",
                className="alert-heading",
            ),
            # html.Br(),
            html.H6(id="error_message"),
        ],
        id="error_status",
        color="danger",
        # style={"textAlign": "center"},
        dismissable=True,
        is_open=False,
    ),
    dbc.Row(
        [
            dbc.Col(
                dcc.Upload(
                    id="upload-data",
                    children=html.Div(
                        [
                            "Drag and Drop or ",
                            html.A("Select Files", className="link-primary"),
                        ]
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
                )
            ),
            dbc.Col(
                dbc.Button(
                    "Reset",
                    color="primary",
                    className="me-1",
                    id="reset-button",
                    n_clicks=0,
                    style={"margin": "10px"},
                ),
                width="auto",
                className="align-self-center",
            ),
        ],
        className="mb-3",
    ),
    dbc.Row(
        [
            dbc.Col(
                dbc.Card(
                    [
                        dbc.CardHeader(
                            "Summary",
                            # className="fw-bold"
                        ),
                        dbc.CardBody(
                            [
                                html.P(className="card-title", id="summary"),
                            ]
                        ),
                    ],
                    color="success",
                    inverse=True,
                    # outline=True,
                ),
                # width=6,
            )
        ],
        className="mb-4",
    ),
    dbc.Row(
        [
            dbc.Col(
                dbc.Card(
                    [
                        dbc.CardHeader("Select Co-product Handling Method"),
                        dbc.CardBody(
                            dcc.Dropdown(
                                [
                                    "User Specification",
                                    "Displacement Method",
                                    "System Level Mass-Based Allocation",
                                    "System Level Energy-Based Allocation",
                                    "System Level Value-Based Allocation",
                                    "Process Level Mass-Based Allocation",
                                    "Process Level Energy-Based Allocation",
                                    "Process Level Value-Based Allocation",
                                ],
                                "User Specification",
                                id="coproduct-handling",
                                placeholder="Select co-product handling method",
                            )
                        ),
                    ],
                    color="secondary",
                    outline=True,
                ),
                # width=6,
            ),
        ],
        className="mb-4",
    ),
    dbc.Row(
        dbc.Col(
            dbc.Card(
                [
                    dbc.CardHeader("Quick Sensitivity Analysis"),
                    dbc.CardBody(
                        [
                            html.H5("Renewable Electricity %", className="text-center"),
                            dcc.Slider(
                                0,
                                1,
                                step=None,
                                marks={
                                    val: "{:.0%}".format(val)
                                    for val in np.linspace(0, 1, 11)
                                },
                                value=0,
                                id="renewable_elec",
                            ),
                        ]
                    ),
                ],
                color="secondary",
                outline=True,
            ),
            # width={"size": 6, "offset": 3}
        ),
        className="mb-4",
    ),
    dbc.Tabs(
        [
            dbc.Tab(label="GHG", tab_id="GHG", activeTabClassName="fw-bold fst-italic"),
            dbc.Tab(label="NOx", tab_id="NOx", activeTabClassName="fw-bold fst-italic"),
            dbc.Tab(
                label="Water", tab_id="Water", activeTabClassName="fw-bold fst-italic"
            ),
            # dbc.Tab(label="N2O", tab_id="N2O", activeTabClassName="fw-bold fst-italic"),
            # dbc.Tab(label="CO2", tab_id="CO2", activeTabClassName="fw-bold fst-italic"),
            # dbc.Tab(label="CH4", tab_id="CH4", activeTabClassName="fw-bold fst-italic"),
            dbc.Tab(label="CO", tab_id="CO", activeTabClassName="fw-bold fst-italic"),
            dbc.Tab(label="SOx", tab_id="SOx", activeTabClassName="fw-bold fst-italic"),
            dbc.Tab(
                label="PM10", tab_id="PM10", activeTabClassName="fw-bold fst-italic"
            ),
            dbc.Tab(
                label="PM2.5", tab_id="PM2.5", activeTabClassName="fw-bold fst-italic"
            ),
            dbc.Tab(label="VOC", tab_id="VOC", activeTabClassName="fw-bold fst-italic"),
            # dbc.Tab(label="BC", tab_id="BC", activeTabClassName="fw-bold fst-italic"),
            # dbc.Tab(label="OC", tab_id="OC", activeTabClassName="fw-bold fst-italic"),
        ],
        id="tabs",
        active_tab="GHG",
    ),
    html.Br(),
    dbc.Row(
        [
            dbc.Col(dcc.Graph(id="graph1"), md=6),
            dbc.Col(dcc.Graph(id="graph2"), md=6),
        ],
        style={"width": "100%"},
    ),
    dbc.Row(
        [
            dbc.Col(dcc.Graph(id="graph3"), md=6),
            dbc.Col(dcc.Graph(id="graph4"), md=6),
        ],
        style={"width": "100%"},
    ),
    dbc.Container(id="dropdown"),
    dbc.Row(id={"type": "datatable", "index": 0}, className="mb-5"),
]

sensitivity_content = [
    html.Br(),
    dbc.Alert(
        [
            html.H5(
                "Results cannot be updated due to the following error in the LCI file: ",
                className="alert-heading",
            ),
            html.H6("", id="sensitivity_error_message"),
        ],
        id="sensitivity_error_status",
        color="danger",
        # style={"textAlign": "center"},
        dismissable=True,
        is_open=False,
    ),
    dcc.Upload(
        id="upload-data-sensitivity",
        children=html.Div(
            [
                "Drag and Drop or ",
                html.A("Select Multiple LCI Files", className="link-primary"),
                " For Sensitivity Analysis",
            ]
        ),
        style={
            "width": "100%",
            "height": "60px",
            "lineHeight": "60px",
            "borderWidth": "1px",
            "borderStyle": "dashed",
            "borderRadius": "5px",
            "textAlign": "center",
            # "margin": "10px",
        },
        # Allow multiple files to be uploaded
        multiple=True,
        className="mb-4",
    ),
    dbc.Card(
        [
            dbc.CardHeader("Select Co-product Handling Method"),
            dbc.CardBody(
                dcc.Dropdown(
                    [
                        "User Specification",
                        "Displacement Method",
                        "System Level Mass-Based Allocation",
                        "System Level Energy-Based Allocation",
                        "System Level Value-Based Allocation",
                        "Process Level Mass-Based Allocation",
                        "Process Level Energy-Based Allocation",
                        "Process Level Value-Based Allocation",
                    ],
                    "User Specification",
                    id="coproduct-handling-sensitivity",
                    placeholder="Select co-product handling method",
                ),
            ),
        ],
        className="mb-4",
    ),
    dbc.Tabs(
        [
            dbc.Tab(label="GHG", tab_id="GHG", activeTabClassName="fw-bold fst-italic"),
            dbc.Tab(label="NOx", tab_id="NOx", activeTabClassName="fw-bold fst-italic"),
            dbc.Tab(
                label="Water", tab_id="Water", activeTabClassName="fw-bold fst-italic"
            ),
            # dbc.Tab(label="N2O", tab_id="N2O", activeTabClassName="fw-bold fst-italic"),
            # dbc.Tab(label="CO2", tab_id="CO2", activeTabClassName="fw-bold fst-italic"),
            # dbc.Tab(label="CH4", tab_id="CH4", activeTabClassName="fw-bold fst-italic"),
            dbc.Tab(label="CO", tab_id="CO", activeTabClassName="fw-bold fst-italic"),
            dbc.Tab(label="SOx", tab_id="SOx", activeTabClassName="fw-bold fst-italic"),
            dbc.Tab(
                label="PM10", tab_id="PM10", activeTabClassName="fw-bold fst-italic"
            ),
            dbc.Tab(
                label="PM2.5", tab_id="PM2.5", activeTabClassName="fw-bold fst-italic"
            ),
            dbc.Tab(label="VOC", tab_id="VOC", activeTabClassName="fw-bold fst-italic"),
            # dbc.Tab(label="BC", tab_id="BC", activeTabClassName="fw-bold fst-italic"),
            # dbc.Tab(label="OC", tab_id="OC", activeTabClassName="fw-bold fst-italic"),
        ],
        id="sensitivity-tabs",
        active_tab="GHG",
    ),
    dcc.Graph(id="graph1-sensitivity"),
]

overall_tabs = dbc.Tabs(
    [
        dbc.Tab(single_file_content, label="Case Study"),
        dbc.Tab(sensitivity_content, label="Sensitivity Analysis"),
    ]
)

content = [
    dcc.Store(id="results"),
    dcc.Store(id="sensitivity-results"),
    html.Br(),
    html.H1(children="SOT LCA Results", className="text-dark"),
    html.H3(
        children="""
    RD Production from Corn Stover via Biochem Pathway
""",
        className="text-muted text-decoration-underline",
    ),
    html.Hr(),
    overall_tabs,
]

app.layout = dbc.Container(
    [
        dcc.Location(id="url", refresh=False),
        dbc.Row([dbc.Col(navbar, md=3), dbc.Col(content, md=9, className="mt-10")]),
    ],
    # fluid=True
)


def parse_contents(contents, filename, date):
    """
    Parse the uploaded LCI file
    """
    content_type, content_string = contents.split(",")

    decoded = base64.b64decode(content_string)
    if "xls" in filename:
        # Assume that the user uploaded an excel file
        lci_file = io.BytesIO(decoded)
    else:
        lci_file = "Only .xls files are supported."

    return lci_file


def make_waterfall_plot(res, metric="GHG", n=4):
    """
    Generate the waterfall plot
    """

    df = res.copy()
    col = metric + "_Sum"

    df.loc[df[col] < 0, "Resource"] = df.loc[df[col] < 0, "Resource"].apply(
        lambda x: "Disp. Credit of " + x
    )
    dfp = df[df[col] > 0].groupby("Resource", as_index=False)[col].sum()
    dfn = df[df[col] < 0].groupby("Resource", as_index=False)[col].sum()
    df1 = dfp.nlargest(n, col)
    df2 = dfn.nsmallest(n, col)
    other = df[col].sum() - df1[col].sum() - df2[col].sum()

    for_plot = pd.concat(
        [
            df1[["Resource", col]],
            pd.Series({"Resource": "Other", col: other}).to_frame().T,
            df2[["Resource", col]],
        ]
    )

    fig = go.Figure(
        go.Waterfall(
            orientation="v",
            measure=["relative"] * len(for_plot) + ["total"],
            x=for_plot["Resource"].to_list() + ["Total"],
            y=for_plot[col].to_list() + [0],
            textposition="outside",
            text=[
                "{:,.2f}".format(val)
                for val in for_plot[col].to_list() + [df[col].sum()]
            ],
            connector={"line": {"color": "rgb(63, 63, 63)"}},
        )
    )

    fig.update_layout(showlegend=False)

    return fig


@app.callback(
    Output({"type": "datatable", "index": MATCH}, "children"),
    Input({"type": "process_dropdown", "index": MATCH}, "value"),
    State("results", "data"),
    State("reset_status", "is_open"),
)
def show_datatable(process_to_edit, stored_data, rs):
    """
    Generate the data table
    """
    if (process_to_edit is None) or (rs):
        return []
    else:
        data = json.loads(stored_data)
        lci_data = data["lci"]
        lci_mapping = {
            key: pd.read_json(value, orient="split") for key, value in lci_data.items()
        }
        df = lci_mapping[process_to_edit]
        cols = [{"id": c, "name": c, "editable": (c == "Amount")} for c in df.columns]
        for col in cols:
            if col["name"] == "Amount":
                col["type"] = "numeric"
                col["format"] = Format(precision=2, scheme=Scheme.decimal_or_exponent)
        return [
            DataTable(
                id={"type": "lci_datatable", "index": 0},
                data=df.to_dict("records"),
                columns=cols,
                fixed_rows={"headers": True},
                style_cell={
                    "minWidth": 95,
                    "maxWidth": 95,
                    "width": 95,
                    "whiteSpace": "normal",
                    "height": "auto",
                    "lineHeight": "15px",
                },
                style_header={
                    "backgroundColor": "rgb(210, 210, 210)",
                    "fontWeight": "bold",
                },
                style_data_conditional=[
                    {
                        "if": {"row_index": "odd"},
                        "backgroundColor": "rgb(220, 220, 220)",
                    },
                    {"if": {"column_editable": True}, "color": "blue"},
                ],
                style_table={
                    "height": 400,
                    "overflowX": "auto",
                },
                tooltip_data=[
                    {
                        column: {"value": str(value), "type": "markdown"}
                        for column, value in row.items()
                    }
                    for row in df.to_dict("records")
                ],
                tooltip_duration=None,
            )
        ]


# add callback for toggling the collapse on small screens
@app.callback(
    Output("navbar-collapse", "is_open"),
    # Output("navbar-content", "children"),
    # Output("navbar-brand", "children"),
    Input("navbar-toggler", "n_clicks"),
    State("navbar-collapse", "is_open"),
)
def toggle_navbar_collapse(n, is_open):
    """
    Toggle the navbar
    """
    if n:
        return not is_open
    return is_open


@app.callback(
    Output("results", "data"),
    Output("dropdown", "children"),
    Output("upload-data", "contents"),
    Output("renewable_elec", "value"),
    Input("upload-data", "contents"),
    Input("coproduct-handling", "value"),
    Input("reset-button", "n_clicks"),
    # Input("update-lci", "n_clicks"),
    Input({"type": "update-lci", "index": ALL}, "n_clicks"),
    Input("url", "pathname"),
    State("upload-data", "filename"),
    State("upload-data", "last_modified"),
    State("results", "data"),
    State({"type": "lci_datatable", "index": ALL}, "data"),
    State({"type": "process_dropdown", "index": ALL}, "value"),
)
def update_results(
    contents,
    coproduct,
    n_clicks1,
    n_clicks2,
    pathname,
    filename,
    date,
    stored_data,
    data_table,
    process_to_edit,
):
    """
    Update the LCA results
    """
    reset_status = False
    update_status = False
    error_status = False
    dropdown_items = []
    lci_data = {}
    coproduct_mapping = {}  # The coproduct mapping specified in the uploaded file
    updated_coproduct_mapping = {}  # The coproduct mapping used in the calculation
    final_process_mapping = {}
    data_status = "OK"
    dropdown_value = None
    uploaded = False  # Whether a new LCI file has been uploaded
    lci_new = None
    coproduct_res = pd.DataFrame()
    # error_message = ""

    ctx = dash.callback_context
    changed_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if contents or ("update-lci" in changed_id) or (changed_id == "coproduct-handling"):
        if contents:
            lci_new = parse_contents(contents, filename, date)

            if not isinstance(lci_new, str):
                lci_mapping, coproduct_mapping, final_process_mapping = read_data(
                    lci_new
                )
                uploaded = True
        if (
            ("update-lci" in changed_id)
            or (changed_id == "coproduct-handling")
            or isinstance(lci_new, str)
        ):
            data = json.loads(stored_data)
            uploaded = data["uploaded"]
            lci_data = data["lci"]
            lci_mapping = {
                key: pd.read_json(value, orient="split")
                for key, value in lci_data.items()
            }
            coproduct_mapping = data[
                "coproduct"
            ]  # The original co-product handling methods specified in the uploaded LCI file
            final_process_mapping = data["final_process"]

            if "update-lci" in changed_id:
                lci_mapping[process_to_edit[0]] = pd.DataFrame(data_table[0])
                dropdown_value = process_to_edit[0]

        if coproduct != "User Specification":
            updated_coproduct_mapping = {key: coproduct for key in coproduct_mapping}
        else:
            updated_coproduct_mapping = coproduct_mapping.copy()

        data_status = data_check(
            lci_mapping, updated_coproduct_mapping, final_process_mapping
        )
        if data_status == "OK":
            overall_lci, final_process = generate_final_lci(
                lci_mapping, updated_coproduct_mapping, final_process_mapping, True
            )
            res_new = calc(overall_lci)
            update_status = True
            coproduct_lci = generate_coproduct_lci(
                lci_mapping, updated_coproduct_mapping, final_process_mapping
            )
            if coproduct_lci is not None:
                coproduct_res = calc(coproduct_lci)
        else:
            data = json.loads(stored_data)
            res_new = pd.read_json(data["pd"], orient="split")
            coproduct_res = pd.read_json(data["coproduct_res"], orient="split")
            error_status = True
        # if lci_new is not None:
        if isinstance(lci_new, str):
            data_status = lci_new
            error_status = True
            update_status = False
    else:
        if changed_id == "reset-button":
            reset_status = True
        file_to_use = "Feedstock test2-with INL data.xlsm"
        if "Sludge" in pathname:
            file_to_use = "sludge HTL3.xlsm"
        lci_mapping, coproduct_mapping, final_process_mapping = read_data(
            # "2021 Biochem SOT via BDO_working.xlsm"
            # "Feedstock test2.xlsm"
            file_to_use
        )
        updated_coproduct_mapping = coproduct_mapping.copy()
        overall_lci, final_process = generate_final_lci(
            lci_mapping, updated_coproduct_mapping, final_process_mapping, True
        )
        res_new = calc(overall_lci)
        coproduct_lci = generate_coproduct_lci(
            lci_mapping, updated_coproduct_mapping, final_process_mapping
        )
        if coproduct_lci is not None:
            coproduct_res = calc(coproduct_lci)

    lci_data = {
        key: value.to_json(orient="split", date_format="iso")
        for key, value in lci_mapping.items()
    }

    if uploaded:
        dropdown_items = [
            dbc.Row(
                [
                    dbc.Col(html.H5(["Edit Life Cycle Inventory Data"])),
                    # dbc.Col(dbc.Button("Update", color="secondary", className="me-1", id={'type': 'update-lci', 'index': 0}))
                ]
            ),
            # dbc.Row(dbc.Col(dcc.Dropdown(sheet_names, id={'type': 'process_dropdown', 'index': 0})))
            dbc.Row(
                [
                    dbc.Col(
                        dcc.Dropdown(
                            list(lci_mapping.keys()),
                            id={"type": "process_dropdown", "index": 0},
                            value=dropdown_value,
                            # value=None,
                        )
                    ),
                    dbc.Col(
                        dbc.Button(
                            "Update",
                            color="success",
                            className="mb-3",
                            id={"type": "update-lci", "index": 0},
                        ),
                        width="auto",
                    ),
                ]
            ),
        ]

    # Calcualte the parameters required for biorefinery-level results
    coproduct_method = coproduct_mapping[final_process]
    if "Mass" in coproduct_mapping:
        basis = "mass"
    elif "Energy" in coproduct_method:
        basis = "energy"
    elif "Value" in coproduct_method:
        basis = "value"
    else:
        basis = None
    final_process_lci = format_input(lci_mapping[final_process], basis=basis)
    main_product_df = final_process_lci.loc[final_process_lci["Type"] == "Main Product"]
    main_product_series = main_product_df.iloc[0].copy()
    main_product_series["Input Amount"] = main_product_series["Amount"]
    main_product_category = res_new.loc[
        res_new["Type"] == "Main Product", "Category"
    ].values[0]
    main_product_series["Primary Unit"] = display_units[main_product_category]
    conversion = unit_conversion(main_product_series)

    total_biomass = 0  # Initialization
    total_coproduct = 0

    biomass_df = final_process_lci.loc[
        final_process_lci["Category"].isin(["Biomass", "Waste"])
    ].copy()
    if len(biomass_df) > 0:
        biomass_df = biomass_df.rename(columns={"Amount": "Input Amount"})
        biomass_df["Primary Unit"] = "ton"
        biomass_df["Amount"] = biomass_df.apply(unit_conversion, axis=1)
        total_biomass = biomass_df["Amount"].sum() / conversion
    else:  # for waste to energy pathways where the feedstock is not biomass
        biomass_df = overall_lci.loc[
            overall_lci["Category"].isin(["Biomass", "Waste"])
        ].copy()
        if len(biomass_df) > 0:
            biomass_df = biomass_df.rename(columns={"Amount": "Input Amount"})
            biomass_df["Primary Unit"] = "ton"
            biomass_df["Amount"] = biomass_df.apply(unit_conversion, axis=1)
            main_product_df = overall_lci.loc[overall_lci["Type"] == "Main Product"]
            main_product_series = main_product_df.iloc[0].copy()
            main_product_series["Input Amount"] = main_product_series["Amount"]
            main_product_category = res_new.loc[
                res_new["Type"] == "Main Product", "Category"
            ].values[0]
            main_product_series["Primary Unit"] = display_units[main_product_category]
            conversion = unit_conversion(main_product_series)
            total_biomass = biomass_df["Amount"].sum() / conversion

    if len(coproduct_res) > 0:
        coproduct_category = coproduct_res.loc[
            coproduct_res["Type"] == "Main Product", "Category"
        ].values[0]
        coproduct_target_unit = display_units[coproduct_category]
        coproduct_df = final_process_lci.loc[
            (final_process_lci["Type"] == "Co-product")
            & (
                final_process_lci["Always Use Displacement Method for Co-Product?"]
                == "No"
            ),
        ].copy()
        coproduct_df = coproduct_df.rename(columns={"Amount": "Input Amount"})
        coproduct_df["Primary Unit"] = coproduct_target_unit
        coproduct_df["Amount"] = coproduct_df.apply(unit_conversion, axis=1)
        total_coproduct = coproduct_df["Amount"].sum() / conversion

    data_to_return = {
        "pd": res_new.to_json(date_format="iso", orient="split"),
        "coproduct_res": coproduct_res.to_json(date_format="iso", orient="split"),
        "lci": lci_data,
        "coproduct": coproduct_mapping,
        "final_process": final_process_mapping,
        "r_status": reset_status,
        "p_status": update_status,
        "e_status": error_status,
        "e_message": data_status,
        "uploaded": uploaded,
        # "ratio": ratio,
        "total_biomass": total_biomass,
        "total_coproduct": total_coproduct,
    }

    return json.dumps(data_to_return), dropdown_items, None, 0


@app.callback(
    Output("graph1", "figure"),
    Output("graph2", "figure"),
    Output("graph3", "figure"),
    Output("graph4", "figure"),
    Output("summary", "children"),
    Output("reset_status", "is_open"),
    Output("update_status", "is_open"),
    Output("error_status", "is_open"),
    Output("error_message", "children"),
    Input("results", "data"),
    Input("tabs", "active_tab"),
    Input("renewable_elec", "value"),
    State("reset_status", "is_open"),
    State("update_status", "is_open"),
    State("error_status", "is_open"),
    State("error_message", "children"),
)
def update_figures(json_data, tab, re, rs, us, es, em):
    """
    Update the visualizations
    """
    data = json.loads(json_data)
    ctx = dash.callback_context
    changed_id = ctx.triggered[0]["prop_id"].split(".")[0]

    unit_sup = " CO2e" if tab == "GHG" else ""
    if tab == "Water":
        tab = "Water consumption: gallons"
        tab_summary = "Water Consumption"
    else:
        tab_summary = tab + " Emission"

    if changed_id == "results":
        reset_status = data["r_status"]
        update_status = data["p_status"]
        error_status = data["e_status"]
        error_message = data["e_message"]
    else:
        reset_status = rs
        update_status = us
        error_status = es
        error_message = em

    res_new_with_incumbent = pd.read_json(data["pd"], orient="split")
    coproduct_with_incumbent = pd.read_json(data["coproduct_res"], orient="split")

    res_new_with_incumbent.loc[
        (res_new_with_incumbent["Resource"] == "Electricity")
        & (~res_new_with_incumbent["Pathway"].str.contains("Incumbent"))
        & (res_new_with_incumbent["Type"].str.contains("Input")),
        tab + "_Sum",
    ] = res_new_with_incumbent.loc[
        res_new_with_incumbent["Resource"] == "Electricity", tab + "_Sum"
    ] * (
        1 - re
    )

    res_new = res_new_with_incumbent[
        ~res_new_with_incumbent["Pathway"].str.contains("Incumbent")
    ]

    main_product_total = res_new[tab + "_Sum"].sum()
    main_product_category = res_new.loc[
        res_new["Type"] == "Main Product", "Category"
    ].values[0]
    main_product_target_unit = display_units[main_product_category]

    fig1_new = px.bar(
        res_new_with_incumbent, x="Pathway", y=tab + "_Sum", color="Process"
    )
    fig1_new.update_layout(barmode="relative", title="Breakdown of " + tab_summary)
    fig1_new.update_traces(marker_line_width=0)
    fig1_new.update_yaxes(
        title=f"{tab_summary} ({metric_units[tab]}{unit_sup}/{main_product_target_unit})"
    )

    fig2_new = px.bar(
        res_new,
        x="Process",
        y=tab + "_Sum",
        color="Category",
        custom_data=["Category"],
    )
    fig2_new.update_layout(barmode="relative")
    fig2_new.update_traces(marker_line_width=0)
    fig2_new.update_layout(title="Breakdown of " + tab_summary + " by Process")
    fig2_new.update_xaxes(title="Process")
    fig2_new.update_yaxes(
        title=f"{tab_summary} ({metric_units[tab]}{unit_sup}/{main_product_target_unit})"
    )

    fig3_new = make_waterfall_plot(res_new, tab)
    # fig2_new = px.bar(
    #     res_new,
    #     x="Resource",
    #     y="Input Amount",
    #     color="Process",
    #     custom_data=["Process"],
    # )
    fig3_new.update_layout(title="Waterfall Chart of " + tab_summary + " by Inputs")
    # fig2_new.update_xaxes(title='Process')
    fig3_new.update_yaxes(
        title=f"{tab_summary} ({metric_units[tab]}{unit_sup}/{main_product_target_unit})"
    )

    # fig3_new = px.pie(res_new, values=tab + "_Sum", names="Category")
    # fig3_new.update_layout(title="% Contribution to " + tab + " Emissions")
    # # fig3_new.update_xaxes(title='Process')
    # # fig3_new.update_yaxes(title='GHG Emissions (g CO2e/MJ)')

    fig4_new = px.treemap(
        res_new,
        path=[px.Constant("all"), "Process", "Category", "Resource"],
        values=tab + "_Sum",
        color="Process",
    )
    fig4_new.update_layout(title="Breakdown of " + tab_summary + " by Inputs")
    # fig4_new.update_xaxes(title='Process')
    # fig4_new.update_yaxes(title='GHG Emissions (g CO2e/MJ)')

    # main_product_total = res_new[tab + "_Sum"].sum()
    # main_product_category = res_new.loc[
    #     res_new["Type"] == "Main Product", "Category"
    # ].values[0]
    # main_product_target_unit = display_units[main_product_category]

    main_incumbent_total = res_new_with_incumbent.loc[
        res_new_with_incumbent["Pathway"].str.contains("Incumbent"),
        tab + "_Sum",
    ].sum()

    main_diff = 1 - main_product_total / main_incumbent_total
    main_change = "increase" if main_diff <= 0 else "reduction"
    main_diff = abs(main_diff)
    main_incumbent_resource = res_new_with_incumbent.loc[
        res_new_with_incumbent["Pathway"].str.contains("Incumbent"), "Resource"
    ].values[0]

    # For biorefinery-level results
    main_conversion = 1
    coproduct_conversion = 1
    # if main_product_category in [
    #     "Electricity",
    #     "Fuel",
    # ]:
    #     main_conversion = energy.loc["MJ", "mmBTU"]

    total_biomass = data["total_biomass"]
    total_coproduct = data["total_coproduct"]
    main_contribution = (
        main_product_total
        * 1
        * main_conversion
        / total_biomass
        / biorefinery_conversion[tab]
    )
    main_incumbent_contribution = (
        main_incumbent_total
        * 1
        * main_conversion
        / total_biomass
        / biorefinery_conversion[tab]
    )

    coproduct_contribution = 0
    coproduct_incumbent_contribution = 0

    summary = [
        html.H4(
            f"Life-Cycle {tab_summary} of Main Product: {main_product_total:,.1f} {metric_units[tab]}/{main_product_target_unit}"
        ),
        html.Ul(
            html.Li(
                html.H5(
                    f"{main_diff:.0%} {main_change} compared to conventional {main_incumbent_resource}"
                )
            )
        ),
    ]
    if len(coproduct_with_incumbent) > 0:
        coproduct_with_incumbent.loc[
            (coproduct_with_incumbent["Resource"] == "Electricity")
            & (~coproduct_with_incumbent["Pathway"].str.contains("Incumbent"))
            & (coproduct_with_incumbent["Type"].str.contains("Input")),
            tab + "_Sum",
        ] = coproduct_with_incumbent.loc[
            coproduct_with_incumbent["Resource"] == "Electricity", tab + "_Sum"
        ] * (
            1 - re
        )  # quick sensitivity analysis for renewable electricity %

        coproduct_res = coproduct_with_incumbent[
            ~coproduct_with_incumbent["Pathway"].str.contains("Incumbent")
        ]
        # if len(coproduct_res) > 0:
        coproduct_total = coproduct_res[tab + "_Sum"].sum()
        coproduct_category = coproduct_res.loc[
            coproduct_res["Type"] == "Main Product", "Category"
        ].values[0]
        coproduct_target_unit = display_units[coproduct_category]

        coproduct_incumbent_total = coproduct_with_incumbent.loc[
            coproduct_with_incumbent["Pathway"].str.contains("Incumbent"),
            tab + "_Sum",
        ].sum()

        coproduct_diff = 1 - coproduct_total / coproduct_incumbent_total
        coproduct_change = "increase" if coproduct_diff <= 0 else "reduction"
        coproduct_diff = abs(coproduct_diff)
        coproduct_incumbent_resource = coproduct_with_incumbent.loc[
            coproduct_with_incumbent["Pathway"].str.contains("Incumbent"), "Resource"
        ].values[0]

        # For biorefinery-level results

        # if coproduct_category in [
        #     "Electricity",
        #     "Fuel",
        # ]:
        #     coproduct_conversion = energy.loc["MJ", "mmBTU"]
        coproduct_contribution = (
            coproduct_total
            * total_coproduct
            * coproduct_conversion
            / total_biomass
            / biorefinery_conversion[tab]
        )
        coproduct_incumbent_contribution = (
            coproduct_incumbent_total
            * total_coproduct
            * coproduct_conversion
            / total_biomass
            / biorefinery_conversion[tab]
        )
        if coproduct_total > 0:
            summary = summary + [
                html.H4(
                    f"\nLife-Cycle {tab_summary} of Co-Product: {coproduct_total:,.1f} {metric_units[tab]}/{coproduct_target_unit}"
                ),
                html.Ul(
                    [
                        html.Li(
                            html.H5(
                                f"{coproduct_diff:.0%} {coproduct_change} compared to conventional {coproduct_incumbent_resource}"
                            )
                        )
                    ]
                ),
            ]

    show_breakdown = True  # For displacement, set to False to hide the contributions by main and co-product to avoid confusion
    if coproduct_contribution <= 0:
        coproduct_contribution = coproduct_incumbent_contribution
        show_breakdown = False
    biorefinery_res = main_contribution + coproduct_contribution
    biorefinery_incumbent_res = (
        main_incumbent_contribution + coproduct_incumbent_contribution
    )
    biorefinery_diff = 1 - biorefinery_res / biorefinery_incumbent_res
    biorefinery_change = "increase" if biorefinery_diff <= 0 else "reduction"
    biorefinery_diff = abs(biorefinery_diff)

    if ~math.isinf(biorefinery_res):
        summary = summary + [
            html.H4(
                f"Biorefinery-level results: {biorefinery_res:,.1f} {biorefinery_units[tab]}/ton"
            ),
            html.Ul(
                html.Li(
                    html.H5(
                        (
                            f"{biorefinery_diff:.0%} {biorefinery_change} compared to the incumbent products."
                        )
                    )
                )
            ),
        ]
    if (len(coproduct_with_incumbent) > 0) and show_breakdown:
        summary = summary + [
            html.Ul(
                [
                    html.Li(
                        html.H5(
                            f"Contribution by the main product: {main_contribution:,.1f} {biorefinery_units[tab]}/ton"
                        )
                    ),
                    html.Li(
                        html.H5(
                            f"Contribution by the coproduct: {coproduct_contribution:,.1f} {biorefinery_units[tab]}/ton"
                        )
                    ),
                ]
            )
        ]

    return (
        fig1_new,
        fig2_new,
        fig3_new,
        fig4_new,
        summary,
        reset_status,
        update_status,
        error_status,
        error_message,
    )


def sensitivity_analysis(list_of_contents, list_of_names, list_of_dates):
    """
    Calcualte LCA results for multiple LCI files
    """
    if list_of_contents is not None:
        df = pd.DataFrame()
        coproduct_mapping_sensitivity = {}
        final_process_sensitivity = {}
        lci_data_sensitivity = {}
        file_error_sensitivity = {}

        for content, filename, date in zip(
            list_of_contents, list_of_names, list_of_dates
        ):
            lci_file = parse_contents(content, filename, date)
            if not isinstance(lci_file, str):
                lci_mapping, coproduct_mapping, final_process_mapping = read_data(
                    lci_file
                )

                coproduct_mapping_sensitivity.update({filename: coproduct_mapping})
                final_process_sensitivity.update({filename: final_process_mapping})

                lci_data = {
                    key: value.to_json(orient="split", date_format="iso")
                    for key, value in lci_mapping.items()
                }
                lci_data_sensitivity.update({filename: lci_data})
            else:
                file_error_sensitivity.update({filename: lci_file})

        return (
            coproduct_mapping_sensitivity,
            final_process_sensitivity,
            lci_data_sensitivity,
            file_error_sensitivity,  # Stores the uploaded files that are in a unsupported format
        )
    return {}, {}, {}, {}


@app.callback(
    Output("sensitivity-results", "data"),
    Output("upload-data-sensitivity", "contents"),
    Input("upload-data-sensitivity", "contents"),
    Input("coproduct-handling-sensitivity", "value"),
    State("upload-data-sensitivity", "filename"),
    State("upload-data-sensitivity", "last_modified"),
    State("sensitivity-results", "data"),
)
def update_sensitivity_results(contents, coproduct, filenames, dates, stored_data):
    """
    Store sensitivity analysis results.
    """
    df = pd.DataFrame()
    sensitivity_error_status = False
    sensitivity_error_message = []
    coproduct_mapping_sensitivity = {}
    final_process_sensitivity = {}
    lci_data_sensitivity = {}
    file_error_sensitivity = {}

    ctx = dash.callback_context
    changed_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if contents:
        (
            coproduct_mapping_sensitivity,
            final_process_sensitivity,
            lci_data_sensitivity,
            file_error_sensitivity,
        ) = sensitivity_analysis(contents, filenames, dates)

    elif changed_id == "coproduct-handling-sensitivity":
        data = json.loads(stored_data)
        lci_data_sensitivity = data["lci_data_sensitivity"]
        final_process_sensitivity = data["final_process_sensitivity"]
        coproduct_mapping_sensitivity = data["coproduct_mapping_sensitivity"]
        file_error_sensitivity = data["file_error_sensitivity"]

    for filename, message in file_error_sensitivity.items():
        sensitivity_error_message.append(filename + ": " + message)

    for filename in lci_data_sensitivity.keys():
        lci_mapping = {
            key: pd.read_json(value, orient="split")
            for key, value in lci_data_sensitivity[filename].items()
        }
        final_process_mapping = final_process_sensitivity[filename]
        if coproduct != "User Specification":
            coproduct_mapping = {
                key: coproduct for key in coproduct_mapping_sensitivity[filename]
            }
        else:
            coproduct_mapping = coproduct_mapping_sensitivity[filename].copy()

        data_status = data_check(lci_mapping, coproduct_mapping, final_process_mapping)
        if data_status != "OK":
            if not sensitivity_error_status:
                sensitivity_error_status = True
            sensitivity_error_message.append(filename + ": " + data_status)
        else:
            overall_lci = generate_final_lci(
                lci_mapping, coproduct_mapping, final_process_mapping
            )
            lca_res = calc(overall_lci, False)
            lca_res["FileName"] = filename.rsplit(".", 1)[0]
            df = pd.concat([df, lca_res], ignore_index=True)

    data_to_return = {
        "pd": df.to_json(date_format="iso", orient="split"),
        "e_status": sensitivity_error_status,
        "e_message": sensitivity_error_message,
        "coproduct_mapping_sensitivity": coproduct_mapping_sensitivity,
        "final_process_sensitivity": final_process_sensitivity,
        "lci_data_sensitivity": lci_data_sensitivity,
        "file_error_sensitivity": file_error_sensitivity,
    }
    return json.dumps(data_to_return), None


@app.callback(
    Output("graph1-sensitivity", "figure"),
    Output("sensitivity_error_status", "is_open"),
    Output("sensitivity_error_message", "children"),
    Input("sensitivity-results", "data"),
    Input("sensitivity-tabs", "active_tab"),
    State("sensitivity_error_status", "is_open"),
    State("sensitivity_error_message", "children"),
)
def update_sensitivity_figures(json_data, tab, es, em):
    """
    Update the visualizations for sensitivity analysis.
    """
    data = json.loads(json_data)
    ctx = dash.callback_context
    changed_id = ctx.triggered[0]["prop_id"].split(".")[0]

    unit_sup = " CO2e" if tab == "GHG" else ""
    if tab == "Water":
        tab = "Water consumption: gallons"
        tab_summary = "Water Consumption"
    else:
        tab_summary = tab + " Emission"

    if changed_id == "sensitivity-results":
        sensitivity_error_status = data["e_status"]
        sensitivity_error_message = data["e_message"]
        children = []
        if sensitivity_error_status:
            for message in sensitivity_error_message:
                children.extend([message, html.Br()])
        if len(children) > 0:
            children = children[:-1]

    else:
        sensitivity_error_status = es
        children = em

    df = pd.read_json(data["pd"], orient="split")

    if len(df) > 0:
        main_product_category = df.loc[df["Type"] == "Main Product", "Category"].values[
            0
        ]
        main_product_target_unit = display_units[main_product_category]

        fig1_sensitivity = px.bar(
            df,
            x="FileName",
            y=tab + "_Sum",
            color="Category",
            custom_data=["Category"],
        )
        fig1_sensitivity.update_layout(barmode="relative")
        fig1_sensitivity.update_traces(marker_line_width=0)
        fig1_sensitivity.update_layout(
            title="Breakdown of " + tab_summary + " by Process"
        )
        fig1_sensitivity.update_xaxes(title="Cases")
        fig1_sensitivity.update_yaxes(
            title=f"{tab_summary} ({metric_units[tab]}{unit_sup}/{main_product_target_unit})"
        )
        return (
            fig1_sensitivity,
            sensitivity_error_status,
            children,
        )
    else:
        return go.Figure(), False, ""


if __name__ == "__main__":
    app.run_server(debug=True)
