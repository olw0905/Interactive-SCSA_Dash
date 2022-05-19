# TODO: check upper or lower cases for unit, input, etc.  Decision: keep using lower case and change the case before visualization.
# TODO: use end_use_dict
# TODO: check the functional unit
from json.tool import main
import pandas as pd

# lookup_table = pd.read_csv("lookup_table.csv", index_col=0, header=0)
# category = pd.read_csv("category.csv", index_col=0, header=0).squeeze()

metrics = [
    "Total energy, Btu",
    "Fossil fuels, Btu",
    "Coal, Btu",
    "Natural gas, Btu",
    "Petroleum, Btu",
    "Water consumption: gallons",
    "VOC",
    "CO",
    "NOx",
    "PM10",
    "PM2.5",
    "SOx",
    "BC",
    "OC",
    "CH4",
    "N2O",
    "CO2",
    "Biogenic CO2",
    "CO2 (w/ C in VOC & CO)",
    "GHG",
]

combination_basis = {  # The basis for combinaning multiple "main products"
    "Biomass": "kg",
    "Fuel": "mmBTU",
    "Electricity": "mmBTU",
    "Chemicals and catalysts": "kg",
}

primary_units = {
    "Fuel": "mmBTU",
    "Biomass": "ton",
    "Electricity": "mmBTU",
    "Chemicals and catalysts": "g",
    "Water": "gal",
    "Transportation": "mmBTU",  # For transportation, diesel is used
}  # The functional unit for calculation

display_units = {
    "Fuel": "MJ",  # gram, gal, or BTU per MJ
    "Biomass": "ton",  # gram, gal, or BTU per ton
    "Electricity": "MJ",  # gram, gal, or BTU per MJ
    "Chemicals and catalysts": "g",  # gram, gal, or BTU per g
    # "Water": "gal",
}  # The units for the final results

units = pd.read_excel(
    "Lookup table_prototyping.xlsx", sheet_name="Units", header=0, index_col=0
).squeeze("columns")
# units.index = units.index.str.lower()

mass = pd.read_excel(
    "Lookup table_prototyping.xlsx", sheet_name="Mass", header=0, index_col=0
)
# mass.columns = mass.columns.str.lower()
# mass.index = mass.index.str.lower()

volume = pd.read_excel(
    "Lookup table_prototyping.xlsx", sheet_name="Volume", header=0, index_col=0
)
# volume.columns = volume.columns.str.lower()
# volume.index = volume.index.str.lower()

energy = pd.read_excel(
    "Lookup table_prototyping.xlsx", sheet_name="Energy", header=0, index_col=0
)
# energy.columns = energy.columns.str.lower()
# energy.index = energy.index.str.lower()

length = pd.read_excel(
    "Lookup table_prototyping.xlsx", sheet_name="Length", header=0, index_col=0
)
# length.columns = length.columns.str.lower()
# length.index = length.index.str.lower()

mass_units = mass.columns.to_list()
volume_units = volume.columns.to_list()
energy_units = energy.columns.to_list()
length_units = length.columns.to_list()

properties = pd.read_excel(
    "Lookup table_prototyping.xlsx", sheet_name="Fuel specs", skiprows=1, index_col=0
)
properties.index = properties.index.str.lower()


co2_carbon = 12 / 44
co_carbon = 12 / 28
voc_carbon = 0.85

co2_gwp = 1
ch4_gwp = 30
n2o_gwp = 265


def volume_to_mass(vol, input_unit, density):
    """
    Convert volume to kg
    """
    return vol * volume.loc["m3", input_unit] * density


def mass_to_energy(mas, input_unit, lhv):
    """
    Convert mass to MJ
    """
    return mas * mass.loc["kg", input_unit] * lhv


def energy_to_mass(ene, input_unit, lhv):
    """
    Convert energy to kg
    """
    return ene * energy.loc["MJ", input_unit] / lhv


