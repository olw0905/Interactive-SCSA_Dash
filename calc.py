import pandas as pd
from utils import process, calculate_allocation_ratio, format_input


def read_data(lci_file):
    """
    Read the content of the LCI file to generate a dictionary for use in the calc fuction.

    Parameters:
        lci_file: the uploaded LCI file.

    Return:
        lci_mapping: a dictionary of process name and LCI data that can be used in the calc function to perform LCA calculation.
        coproduct_mapping: a dictionary of co-product handling method.
        final_process_mapping: a dictionary indicating whether each process produces the end product.
    """
    exclude_list = [
        "Introduction",
        "SI - Co-products",
        "SI - Resources",
        "SI - End Use",
        "SI - Units",
        "SI - Payload",
        "Template",
        "INL Data",
    ]
    xl = pd.ExcelFile(lci_file)
    sheet_names = xl.sheet_names

    lci_mapping = dict()
    coproduct_mapping = dict()
    final_process_mapping = dict()
    for sheet in sheet_names:
        if sheet not in exclude_list:
            coproduct = pd.read_excel(
                lci_file, sheet_name=sheet, nrows=1, usecols=[2], header=None
            ).squeeze()
            final_process = pd.read_excel(
                lci_file,
                sheet_name=sheet,
                nrows=1,
                usecols=[2],
                skiprows=1,
                header=None,
            ).squeeze()
            urban_share = pd.read_excel(
                lci_file,
                sheet_name=sheet,
                nrows=1,
                usecols=[2],
                skiprows=2,
                header=None,
            ).squeeze()
            df = pd.read_excel(lci_file, sheet_name=sheet, skiprows=4)
            df["Process"] = df["Process"].fillna(method="ffill").fillna(sheet)
            df["Urban Share"] = df["Urban Share"].fillna(urban_share)
            lci_mapping.update({sheet: df})
            coproduct_mapping.update({sheet: coproduct})
            final_process_mapping.update({sheet: final_process})

    return lci_mapping, coproduct_mapping, final_process_mapping


def data_check(lci_mapping, coproduct_mapping, final_process_mapping):
    """
    Check for mistakes in the input LCI file.

    Parameters:
        lci_mapping: a dicttionary of the original LCI fileself.
    Return:
        A string indicating the status of data check.
    """

    for sheet, df in lci_mapping.items():
        main_product = df.loc[df["Type"] == "Main Product", "Category"].unique()
        l = len(main_product)

        # The main product of each process must be specified
        if l < 1:
            return f'Please specify the main product of process "{sheet}".'

        # Only one type of main product is allowed
        if l > 1:
            return (
                f'Main products of different categories cannot be combined. Process "{sheet}" contains {l} categories of main products: '
                + ", ".join(["{}"] * l).format(*main_product)
                + "."
            )

        # Moisture content must be between 0 and 1
        if ~df["Moisture"].fillna(0).between(0, 1).all():
            return f'Moisture content must be between 0 and 1. Please correct moisture specifications for Process "{sheet}".'

        # If a resource is from another stage, the previous stage column must be specified and the specified process must exist
        other_process = df.loc[df["Type"] == "Input from Another Stage"]
        source_process_specified = other_process["Previous Stage"].isin(
            lci_mapping.keys()
        )
        if ~(source_process_specified.all()):
            resource = other_process.loc[~source_process_specified, "Resource"].values[
                0
            ]
            return f'The process from which "{resource}" in Process "{sheet}" is produced either is not specified or does not exist.'

        # Electricity mix must be specified
        electricity = df.loc[df["Resource"] == "Electricity"]
        if electricity["End Use"].isna().any():
            return f'Please check Process "{sheet}": Electricity mix must be specified in the "End Use" column.'

    # One and only one final process can be specified
    final_process_list = list(final_process_mapping.values())
    final_process_number = final_process_list.count("Yes")
    if final_process_number < 1:
        return "The process producing the end product must be specified."
    elif final_process_number > 1:
        return "More than one processes produce the end product. Only one is allowed."

    # Process-level and system-level allocation method cannot be selected at the same time
    process_allocation_used = False
    system_allocation_used = False
    process_sheet = ""
    system_sheet = ""

    for sheet, allocation_method in coproduct_mapping.items():
        if "Process" in allocation_method:
            process_allocation_used = True
            process_sheet = sheet
            break

    for sheet, allocation_method in coproduct_mapping.items():
        if "System" in allocation_method:
            system_allocation_used = True
            system_sheet = sheet
            break

    if process_allocation_used and system_allocation_used:
        return f'System-level allocation (Process "{system_sheet}") and process-level allocation (Process "{process_sheet}") should not be used at the same time.'

    # Check passed!
    else:
        return "OK"


