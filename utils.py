# TODO: check upper or lower cases for unit, input, etc.  Decision: keep using lower case and change the case before visualization.
# TODO: use end_use_dict
# TODO: check the functional unit
# from json.tool import main
import pandas as pd

# data_file = "Lookup table_prototyping.xlsx"
data_file = "Lookup table_prototyping_greet2022.xlsx"
files = {
    "biochem": [
        "static/Biochemical conversion via BDO.xlsm",
        "static/Biochemical conversion via Acids.xlsm",
    ],
    "sludge": [
        "static/Sludge HTL with NH3 removal.xlsm",
        "static/Sludge HTL without NH3 removal.xlsm",
    ],
    "cfp": "",
    "cap": [
        "static/Algae CAP via BDO.xlsm",
        "static/Algae CAP via acids.xlsm",
    ],
    "ahtl": "",
    "idl": "",
}

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
    "Urban VOC",
    "Urban CO",
    "Urban NOx",
    "Urban PM10",
    "Urban PM2.5",
    "Urban SOx",
    "Urban BC",
    "Urban OC",
]

metric_units = {
    "Total energy, Btu": "MJ",
    "Fossil fuels, Btu": "MJ",
    "Coal, Btu": "MJ",
    "Natural gas, Btu": "MJ",
    "Petroleum, Btu": "MJ",
    "Water consumption: gallons": "gallons",
    "VOC": "g",
    "CO": "g",
    "NOx": "g",
    "PM10": "g",
    "PM2.5": "g",
    "SOx": "g",
    "BC": "g",
    "OC": "g",
    "CH4": "g",
    "N2O": "g",
    "CO2": "g",
    "Biogenic CO2": "g",
    "CO2 (w/ C in VOC & CO)": "g",
    "GHG": "g",
    "Urban VOC": "g",
    "Urban CO": "g",
    "Urban NOx": "g",
    "Urban PM10": "g",
    "Urban PM2.5": "g",
    "Urban SOx": "g",
    "Urban BC": "g",
    "Urban OC": "g",
}

biorefinery_units = {  # The units used to show biorefinery-level results
    "Total energy, Btu": "MJ",
    "Fossil fuels, Btu": "MJ",
    "Coal, Btu": "MJ",
    "Natural gas, Btu": "MJ",
    "Petroleum, Btu": "MJ",
    "Water consumption: gallons": "gallons",
    "VOC": "kg",
    "CO": "kg",
    "NOx": "kg",
    "PM10": "kg",
    "PM2.5": "kg",
    "SOx": "kg",
    "BC": "kg",
    "OC": "kg",
    "CH4": "kg",
    "N2O": "kg",
    "CO2": "kg",
    "Biogenic CO2": "kg",
    "CO2 (w/ C in VOC & CO)": "kg",
    "GHG": "kg",
    "Urban VOC": "kg",
    "Urban CO": "kg",
    "Urban NOx": "kg",
    "Urban PM10": "kg",
    "Urban PM2.5": "kg",
    "Urban SOx": "kg",
    "Urban BC": "kg",
    "Urban OC": "kg",
}

abatement_cost_units = {
    "Total energy, Btu": "MJ",
    "Fossil fuels, Btu": "MJ",
    "Coal, Btu": "MJ",
    "Natural gas, Btu": "MJ",
    "Petroleum, Btu": "MJ",
    "Water consumption: gallons": "gallons",
    "VOC": "metric ton",
    "CO": "metric ton",
    "NOx": "metric ton",
    "PM10": "metric ton",
    "PM2.5": "metric ton",
    "SOx": "metric ton",
    "BC": "metric ton",
    "OC": "metric ton",
    "CH4": "metric ton",
    "N2O": "metric ton",
    "CO2": "metric ton",
    "Biogenic CO2": "metric ton",
    "CO2 (w/ C in VOC & CO)": "metric ton",
    "GHG": "metric ton",
    "Urban VOC": "metric ton",
    "Urban CO": "metric ton",
    "Urban NOx": "metric ton",
    "Urban PM10": "metric ton",
    "Urban PM2.5": "metric ton",
    "Urban SOx": "metric ton",
    "Urban BC": "metric ton",
    "Urban OC": "metric ton",
}

