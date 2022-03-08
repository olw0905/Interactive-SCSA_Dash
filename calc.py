import json
import pandas as pd
import numpy as np
from ibrutils import (
    format_input,
    process,
    unit_conversion,
    properties,
    calculate_lca,
    generate_feedstock_lci,
    generate_transport_lci,
)

# from lookup_table import category, end_use_dict

category = pd.read_csv("category.csv", index_col=0, header=0).squeeze()

with open("end_use.json") as json_file:
    end_use_dict = json.load(json_file)

def calc(lci_file):
    # lci_file = "Prototyping LCI - combined LCI file.xlsx"
    harvest = pd.read_excel(
        lci_file,
        sheet_name="Feedstock production",
        skiprows=2,
        nrows=2,
        index_col=0,
        na_values="--",
    )
    harvest = harvest.fillna(0)
    harvest.index.name = "Process"

# Make adjustment based on the loss factor
    harvest["Adjustment"] = 1 / (1 - harvest["Loss"])
    harvest["Adjustment"] = harvest["Adjustment"].iloc[::-1].cumprod()
    harvest["Energy Consump (mBtu/dry ton)"] = (
        harvest["Energy Consump (mBtu/dry ton)"] * harvest["Adjustment"]
    )

    transport1 = pd.read_excel(
        lci_file,
        sheet_name="Feedstock production",
        skiprows=6,
        nrows=1,
        index_col=0,
        na_values="--",
    )
    transport1 = transport1.fillna(0)

# Make adjustment based on the loss factor
    transport1["Adjustment"] = 1 / (1 - transport1["Loss"])
    transport1["Adjustment"] = transport1["Adjustment"].iloc[::-1].cumprod()
    transport1["Distance (mi)"] = transport1["Distance (mi)"] * transport1["Adjustment"]

    preprocessing = pd.read_excel(
        lci_file,
        sheet_name="Feedstock production",
        skiprows=9,
        nrows=4,
        index_col=0,
        na_values="--",
    )
    preprocessing = preprocessing.fillna(0)
    preprocessing.index.name = "Process"

# Make adjustment based on the loss factor
    preprocessing["Adjustment"] = 1 / (1 - preprocessing["Loss"])
    preprocessing["Adjustment"] = preprocessing["Adjustment"].iloc[::-1].cumprod()
    preprocessing["Energy Consump (mBtu/dry ton)"] = (
        preprocessing["Energy Consump (mBtu/dry ton)"] * preprocessing["Adjustment"]
    )

    transport2 = pd.read_excel(
        lci_file,
        sheet_name="Feedstock production",
        skiprows=15,
        nrows=1,
        index_col=0,
        na_values="--",
    )
    transport2 = transport2.fillna(0)

