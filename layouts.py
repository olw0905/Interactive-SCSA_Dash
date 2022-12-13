"""
    Layout of the tool.
"""
import dash_bootstrap_components as dbc
import numpy as np
from dash import dcc, html
from dash.dash_table import DataTable

from utils import mass_units

add_modal = dbc.Modal(
    [
        dbc.ModalHeader(dbc.ModalTitle("Provide the name of the new case")),
        dbc.ModalBody(
            dbc.Input(
                id="case-name",
                placeholder="Provide the name of the new case",
                type="text",
            ),
        ),
        dbc.ModalFooter(
            [
                dbc.Button("Add", id="add-case-name", n_clicks=0),
                dbc.Button("Cancel", id="cancel-case", color="danger", n_clicks=0),
            ]
        ),
    ],
    id="add_modal",
    is_open=False,
)

edit_modal = dbc.Modal(
    [
        dbc.ModalHeader(dbc.ModalTitle("Select the case to edit")),
        dbc.ModalBody(
            dcc.Dropdown(
                id="edit-case-dropdown",
                placeholder="Case Name",
            )
        ),
        dbc.ModalFooter(
            [
                dbc.Button("Edit", id="edit-case-name", color="success", n_clicks=0),
                dbc.Button("Cancel", id="cancel-edit", color="danger", n_clicks=0),
            ]
        ),
    ],
    id="edit_modal",
    is_open=False,
)

nav_item = dbc.Nav(
    [
        dbc.NavItem(html.Br(), className="d-none d-md-block"),
        dbc.NavItem(html.Br(), className="d-none d-md-block"),
        dbc.NavItem(html.H2("Biofuel Pathways"), className="d-none d-md-block"),
        # dbc.NavItem(dbc.NavLink("")),
        dbc.NavItem(html.Hr(), className="d-none d-md-block"),
        dbc.NavItem(html.Br()),
        # dbc.NavItem(dbc.NavLink("Test")),
        dbc.NavItem(
            dbc.NavLink(
                "Biochemical Conversion",
                # href="/Biochemical-Conversion",
                href="/Biochemical-Conversion",
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
        dbc.NavItem(
            dbc.NavLink(
                "Combined Algae Processing",
                href="/Combined-Algae-Processing",
                active="exact",
                external_link=True,
                # disabled=True,
            )
        ),
        dbc.NavItem(
            dbc.NavLink(
                "Catalytic Fast Pyrolysis",
                href="/Catalytic-Fast-Pyrolysis",
                active="exact",
                external_link=True,
                disabled=True,
            )
        ),
        dbc.NavItem(
            dbc.NavLink(
                "Indirect Hydrothermal Liquefaction",
                href="/Indirect-Hydrothermal-Liquefaction",
                active="exact",
                external_link=True,
                disabled=True,
            )
        ),
        dbc.NavItem(
            dbc.NavLink(
                "Algae Hydrothermal Liquefaction",
                href="/Algae-Hydrothermal-Liquefaction",
                active="exact",
                external_link=True,
                disabled=True,
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
abatement_cost_card = dbc.Card(
    [
        dbc.CardHeader("Specify the Price Range to Plot the Abatement Cost"),
        dbc.CardBody(
            [
                dbc.Row(
                    [
                        dbc.Col(html.H6(""), md=3, className="text-center"),
                        dbc.Col(html.H6("Minimum"), md=3, className="text-center"),
                        dbc.Col(html.H6("Maximum"), md=3, className="text-center"),
                        dbc.Col(html.H6("Unit"), md=3, className="text-center"),
                    ],
                    align="center",
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            html.H5(
                                "Main product price range",
                                id="main_price",
                            ),
                            className="text-end",
                            md=3,
                        ),
                        dbc.Col(
                            dbc.Input(
                                placeholder="Minimum",
                                type="number",
                                id="bmin",
                                value=4,
                            ),
                            md=3,
                        ),
                        dbc.Col(
                            dbc.Input(
                                placeholder="Maximum",
                                type="number",
                                id="bmax",
                                value=8,
                            ),
                            md=3,
                        ),
                        dbc.Col(
                            dcc.Dropdown(
                                id="main-price-unit",
                                placeholder="Unit",
                            ),
                            md=3,
                        ),
                    ],
                    align="center",
                    className="mb-2",
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            html.H5("Incumbent price range", id="incumbent_price"),
                            className="text-end",
                            md=3,
                        ),
                        dbc.Col(
                            dbc.Input(
                                placeholder="Minimum",
                                type="number",
                                id="fmin",
                                value=2,
                            ),
                            md=3,
                        ),
                        dbc.Col(
                            dbc.Input(
                                placeholder="Maximum",
                                type="number",
                                id="fmax",
                                value=6,
                            ),
                            md=3,
                        ),
                        dbc.Col(
                            dcc.Dropdown(
                                id="incumbent-price-unit",
                                placeholder="Unit",
                            ),
                            md=3,
                        ),
                    ],
                    align="center",
                ),
                dbc.Row(dbc.Col(html.Div(id="abatement-cost-summary"))),
            ]
            # color="secondary",
            # outline=True,
        ),
    ],
    className="mb-4",
    color="secondary",
    outline=True,
)

carbon_price_card = dbc.Card(
    [
        dbc.CardHeader("Carbon Credit"),
        dbc.CardBody(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            html.H5(
                                "Carbon Price",
                                id="carbon-price",
                            ),
                            className="text-end",
                            md=3,
                        ),
                        dbc.Col(
                            dbc.Input(
                                # placeholder="value",
                                type="number",
                                id="carbon-price-value",
                                value=200,
                            ),
                            md=4,
                        ),
                        dbc.Col(
                            dcc.Dropdown(
                                id="carbon-price-unit",
                                placeholder="Unit",
                                options=["$/" + unit for unit in mass_units],
                                value="$/metric ton",
                            ),
                            md=4,
                        ),
                    ],
                    align="center",
                    className="mb-2",
                ),
                dbc.Row(dbc.Col(html.Div(id="carbon-credit-summary"))),
                # dbc.Row(
                #     [
                #         dbc.Col(
                #             html.H5("Incumbent price range", id="incumbent_price"),
                #             className="text-end",
                #             md=3,
                #         ),
                #         dbc.Col(
                #             dbc.Input(
                #                 placeholder="Minimum",
                #                 type="number",
                #                 id="fmin",
                #                 value=2,
                #             ),
                #             md=3,
                #         ),
                #         dbc.Col(
                #             dbc.Input(
                #                 placeholder="Maximum",
                #                 type="number",
                #                 id="fmax",
                #                 value=6,
                #             ),
                #             md=3,
                #         ),
                #         dbc.Col(
                #             dcc.Dropdown(
                #                 id="incumbent-price-unit",
                #                 placeholder="Unit",
                #             ),
                #             md=3,
                #         ),
                #     ],
                #     align="center",
                # ),
            ]
            # color="secondary",
            # outline=True,
        ),
    ],
    className="mb-4",
    color="secondary",
    outline=True,
    id="carbon-price-card",
)