biorefinery_conversion = {  # The conversion used to calculate biorefinery-level results
    "Total energy, Btu": 1,
    "Fossil fuels, Btu": 1,
    "Coal, Btu": 1,
    "Natural gas, Btu": 1,
    "Petroleum, Btu": 1,
    "Water consumption: gallons": 1,
    "VOC": 1000,
    "CO": 1000,
    "NOx": 1000,
    "PM10": 1000,
    "PM2.5": 1000,
    "SOx": 1000,
    "BC": 1000,
    "OC": 1000,
    "CH4": 1000,
    "N2O": 1000,
    "CO2": 1000,
    "Biogenic CO2": 1000,
    "CO2 (w/ C in VOC & CO)": 1000,
    "GHG": 1000,
    "Urban VOC": 1000,
    "Urban CO": 1000,
    "Urban NOx": 1000,
    "Urban PM10": 1000,
    "Urban PM2.5": 1000,
    "Urban SOx": 1000,
    "Urban BC": 1000,
    "Urban OC": 1000,
}

combination_basis = {  # The basis for combinaning multiple "main products"
    "Biomass": "kg",
    "Process fuel": "mmBTU",
    "Electricity": "mmBTU",
    "Chemicals and catalysts": "kg",
}

primary_units = {
    # Function "process_ser" requires to use g for mass and mmBTU for energy.
    "Process fuel": "mmBTU",
    "Biomass": "g",
    "Electricity": "mmBTU",
    "Chemicals and catalysts": "g",
    "Water": "gal",
    "Transportation": "mmBTU",  # For transportation, diesel is used
    "Waste": "g",
    "Infrastructure": "g",
    "Emissions and sequestration": "g",
    "Other": "g",
}  # The functional unit for calculation

display_units = {
    "Process fuel": "MJ",  # gram, gal, or BTU per MJ
    "Biomass": "ton",  # gram, gal, or BTU per ton
    "Electricity": "MJ",  # gram, gal, or BTU per MJ
    "Chemicals and catalysts": "g",  # gram, gal, or BTU per g
    "Waste": "g",
    "Emissions and sequestration": "g",
    "Other": "g",
    # "Water": "gal",
}  # The units for the final results

units = pd.read_excel(data_file, sheet_name="Units", header=0, index_col=0).squeeze(
    "columns"
)
# units.index = units.index.str.lower()

mass = pd.read_excel(data_file, sheet_name="Mass", header=0, index_col=0)
# mass.columns = mass.columns.str.lower()
# mass.index = mass.index.str.lower()

volume = pd.read_excel(data_file, sheet_name="Volume", header=0, index_col=0)
# volume.columns = volume.columns.str.lower()
# volume.index = volume.index.str.lower()

energy = pd.read_excel(data_file, sheet_name="Energy", header=0, index_col=0)
# energy.columns = energy.columns.str.lower()
# energy.index = energy.index.str.lower()

length = pd.read_excel(data_file, sheet_name="Length", header=0, index_col=0)
# length.columns = length.columns.str.lower()
# length.index = length.index.str.lower()

mass_units = mass.columns.to_list()
volume_units = volume.columns.to_list()
energy_units = energy.columns.to_list()
length_units = length.columns.to_list()

potential_units = {
    "Process fuel": energy_units + volume_units + mass_units,
    "Biomass": mass_units,
    "Electricity": energy_units,
    "Chemicals and catalysts": mass_units,
    "Water": volume_units + mass_units,
    "Transportation": energy_units,  # For transportation, diesel is used
    "Waste": mass_units,
    "Emissions and sequestration": mass_units,
    "Other": mass_units,
}

properties = pd.read_excel(data_file, sheet_name="Fuel specs", skiprows=1, index_col=0)
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


def unit_conversion(
    series,
    input_unit_col="Unit",
    input_amount_col="Input Amount",
    output_unit_col="Primary Unit",
):
    "Perform unit operation for each LCI data entry"
    input_unit = series[input_unit_col]
    amount = series[input_amount_col]
    density = series["Density"]
    lhv = series["LHV"]
    output_unit = series[output_unit_col]

    if units[input_unit] != units[output_unit]:
        if (
            output_unit in volume_units
        ):  # Ouput is volume, then input must be mass, because only water has output unit of volume. Modified from origin
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