# def calculate_allocation_ratio(df, basis="mass"):
#     """
#     Calculate allcation ratio
#     """
#     product_flag = (df["Type"] == "Main Product") | (
#         (df["Type"] == "Co-product")
#         & (df["Always Use Displacement Method for Co-Product?"] == "No")
#         & (
#             df["Amount"] > 0
#         )  # if amount is less than zero, it means displacement method has been applied (for example, if displacement method is used for a process)
#     )  # Select the products that should be accounted for when calculating allocation ratios
#     products = df[product_flag].copy()
#     products = products.rename(columns={"Amount": "Input Amount"})

#     if basis in ["mass", "energy"]:
#         products["Primary Unit"] = "kg" if basis == "mass" else "mmBTU"
#         products["Amount"] = products.apply(unit_conversion, axis=1)

#     else:
#         ###################### Implement market-value-based allocation here ###########################
#         try:  # If price is not specified for a process, return 1 (i.e., assume there is no co-product)
#             products["Primary Unit"] = products["Market Price Unit"].str[
#                 2:
#             ]  # Obtain the unit: if the market price unit is $/kg, the calculated unit should be kg.
#             products["Amount"] = products.apply(unit_conversion, axis=1)
#             products["Amount"] = products["Amount"] * products["Market Price"]
#         except:
#             return 1

#     # products = products[
#     #     products["Amount"] > 0
#     # ]  # Elimante the co-products to which displacement method has been applied
#     ratio = (
#         products.loc[products["Type"] == "Main Product", "Amount"].sum()
#         / products["Amount"].sum()
#     )
#     return ratio


def allocation(df, basis="mass"):
    """
    Calcuate the LCI data after allocation

    Parameters:
        df: the original LCI dataframe that contains inputs and outputs
        basis: the basis for process-level allocation. Must be one of the following: "mass", "energy", or "value".
    """
    ratio = calculate_allocation_ratio(df, basis)

    not_allocated = (df["Type"] == "Main Product") | (
        (df["Type"] == "Co-product")
        & (df["Always Use Displacement Method for Co-Product?"] == "No")
        & (
            df["Amount"] > 0
        )  # if amount is less than zero, it means displacement method has been applied (for example, if displacement method is used for a process)
    )
    allocated = df[~not_allocated].copy()

    # allocated['Ratio'] = allocated
    allocated["Amount"] = allocated["Amount"] * allocated["Product Train"].fillna(
        "Both"
    ).map(
        {"Both": ratio, "Co-product": 0, "Main product": 1, "Main Product": 1}
    ).fillna(
        ratio
    )

    allocated = allocated[allocated["Amount"] != 0]
    allocated.loc[
        (allocated["Type"] == "Co-product") & (allocated["Amount"] > 0), "Amount"
    ] = -allocated.loc[
        (allocated["Type"] == "Co-product") & (allocated["Amount"] > 0), "Amount"
    ]  # Only for the co-products for which displacement methods should but have not been applied

    return pd.concat(
        [allocated, df[df["Type"].isin(["Main Product"])]], ignore_index=True
    )


