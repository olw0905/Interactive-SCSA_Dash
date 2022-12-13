import json
import math

import dash
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
from dash import Input, Output, State, callback, dcc, html
from dash.dash_table.Format import Format, Scheme

from functions import (
    generate_abatement_cost,
    generate_carbon_credit,
    make_waterfall_plot,
    parse_contents,
    quick_sensitivity,
    sensitivity_analysis,
)
from calc import (
    data_check,
    generate_coproduct_lci,  # calc,
    generate_final_lci,
    postprocess,
    read_data,
)
from utils import (
    format_input,
    abatement_cost_units,
    biorefinery_conversion,
    biorefinery_units,
    calculate_lca,
    display_units,
    files,
    mass,
    mass_units,
    metric_units,
    potential_units,
    unit_conversion,
)

#############################################################
# Callback for download results
@callback(
    Output("download-csv", "data"),
    Input("download-res-button", "n_clicks"),
    State("results", "data"),
    prevent_initial_call=True,
)
def download_files(n_clicks, stored_data):
    data = json.loads(stored_data)
    # lci_data = data["lci"]
    df = pd.read_json(data["pd"], orient="split")
    df = df.loc[~df["Pathway"].str.contains("Incumbent")]
    return dcc.send_data_frame(df.to_csv, "results.csv")


#############################################################


@callback(
    Output("download-pathway", "href"),
    Output("download-pathway", "download"),
    Input("url", "pathname"),
    Input("scenario-radioitems", "value"),
)
def download_files(pathname, value):
    file_to_use = ""
    file_name = ""
    if "Biochemical" in pathname:
        file_to_use = files["biochem"][value]
        file_name = "Biochem-BDO.xlsm" if value == 0 else "Biochem-Acids.xlsm"
    elif "Sludge" in pathname:
        file_to_use = files["sludge"][value]
        file_name = (
            "Sludge HTL_without NH3 removal.xlsm"
            if value == 0
            else "Sludge HTL_with NH3 removal.xlsm"
        )
    elif "Combined" in pathname:
        file_to_use = files["cap"][value]
        file_name = "CAP via BDO.xlsm" if value == 0 else "CAP via acids.xlsm"
    return file_to_use, file_name


@callback(
    Output("pathway-title", "children"),
    Output("scenario-radioitems", "options"),
    Output("scenario-radioitems", "value"),
    Output("scenario-collapse", "is_open"),
    Input("url", "pathname"),
)
def update_pathway_title(pathname):
    """
    Update the pathway title
    """
    is_open = False
    options = []
    value = None
    pathway_tile = "In development"

    if "Biochemical" in pathname:
        pathway_title = "RD Production from Corn Stover via Biochemical Conversion"
        options = [
            {"label": "via BDO", "value": 0},
            {"label": "via Acids", "value": 1},
        ]
        value = 0
        is_open = True
    if "Sludge" in pathname:
        pathway_title = "RD Production from WWTP's Sludge via Hydrothermal Liquefaction"
        options = [
            {"label": "with Ammonia Removal", "value": 0},
            {"label": "without Ammonia Removal", "value": 1},
        ]
        value = 1
        is_open = True
    if "Combined" in pathname:
        pathway_title = "RD Production from Combined Algae Processing"
        options = [
            {"label": "via BDO", "value": 0},
            {"label": "via Acids", "value": 1},
        ]
        value = 1
        is_open = True
    return pathway_title, options, value, is_open


@callback(
    Output("lci_datatable", "data"),
    Output("lci_datatable", "columns"),
    Output("lci_datatable", "tooltip_data"),
    Output("datatable_collapse", "is_open"),
    Input("process_dropdown", "value"),
    State("results", "data"),
    State("reset_status", "is_open"),
)
def show_datatable(process_to_edit, stored_data, rs):
    """
    Generate the data table
    """
    if (process_to_edit is None) or (rs):
        # return pd.DataFrame().to_dict("records"), [], []
        return None, [], [], False
    else:
        data = json.loads(stored_data)
        lci_data = data["lci"]
        lci_mapping = {
            key: pd.read_json(value, orient="split") for key, value in lci_data.items()
        }
        df = lci_mapping[process_to_edit]
        data = df.to_dict("records")
        cols = [{"id": c, "name": c, "editable": (c == "Amount")} for c in df.columns]
        for col in cols:
            if col["name"] == "Amount":
                col["type"] = "numeric"
                col["format"] = Format(precision=2, scheme=Scheme.decimal_or_exponent)
        tooltip_data = [
            {
                column: {"value": str(value), "type": "markdown"}
                for column, value in row.items()
            }
            for row in data
        ]
        return data, cols, tooltip_data, True