def unit_conversion(series):
    "Perform unit operation for each LCI data entry"
    input_unit = series["Unit"]
    amount = series["Input Amount"]
    density = series["Density"]
    lhv = series["LHV"]
    output_unit = series["Primary Unit"]

    if units[input_unit] != units[output_unit]:
        if (
            output_unit in volume_units
        ):  # Ouput is vlume, them input must be mass, because only water has output unit of volume. Modified from origin
            m3_amount = amount * mass.loc["kg", input_unit] / density
            return m3_amount * volume.loc[output_unit, "m3"]
        elif input_unit in volume_units:  # Input unit is volume
            kg_amount = volume_to_mass(amount, input_unit, density)  # Amount in kg
            if (
                output_unit in mass_units
            ):  # Input unit is volume and output unit is mass
                return kg_amount * mass.loc[output_unit, "kg"]
            else:  # Input unit is volume and output unit is energy
                return kg_amount * lhv * energy.loc[output_unit, "MJ"]
        elif output_unit in energy_units:  # output is energy and input is mass
            return (
                mass_to_energy(amount, input_unit, lhv) * energy.loc[output_unit, "MJ"]
            )
        else:  # output is mass and input is energy
            return energy_to_mass(amount, input_unit, lhv) * mass.loc[output_unit, "kg"]
    elif input_unit in mass_units:  # Both input and output are mass unit.
        return amount * mass.loc[output_unit, input_unit]
    elif input_unit in energy_units:  # Both input and output are energy unit.
        return amount * energy.loc[output_unit, input_unit]
    else:  # Both input and output are volume unit.
        return amount * volume.loc[output_unit, input_unit]


# Process emission factors read from the data extraction file
production_emissions = pd.read_excel(
    "Lookup table_prototyping.xlsx",
    sheet_name="Production",
    index_col=0,
    skipfooter=2,
)
production_emissions = production_emissions.dropna()
production_emissions.loc["Biogenic CO2"] = 0
production_emissions.index = production_emissions.index.str.strip()
production_emissions = production_emissions.drop(["Category", "Primary Unit"])

chemicals_emissions = pd.read_excel(
    "Lookup table_prototyping.xlsx",
    sheet_name="Chemicals",
    index_col=0,
    skipfooter=2,
)
chemicals_emissions = chemicals_emissions.dropna()
chemicals_emissions.loc["Biogenic CO2"] = 0
chemicals_emissions.index = chemicals_emissions.index.str.strip()
chemicals_emissions = chemicals_emissions.drop(["Category", "Primary Unit"])

feedstock_emissions = pd.read_excel(
    "Lookup table_prototyping.xlsx", sheet_name="Feedstock", index_col=0, skipfooter=2
)
feedstock_emissions = feedstock_emissions.dropna()
feedstock_emissions.loc["Biogenic CO2"] = 0
feedstock_emissions.index = feedstock_emissions.index.str.strip()
feedstock_emissions = feedstock_emissions.drop(["Category", "Primary Unit"])

combined_ci_table = pd.concat(
    [production_emissions, chemicals_emissions, feedstock_emissions], axis=1
)
combined_ci_table.columns = combined_ci_table.columns.str.lower()

end_use = pd.read_excel(
    "Lookup table_prototyping.xlsx",
    sheet_name="End use test",
    index_col=0,
    header=[0, 1],
    skipfooter=2,
)
end_use = end_use.drop("Primary Unit").fillna(0)
end_use.columns = end_use.columns.set_levels(
    [end_use.columns.levels[0].str.lower(), end_use.columns.levels[1].str.lower()]
)