def generate_final_lci(
    lci_mapping,
    coproduct_mapping,
    final_process_mapping,
    return_final_process=False,
    apply_loss_factor=True,
):
    """
    Generatethe final LCI file used for LCA calculation

    Parameters:
        lci_mapping: a dictionary of process name and LCI data that can be used in the calc function to perform LCA calculation.
        coproduct_mapping: a dictionary of co-product handling method. The values can be one of the following:
            Displacement Method, Process Level Mass-Based Allocation, Process Level Energy-Based Allocation, Process Level Value-Based Allocation,
            System Level Mass-Based Allocation, system Level-Based Energy Allocation, System Level Value-Based Allocation.
    Return:
        lci_mapping_processed: the LCI data after applying the co-product handling method
    """
    system_allocation = (
        False  # A flag indicating whether system-level allocation is used
    )
    system_allocation_basis = "mass"  # The basis used for system-level allocation

    step_mapping = {}
    for sheet in lci_mapping:
        # df = format_input(lci_mapping[sheet])
        if "Process" in coproduct_mapping[sheet]:
            if "Mass" in coproduct_mapping[sheet]:
                df = format_input(lci_mapping[sheet], basis="mass")
                step_mapping.update({sheet: allocation(df, "mass")})
            elif "Energy" in coproduct_mapping[sheet]:
                df = format_input(lci_mapping[sheet], basis="energy")
                step_mapping.update({sheet: allocation(df, "energy")})
            else:
                df = format_input(lci_mapping[sheet], basis="value")
                step_mapping.update({sheet: allocation(df, "value")})
        elif "Displacement" in coproduct_mapping[sheet]:
            df = format_input(lci_mapping[sheet])
            df.loc[df["Type"] == "Co-product", "Amount"] = -df.loc[
                df["Type"] == "Co-product", "Amount"
            ]
            step_mapping.update({sheet: df})
        else:  # System-level allocation, no processing needed at this stage
            if "Mass" in coproduct_mapping[sheet]:
                df = format_input(lci_mapping[sheet], basis="mass")
            elif "Energy" in coproduct_mapping[sheet]:
                df = format_input(lci_mapping[sheet], basis="energy")
                system_allocation_basis = "energy"
            else:
                df = format_input(lci_mapping[sheet], basis="value")
                system_allocation_basis = "value"
            step_mapping.update({sheet: df})
            system_allocation = True
            # if "Energy" in coproduct_mapping[sheet]:
            #     system_allocation_basis = "energy"
            # elif "Value" in coproduct_mapping[sheet]:
            #     system_allocation_basis = "value"
    # return step_mapping
    lcis = process(step_mapping)
    # return lcis

    # Locate the last process
    for sheet, process_bool in final_process_mapping.items():
        if process_bool == "Yes":
            final_process = sheet
            break

    overall_lci = lcis[final_process]
    # return overall_lci, lcis, system_allocation, system_allocation_basis
    if system_allocation:
        overall_lci["Product Train"] = "Both"
        overall_lci = allocation(overall_lci, system_allocation_basis)

    main_products = overall_lci[overall_lci["Type"] == "Main Product"]
    # main_product_category = main_products["Category"].values[0]
    main_product_resource = main_products["Resource"].values[0]
    main_product_end_use = main_products["End Use"].values[0]
    rd_dist_loss = 1.00004514306778

    if (
        ("renewable diesel" in main_product_resource)
        and ("distribution" in main_product_end_use)
        and (apply_loss_factor)
    ):
        overall_lci.loc[overall_lci["Type"] != "Main Product", "Amount"] = (
            overall_lci.loc[overall_lci["Type"] != "Main Product", "Amount"]
            * rd_dist_loss
        )

    if return_final_process:
        return overall_lci, final_process
    else:
        return overall_lci


def generate_coproduct_lci_mapping(
    lci_mapping_original, coproduct_mapping, final_process_mapping
):
    """
    Generatethe lci_mapping used for LCA calculation for the coproduct

    Parameters:
        lci_mapping: a dictionary of process name and LCI data that can be used in the calc function to perform LCA calculation.
        coproduct_mapping: a dictionary of co-product handling method. The values can be one of the following:
            Displacement Method, Process Level Mass-Based Allocation, Process Level Energy-Based Allocation, Process Level Value-Based Allocation,
            System Level Mass-Based Allocation, system Level-Based Energy Allocation, System Level Value-Based Allocation.
    Return:
        lci_mapping_processed: the LCI data after applying the co-product handling method
    """

    lci_mapping = lci_mapping_original.copy()

    # Locate the last process
    final_process = None
    for sheet, process_bool in final_process_mapping.items():
        # if process_bool == "Yes":
        #     final_process = sheet
        #     break
        df = lci_mapping[sheet]
        if (
            len(
                df.loc[
                    (df["Type"] == "Co-product")
                    & (df["Always Use Displacement Method for Co-Product?"] != "Yes")
                ]
            )
            > 0
        ):
            final_process = sheet
            break
    if final_process is None:
        return None  # There is no co-product to analyze
    else:
        coproduct_final_process_mapping = {
            sheet: "No" for sheet in final_process_mapping
        }
        coproduct_final_process_mapping[final_process] = "Yes"

        df = lci_mapping[final_process].copy()
        if "Displacement" in coproduct_mapping[final_process]:
            # df = lci_mapping[final_process].copy()
            # if (
            #     len(
            #         df.loc[
            #             (df["Type"] == "Co-product")
            #             & (df["Always Use Displacement Method for Co-Product?"] != "Yes")
            #         ]
            #     )
            #     == 0
            # ):  # There is no co-product to analyze
            #     return None
            df = df.loc[
                (df["Type"] == "Co-product")
                & (df["Always Use Displacement Method for Co-Product?"] != "Yes")
            ]
            df["Type"] = "Main Product"
            df[
                "End Use"
            ] = ""  # End use is already accounted for when calculating main product results with displacement method
            # return None
        else:
            # df = lci_mapping[final_process].copy()
            # if (
            #     len(
            #         df.loc[
            #             (df["Type"] == "Co-product")
            #             & (df["Always Use Displacement Method for Co-Product?"] != "Yes")
            #         ]
            #     )
            #     == 0
            # ):  # There is no co-product to analyze
            #     return None
            df.loc[
                (df["Type"] == "Co-product")
                & (df["Always Use Displacement Method for Co-Product?"] != "Yes"),
                "Type",
            ] = "Main"
            df.loc[
                df["Type"] == "Main Product",
                "Always Use Displacement Method for Co-Product?",
            ] = "No"
            df.loc[df["Type"] == "Main Product", "Type"] = "Co-product"
            df.loc[df["Type"] == "Main", "Type"] = "Main Product"

            df["Product Train"] = df["Product Train"].map(
                {
                    "Both": "Both",
                    "Co-product": "Main product",
                    "Main product": "Co-product",
                    "Main Product": "Co-product",
                }
            )

            # lci_mapping.update({final_process: df})
            # return lci_mapping
    lci_mapping.update({final_process: df})
    return lci_mapping, coproduct_final_process_mapping, final_process