def process_ser(ser):
    """
    Process the background LCA data: convert the functional unit used by GREET to that used by the tool.
    Parameter:
        ser: the dataframe to be processed
    Return:
        ser: the data series that has been processed
    """
    unit = ser["Functional Unit"]
    # unit must be either a mass unit (e.g., kg), energy unit (e.g., MJ), or volume (e.g., gal, for water only)
    if unit in mass_units:
        ser.iloc[1:] = ser.iloc[1:] / mass.loc["g", unit]
    elif unit in energy_units:
        ser.iloc[1:] = ser.iloc[1:] / energy.loc["mmBTU", unit]
    else:  # the functional unit for water is gallon. No conversion is needed.
        pass
    return ser


# Process emission factors read from the data extraction file
production_emissions = pd.read_excel(
    data_file,
    sheet_name="Production",
    index_col=0,
    skipfooter=2,
)
production_emissions = production_emissions.dropna()
production_emissions.loc["Biogenic CO2"] = 0
production_emissions.index = production_emissions.index.str.strip()
production_emissions = production_emissions.apply(process_ser, axis=0)
production_emissions = production_emissions.drop(["Functional Unit"])

chemicals_emissions = pd.read_excel(
    data_file,
    sheet_name="Chemicals",
    index_col=0,
    skipfooter=2,
)
chemicals_emissions = chemicals_emissions.dropna()
chemicals_emissions.loc["Biogenic CO2"] = 0
chemicals_emissions.index = chemicals_emissions.index.str.strip()
chemicals_emissions = chemicals_emissions.apply(process_ser, axis=0)
chemicals_emissions = chemicals_emissions.drop(["Functional Unit"])

feedstock_emissions = pd.read_excel(
    data_file, sheet_name="Feedstock", index_col=0, skipfooter=2
)
feedstock_emissions = feedstock_emissions.dropna()
feedstock_emissions.loc["Biogenic CO2"] = 0
feedstock_emissions.index = feedstock_emissions.index.str.strip()
feedstock_emissions = feedstock_emissions.apply(process_ser, axis=0)
feedstock_emissions = feedstock_emissions.drop(["Functional Unit"])

combined_ci_table = pd.concat(
    [production_emissions, chemicals_emissions, feedstock_emissions], axis=1
)
combined_ci_table.columns = combined_ci_table.columns.str.lower()

end_use = pd.read_excel(
    data_file,
    sheet_name="End use test",
    index_col=0,
    header=[0, 1],
    skipfooter=2,
)
end_use = end_use.fillna(0)
end_use = end_use.apply(process_ser, axis=0)
end_use = end_use.drop("Functional Unit")
end_use.index = end_use.index.str.strip()
end_use.columns = end_use.columns.set_levels(
    [end_use.columns.levels[0].str.lower(), end_use.columns.levels[1].str.lower()]
)

# Add urban emission items to end use
urban_emissions_items = ["VOC", "CO", "NOx", "PM10", "PM2.5", "SOx", "BC", "OC"]
urban_end_use = end_use.loc[urban_emissions_items].copy()
urban_end_use.index = "Urban " + urban_end_use.index
end_use = pd.concat([end_use, urban_end_use], axis=0)