def emission_factor(ser):
    """
    Calculate the emission factor for each entry

    Parameter:
        ser: a series (entry) in the overall LCI dataframe
    """

    zero_emissions = pd.Series(
        0, index=combined_ci_table.index
    )  # Create a Series for zero emissions

    if (
        "Input" in ser["Type"]
    ):  # For inputs, both production and end use emissions should be included
        if ser["Resource"] == "electricity":
            # if pd.isnull(ser["End Use"]):
            if ser["End Use"] == "":
                return combined_ci_table[
                    "electricity_u.s. mix"
                ]  # If not generation mix is not specified, use national average
            else:
                return combined_ci_table[ser["Resource"] + "_" + ser["End Use"]]
        # elif pd.isnull(ser["End Use"]):
        elif ser["End Use"] == "":
            return combined_ci_table[ser["Resource"]]
        else:
            return combined_ci_table[ser["Resource"]].add(
                end_use[ser["Resource"], ser["End Use"]], fill_value=0
            )

    elif (
        "Co-product" in ser["Type"]
    ):  # For co-products, the difference between end use emissions for the product and incumbent should be accounted for
        if ser["Incumbent Resource"] == "electricity":
            # if pd.isnull(ser["End Use"]):
            if ser["End Use"] == "":
                return combined_ci_table[
                    "electricity_u.s. mix"
                ]  # If not generation mix is not specified, use national average
            else:
                return combined_ci_table[
                    ser["Incumbent Resource"] + "_" + ser["Incumbent End Use"]
                ]
        else:
            incumbent_emission = (
                combined_ci_table[ser["Incumbent Resource"]]
                # if pd.isnull(ser["Incumbent End Use"])
                if ser["Incumbent End Use"] == ""
                else combined_ci_table[ser["Incumbent Resource"]].add(
                    end_use[ser["Incumbent Resource"], ser["Incumbent End Use"]],
                    fill_value=0,
                )
            )
            # if pd.isnull(ser["End Use"]):
            if ser["End Use"] == "":
                return incumbent_emission
            else:
                return incumbent_emission.sub(
                    end_use[ser["Resource"], ser["End Use"]], fill_value=0
                )
    else:  # Main product
        # if pd.isnull(ser["End Use"]):
        if ser["End Use"] == "":
            return zero_emissions
        else:
            return zero_emissions.add(
                end_use[ser["Resource"], ser["End Use"]], fill_value=0
            )


def convert_transport_lci(df):
    """
    df: the original LCI file that contains transportation material, distance, and moisture
    """

    xl = pd.ExcelFile("Lookup table_prototyping.xlsx")
    nrows = xl.book["Transportation"].max_row

    fuel_economy = xl.parse(
        sheet_name="Transportation", skipfooter=34, index_col=0
    ).dropna(axis=1, how="all")

    payload = xl.parse(
        sheet_name="Transportation", skiprows=4, skipfooter=28, index_col=0
    ).dropna(axis=1, how="all")

    dff = df.copy()
    dff["Resource"] = dff["Resource"].str.lower()
    transport = dff[dff["Category"] == "Transportation"]
    dff = dff[dff["Category"] != "Transportation"]
    to_append = [dff]

    hhdt_payload = payload.loc["Heavy Heavy-Duty Truck"].dropna()
    t1 = fuel_economy["Heavy Heavy-Duty Truck"].to_frame()
    t2 = hhdt_payload.to_frame()
    btu_per_ton_mile = t1.dot((1 / t2).T)
    btu_per_ton_mile.columns = btu_per_ton_mile.columns.str.lower()

    for index, row in transport.iterrows():
        resource = row.at[
            "Resource"
        ]  # Assuming transport is a series, i.e., there is only one row for transportation
        unit = row.at["Unit"]
        distance = row.at["Amount"] * length.loc["mi", unit]

        to_desti_fuel = (
            btu_per_ton_mile.at["Trip from Product Origin to Destination", resource]
            * distance
            / 1000000
        )  # MMBtu per dry ton
        to_origin_fuel = (
            btu_per_ton_mile.at[
                "Trip from Product Destination Back to Origin", resource
            ]
            * distance
            / 1000000
        )  # MMBtu per dry ton
        # The row of transported resource and its amount
        transport_entry = dff[
            (dff["Type"].str.contains("Input")) & (dff["Resource"] == resource)
        ].copy()
        transport_entry["Primary Unit"] = "ton"  # The unit of paylod is always ton
        transport_entry = transport_entry.rename(columns={"Amount": "Input Amount"})
        transport_entry = pd.merge(
            transport_entry,
            properties,
            left_on="Resource",
            right_index=True,
            how="left",
        )
        transport_entry["transport_amount_in_ton"] = transport_entry.apply(
            unit_conversion, axis=1
        )
        transport_amount = transport_entry["transport_amount_in_ton"].sum()

        df_trans = pd.DataFrame(
            {
                # "Type": ["Input"] * 2,
                # "Process": ["Feedstock production"] * 2,
                # "Category": ["Transportation"] * 2,
                "Type": [row.at["Type"]] * 2,
                "Process": [row.at["Process"]] * 2,
                "Category": [row.at["Category"]] * 2,
                "Resource": ["diesel"] * 2,
                "End Use": ["loaded", "empty"],
                "Amount": [
                    to_desti_fuel * transport_amount,
                    to_origin_fuel * transport_amount,
                ],
                "Unit": ["mmBTU"] * 2,
            }
        )

        to_append.append(df_trans)

    return pd.concat(to_append)


