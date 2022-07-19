import base64
import io

import numpy as np
import pandas as pd
import plotly.graph_objs as go

from calc import read_data
from utils import display_units, energy, mass, metric_units, properties, unit_conversion


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


def elec_sensitivity(dff, renew_elec_share):
    """
    Perform sensitivity analysis for renewable electricity share
    """
    if renew_elec_share == 0:
        return dff

    df = dff.copy()
    elec_df = df.loc[(df["Type"] == "Input") & (df["Resource"] == "electricity")]
    elec_to_append = elec_df.copy()
    elec_to_append["End Use"] = "renewable"
    elec_to_append["Amount"] = elec_to_append["Amount"] * renew_elec_share
    # df.loc[(df['Type']=='Input')&(df['Resource']='electricity')]
    df.loc[
        (df["Type"] == "Input") & (df["Resource"] == "electricity"), "Amount"
    ] = df.loc[
        (df["Type"] == "Input") & (df["Resource"] == "electricity"), "Amount"
    ] * (
        1 - renew_elec_share
    )

    return pd.concat([df, elec_to_append], ignore_index=True)


def rng_sensitivity(dff, rng_share):
    """
    Perform sensitivity analysis for RNG share
    """
    if rng_share == 0:
        return dff

    df = dff.copy()
    ng_df = df.loc[(df["Type"] == "Input") & (df["Resource"] == "natural gas")]
    ng_to_append = ng_df.copy()
    ng_to_append["Resource"] = "renewable natural gas"
    ng_to_append["Amount"] = ng_to_append["Amount"] * rng_share
    # df.loc[(df['Type']=='Input')&(df['Resource']='electricity')]
    df.loc[
        (df["Type"] == "Input") & (df["Resource"] == "natural gas"), "Amount"
    ] = df.loc[
        (df["Type"] == "Input") & (df["Resource"] == "natural gas"), "Amount"
    ] * (
        1 - rng_share
    )

    return pd.concat([df, ng_to_append], ignore_index=True)


def quick_sensitivity(dff, renew_elec_share, rng_share):
    """
    All-in-one funciton for quick sensitivity analysis
    """
    df = dff.copy()
    df = elec_sensitivity(df, renew_elec_share)
    df = rng_sensitivity(df, rng_share)
    return df


def make_waterfall_plot(res, metric="GHG", n=4):
    """
    Generate the waterfall plot
    """

    df = res.copy()
    col = metric + "_Sum"

    df.loc[
        (df[col] < 0) & (~df["Resource"].str.lower().str.contains("sequestration")),
        "Resource",
    ] = df.loc[
        (df[col] < 0) & (~df["Resource"].str.lower().str.contains("sequestration")),
        "Resource",
    ].apply(
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


def generate_abatement_cost(
    fmin,
    fmax,
    funit,
    bmin,
    bmax,
    bunit,
    fossil_metric,
    biofuel_metric,
    main_product_category,
    main_incumbent_resource,
    main_product_resource,
    n=5,
):
    """
    Calculate the abatement cost
    """
    if (
        (fmin is not None)
        and (fmax is not None)
        and (funit is not None)
        and (bmin is not None)
        and (bmax is not None)
        and (bunit is not None)
    ):
        funit = funit[2:]  # remove the leading "$/"
        bunit = bunit[2:]  # remove the leading "$/"
        df_conversion = pd.DataFrame(
            {
                "Input Amount": [1, 1],
                "Unit": [funit, bunit],
                "Primary Unit": [display_units[main_product_category]] * 2,
                "Resource": [main_incumbent_resource, main_product_resource],
            }
        )
        df_conversion = pd.merge(
            df_conversion, properties, left_on="Resource", right_index=True, how="left"
        )
        f_conversion_ratio, b_conversion_ratio = df_conversion.apply(
            unit_conversion, axis=1
        ).values

        fossil_cost_provided = np.linspace(fmin, fmax, n)
        fossil_cost = fossil_cost_provided / f_conversion_ratio  # price in $/MJ
        biofuel_cost_provided = np.linspace(bmin, bmax, n)
        biofuel_cost = biofuel_cost_provided / b_conversion_ratio  # price in $/MJ

        abatement_cost = (fossil_cost - biofuel_cost.reshape(-1, 1)) / (
            biofuel_metric - fossil_metric
        )
        df = pd.DataFrame(
            abatement_cost, index=biofuel_cost_provided, columns=fossil_cost_provided
        )
        cols = df.columns
        df = df.reset_index(drop=False).rename(columns={"index": "biofuel_cost"})
        df = pd.melt(
            df,
            id_vars=["biofuel_cost"],
            value_vars=cols,
            var_name="fossil_cost",
            value_name="abatement_cost",
        )
        # fig = px.line(df, x="biofuel_cost", y="abatement_cost", color="fossil_cost")
        # return fig
    else:
        # fig = go.Figure()
        # fig.update_layout(
        #     title="Please provide price ranges to plot the abatement cost"
        # )
        df = pd.DataFrame()
    return df


def generate_carbon_credit(
    cprice, cunit, main_product_category, fossil_ghg, biofuel_ghg
):
    """
    Calcualte carbon credits
    """
    cunit = cunit[2:]
    cprice = (
        cprice * mass.loc[cunit, metric_units["GHG"]]
    )  # Calculate carbon price in $/g

    fuel_credit = cprice * (
        fossil_ghg - biofuel_ghg
    )  # calculate carbon credit, the results are in $/MJ for fuels

    if main_product_category in ["Process fuel"]:
        fuel_credit = (
            fuel_credit * energy.loc["MJ", "GGE"]
        )  # calculate carbon credit in $/GGE for fuels

    return fuel_credit


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