def apply_urban_share(ser, share):
    """
    Apply urban emission factors to end use emissions.

    Parameters:
        ser: a series representing emission factors for the end use of a particular fuel.
        share: the urban share.
    Return:
        a series representing emission factors after urban share is applied.
    """

    urban_share_ser = pd.Series(1, index=ser.index)
    urban_share_ser[urban_share_ser.index.str.contains("Urban")] = share
    return ser.mul(urban_share_ser, fill_value=0)


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

        # Calcualte the input emission factor for electricity
        if ser["Resource"] == "electricity":
            # if pd.isnull(ser["End Use"]):
            if ser["End Use"] == "":
                return combined_ci_table[
                    "electricity_u.s. mix"
                ]  # If not generation mix is not specified, use national average
            else:
                return combined_ci_table[ser["Resource"] + "_" + ser["End Use"]]
        # Calcualte the input emission factor for special items (i.e., CO2, VOC, CO2 sequestration, etc.)
        elif "Emissions" in ser["Category"]:
            return apply_urban_share(
                combined_ci_table[ser["Resource"]], ser["Urban Share"]
            )
        # Calcualte the input emission factor for resources other than electricity
        # elif pd.isnull(ser["End Use"]):
        elif ser["End Use"] == "":
            return combined_ci_table[ser["Resource"]]
        else:
            return combined_ci_table[ser["Resource"]].add(
                apply_urban_share(
                    end_use[ser["Resource"], ser["End Use"]], ser["Urban Share"]
                ),
                fill_value=0,
            )

    elif "Intermediate" in ser["Type"]:  # Intermediate products
        if (ser["Resource"] == "electricity") or (ser["End Use"] == ""):
            return zero_emissions
        else:
            return zero_emissions.add(
                apply_urban_share(
                    end_use[ser["Resource"], ser["End Use"]], ser["Urban Share"]
                ),
                fill_value=0,
            )
    elif (
        "Co-product" in ser["Type"]
    ):  # For co-products, the difference between end use emissions for the product and incumbent should be accounted for
        if ser["Incumbent Product"] == "electricity":
            # if pd.isnull(ser["End Use"]):
            if ser["End Use"] == "":
                return combined_ci_table[
                    "electricity_u.s. mix"
                ]  # If not generation mix is not specified, use national average
            else:
                return combined_ci_table[
                    ser["Incumbent Product"] + "_" + ser["End Use of Incumbent Product"]
                ]
        else:
            incumbent_emission = (
                combined_ci_table[ser["Incumbent Product"]]
                # if pd.isnull(ser["Incumbent End Use"])
                if ser["End Use of Incumbent Product"] == ""
                else combined_ci_table[ser["Incumbent Product"]].add(
                    apply_urban_share(
                        end_use[
                            ser["Incumbent Product"],
                            ser["End Use of Incumbent Product"],
                        ],
                        ser["Urban Share"],
                    ),
                    fill_value=0,
                )
            )
            # if pd.isnull(ser["End Use"]):
            if ser["End Use"] == "":
                return incumbent_emission
            else:
                return incumbent_emission.sub(
                    apply_urban_share(
                        end_use[ser["Resource"], ser["End Use"]], ser["Urban Share"]
                    ),
                    fill_value=0,
                )
    else:  # Main product
        # if pd.isnull(ser["End Use"]):
        if ser["End Use"] == "":
            return zero_emissions
        else:
            return zero_emissions.add(
                apply_urban_share(
                    end_use[ser["Resource"], ser["End Use"]], ser["Urban Share"]
                ),
                fill_value=0,
            )