def generate_coproduct_lci(
    lci_mapping_original, coproduct_mapping, final_process_mapping
):
    """
    Generatethe final LCI file used for LCA calculation for the coproduct

    Parameters:
        lci_mapping: a dictionary of process name and LCI data that can be used in the calc function to perform LCA calculation.
        coproduct_mapping: a dictionary of co-product handling method. The values can be one of the following:
            Displacement Method, Process Level Mass-Based Allocation, Process Level Energy-Based Allocation, Process Level Value-Based Allocation,
            System Level Mass-Based Allocation, system Level-Based Energy Allocation, System Level Value-Based Allocation.
    Return:
        lci_mapping_processed: the LCI data after applying the co-product handling method
    """
    # system_allocation = (
    #     False  # A flag indicating whether system-level allocation is used
    # )
    # system_allocation_basis = "mass"  # The basis used for system-level allocation
    coproduct_mappings = generate_coproduct_lci_mapping(
        lci_mapping_original, coproduct_mapping, final_process_mapping
    )

    if coproduct_mappings is None:
        return None

    lci_mapping, coproduct_final_process_mapping, final_process = coproduct_mappings
    overall_lci = generate_final_lci(
        lci_mapping, coproduct_mapping, coproduct_final_process_mapping
    )

    # # Locate the last process
    # for sheet, process_bool in final_process_mapping.items():
    #     if process_bool == "Yes":
    #         final_process = sheet
    #         break

    # if "Displacement" in coproduct_mapping[final_process]:
    #     return None
    # else:
    #     df = lci_mapping[final_process].copy()
    #     if (
    #         len(
    #             df.loc[
    #                 (df["Type"] == "Co-product")
    #                 & (df["Always Use Displacement Method for Co-Product?"] != "Yes")
    #             ]
    #         )
    #         == 0
    #     ):  # There is no co-product to analyze
    #         return None
    #     df.loc[
    #         (df["Type"] == "Co-product")
    #         & (df["Always Use Displacement Method for Co-Product?"] != "Yes"),
    #         "Type",
    #     ] = "Main"
    #     df.loc[
    #         df["Type"] == "Main Product",
    #         "Always Use Displacement Method for Co-Product?",
    #     ] = "No"
    #     df.loc[df["Type"] == "Main Product", "Type"] = "Co-product"
    #     df.loc[df["Type"] == "Main", "Type"] = "Main Product"

    #     df["Product Train"] = df["Product Train"].map(
    #         {"Both": "Both", "Co-product": "Main product", "Main product": "Co-product"}
    #     )

    #     lci_mapping.update({final_process: df})

    # step_mapping = {}
    # for sheet in lci_mapping:
    #     df = format_input(lci_mapping[sheet])
    #     if "Process" in coproduct_mapping[sheet]:
    #         if "Mass" in coproduct_mapping[sheet]:
    #             step_mapping.update({sheet: allocation(df, "mass")})
    #         elif "Energy" in coproduct_mapping[sheet]:
    #             step_mapping.update({sheet: allocation(df, "energy")})
    #         else:
    #             step_mapping.update({sheet: allocation(df, "value")})
    #     elif "Displacement" in coproduct_mapping[sheet]:
    #         df.loc[df["Type"] == "Co-product", "Amount"] = -df.loc[
    #             df["Type"] == "Co-product", "Amount"
    #         ]
    #         step_mapping.update({sheet: df})
    #     else:  # System-level allocation, no processing needed at this stage
    #         step_mapping.update({sheet: df})
    #         system_allocation = True
    #         if "Energy" in coproduct_mapping[sheet]:
    #             system_allocation_basis = "energy"
    #         elif "Value" in coproduct_mapping[sheet]:
    #             system_allocation_basis = "value"

    # lcis = process(step_mapping)

    # overall_lci = lcis[final_process]

    # if system_allocation:
    #     overall_lci["Product Train"] = "Both"
    # overall_lci = allocation(overall_lci, system_allocation_basis)

    return overall_lci, coproduct_final_process_mapping, final_process


