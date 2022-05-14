# TODO: check upper or lower cases for unit, input, etc.  Decision: keep using lower case and change the case before visualization.
# TODO: use end_use_dict
# TODO: check the functional unit
import pandas as pd

lookup_table = pd.read_csv("lookup_table.csv", index_col=0, header=0)
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
    "Fuel": "mmbtu",
    "Electricity": "mmbtu",
    "Chemicals and catalysts": "kg",
}

units = pd.read_excel(
    "Lookup table_prototyping.xlsx", sheet_name="Units", header=0, index_col=0
).squeeze("columns")
units.index = units.index.str.lower()

mass = pd.read_excel(
    "Lookup table_prototyping.xlsx", sheet_name="Mass", header=0, index_col=0
)
mass.columns = mass.columns.str.lower()
mass.index = mass.index.str.lower()

volume = pd.read_excel(
    "Lookup table_prototyping.xlsx", sheet_name="Volume", header=0, index_col=0
)
volume.columns = volume.columns.str.lower()
volume.index = volume.index.str.lower()

energy = pd.read_excel(
    "Lookup table_prototyping.xlsx", sheet_name="Energy", header=0, index_col=0
)
energy.columns = energy.columns.str.lower()
energy.index = energy.index.str.lower()

length = pd.read_excel(
    "Lookup table_prototyping.xlsx", sheet_name="Length", header=0, index_col=0
)
length.columns = length.columns.str.lower()
length.index = length.index.str.lower()

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
    return ene * energy.loc["mj", input_unit] / lhv


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
                return kg_amount * lhv * energy.loc[output_unit, "mj"]
        elif output_unit in energy_units:  # output is energy and input is mass
            return (
                mass_to_energy(amount, input_unit, lhv) * energy.loc[output_unit, "mj"]
            )
        else:  # output is mass and input is energy
            return energy_to_mass(amount, input_unit, lhv) * mass.loc[output_unit, "kg"]
    elif input_unit in mass_units:  # Both input and output are mass unit.
        return amount * mass.loc[output_unit, input_unit]
    elif input_unit in energy_units:  # Both input and output are energy unit.
        return amount * energy.loc[output_unit, input_unit]
    else:  # Both input and output are volume unit.
        return amount * volume.loc[output_unit, input_unit]


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
                "Unit": ["mmbtu"] * 2,
            }
        )

        to_append.append(df_trans)

    return pd.concat(to_append)


#
#
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
    lower_case_cols = ["Resource", "End Use", "Unit"]

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


def calculate_lca(df_lci):
    """
    Calculate LCA results from LCI

    Parameters:
        df_lci: LCI table
    """
    # lookup_table.index = lookup_table.index.str.lower()
    df_lci["ID"] = df_lci["ID"].str.lower()
    res = pd.merge(df_lci, lookup_table, left_on="ID", right_index=True, how="left")
    res["Primary Unit"] = res["Primary Unit"].str.lower()
    res["Unit"] = res["Unit"].str.lower()
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
    res = res[res["Type"] != "Main Product"]

    for metric in metrics:
        res[metric + "_Sum"] = res["Amount"] * res[metric]
        res[metric + "_Sum"] = (
            res[metric + "_Sum"] / 1055.055853
        )  # Convert the functional unit from mmBtu to MJ

    return res


# def generate_feedstock_lci(
#     lci, end_uses, to_concat=pd.DataFrame(), process_name="Feedstock Harvest"
# ):
#     """
#     Generate the formatted harvest LCI dataframe from the input.
#     Parameter:
#         harvest: the dataframe containing the input harvest LCI data.
#         end_uses: a dictionary indicating the end uses of the fuels.
#         to_concat: a dataframe containing the feedstock (main input) and main output of the process.
#     """
#     for fuel in ["Diesel", "Electricity", "Natural Gas"]:
#         lci[fuel] = lci["Energy Consump (mBtu/dry ton)"] * lci[fuel + " %"]
#     df = pd.melt(
#         lci,
#         value_vars=["Diesel", "Electricity", "Natural Gas"],
#         value_name="Amount",
#         var_name="Resource",
#         ignore_index=False,
#     ).reset_index()
#     df["Amount"] = df["Amount"] * 1000  # Convert mBtu to Btu
#     df["Unit"] = "Btu"
#     df["End Use"] = df["Resource"].map(end_uses)
#     # df['Category'] = ''
#     df["Category"] = df["Resource"].str.lower().map(category)
#     df["Process"] = process_name
#     df["Type"] = "Input"
#
#     df = pd.concat([df, to_concat], ignore_index=True)
#
#     return df
#
#
# fuel_economy = pd.read_excel(
#     "Lookup table_prototyping.xlsx",
#     sheet_name="Transportation",
#     skipfooter=34,
#     index_col=0,
# ).dropna(axis=1, how="all")
# fuel_economy = fuel_economy[["Heavy Heavy-Duty Truck"]]
#
#
# def generate_transport_lci(
#     transport, to_concat=pd.DataFrame(), process="Feedstock transport"
# ):
#     to_append = []
#     for index, row in transport.iterrows():
#         resource = "Corn Stover_1 leg" if "#1" in index else "Corn Stover_2 leg"
#         unit = "mile"  # Assuming transport is a series, i.e., there is only one row for transportation
#         distance = row.at["Distance (mi)"]
#         payload = row.at["Payload (wet tons)"] * (1 - row.at["MC"])
#         btu_per_ton_mile = fuel_economy / payload
#
#         to_desti_fuel = (
#             btu_per_ton_mile.at[
#                 "Trip from Product Origin to Destination", "Heavy Heavy-Duty Truck"
#             ]
#             * distance
#             / 1000000
#         )  # MMBtu per ton
#         to_origin_fuel = (
#             btu_per_ton_mile.at[
#                 "Trip from Product Destination Back to Origin", "Heavy Heavy-Duty Truck"
#             ]
#             * distance
#             / 1000000
#         )  # MMBtu per ton
#         df_trans = pd.DataFrame(
#             {
#                 "Type": ["Input"] * 2,
#                 "Process": [process] * 2,
#                 "Category": ["Transportation"] * 2,
#                 "Resource": ["diesel"] * 2,
#                 "End Use": ["loaded", "empty"],
#                 "Amount": [to_desti_fuel, to_origin_fuel],
#                 "Unit": ["mmbtu"] * 2,
#             }
#         )
#
#         to_append.append(df_trans)
#
#     to_append.append(to_concat)
#
#     return pd.concat(to_append)