carbon_price_collapse = dbc.Collapse(carbon_price_card, id="collapse")

dropdown_items = dbc.Collapse(
    [
        dbc.Row(
            [
                dbc.Col(
                    html.H5(
                        "Cases Added:",
                        # className="me-0"
                    ),
                    width="auto",
                    # className="me-0",
                ),
                dbc.Col(html.H5(id="existing-cases", className="text-success")),
            ],
            className="gx-2",
        ),
        dbc.Row(
            [
                dbc.Col(
                    html.P(
                        children="Edit Life Cycle Inventory Data for Case",
                        className="fst-italic fs-5 text-decoration-underline",
                    ),
                    width="auto",
                ),
                dbc.Col(
                    html.P(
                        id="edit-case",
                        children="",
                        className="fst-italic fs-5 text-decoration-underline text-success",
                    )
                ),
            ],
            className="gx-2",
        ),
        dbc.Row(
            [
                dbc.Col(
                    dcc.Dropdown(
                        id="process_dropdown",
                    )
                ),
                dbc.Col(
                    dbc.Button(
                        "Save Changes",
                        color="success",
                        className="mb-3",
                        n_clicks=0,
                        id="save-case",
                    ),
                    width="auto",
                ),
            ]
        ),
    ],
    id="dropdown_collapse",
)