# def calc(sheet_names, step_mapping):
# def calc(lci_mapping, final_process_mapping, coprod="displacement", basis="mass"):
def postprocess(res):
    """
    Postprocessing of the caluclated LCA results dataframe.
    """

    # overall_lci["End Use"] = overall_lci["End Use"].fillna("")
    # overall_lci["ID"] = overall_lci.apply(
    #     # lambda a: a['Resource'] if (pd.isna(a['End Use']))|(a['Resource'] == 'Electricity') else a['Resource']+'_'+a['End Use'], axis=1
    #     # lambda a: a['Resource'] if pd.isna(a['End Use']) else a['Resource']+'_'+a['End Use'], axis=1
    #     lambda a: a["Resource"]
    #     if a["End Use"] == ""
    #     else a["Resource"] + "_" + a["End Use"],
    #     axis=1,
    # )
    # # overall_lci.loc[overall_lci["Type"] == "Co-product", "Amount"] = (
    # #     overall_lci.loc[overall_lci["Type"] == "Co-product", "Amount"] * -1
    # # )

    # res = calculate_lca(overall_lci, include_incumbent)
    # # res.loc[res['Category']!='Co-Product', 'Category'] = res.loc[res['Category']!='Co-Product', 'Resource'].map(category)
    res["Process"] = res["Process"].str.title()
    res["Process"] = (
        res["Process"]
        .str.replace("Htl", "HTL")
        .str.replace("Cfp", "CFP")
        .str.replace("Idl", "IDL")
        # .str.replace("Bdo", "BDO")
    )
    res["Resource"] = res["Resource"].str.title()
    res["Resource"] = (
        res["Resource"]
        .str.replace("Co2", "CO2")
        .str.replace("Wwt", "WWT")
        .str.replace("Fgd", "FGD")
        .str.replace("Bdo", "BDO")
    )
    if "Pathway" in res.columns:
        res["Pathway"] = (
            res["Pathway"]
            .str.replace("Co2", "CO2")
            .str.replace("Wwt", "WWT")
            .str.replace("Fgd", "FGD")
            .str.replace("Bdo", "BDO")
        )

    res = res.rename(columns={"Process": "Life-Cycle Stage"})

    res.loc[res["Type"].str.contains("Co-product"), "Category"] = "Co-product Credits"
    res.loc[
        (res["Category"] == "Emissions and sequestration")
        & (res["Resource"].str.contains("Sequestration")),
        "Category",
    ] = "Carbon sequestration"
    res.loc[(res["Category"] == "Emissions and sequestration"), "Resource",] = (
        "Other "
        + res.loc[res["Category"] == "Emissions and sequestration", "Resource"]
        + " emission"
    )
    # res["Resource"] = (
    #     res["Resource"].str.replace("Wwt", "WWT").str.replace("Fgd", "FGD")
    # )

    # Restore surrogates
    res.loc[res["Surrogate For"].notna(), "Resource"] = res.loc[
        res["Surrogate For"].notna(), "Surrogate For"
    ]

    return res


# def calculation_in_one(lci_file):
#     """
#     Calculate the results from the uploaded LCI file.
#
#     Parameter:
#         lci_file: uploaded LCI file
#
#     Return:
#         res: the dataframe containing the final LCA results
#     """
#     lci_mapping, coproduct_mapping, final_process_mapping = read_data(lci_file)
#     data_status = data_check(lci_mapping, coproduct_mapping, final_process_mapping)
#
#     if data_status == "OK":
#         overall_lci = generate_final_lci(
#             lci_mapping, coproduct_mapping, final_process_mapping
#         )
#         res = calc(overall_lci)
#         return res
#
#     else:
#         return data_status