# Make adjustment based on the loss factor
    transport2["Adjustment"] = 1 / (1 - transport2["Loss"])
    transport2["Adjustment"] = transport2["Adjustment"].iloc[::-1].cumprod()
    transport2["Distance (mi)"] = transport2["Distance (mi)"] * transport2["Adjustment"]

    lci_harvest = generate_feedstock_lci(
        harvest,
        end_uses={
            "Diesel": "Farming Tractor",
            "Electricity": "U.S. Mix",
            "Natural Gas": "Stationary Reciprocating Engine",
        },
        to_concat=pd.DataFrame(
            {
                "Type": ["Input", "Output"],
                "Resource": ["Corn Stover_1 leg"] * 2,
                "Amount": [
                    1 * harvest["Adjustment"].max(),
                    1,
                ],  # Calculate the amount of the main input based on the overall loss factor.
                "Unit": ["ton"] * 2,
                "End Use": [""] * 2,
                "Category": ["", "Main product"],
                "Process": ["Feedstock Harvest", ""],
            }
        ),
    )

    lci_preprocessing = generate_feedstock_lci(
        preprocessing,
        end_uses={
            "Diesel": "Stationary Reciprocating Engine",
            "Electricity": "U.S. Mix",
            "Natural Gas": "Stationary Reciprocating Engine",
        },
        to_concat=pd.DataFrame(
            {
                "Type": ["Input", "Output"],
                "Category": ["Output from another step", "Main product"],
                "Resource": ["Corn Stover_1 leg"] * 2,
                "Amount": [1 * preprocessing["Adjustment"].max(), 1],
                "Unit": ["ton"] * 2,
                "End Use": ["Feedstock Transport1", ""],
                "Process": ["Feedstock Preprocessing", ""],
            }
        ),
        process_name="Feedstock Preprocessing",
    )

    lci_transport1 = generate_transport_lci(
        transport1,
        to_concat=pd.DataFrame(
            {
                "Type": ["Input", "Output"],
                "Category": ["Output from another step", "Main product"],
                "Process": ["", ""],
                "Resource": "Corn Stover_1 leg",
                "Amount": [1 * transport1["Adjustment"].max(), 1],
                "Unit": "ton",
                "End Use": ["Feedstock Harvest", ""],
            }
        ),
    )

    lci_transport2 = generate_transport_lci(
        transport2,
        to_concat=pd.DataFrame(
            {
                "Type": ["Input", "Output"],
                "Category": ["Output from another step", "Main product"],
                "Process": ["", ""],
                "Resource": "Corn Stover_2 leg",
                "Amount": [1 * transport2["Adjustment"].max(), 1],
                "Unit": "ton",
                "End Use": ["Feedstock Preprocessing", ""],
            }
        ),
    )

    fuel = pd.read_excel(
        lci_file,
        sheet_name="Feedstock production",
        skiprows=21,
        na_values=["-", "--"],
        index_col=0,
    )

# Process the LCI data
    fuel[["Burn Lignin", "Convert Lignin"]] = (
        fuel[["Burn Lignin", "Convert Lignin"]]
        / fuel.loc["Hydrocarbon Fuel", ["Burn Lignin", "Convert Lignin"]]
    )
    fuel["Unit"] = fuel["Unit"].str.lower()
    fuel["Unit"] = fuel["Unit"].str.replace("/hr", "")
    fuel["Unit"] = fuel["Unit"].map({"kw": "kwh"}).fillna(fuel["Unit"])
    fuel = fuel.reset_index().rename(columns={"index": "Resource"})

    fuel = fuel.dropna(subset="Resource")
    fuel["Resource"] = fuel["Resource"].str.lower()
    fuel.loc[
        fuel["Resource"].str.contains("both", regex=False, na=False), "Resource"
    ] = np.nan
    fuel.loc[
        fuel["Resource"].str.contains("train", regex=False, na=False), "Resource"
    ] = np.nan

    fuel["Resource"] = fuel["Resource"].fillna(method="pad")
    fuel = fuel.reset_index(drop=True)

# Process the "Convert Lignin Case"
    case = "Convert Lignin"
    conversion = fuel[["Resource", case, "Unit", "Product Train"]]
    products_end = conversion[conversion["Resource"].str.contains("resource")].index.values[
        0
    ]
    inputs_end = conversion[conversion["Resource"].str.contains("waste")].index.values[0]

# Read co-products
    conversion_coproducts = conversion.iloc[:products_end]
    conversion_coproducts = conversion_coproducts.dropna(
        subset=[case, "Unit", "Product Train"], how="all"
    )
    conversion_coproducts[case] = conversion_coproducts[case].fillna(0)
    conversion_coproducts[case] = conversion_coproducts[case] * -1
    conversion_coproducts = conversion_coproducts[
        conversion_coproducts["Resource"] != "hydrocarbon fuel"
    ]
    conversion_coproducts["Category"] = "Co-Product"

# Read resource consumption
    conversion_inputs = conversion.iloc[products_end + 1 : inputs_end]
    conversion_inputs = conversion_inputs.dropna(subset=["Product Train"])
    # conversion_inputs["Category"] = "Fuel Production"

# Generate the final LCI for calculation
    conversion_lci = pd.concat([conversion_coproducts, conversion_inputs])
    conversion_lci = conversion_lci.rename(columns={case: "Amount"})

    end_uses = end_use_dict