# add callback for toggling the collapse on small screens
@callback(
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


@callback(
    Output("results", "data"),
    Output("upload-data", "contents"),
    Output("renewable_elec", "value"),
    Output("rng_share", "value"),
    Output("incumbent-price-unit", "options"),
    Output("main-price-unit", "options"),
    Output("incumbent-price-unit", "value"),
    Output("main-price-unit", "value"),
    Input("upload-data", "contents"),
    Input("coproduct-handling", "value"),
    Input("reset-button", "n_clicks"),
    Input("renewable_elec", "value"),
    Input("rng_share", "value"),
    Input("url", "pathname"),
    Input("scenario-radioitems", "value"),
    State("upload-data", "filename"),
    State("upload-data", "last_modified"),
    State("results", "data"),
    State("lci_datatable", "data"),
    State("process_dropdown", "value"),
)
def update_results(
    contents,
    coproduct,
    n_clicks1,
    # n_clicks2,
    renewable_elec_share,
    rng_share,
    pathname,
    value,
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
    # dropdown_items = []
    lci_data = {}
    coproduct_mapping = {}  # The coproduct mapping specified in the uploaded file
    updated_coproduct_mapping = {}  # The coproduct mapping used in the calculation
    final_process_mapping = {}
    data_status = "OK"
    # dropdown_value = None
    uploaded = False  # Whether a new LCI file has been uploaded
    lci_new = None
    coproduct_res = pd.DataFrame()
    renew_elec = 0
    rng = 0
    # error_message = ""

    ctx = dash.callback_context
    changed_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if (
        contents
        # or ("update-lci" in changed_id)
        or (changed_id in ["coproduct-handling", "renewable_elec", "rng_share"])
    ):
        if contents:
            lci_new = parse_contents(contents, filename, date)

            if not isinstance(lci_new, str):
                lci_mapping, coproduct_mapping, final_process_mapping = read_data(
                    lci_new
                )
                uploaded = True
        if (
            (changed_id in ["coproduct-handling", "renewable_elec", "rng_share"])
            # or ("update-lci" in changed_id)
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
            renew_elec = renewable_elec_share
            rng = rng_share

            # if "update-lci" in changed_id:
            #     lci_mapping[process_to_edit] = pd.DataFrame(data_table)
            #     dropdown_value = process_to_edit
            #     renew_elec = 0
            #     rng = 0

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
            # overall_lci = elec_sensitivity(overall_lci, renew_elec)
            # overall_lci = rng_sensitivity(overall_lci, rng)
            overall_lci = quick_sensitivity(overall_lci, renew_elec, rng)
            res_new = postprocess(calculate_lca(overall_lci))
            update_status = True
            coproduct_return = generate_coproduct_lci(
                lci_mapping, updated_coproduct_mapping, final_process_mapping
            )
            if coproduct_return is not None:
                # coproduct_lci = elec_sensitivity(coproduct_lci, renew_elec)
                # coproduct_lci = rng_sensitivity(coproduct_lci, rng)
                (
                    coproduct_lci,
                    coproduct_final_process_mapping,
                    coproduct_final_process,
                ) = coproduct_return
                coproduct_lci = quick_sensitivity(coproduct_lci, renew_elec, rng)
                coproduct_res = postprocess(calculate_lca(coproduct_lci))
            else:
                coproduct_final_process = final_process
        else:  # Errors esist in the uploaded LCI file, restore to the previous results
            data = json.loads(stored_data)
            uploaded = data["uploaded"]
            lci_data = data["lci"]
            lci_mapping = {
                key: pd.read_json(value, orient="split")
                for key, value in lci_data.items()
            }
            coproduct_mapping = data["coproduct"]
            updated_coproduct_mapping = coproduct_mapping.copy()
            final_process_mapping = data["final_process"]
            res_new = pd.read_json(data["pd"], orient="split")
            coproduct_res = pd.read_json(data["coproduct_res"], orient="split")
            error_status = True
            update_status = False
            renew_elec = 0
            rng = 0

            coproduct_return = generate_coproduct_lci(
                lci_mapping, updated_coproduct_mapping, final_process_mapping
            )
            if coproduct_return is not None:
                (
                    coproduct_lci,
                    coproduct_final_process_mapping,
                    coproduct_final_process,
                ) = coproduct_return
                # coproduct_lci = elec_sensitivity(coproduct_lci, renew_elec)
                # coproduct_lci = rng_sensitivity(coproduct_lci, rng)
                coproduct_lci = quick_sensitivity(coproduct_lci, renew_elec, rng)
                coproduct_res = postprocess(calculate_lca(coproduct_lci))
            else:
                for sheet, process_bool in final_process_mapping.items():
                    if process_bool == "Yes":
                        final_process = sheet
                        break
                coproduct_final_process = final_process
        # if lci_new is not None:
        if isinstance(lci_new, str):
            data_status = lci_new
            error_status = True
            update_status = False
    else:
        if changed_id == "reset-button":
            reset_status = True
            renew_elec = 0
            rng = 0
        file_to_use = ""
        if "Biochemical" in pathname:
            file_to_use = files["biochem"][value]
        elif "Sludge" in pathname:
            file_to_use = files["sludge"][value]
        elif "Combined" in pathname:
            file_to_use = files["cap"][value]
        lci_mapping, coproduct_mapping, final_process_mapping = read_data(
            # "2021 Biochem SOT via BDO_working.xlsm"
            # "Feedstock test2.xlsm"
            file_to_use
        )
        updated_coproduct_mapping = coproduct_mapping.copy()
        overall_lci, final_process = generate_final_lci(
            lci_mapping, updated_coproduct_mapping, final_process_mapping, True
        )
        # overall_lci = elec_sensitivity(overall_lci, renew_elec)
        # overall_lci = rng_sensitivity(overall_lci, rng)
        overall_lci = quick_sensitivity(overall_lci, renew_elec, rng)
        res_new = postprocess(calculate_lca(overall_lci))
        coproduct_return = generate_coproduct_lci(
            lci_mapping, updated_coproduct_mapping, final_process_mapping
        )
        if coproduct_return is not None:
            (
                coproduct_lci,
                coproduct_final_process_mapping,
                coproduct_final_process,
            ) = coproduct_return
            # coproduct_lci = elec_sensitivity(coproduct_lci, renew_elec)
            # coproduct_lci = rng_sensitivity(coproduct_lci, rng)
            coproduct_lci = quick_sensitivity(coproduct_lci, renew_elec, rng)
            coproduct_res = postprocess(calculate_lca(coproduct_lci))
        else:
            coproduct_final_process = final_process

        lci_data = {
            key: value.to_json(orient="split", date_format="iso")
            for key, value in lci_mapping.items()
        }

    # Calcualte the parameters required for biorefinery-level results
    coproduct_method = coproduct_mapping[coproduct_final_process]
    if "Mass" in coproduct_mapping:
        basis = "mass"
    elif "Energy" in coproduct_method:
        basis = "energy"
    elif "Value" in coproduct_method:
        basis = "value"
    else:
        basis = None
    final_process_lci = format_input(lci_mapping[coproduct_final_process], basis=basis)
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
    potential_price_unit = [
        "$/" + unit for unit in potential_units[main_product_category]
    ]
    dorpdown_value = (
        "$/GGE"
        if main_product_category in ["Process fuel"]
        else potential_price_unit[0]
    )

    # return json.dumps(data_to_return), dropdown_items, None, 0
    return (
        json.dumps(data_to_return),
        # dropdown_items,
        None,
        renew_elec,
        rng,
        potential_price_unit,
        potential_price_unit,
        dorpdown_value,
        dorpdown_value,
    )


@callback(
    Output("collapse", "is_open"),
    Input("tabs", "active_tab"),
)
def hide_carbon_price(tab):
    """
    Hide the carbon price card
    """
    if tab == "GHG":
        # return "mb-4"
        return True
    else:
        # return "mb-4 d-none"
        return False


@callback(
    Output("graph1", "figure"),
    Output("graph2", "figure"),
    Output("graph3", "figure"),
    Output("graph4", "figure"),
    Output("summary", "children"),
    Output("reset_status", "is_open"),
    Output("update_status", "is_open"),
    Output("error_status", "is_open"),
    Output("error_message", "children"),
    Output("main_price", "children"),
    Output("incumbent_price", "children"),
    Output("abatement-cost-summary", "children"),
    Output("carbon-credit-summary", "children"),
    Input("results", "data"),
    Input("tabs", "active_tab"),
    Input("fmin", "value"),
    Input("fmax", "value"),
    Input("incumbent-price-unit", "value"),
    Input("bmin", "value"),
    Input("bmax", "value"),
    Input("main-price-unit", "value"),
    Input("carbon-price-value", "value"),
    Input("carbon-price-unit", "value"),
    # Input("renewable_elec", "value"),
    State("reset_status", "is_open"),
    State("update_status", "is_open"),
    State("error_status", "is_open"),
    State("error_message", "children"),
)
def update_figures(
    json_data, tab, fmin, fmax, funit, bmin, bmax, bunit, cprice, cunit, rs, us, es, em
):
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
    elif tab in [
        "Total energy",
        # "Fossil fuels",
        "Coal",
        "Natural gas",
        "Petroleum",
    ]:
        tab_summary = tab + " consumption"
        tab = tab + ", Btu"
    elif tab == "Fossil energy":
        tab_summary = tab + " consumption"
        tab = "Fossil fuels, Btu"
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
    res_new_with_incumbent = res_new_with_incumbent.loc[
        ~(
            (res_new_with_incumbent[tab + "_Sum"] == 0)
            & (res_new_with_incumbent["Type"].str.contains("Input"))
        )
    ]
    coproduct_with_incumbent = pd.read_json(data["coproduct_res"], orient="split")

    # res_new_with_incumbent.loc[
    #     (res_new_with_incumbent["Resource"] == "Electricity")
    #     & (~res_new_with_incumbent["Pathway"].str.contains("Incumbent"))
    #     & (res_new_with_incumbent["Type"].str.contains("Input")),
    #     tab + "_Sum",
    # ] = res_new_with_incumbent.loc[
    #     res_new_with_incumbent["Resource"] == "Electricity", tab + "_Sum"
    # ] * (
    #     1 - re
    # )

    res_new = res_new_with_incumbent[
        ~res_new_with_incumbent["Pathway"].str.contains("Incumbent")
    ]
    # res_new = res_new.loc[res_new[tab + "_Sum"] != 0]

    main_product_total = res_new[tab + "_Sum"].sum()
    main_product_category = res_new.loc[
        res_new["Type"] == "Main Product", "Category"
    ].values[0]
    main_product_target_unit = display_units[main_product_category]

    # df_positive = res_new_with_incumbent[res_new_with_incumbent[tab + "_Sum"] > 0]
    # df_negative = res_new_with_incumbent[res_new_with_incumbent[tab + "_Sum"] < 0]
    # df_positive = df_positive.groupby(["Pathway", "Life-Cycle Stage"], as_index=False)[
    #     tab + "_Sum"
    # ].sum()
    # df_negative = df_negative.groupby(["Pathway", "Life-Cycle Stage"], as_index=False)[
    #     tab + "_Sum"
    # ].sum()
    # df_fig1 = pd.concat([df_positive, df_negative], ignore_index=True)

    # fig1_new = px.bar(
    #     df_fig1,
    #     x="Pathway",
    #     y=tab + "_Sum",
    #     color="Life-Cycle Stage",
    #     category_orders={"Pathway": res_new_with_incumbent["Pathway"].values},
    # )
    fig1_new = px.histogram(
        res_new_with_incumbent,
        x="Pathway",
        y=tab + "_Sum",
        color="Life-Cycle Stage",
        category_orders={"Pathway": res_new_with_incumbent["Pathway"].values},
    )
    fig1_new.update_layout(
        barmode="relative",
        title={
            "text": "Breakdown of " + tab_summary,
            "y": 0.95,
            "x": 0.5,
            "xanchor": "center",
            "yanchor": "top",
        },
    )
    fig1_new.update_traces(marker_line_width=0)
    fig1_new.update_yaxes(
        title=f"{tab_summary} ({metric_units[tab]}{unit_sup}/{main_product_target_unit})"
    )

    # df_fig2 = res_new.groupby(["Life-Cycle Stage", "Category"], as_index=False)[
    #     tab + "_Sum"
    # ].sum()
    # fig2_new = px.bar(
    #     df_fig2,
    #     x="Life-Cycle Stage",
    #     y=tab + "_Sum",
    #     color="Category",
    #     custom_data=["Category"],
    #     category_orders={"Life-Cycle Stage": res_new["Life-Cycle Stage"].values},
    # )
    fig2_new = px.histogram(
        res_new,
        x="Life-Cycle Stage",
        y=tab + "_Sum",
        color="Category",
        category_orders={"Life-Cycle Stage": res_new["Life-Cycle Stage"].values},
    )
    fig2_new.update_layout(barmode="relative")
    fig2_new.update_traces(marker_line_width=0)
    fig2_new.update_layout(
        title={
            "text": "Breakdown of " + tab_summary + " by Stage",
            "y": 0.95,
            "x": 0.5,
            "xanchor": "center",
            "yanchor": "top",
        }
    )
    fig2_new.update_xaxes(title="Life-Cycle Stage")
    fig2_new.update_yaxes(
        title=f"{tab_summary} ({metric_units[tab]}{unit_sup}/{main_product_target_unit})"
    )

    fig3_new = make_waterfall_plot(res_new, tab)
    # fig2_new = px.bar(
    #     res_new,
    #     x="Resource",
    #     y="Input Amount",
    #     color="Life-Cycle Stage",
    #     custom_data=["Life-Cycle Stage"],
    # )
    fig3_new.update_layout(
        title={
            "text": "Waterfall Chart of " + tab_summary + " by Inputs",
            "y": 0.95,
            "x": 0.5,
            "xanchor": "center",
            "yanchor": "top",
        }
    )
    # fig2_new.update_xaxes(title='Process')
    fig3_new.update_yaxes(
        title=f"{tab_summary} ({metric_units[tab]}{unit_sup}/{main_product_target_unit})"
    )

    # fig3_new = px.pie(res_new, values=tab + "_Sum", names="Category")
    # fig3_new.update_layout(title="% Contribution to " + tab + " Emissions")
    # # fig3_new.update_xaxes(title='Process')
    # # fig3_new.update_yaxes(title='GHG Emissions (g CO2e/MJ)')

    # fig4_new = px.treemap(
    #     res_new,
    #     path=[px.Constant("all"), "Life-Cycle Stage", "Category", "Resource"],
    #     values=tab + "_Sum",
    #     color="Life-Cycle Stage",
    # )
    # fig4_new.update_layout(title="Breakdown of " + tab_summary + " by Inputs")
    # # fig4_new.update_xaxes(title='Process')
    # # fig4_new.update_yaxes(title='GHG Emissions (g CO2e/MJ)')

    # # main_product_total = res_new[tab + "_Sum"].sum()
    # # main_product_category = res_new.loc[
    # #     res_new["Type"] == "Main Product", "Category"
    # # ].values[0]
    # # main_product_target_unit = display_units[main_product_category]

    main_incumbent_total = res_new_with_incumbent.loc[
        res_new_with_incumbent["Pathway"].str.contains("Incumbent"),
        tab + "_Sum",
    ].sum()

    main_diff = 1 - main_product_total / main_incumbent_total
    main_change = "increase" if main_diff <= 0 else "reduction"
    main_diff = abs(main_diff)
    main_product_resource = res_new_with_incumbent.loc[
        res_new_with_incumbent["Type"] == "Main Product", "Resource"
    ].values[0]
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
        html.H5(
            f"Life-Cycle {tab_summary} of Main Product: {main_product_total:,.1f} {metric_units[tab]}/{main_product_target_unit}",
            className="text-success",
        ),
        html.Ul(
            html.Li(
                html.P(
                    f"{main_diff:.0%} {main_change} compared to conventional {main_incumbent_resource.lower()}",
                ),
                className="text-success",
            )
        ),
    ]
    if tab == "Fossil fuels, Btu":
        summary = summary + [
            html.Ul(
                html.Li(
                    html.P(
                        f"Net energy balance: {1-main_product_total:,.1f} {metric_units[tab]}/{main_product_target_unit}"
                    ),
                    className="text-success",
                )
            ),
        ]
    if len(coproduct_with_incumbent) > 0:
        #     coproduct_with_incumbent.loc[
        #         (coproduct_with_incumbent["Resource"] == "Electricity")
        #         & (~coproduct_with_incumbent["Pathway"].str.contains("Incumbent"))
        #         & (coproduct_with_incumbent["Type"].str.contains("Input")),
        #         tab + "_Sum",
        #     ] = coproduct_with_incumbent.loc[
        #         coproduct_with_incumbent["Resource"] == "Electricity", tab + "_Sum"
        #     ] * (
        #         1 - re
        #     )  # quick sensitivity analysis for renewable electricity %

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
                html.Hr(),
                html.H5(
                    f"\nLife-Cycle {tab_summary} of Co-Product: {coproduct_total:,.1f} {metric_units[tab]}/{coproduct_target_unit}",
                    className="text-warning",
                ),
                html.Ul(
                    [
                        html.Li(
                            html.P(
                                f"{coproduct_diff:.0%} {coproduct_change} compared to conventional {coproduct_incumbent_resource.lower()}"
                            ),
                        )
                    ],
                    className="text-warning",
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
            html.Hr(),
            html.H5(
                f"Biorefinery-level results: {biorefinery_res:,.1f} {biorefinery_units[tab]}/ton",
                className="text-primary",
            ),
            html.Ul(
                html.Li(
                    html.P(
                        (
                            f"{biorefinery_diff:.0%} {biorefinery_change} compared to the incumbent products"
                        )
                    ),
                    className="mb-0 text-primary",
                ),
                # style={"margin-bottom": "0"},
                className="mb-0",
            ),
        ]
    if (len(coproduct_with_incumbent) > 0) and show_breakdown:
        summary = summary + [
            html.Ul(
                [
                    html.Li(
                        html.P(
                            f"Contribution by the main product: {main_contribution:,.1f} {biorefinery_units[tab]}/ton"
                        )
                    ),
                    html.Li(
                        html.P(
                            f"Contribution by the coproduct: {coproduct_contribution:,.1f} {biorefinery_units[tab]}/ton"
                        )
                    ),
                ],
                className="text-primary",
            )
        ]

    df = generate_abatement_cost(
        fmin,
        fmax,
        funit,
        bmin,
        bmax,
        bunit,
        fossil_metric=main_incumbent_total,
        biofuel_metric=main_product_total,
        main_product_category=main_product_category,
        main_incumbent_resource=main_incumbent_resource,
        main_product_resource=main_product_resource,
    )
    if len(df) > 0:
        if abatement_cost_units[tab] in mass_units:
            df["abatement_cost"] = (
                df["abatement_cost"]
                * mass.loc[metric_units[tab], abatement_cost_units[tab]]
            )  # Convert $/g to $/metric ton. Other units do not need the conversion step
        fig4_new = px.line(
            df,
            x="biofuel_cost",
            y="abatement_cost",
            color="fossil_cost",
            labels={
                "fossil_cost": f"{main_incumbent_resource} Price ({funit})",
                "biofuel_cost": f"{main_product_resource} Price ({bunit})",
                "abatement_cost": f"{tab_summary} abatement cost ($/{abatement_cost_units[tab]})",
            },
            # title=f"{tab_summary} Abatement Cost",
        )
        fig4_new.update_layout(
            title={
                "text": f"{tab_summary} Abatement Cost",
                "y": 0.95,
                "x": 0.5,
                "xanchor": "center",
                "yanchor": "top",
            }
        )
    else:
        fig4_new = go.Figure()
        fig4_new.update_layout(
            title={
                "text": "Please provide price ranges to plot the abatement cost",
                "y": 0.95,
                "x": 0.5,
                "xanchor": "center",
                "yanchor": "top",
            }
        )
    main_price = f"{main_product_resource} Price"
    incumbent_price = f"{main_incumbent_resource} Price"
    abatement_cost_max = df["abatement_cost"].max()
    abatement_cost_min = df["abatement_cost"].min()
    abatement_cost_summary = [
        html.H5(
            f"The estimated {tab} abatement cost ranges between {abatement_cost_min:.2f} and {abatement_cost_max:.2f} $/{abatement_cost_units[tab]} (See Figure 4 for details).",
            className="text-success mt-3",
        ),
    ]

    if tab == "GHG":
        credit = generate_carbon_credit(
            cprice=cprice,
            cunit=cunit,
            main_product_category=main_product_category,
            fossil_ghg=main_incumbent_total,
            biofuel_ghg=main_product_total,
        )
        credit_unit = (
            "GGE"
            if main_product_category in ["Process fuel"]
            else display_units[main_product_category]
        )
        carbon_credit_summary = html.H5(
            f"The estimated carbon credit is ${credit:.2f}/{credit_unit}.",
            className="text-success mt-3",
        )
    else:
        carbon_credit_summary = ""

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
        main_price,
        incumbent_price,
        abatement_cost_summary,
        carbon_credit_summary,
    )


@callback(
    Output("edit-case", "children"),
    Output("process_dropdown", "value"),
    Input("add-case-name", "n_clicks"),
    Input("perform-sensitivity-analysis", "n_clicks"),
    Input("edit-case-name", "n_clicks"),
    State("edit-case-dropdown", "value"),
    State("case-name", "value"),
    State("edit-case", "children"),
)
def update_case_name(n1, n2, n3, case_to_edit, case_to_add, case_editing):
    """
    Update case name based on user input.
    """
    ctx = dash.callback_context
    changed_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if changed_id in ["add-case-name"]:
        if (case_to_add is not None) and (case_to_add != ""):
            case = case_to_add
        else:
            case = case_editing
    elif changed_id in ["edit-case-name"]:
        if (case_to_edit is not None) and (case_to_edit != ""):
            case = case_to_edit
        else:
            case = case_editing
    else:
        case = case_editing
    if (case is not None) and (case != ""):
        return f"{case}", None
    else:
        return "", None


@callback(
    Output("add_modal", "is_open"),
    Input("add-case-btn", "n_clicks"),
    Input("add-case-name", "n_clicks"),
    Input("cancel-case", "n_clicks"),
)
def add_new_case(n1, n2, n3):
    """
    Add a new case manually
    """
    is_open = False

    ctx = dash.callback_context
    changed_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if changed_id in ["add-case-btn"]:
        is_open = True
    elif changed_id in ["add-case-name", "cancel-case"]:
        is_open = False
    return is_open


@callback(
    Output("edit_modal", "is_open"),
    Input("edit-case-btn", "n_clicks"),
    Input("edit-case-name", "n_clicks"),
    Input("cancel-edit", "n_clicks"),
)
def edit_case(n1, n2, n3):
    """
    Edit an existing case
    """
    is_open = False

    ctx = dash.callback_context
    changed_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if changed_id in ["edit-case-btn"]:
        is_open = True
    elif changed_id in ["edit-case-name", "cancel-edit"]:
        is_open = False
    return is_open


@callback(
    Output("dropdown_collapse", "is_open"),
    Output("generate-results-collapse", "is_open"),
    Output("edit-case-collapse", "is_open"),
    Output("process_dropdown", "options"),
    Output("edit-case-dropdown", "options"),
    Output("edit-case-dropdown", "value"),
    Output("existing-cases", "children"),
    # Input("add-case-name", "n_clicks"),
    # Input("reset-button", "n_clicks"),
    # Input("upload-data", "contents"),
    Input("simple-sensitivity-results", "data"),
    # State("results", "data"),
    # State("case-name", "value"),
)
def update_dropdown_options(stored_data):
    """
    Add a new case manually
    """
    # ctx = dash.callback_context
    # changed_id = ctx.triggered[0]["prop_id"].split(".")[0]

    # if ((changed_id in ["add-case-name"]) and (case_name is not None)
    #         and (case_name != "") and (stored_data is not None)):
    #     data = json.loads(stored_data)
    #     lci_data = data["lci"]
    #     options = list(lci_data.keys())
    #     return True, True, options
    # else:
    #     return False, False, []
    if stored_data is not None:
        data = json.loads(stored_data)
        lci_data_sensitivity = data["lci_data"]
        if (
            len(lci_data_sensitivity) > 1
        ):  # At least one case other than Base Case is added.
            stage_options = list(lci_data_sensitivity["Base Case"].keys())
            case_options = list(lci_data_sensitivity.keys())[1:]
            existing_cases = ", ".join(case_options)
            return True, True, True, stage_options, case_options, None, existing_cases
        return False, False, False, [], [], None, None


@callback(
    Output("simple-sensitivity-results", "data"),
    # Output("existing-cases", "children"),
    Input("add-case-name", "n_clicks"),
    Input("save-case", "n_clicks"),
    Input("perform-sensitivity-analysis", "n_clicks"),
    Input("reset-button", "n_clicks"),
    Input("upload-data", "contents"),
    Input("renewable_elec", "value"),
    Input("rng_share", "value"),
    Input("coproduct-handling", "value"),
    # State("existing-cases", "children"),
    State("case-name", "value"),
    State("edit-case", "children"),
    State("results", "data"),
    State("simple-sensitivity-results", "data"),
    State("lci_datatable", "data"),
    State("process_dropdown", "value"),
)
def add_case_data(
    n1,
    n2,
    n3,
    n4,
    contents,
    renew_elec,
    rng,
    coproduct,
    # existing_cases,
    case_adding,
    case_editing,
    base_case_data,
    quick_sens_data,
    data_table,
    process_to_edit,
):
    """
    Add a new case manually
    """

    # coproduct_mapping_sensitivity = {}
    # final_process_sensitivity = {}
    df = pd.DataFrame()
    lci_data_sensitivity = {}
    # dropdown_items = []
    # is_open = False

    ctx = dash.callback_context
    changed_id = ctx.triggered[0]["prop_id"].split(".")[0]

    # if changed_id in ["add-case-btn"]:
    #     is_open = True

    if (changed_id in ["add-case-name"]) and (quick_sens_data is not None):
        sensitivity_data = json.loads(quick_sens_data)
        lci_data_sensitivity = sensitivity_data["lci_data"]
        if (
            (case_adding is not None)
            and (case_adding != "")
            and (base_case_data is not None)
        ):
            # Copy LCI data of the base case
            data = json.loads(base_case_data)
            base_lci = data["lci"]
            if "Base Case" not in lci_data_sensitivity.keys():
                lci_data_sensitivity["Base Case"] = base_lci

            lci_data_sensitivity.update({case_adding: base_lci})
            # is_open = False

            # # existing_cases = (
            # #     case_name
            # #     if existing_cases is None
            # #     else existing_cases + ", " + case_name
            # # )
            # existing_cases = ", ".join(list(lci_data_sensitivity.keys())[1:])

    elif (changed_id in ["save-case"]) and (quick_sens_data is not None):
        sensitivity_data = json.loads(quick_sens_data)

        lci_data_sensitivity = sensitivity_data["lci_data"]

        if (case_editing is not None) and (case_editing != ""):
            lci_data = lci_data_sensitivity[case_editing]
            lci_mapping = {
                key: pd.read_json(value, orient="split")
                for key, value in lci_data.items()
            }
            if (process_to_edit is not None) and (len(data_table) > 0):
                lci_mapping[process_to_edit] = pd.DataFrame(data_table)
                lci_data_sensitivity[case_editing] = {
                    key: value.to_json(orient="split", date_format="iso")
                    for key, value in lci_mapping.items()
                }

    elif (
        changed_id
        in [
            "perform-sensitivity-analysis",
            "renewable_elec",
            "rng_share",
            "coproduct-handling",
        ]
    ) and (quick_sens_data is not None):
        sensitivity_data = json.loads(quick_sens_data)
        lci_data_sensitivity = sensitivity_data["lci_data"]
        data = json.loads(base_case_data)
        for case_name in sensitivity_data["lci_data"]:
            lci_data = lci_data_sensitivity[case_name]
            lci_mapping = {
                key: pd.read_json(value, orient="split")
                for key, value in lci_data.items()
            }
            coproduct_mapping = data["coproduct"]
            if coproduct != "User Specification":
                coproduct_mapping = {key: coproduct for key in coproduct_mapping}
            final_process_mapping = data["final_process"]
            overall_lci = generate_final_lci(
                lci_mapping, coproduct_mapping, final_process_mapping
            )
            overall_lci = quick_sensitivity(overall_lci, renew_elec, rng)
            lca_res = postprocess(calculate_lca(overall_lci, False))
            lca_res["FileName"] = case_name
            df = pd.concat([df, lca_res], ignore_index=True)
    # elif changed_id in ["reset-button", "upload-data"]:
    #     existing_cases = None

    sensitivity_data = {
        "lci_data": lci_data_sensitivity,
        "pd": df.to_json(date_format="iso", orient="split"),
    }
    return json.dumps(sensitivity_data)
    # , existing_cases


@callback(
    Output("manual-sensitivity-figs", "children"),
    Input("simple-sensitivity-results", "data"),
    Input("tabs", "active_tab"),
    # Input("coproduct-handling", "value"),
    # State("results", "data"),
)
def manual_sensitivity_analysis(
    quick_sens_data,
    tab,
    # base_case_data,
    # quick_sens_data,
):
    """
    Manual sensitivity analysis
    """
    sensitivity_data = json.loads(quick_sens_data)
    df = pd.read_json(sensitivity_data["pd"], orient="split")
    if len(df) == 0:
        return []
    else:
        # df = pd.DataFrame()
        # ctx = dash.callback_context
        # changed_id = ctx.triggered[0]["prop_id"].split(".")[0]

        # if changed_id in ["perform-sensitivity-analysis"]:
        #     data = json.loads(base_case_data)
        #     sensitivity_data = json.loads(quick_sens_data)
        #     lci_data_sensitivity = sensitivity_data["lci_data"]
        #     for case_name in sensitivity_data["lci_data"]:
        #         lci_data = lci_data_sensitivity[case_name]
        #         lci_mapping = {
        #             key: pd.read_json(value, orient="split")
        #             for key, value in lci_data.items()
        #         }
        #         coproduct_mapping = data["coproduct"]
        #         final_process_mapping = data["final_process"]
        #         overall_lci = generate_final_lci(
        #             lci_mapping, coproduct_mapping, final_process_mapping
        #         )
        #         lca_res = postprocess(calculate_lca(overall_lci, False))
        #         lca_res["FileName"] = case_name
        #         df = pd.concat([df, lca_res], ignore_index=True)

        unit_sup = " CO2e" if tab == "GHG" else ""
        if tab == "Water":
            tab = "Water consumption: gallons"
            tab_summary = "Water Consumption"
        elif tab in [
            "Total energy",
            # "Fossil fuels",
            "Coal",
            "Natural gas",
            "Petroleum",
        ]:
            tab_summary = tab + " consumption"
            tab = tab + ", Btu"
        elif tab == "Fossil energy":
            tab_summary = tab + " consumption"
            tab = "Fossil fuels, Btu"
        else:
            tab_summary = tab + " Emission"

        # if len(df) > 0:
        df = df.loc[df[tab + "_Sum"] != 0]
        main_product_category = df.loc[df["Type"] == "Main Product", "Category"].values[
            0
        ]
        main_product_target_unit = display_units[main_product_category]

        # fig1_manual_sensitivity = px.bar(
        #     df,
        #     x="FileName",
        #     y=tab + "_Sum",
        #     color="Category",
        #     custom_data=["Category"],
        # )
        fig1_manual_sensitivity = px.histogram(
            df,
            x="FileName",
            y=tab + "_Sum",
            color="Category",
            # custom_data=["Category"],
        )
        fig1_manual_sensitivity.update_layout(barmode="relative")
        fig1_manual_sensitivity.update_traces(marker_line_width=0)
        fig1_manual_sensitivity.update_layout(
            title={
                "text": "Breakdown of " + tab_summary,
                "y": 0.95,
                "x": 0.5,
                "xanchor": "center",
                "yanchor": "top",
            }
        )
        fig1_manual_sensitivity.update_xaxes(title="Cases")
        fig1_manual_sensitivity.update_yaxes(
            title=f"{tab_summary} ({metric_units[tab]}{unit_sup}/{main_product_target_unit})"
        )

        df2 = df.groupby("FileName", as_index=False)[tab + "_Sum"].sum()
        df2["Relative"] = df2[tab + "_Sum"] / df2.loc[0, tab + "_Sum"]
        df2["Change"] = df2["Relative"] - 1
        # df2["Text"] = df2["Change"].apply(
        #     lambda t: "{:.1%} increase from the Base Case".format(abs(t))
        #     if t >= 0
        #     else "{:.1%} reduction from the Base Case".format(abs(t))
        # )
        df2["Text"] = df2[[tab + "_Sum", "Change"]].apply(
            lambda t: f"{t[0]:.1f} ({t[1]:+.1%})", axis=1
        )
        df2.loc[0, "Text"] = f"{df2.loc[0, tab+'_Sum']:.1f}"
        fig2_manual_sensitivity = px.bar(
            df2,
            x="FileName",
            # y="Relative",
            y=tab + "_Sum",
            text="Text",
            category_orders={"FileName": df["FileName"].values},
            labels=dict(FileName="Cases"),
            # text=(df2[tab + "_Relative"] - 1).tolist()
            # color="Category",
            # custom_data=["Category"],
        )
        fig2_manual_sensitivity.update_traces(textposition="outside")
        fig2_manual_sensitivity.update_layout(
            uniformtext_minsize=14, uniformtext_mode="show"
        )
        fig2_manual_sensitivity.update_layout(
            title={
                "text": f"Change in {tab_summary} Relative to the Base Case",
                "y": 0.95,
                "x": 0.5,
                "xanchor": "center",
                "yanchor": "top",
            }
        )
        fig2_manual_sensitivity.update_yaxes(
            title=f"{tab_summary} ({metric_units[tab]}{unit_sup}/{main_product_target_unit})"
        )
        return [
            dbc.Row(
                dbc.Col(
                    dcc.Graph(
                        config={
                            "toImageButtonOptions": {
                                "filename": "Sensitivity-fig3",
                                "scale": 2,
                            }
                        },
                        figure=fig1_manual_sensitivity,
                    )
                )
            ),
            dbc.Row(
                dbc.Col(
                    dcc.Graph(
                        config={
                            "toImageButtonOptions": {
                                "filename": "Sensitivity-fig4",
                                "scale": 2,
                            }
                        },
                        figure=fig2_manual_sensitivity,
                    )
                )
            ),
        ]


@callback(
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
            lca_res = postprocess(calculate_lca(overall_lci, False))
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


@callback(
    Output("graph1-sensitivity", "figure"),
    Output("graph2-sensitivity", "figure"),
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
    elif tab in [
        "Total energy",
        # "Fossil fuels",
        "Coal",
        "Natural gas",
        "Petroleum",
    ]:
        tab_summary = tab + " consumption"
        tab = tab + ", Btu"
    elif tab == "Fossil energy":
        tab_summary = tab + " consumption"
        tab = "Fossil fuels, Btu"
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
        df = df.loc[df[tab + "_Sum"] != 0]
        main_product_category = df.loc[df["Type"] == "Main Product", "Category"].values[
            0
        ]
        main_product_target_unit = display_units[main_product_category]

        fig1_sensitivity = px.histogram(
            df,
            x="FileName",
            y=tab + "_Sum",
            color="Category",
            # custom_data=["Category"],
        )
        fig1_sensitivity.update_layout(barmode="relative")
        fig1_sensitivity.update_traces(marker_line_width=0)
        fig1_sensitivity.update_layout(
            title={
                "text": "Breakdown of " + tab_summary,
                "y": 0.95,
                "x": 0.5,
                "xanchor": "center",
                "yanchor": "top",
            }
        )
        fig1_sensitivity.update_xaxes(title="Cases")
        fig1_sensitivity.update_yaxes(
            title=f"{tab_summary} ({metric_units[tab]}{unit_sup}/{main_product_target_unit})"
        )

        df2 = df.groupby("FileName", as_index=False)[tab + "_Sum"].sum()
        df2["Relative"] = df2[tab + "_Sum"] / df2.loc[0, tab + "_Sum"]
        df2["Change"] = df2["Relative"] - 1
        # df2["Text"] = df2["Change"].apply(
        #     lambda t: f"{abs(t):.1%} increase from the Base Case"
        #     if t >= 0
        #     else f"{abs(t):.1%} reduction from the Base Case"
        # )
        df2["Text"] = df2[[tab + "_Sum", "Change"]].apply(
            lambda t: f"{t[0]:.1f} ({t[1]:+.1%})", axis=1
        )
        df2.loc[0, "Text"] = f"Base Case: {df2.loc[0, tab+'_Sum']:.1f}"
        fig2_sensitivity = px.bar(
            df2,
            x="FileName",
            # y="Relative",
            y=tab + "_Sum",
            text="Text",
            category_orders={"FileName": df["FileName"].values},
            labels=dict(FileName="Cases"),
            # text=(df2[tab + "_Relative"] - 1).tolist()
            # color="Category",
            # custom_data=["Category"],
        )
        fig2_sensitivity.update_traces(textposition="outside")
        fig2_sensitivity.update_layout(uniformtext_minsize=14, uniformtext_mode="show")
        fig2_sensitivity.update_layout(
            title={
                "text": f"Change in {tab_summary} Relative to the Base Case",
                "y": 0.95,
                "x": 0.5,
                "xanchor": "center",
                "yanchor": "top",
            }
        )
        fig2_sensitivity.update_yaxes(
            title=f"{tab_summary} ({metric_units[tab]}{unit_sup}/{main_product_target_unit})"
        )

        return (
            fig1_sensitivity,
            fig2_sensitivity,
            sensitivity_error_status,
            children,
        )
    return go.Figure(), go.Figure(), False, ""