def step_processing(step_map, step_name):
    """
    Processing each step that have inputs that are ouputs from another step, convert these inputs.

    Parameters:
    df: the dataframe that contains the original LCI inputs from this step.
    step_map: the dictorinary that contains the mapping between each step and the final dataframe that are already converted.
    """

    dff = step_map[step_name].copy()
    # dff = pd.merge(dff, properties, left_on="Input", right_index=True, how="left")
    outputs_previous = dff[dff["Type"] == "Input from Another Process"].copy()
    dff = dff[dff["Type"] != "Input from Another Process"]
    to_concat = [dff]

    for ind, row in outputs_previous.iterrows():
        step = row.at["Previous Process"]
        step_df = step_map[step]
        row["Input Amount"] = row["Amount"]
        row["Primary Unit"] = step_df.loc[
            step_df["Type"] == "Main Product", "Unit"
        ].values[
            0
        ]  # There should only be one row of "main product" here

        conversion = unit_conversion(row)

        step_df = step_df[step_df["Type"].isin(["Input", "Co-product"])].copy()
        step_df["Amount"] = step_df["Amount"] * conversion

        to_concat.append(step_df)

    df_final = pd.concat(to_concat, ignore_index=True)
    step_map.update({step_name: df_final})

    return step_map


def used_other_process(df):
    """
    Return whether a process used inputs from another process
    """
    return (df["Type"].str.contains("Input from Another Process")).any()


def process(step_mapping, looped=False):
    """
    Process the LCI data by converting inputs from another process to its corresponding LCI data.
    """
    for key, value in step_mapping.items():
        if used_other_process(value):
            out = value[value["Type"] == "Input from Another Process"]
            other_processes = out["Previous Process"].values
            to_process = True
            for other_proc in other_processes:
                if used_other_process(step_mapping[other_proc]):
                    to_process = False
                    break
            if to_process:
                step_mapping = step_processing(step_mapping, key)
                step_mapping = process(step_mapping)
            else:
                return "error"
        else:
            pass
    return step_mapping


def format_input(dff):
    """
    Formatting LCI data:
        1. Convert relevant column to lower cases
        2. Convert wet weight to dry weight
        3. Convert transportation distance to fuel consumption
        4. Merge with the properties dataframe (add the LHV and density columns)
        5. Combining multiple entries of "main products"
        6. Normalize the LCI data: calculate the amount per unit main output

    Parameters:
        dff: Pandas DataFrame containing LCI data
    """

    df = dff.copy()  # Avoid chaning the original df

    # Step 1
    df["End Use"] = df["End Use"].fillna("")
    df["Incumbent Resource"] = df["Incumbent Resource"].fillna("")
    df["Incumbent End Use"] = df["Incumbent End Use"].fillna("")
    df["Always Use Displacement Method for Co-Product?"] = df[
        "Always Use Displacement Method for Co-Product?"
    ].fillna("No")

    lower_case_cols = [
        "Resource",
        "End Use",
        "Incumbent Resource",
        "Incumbent End Use",
        # "Unit",
    ]

    for col in lower_case_cols:
        df[col] = df[col].str.strip().str.lower()

    # Step 2
    df["Moisture"] = df["Moisture"].fillna(0)
    df.loc[df["Category"] != "Transportation", "Amount"] = df.loc[
        df["Category"] != "Transportation", "Amount"
    ] * (1 - df["Moisture"])
    df.loc[df["Category"] == "Transportation", "Amount"] = df.loc[
        df["Category"] == "Transportation", "Amount"
    ] / (1 - df["Moisture"])

    # df.loc[df['Category']!='Transportation', 'Amount'] = df.loc[df['Category']!='Transportation', 'Amount'] / df.loc[df['Type']=='Main Product', 'Amount'].sum()

    # Step 3
    df = convert_transport_lci(df)

    # Step 4
    df = pd.merge(df, properties, left_on="Resource", right_index=True, how="left")

    # Step 5
    main_products = df[df["Type"] == "Main Product"].copy()
    if len(main_products) > 1:
        main_products["Primary Unit"] = combination_basis[
            main_products["Category"].values[0]
        ]
        main_products = main_products.rename(columns={"Amount": "Input Amount"})
        main_products["Amount"] = main_products.apply(unit_conversion, axis=1)
        main_products["Amount"] = main_products["Amount"].sum()
        main_products["Unit"] = main_products["Primary Unit"]
        main_products = main_products.drop(["Input Amount", "Primary Unit"], axis=1)
        df = pd.concat(
            [df[df["Type"] != "Main Product"], main_products.iloc[:1]],
            ignore_index=True,
        )

    # Step 6
    main_product_amount = df.loc[
        df["Type"] == "Main Product", "Amount"
    ].sum()  # TODO: need to make sure the units are consistent
    df["Amount"] = df["Amount"] / main_product_amount

    return df