def convert_transport_lci(df):
    """
    df: the original LCI file that contains transportation material, distance, and moisture
    """

    xl = pd.ExcelFile(data_file)
    nrows = xl.book["Transportation"].max_row

    fuel_economy = xl.parse(
        sheet_name="Transportation",
        # skipfooter=34,
        index_col=0,
        nrows=2,
    ).dropna(axis=1, how="all")

    # payload = xl.parse(
    #     sheet_name="Transportation", skiprows=4, skipfooter=28, index_col=0
    # ).dropna(axis=1, how="all")

    dff = df.copy()
    dff["Resource"] = dff["Resource"].str.lower()
    transport = dff[dff["Category"] == "Transportation"]
    dff = dff[dff["Category"] != "Transportation"]
    to_append = [dff]

    # hhdt_payload = payload.loc["Heavy Heavy-Duty Truck"].dropna()
    # t1 = fuel_economy["Heavy Heavy-Duty Truck"].to_frame()
    # t2 = hhdt_payload.to_frame()
    # btu_per_ton_mile = t1.dot((1 / t2).T)
    # btu_per_ton_mile.columns = btu_per_ton_mile.columns.str.lower()

    for _, row in transport.iterrows():
        resource = row.at[
            "Resource"
        ]  # Assuming transport is a series, i.e., there is only one row for transportation
        unit = row.at["Unit"]
        distance = row.at["Amount"] * length.loc["mi", unit]
        payload_unit = row.at["Payload Unit"]
        resource_payload = row.at["Payload"] * mass.loc["ton", payload_unit]

        btu_per_ton_mile_to_desti = (
            fuel_economy.at[
                "Trip from Product Origin to Destination", "Heavy Heavy-Duty Truck"
            ]
            / resource_payload
        )
        btu_per_ton_mile_to_origin = (
            fuel_economy.at[
                "Trip from Product Destination Back to Origin", "Heavy Heavy-Duty Truck"
            ]
            / resource_payload
        )

        to_desti_fuel = (
            # btu_per_ton_mile.at["Trip from Product Origin to Destination", resource]
            btu_per_ton_mile_to_desti
            * distance
            / 1000000
        )  # MMBtu per dry ton
        to_origin_fuel = (
            # btu_per_ton_mile.at[
            #     "Trip from Product Destination Back to Origin", resource
            # ]
            btu_per_ton_mile_to_origin
            * distance
            / 1000000
        )  # MMBtu per dry ton
        # The row of transported resource and its amount
        transport_entry = dff[
            (~dff["Type"].isin(["Main Product", "Co-product"]))
            & (dff["Resource"] == resource)
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
                "Urban Share": [row.at["Urban Share"]] * 2,
                "Product Train": row["Product Train"] * 2,
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
    outputs_previous = dff[dff["Type"] == "Input from Another Stage"].copy()
    dff = dff[dff["Type"] != "Input from Another Stage"]
    to_concat = [dff]

    for ind, row in outputs_previous.iterrows():
        step = row.at["Previous Stage"]
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

    df_final = pd.concat(to_concat[::-1], ignore_index=True)
    step_map.update({step_name: df_final})

    return step_map


def used_other_process(df):
    """
    Return whether a process used inputs from another stage
    """
    return (df["Type"].str.contains("Input from Another Stage")).any()


def process(step_mapping, looped=False):
    """
    Process the LCI data by converting inputs from another stage to its corresponding LCI data.
    """
    for key, value in step_mapping.items():
        if used_other_process(value):
            out = value[value["Type"] == "Input from Another Stage"]
            other_processes = out["Previous Stage"].values
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


def calculate_allocation_ratio(df, basis="mass"):
    """
    Calculate allcation ratio
    """
    product_flag = (df["Type"] == "Main Product") | (
        (df["Type"] == "Co-product")
        & (df["Always Use Displacement Method for Co-Product?"] == "No")
        & (
            df["Amount"] > 0
        )  # if amount is less than zero, it means displacement method has been applied (for example, if displacement method is used for a process)
    )  # Select the products that should be accounted for when calculating allocation ratios
    products = df[product_flag].copy()
    products = products.rename(columns={"Amount": "Input Amount"})

    if basis in ["mass", "energy"]:
        products["Primary Unit"] = "kg" if basis == "mass" else "mmBTU"
        products["Amount"] = products.apply(unit_conversion, axis=1)

    else:
        ###################### Implement market-value-based allocation here ###########################
        try:  # If price is not specified for a process, return 1 (i.e., assume there is no co-product)
            products["Primary Unit"] = products["Market Price Unit"].str[
                2:
            ]  # Obtain the unit: if the market price unit is $/kg, the calculated unit should be kg.
            products["Amount"] = products.apply(unit_conversion, axis=1)
            products["Amount"] = products["Amount"] * products["Market Price"]
        except:
            return 1

    # products = products[
    #     products["Amount"] > 0
    # ]  # Elimante the co-products to which displacement method has been applied
    ratio = (
        products.loc[products["Type"] == "Main Product", "Amount"].sum()
        / products["Amount"].sum()
    )
    return ratio


def format_input(dff, basis=None):
    """
    Formatting LCI data:
        1. Convert relevant column to lower cases
        2. Convert wet weight to dry weight
        3. Convert transportation distance to fuel consumption
        4. Merge with the properties dataframe (add the LHV and density columns)
        5. Combining multiple entries of "main products"
        6. Consider the loss factor of fuel distribution
        7. Normalize the LCI data: calculate the amount per unit main output

    Parameters:
        dff: Pandas DataFrame containing LCI data
        apply_loss_factor: whether or not to apply the loss factor of fuel distribution
        basis: the basis used for combining multiple main product entries, can be None, "mass", "energy", or "value"
    """

    df = dff.copy()  # Avoid chaning the original df
    # rd_dist_loss = 1.00004514306778  # Loss factor of renewable diesel distribution

    # Step 1
    df["End Use"] = df["End Use"].fillna("")
    df["Incumbent Resource"] = df["Incumbent Product"].fillna("")
    df["End Use of Incumbent Product"] = df["End Use of Incumbent Product"].fillna("")
    df["Always Use Displacement Method for Co-Product?"] = df[
        "Always Use Displacement Method for Co-Product?"
    ].fillna("No")

    lower_case_cols = [
        "Resource",
        "End Use",
        "Incumbent Product",
        "End Use of Incumbent Product",
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
    main_product_category = main_products["Category"].values[0]
    main_product_resource = main_products["Resource"].values[0]
    main_product_end_use = main_products["End Use"].values[0]
    if len(main_products) > 1:
        if (
            basis is None
        ):  # Displacement method, combine multiple entries by the primary unit
            main_products["Primary Unit"] = combination_basis[main_product_category]
            main_products = main_products.rename(columns={"Amount": "Input Amount"})
            main_products["Amount"] = main_products.apply(unit_conversion, axis=1)
            main_products["Amount"] = main_products["Amount"].sum()
            main_products["Unit"] = main_products["Primary Unit"]
            main_products = main_products.drop(["Input Amount", "Primary Unit"], axis=1)
            df = pd.concat(
                [df[df["Type"] != "Main Product"], main_products.iloc[:1]],
                ignore_index=True,
            )
        else:
            main_products.iloc[1:, main_products.columns.get_loc("Type")] = "Co-product"
            main_products["Always Use Displacement Method for Co-Product?"] = "No"
            ratio = calculate_allocation_ratio(main_products, basis=basis)
            df.loc[df["Type"] != "Main Product", "Amount"] = (
                df.loc[df["Type"] != "Main Product", "Amount"] * ratio
            )
            df = pd.concat(
                [df[df["Type"] != "Main Product"], main_products.iloc[:1]],
                ignore_index=True,
            )

    # # Step 6
    # if (
    #     (main_product_resource == "renewable diesel")
    #     and ("distribution" in main_product_end_use)
    #     and (apply_loss_factor)
    # ):
    #     df.loc[df["Type"] == "Main Product", "Amount"] = (
    #         df.loc[df["Type"] == "Main Product", "Amount"] / rd_dist_loss
    #     )

    # Step 7
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
        include_incumbent: whether to include the incumbent product in the result dataframe.
    """

    # df_lci["ID"] = df_lci["ID"].str.lower()
    # res = pd.merge(df_lci, lookup_table, left_on="ID", right_index=True, how="left")
    # res["Primary Unit"] = res["Primary Unit"].str.lower()

    if include_incumbent:
        # Separate out the incumbent product that the main product is compared with
        incumbent_resource = (
            df_lci.loc[df_lci["Type"] == "Main Product", "Incumbent Product"]
            # .fillna("")
            .values[0]
        )
        incumbent_end_use = (
            df_lci.loc[df_lci["Type"] == "Main Product", "End Use of Incumbent Product"]
            # .fillna("")
            .values[0]
        )
        incumbent_urban_share = (
            df_lci.loc[df_lci["Type"] == "Main Product", "Urban Share"]
            # .fillna("")
            .values[0]
        )
        incumbent_category = df_lci.loc[
            df_lci["Type"] == "Main Product", "Category"
        ].values[0]

        main_product = df_lci.loc[df_lci["Type"] == "Main Product", "Resource"].values[
            0
        ]
        df_lci["Pathway"] = main_product.title() + " (Modeled)"

        df_incumbent = pd.DataFrame(
            {
                "Pathway": [incumbent_resource.title() + " (Incumbent)"],
                "Type": ["Input"],
                "Category": [incumbent_category],
                "Resource": [incumbent_resource],
                "Process": [incumbent_resource + " (Incumbent)"],
                "End Use": [incumbent_end_use],
                "Urban Share": [incumbent_urban_share],
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
        + res["Biogenic CO2"] * co2_gwp
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
    if include_incumbent:
        res.loc[res["Pathway"].str.contains("Incumbent"), "Amount"] = 1
    # res = res[res["Type"] != "Main Product"]
    main_product_category = res.loc[res["Type"] == "Main Product", "Category"].values[0]
    calculation_unit = primary_units[main_product_category]
    target_unit = display_units[main_product_category]

    for metric in metrics:
        res[metric + "_Sum"] = res["Amount"] * res[metric]

    # Use MJ as the unit of energy metrics
    for metric in [
        "Total energy, Btu",
        "Fossil fuels, Btu",
        "Coal, Btu",
        "Natural gas, Btu",
        "Petroleum, Btu",
    ]:
        res[metric + "_Sum"] = res[metric + "_Sum"] * energy.loc["MJ", "BTU"]

    if main_product_category in ["Process fuel", "Electricity"]:
        for metric in metrics:
            res[metric + "_Sum"] = (
                res[metric + "_Sum"] / energy.loc[target_unit, calculation_unit]
            )  # Convert the functional unit from calculation unit to target unit
        res.loc[
            res["Type"] == "Main Product", "Unit"
        ] = target_unit  # Update the functional unit of the main product after the conversion
    return res