# end_uses = {
#     "diesel": "Industrial Boiler",
#     "electricity": "U.S. Mix",
#     "natural gas": "Utility/ Industrial Boiler (>100 mmBtu/hr input)",
#     "sodium carbonate": "Use",
#     "toluene": "Combustion",
#     "adipic acid": "Sequestration",
#     "betaketoadipate": "Sequestration",
# }
    conversion_lci["End Use"] = conversion_lci["Resource"].map(end_uses).fillna("")

    conversion_lci["Process"] = "Fuel Production"

    conversion_lci.loc[conversion_lci["Resource"].str.contains("biomass"), "Amount"] = (
        conversion_lci.loc[conversion_lci["Resource"].str.contains("biomass"), "Amount"]
        * 0.8
    )

    conversion_lci.loc[
        conversion_lci["Resource"].str.contains("sulfuric acid"), "Amount"
    ] = (
        conversion_lci.loc[
            conversion_lci["Resource"].str.contains("sulfuric acid"), "Amount"
        ]
        * 0.93
    )

    conversion_lci.loc[
        conversion_lci["Resource"].str.contains("biomass"), "Category"
    ] = "Output from another step"
    conversion_lci.loc[
        conversion_lci["Resource"].str.contains("biomass"), "End Use"
    ] = "feedstock transport2"

    lci_harvest = format_input(lci_harvest)

    lci_preprocessing = format_input(lci_preprocessing)

    lci_transport1 = format_input(lci_transport1)

    lci_transport2 = format_input(lci_transport2)

    lci_conversion = format_input(conversion_lci)

    step_mapping = {
        "feedstock harvest": lci_harvest,
        "feedstock transport1": lci_transport1,
        "feedstock preprocessing": lci_preprocessing,
        "feedstock transport2": lci_transport2,
        "conversion": lci_conversion,
    }  # NOTE: The keys in the map MUST be identical to the "End use" column which specifies the previous process
    lcis = process(step_mapping)

#     feedstock_lci = lcis["feedstock transport2"]
#     feedstock_lci = feedstock_lci[feedstock_lci["Type"] == "Input"].copy()
#     feedstock_lci["End Use"] = feedstock_lci["End Use"].fillna("")
#     feedstock_lci["ID"] = feedstock_lci.apply(
#         # lambda a: a['Input'] if (pd.isna(a['End Use']))|(a['Input'] == 'Electricity') else a['Input']+'_'+a['End Use'], axis=1
#         # lambda a: a['Input'] if pd.isna(a['End Use']) else a['Input']+'_'+a['End Use'], axis=1
#         lambda a: a["Resource"]
#         if a["End Use"] == ""
#         else a["Resource"] + "_" + a["End Use"],
#         axis=1,
#     )
# 
#     feedstock_res = calculate_lca(feedstock_lci)
#     print(feedstock_res["CO2_Sum"].sum())

    overall_lci = lcis["conversion"]
# overall_lci = overall_lci[overall_lci['Type']=='Input'].copy()
    overall_lci["End Use"] = overall_lci["End Use"].fillna("")
    overall_lci["ID"] = overall_lci.apply(
        # lambda a: a['Input'] if (pd.isna(a['End Use']))|(a['Input'] == 'Electricity') else a['Input']+'_'+a['End Use'], axis=1
        # lambda a: a['Input'] if pd.isna(a['End Use']) else a['Input']+'_'+a['End Use'], axis=1
        lambda a: a["Resource"]
        if a["End Use"] == ""
        else a["Resource"] + "_" + a["End Use"],
        axis=1,
    )
    res = calculate_lca(overall_lci)
#     test1 = res.loc[
#         (res["Process"].str.contains("Feedstock")),
#         ["Resource", "Amount", "Unit", "End Use", "CO2_Sum", "GHG_Sum"],
#     ]
#     print(test1["GHG_Sum"].sum())
# 
    res.loc[res['Category']!='Co-Product', 'Category'] = res.loc[res['Category']!='Co-Product', 'Resource'].map(category)
    res['Resource'] = res['Resource'].str.title()
    res['Resource'] = res['Resource'].str.replace('Wwt', 'WWT').str.replace('Fgd', 'FGD')

    return res