def calculate_lca(df_lci, include_incumbent=True):
    """
    Calculate LCA results from LCI

    Parameters:
        df_lci: LCI table
        include_incumbent: whether to include the incumbent resource in the result dataframe.
    """

    # df_lci["ID"] = df_lci["ID"].str.lower()
    # res = pd.merge(df_lci, lookup_table, left_on="ID", right_index=True, how="left")
    # res["Primary Unit"] = res["Primary Unit"].str.lower()

    if include_incumbent:
        # Separate out the incumbent resource that the main product is compared with
        incumbent_resource = (
            df_lci.loc[df_lci["Type"] == "Main Product", "Incumbent Resource"]
            # .fillna("")
            .values[0]
        )
        incumbent_end_use = (
            df_lci.loc[df_lci["Type"] == "Main Product", "Incumbent End Use"]
            # .fillna("")
            .values[0]
        )
        incumbent_category = df_lci.loc[
            df_lci["Type"] == "Main Product", "Category"
        ].values[0]

        main_product = df_lci.loc[df_lci["Type"] == "Main Product", "Resource"].values[
            0
        ]
        df_lci["Pathway"] = main_product + " (Modeled)"

        df_incumbent = pd.DataFrame(
            {
                "Pathway": [incumbent_resource + " (Incumbent)"],
                "Type": ["Input"],
                "Category": [incumbent_category],
                "Resource": [incumbent_resource],
                "Process": [incumbent_resource + " (Incumbent)"],
                "End Use": [incumbent_end_use],
                "Amount": [1],
                "Unit": [primary_units[incumbent_category]],
            }
        )
        df_lci = pd.concat([df_lci, df_incumbent])

    df_emission_factor = df_lci.apply(emission_factor, axis=1)
    res = pd.concat([df_lci, df_emission_factor], axis=1)
    # res["Primary Unit"] = res["Category"].map(primary_units).str.lower()
    res["Primary Unit"] = res["Category"].map(primary_units)

    # res["Unit"] = res["Unit"].str.lower()
    res["Resource"] = res["Resource"].str.lower()

    res["CO2 (w/ C in VOC & CO)"] = (
        res["CO2"]
        + res["CO"] * co_carbon / co2_carbon
        + res["VOC"] * voc_carbon / co2_carbon
    )
    res["GHG"] = (
        res["CO2 (w/ C in VOC & CO)"] * co2_gwp
        + res["CH4"] * ch4_gwp
        + res["N2O"] * n2o_gwp
    )

    # Do unit conversion before calculation
    res = res.rename(columns={"Amount": "Input Amount"})
    res["Amount"] = res.apply(unit_conversion, axis=1)
    res["Unit"] = res["Primary Unit"]
    res["Amount"] = (
        res["Amount"] / res.loc[res["Type"] == "Main Product", "Amount"].sum()
    )
    # res = res[res["Type"] != "Main Product"]
    main_product_category = res.loc[res["Type"] == "Main Product", "Category"].values[0]
    calculation_unit = primary_units[main_product_category]
    target_unit = display_units[main_product_category]

    for metric in metrics:
        res[metric + "_Sum"] = res["Amount"] * res[metric]

    if main_product_category in ["Fuel", "Electricity"]:
        for metric in metrics:
            res[metric + "_Sum"] = (
                res[metric + "_Sum"] / energy.loc[target_unit, calculation_unit]
            )  # Convert the functional unit from calculation unit to target unit

    return res
