from utils import unit_conversion, convert_transport_lci, properties, combination_basis
import pandas as pd


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


def format_input(dff, apply_loss_factor=True, basis=None):
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
    rd_dist_loss = 1.00004514306778  # Loss factor of renewable diesel distribution

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

    # Step 6
    if (
        (main_product_resource == "renewable diesel")
        and ("distribution" in main_product_end_use)
        and (apply_loss_factor)
    ):
        df.loc[df["Type"] == "Main Product", "Amount"] = (
            df.loc[df["Type"] == "Main Product", "Amount"] / rd_dist_loss
        )

    # Step 7
    main_product_amount = df.loc[
        df["Type"] == "Main Product", "Amount"
    ].sum()  # TODO: need to make sure the units are consistent
    df["Amount"] = df["Amount"] / main_product_amount

    return df