single_file_content = [
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
    # dbc.Row(
    #     [
    #         dbc.Col(
    #             dbc.Button(
    #                 "Download Template File",
    #                 color="success",
    #                 href="/static/Data Template.xlsm",
    #                 download="Data Template.xlsm",
    #                 # href="/static/test.txt",
    #                 # download="test.txt",
    #                 external_link=True,
    #             )
    #         ),
    #         dbc.Col(
    #             dbc.Button(
    #                 "Download Pathway File",
    #                 id="download-pathway",
    #                 color="success",
    #                 external_link=True,
    #             )
    #         ),
    #     ],
    #     # justify="evenly",
    #     className="text-center mb-2 mt-3",
    # ),
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
            ####################################
            # Button for download results
            dbc.Col(
                [
                    dbc.Button(
                        "Download Results",
                        color="primary",
                        className="me-1",
                        id="download-res-button",
                        n_clicks=0,
                        style={"margin": "10px"},
                    ),
                    dcc.Download(id="download-csv"),
                ],
                width="auto",
                className="align-self-center",
            ),
            ####################################
        ],
        className="mb-3",
    ),
    dbc.Collapse(
        [
            # dbc.Label("Choose Scenario"),
            dbc.Card(
                [
                    dbc.CardHeader("Choose Scenario"),
                    dbc.CardBody(
                        dbc.RadioItems(
                            # options=[
                            #     {"label": "", "value": 1},
                            #     {"label": "Option 2", "value": 2},
                            #     {"label": "Disabled Option", "value": 3, "disabled": True},
                            # ],
                            # value=1,
                            inline=True,
                            id="scenario-radioitems",
                            labelCheckedClassName="text-primary",
                            inputCheckedClassName="border border-primary bg-primary",
                            className="text-center",
                        )
                    ),
                ],
                color="secondary",
                # inverse=True,
                outline=True,
            ),
            # dbc.Accordion(
            #     dbc.AccordionItem(
            #         [
            #             dbc.RadioItems(
            #                 # options=[
            #                 #     {"label": "", "value": 1},
            #                 #     {"label": "Option 2", "value": 2},
            #                 #     {"label": "Disabled Option", "value": 3, "disabled": True},
            #                 # ],
            #                 # value=1,
            #                 inline=True,
            #                 id="scenario-radioitems",
            #                 labelCheckedClassName="text-success",
            #                 inputCheckedClassName="border border-success bg-success",
            #             )
            #         ],
            #         title="Choose Scenario",
            #     ),
            #     flush=True,
            # ),
        ],
        id="scenario-collapse",
        className="mb-4",
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
                    # inverse=True,
                    outline=True,
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
                            html.H5("Renewable Natural Gas %", className="text-center"),
                            dcc.Slider(
                                0,
                                1,
                                step=None,
                                marks={
                                    val: "{:.0%}".format(val)
                                    for val in np.linspace(0, 1, 11)
                                },
                                value=0,
                                id="rng_share",
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
    dbc.Row(dbc.Col(abatement_cost_card)),
    # dbc.Row(dbc.Col(carbon_price_card)),
    dbc.Row(dbc.Col(carbon_price_collapse)),
    # abatement_cost_card,
    dbc.Tabs(
        [
            dbc.Tab(label="GHG", tab_id="GHG", activeTabClassName="fw-bold fst-italic"),
            dbc.Tab(label="NOx", tab_id="NOx", activeTabClassName="fw-bold fst-italic"),
            dbc.Tab(
                label="Water", tab_id="Water", activeTabClassName="fw-bold fst-italic"
            ),
            dbc.Tab(
                label="Fossil energy",
                tab_id="Fossil energy",
                activeTabClassName="fw-bold fst-italic",
            ),
            dbc.Tab(
                label="Petroleum",
                tab_id="Petroleum",
                activeTabClassName="fw-bold fst-italic",
            ),
            dbc.Tab(
                label="Coal",
                tab_id="Coal",
                activeTabClassName="fw-bold fst-italic",
            ),
            dbc.Tab(
                label="Natural gas",
                tab_id="Natural gas",
                activeTabClassName="fw-bold fst-italic",
            ),
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
            dbc.Tab(
                label="Urban NOx",
                tab_id="Urban NOx",
                activeTabClassName="fw-bold fst-italic",
            ),
            dbc.Tab(
                label="Urban CO",
                tab_id="Urban CO",
                activeTabClassName="fw-bold fst-italic",
            ),
            dbc.Tab(
                label="Urban SOx",
                tab_id="Urban SOx",
                activeTabClassName="fw-bold fst-italic",
            ),
            dbc.Tab(
                label="Urban VOC",
                tab_id="Urban VOC",
                activeTabClassName="fw-bold fst-italic",
            ),
        ],
        id="tabs",
        active_tab="GHG",
    ),
    html.Br(),
    dbc.Row(
        [
            dbc.Col(
                dcc.Graph(
                    id="graph1",
                    config={"toImageButtonOptions": {"filename": "Fig1", "scale": 2}},
                ),
                md=6,
            ),
            dbc.Col(
                dcc.Graph(
                    id="graph2",
                    config={"toImageButtonOptions": {"filename": "Fig2", "scale": 2}},
                ),
                md=6,
            ),
        ],
        style={"width": "100%"},
    ),
    dbc.Row(
        [
            dbc.Col(
                dcc.Graph(
                    id="graph3",
                    config={"toImageButtonOptions": {"filename": "Fig3", "scale": 2}},
                ),
                md=6,
            ),
            dbc.Col(
                [
                    # form,
                    # dbc.Row(
                    #     [
                    #         dbc.Col(dbc.Input(placeholder="Price"), md=3),
                    #         dbc.Col(dbc.Input(placeholder="Price 2"), md=3),
                    #         dbc.Col(dcc.RangeSlider(id="range-slider", min=0, max=10, value=[3, 7]),)
                    #     ]
                    # ),
                    dcc.Graph(
                        id="graph4",
                        config={
                            "toImageButtonOptions": {"filename": "Fig4", "scale": 2}
                        },
                    ),
                ],
                md=6,
            ),
        ],
        style={"width": "100%"},
    ),
    dbc.Row(
        [
            dbc.Col(
                dbc.Button(
                    "Add a sensitivity case",
                    outline=True,
                    color="success",
                    className="mb-3",
                    id="add-case-btn",
                    # className="me-0",
                ),
                width="auto",
            ),
            dbc.Col(
                dbc.Collapse(
                    dbc.Button(
                        "Edit existing cases",
                        outline=True,
                        color="success",
                        className="mb-3",
                        n_clicks=0,
                        id="edit-case-btn",
                    ),
                    id="edit-case-collapse",
                ),
                width="auto",
            ),
            dbc.Col(
                dbc.Collapse(
                    dbc.Button(
                        "Generate results",
                        outline=True,
                        color="success",
                        className="mb-3",
                        n_clicks=0,
                        id="perform-sensitivity-analysis",
                    ),
                    id="generate-results-collapse",
                ),
                width="auto",
            ),
        ],
        className="gx-2",
    ),
    html.Div(id="dropdown", children=dropdown_items),
    # dbc.Row
    dbc.Collapse(
        DataTable(
            id="lci_datatable",
            # data=df.to_dict("records"),
            # columns=cols,
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
            # tooltip_data=[
            #     {
            #         column: {"value": str(value), "type": "markdown"}
            #         for column, value in row.items()
            #     }
            #     for row in df.to_dict("records")
            # ],
            tooltip_duration=None,
        ),
        # id={"type": "datatable", "index": 0},
        className="mb-5",
        id="datatable_collapse",
    ),
    html.Div(id="manual-sensitivity-figs"),
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
            dbc.Tab(
                label="Fossil energy",
                tab_id="Fossil energy",
                activeTabClassName="fw-bold fst-italic",
            ),
            dbc.Tab(
                label="Petroleum",
                tab_id="Petroleum",
                activeTabClassName="fw-bold fst-italic",
            ),
            dbc.Tab(
                label="Coal",
                tab_id="Coal",
                activeTabClassName="fw-bold fst-italic",
            ),
            dbc.Tab(
                label="Natural gas",
                tab_id="Natural gas",
                activeTabClassName="fw-bold fst-italic",
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
    dcc.Graph(
        id="graph1-sensitivity",
        config={"toImageButtonOptions": {"filename": "Sensitivity-fig1", "scale": 2}},
    ),
    dcc.Graph(
        id="graph2-sensitivity",
        config={"toImageButtonOptions": {"filename": "Sensitivity-fig2", "scale": 2}},
    ),
]

overall_tabs = dbc.Tabs(
    [
        dbc.Tab(single_file_content, label="Case Study"),
        dbc.Tab(sensitivity_content, label="Sensitivity Analysis"),
    ]
)

title_name = "GREET-Based Interactive Life-Cycle Assessment of BETO Biofuel Pathways"
content = [
    dcc.Store(id="results"),
    dcc.Store(id="simple-sensitivity-results"),
    dcc.Store(id="sensitivity-results"),
    html.Br(),
    html.H1(
        children=title_name,
        className="text-dark",
    ),
    dbc.Row(
        [
            dbc.Col(
                html.H3(
                    #         children="""
                    #     RD Production from Corn Stover via Biochem Pathway
                    # """,
                    className="text-muted text-decoration-underline",
                    id="pathway-title",
                )
            ),
            dbc.Col(
                dbc.Button(
                    "Download LCI File",
                    id="download-pathway",
                    color="success",
                    external_link=True,
                    # className="me-2",
                    # size="lg",
                ),
                width="auto",
            ),
        ],
        align="center",
    ),
    html.Hr(),
    overall_tabs,
    # dbc.Row(
    #     [
    #         dbc.Col(overall_tabs),
    #         dbc.Col(
    #             dbc.Button(
    #                 "Download Pathway File",
    #                 id="download-pathway",
    #                 color="success",
    #                 external_link=True,
    #                 className="me-4",
    #             ),
    #             width="auto",
    #         ),
    #     ]
    # ),
]

index_page = html.Div(  # The content of the index page
    [
        html.Br(),
        html.Br(),
        html.H1(
            title_name,
            # style={"textAlign": "center"},
        ),
        # html.Br(),
        dbc.Nav(
            [
                # dbc.NavItem(html.Br(), className="d-none d-md-block"),
                dbc.NavItem(html.Br(), className="d-none d-md-block"),
                # dbc.NavItem(html.H2("Biofuel Pathways"), className="d-none d-md-block"),
                # dbc.NavItem(dbc.NavLink("")),
                dbc.NavItem(html.Hr(), className="d-none d-md-block"),
                dbc.NavItem(html.Br()),
                # dbc.NavItem(dbc.NavLink("Test")),
                dbc.NavItem(
                    dbc.NavLink(
                        html.H3("Biochemical Conversion"),
                        # href="/Biochemical-Conversion",
                        href="/Biochemical-Conversion",
                        active="exact",
                        external_link=True,
                    )
                ),
                dbc.NavItem(
                    dbc.NavLink(
                        html.H3("WWT Sludge Hydrothermal Liquefaction"),
                        href="/WWT-Sludge-Hydrothermal-Liquefaction",
                        active="exact",
                        external_link=True,
                    )
                ),
                dbc.NavItem(
                    dbc.NavLink(
                        html.H3("Combined Algae Processing"),
                        href="/Combined-Algae-Processing",
                        active="exact",
                        external_link=True,
                        # disabled=True,
                    )
                ),
                dbc.NavItem(
                    dbc.NavLink(
                        html.H3("Catalytic Fast Pyrolysis"),
                        href="/Catalytic-Fast-Pyrolysis",
                        active="exact",
                        external_link=True,
                        disabled=True,
                    )
                ),
                dbc.NavItem(
                    dbc.NavLink(
                        html.H3("Indirect Hydrothermal Liquefaction"),
                        href="/Indirect-Hydrothermal-Liquefaction",
                        active="exact",
                        external_link=True,
                        disabled=True,
                    )
                ),
                dbc.NavItem(
                    dbc.NavLink(
                        html.H3("Algae Hydrothermal Liquefaction"),
                        href="/Algae-Hydrothermal-Liquefaction",
                        active="exact",
                        external_link=True,
                        disabled=True,
                    )
                ),
            ],
            vertical="md",
            # horizontal="center",
            pills=True,
            className="text-center",
        )
        # dbc.Card(
        #     [
        #         dbc.CardHeader("Table of Contents"),
        #         dbc.CardBody(
        #             [
        #                 dcc.Link(
        #                     "Biochemical Conversion", href="/Biochemical-Conversion"
        #                 ),
        #                 html.Br(),
        #                 dcc.Link(
        #                     "WWT Sludge Hydrothermal Liquefaction",
        #                     href="/WWT-Sludge-Hydrothermal-Liquefaction",
        #                 ),
        #             ]
        #         ),
        #     ],
        #     style={
        #         "textAlign": "center",
        #     },
        # ),
    ]
)

# The content when a pathway is selected
pathway_page = [
    add_modal,
    edit_modal,
    dbc.Row([dbc.Col(navbar, md=3), dbc.Col(content, md=9, className="mt-10")]),
]

url_bar_and_content_div = dbc.Container(
    [
        dcc.Location(id="url", refresh=False),
        html.Div(id="page-content"),
        # dbc.Row([dbc.Col(navbar, md=3), dbc.Col(content, md=9, className="mt-10")]),
    ],
    # fluid=True
)
