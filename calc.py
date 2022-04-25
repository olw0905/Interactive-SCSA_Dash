import pandas as pd
# from lookup_table import lookup_table
from utils import process, format_input, calculate_lca

category = pd.read_csv("category.csv", index_col=0, header=0).squeeze()

def read_data(lci_file):
    '''
        Read the content of the LCI file to generate a dictionary for use in the calc fuction.

        Parameters:
            lci_file: the uploaded LCI file.

        Return:
            lci_mapping: a dictionary of process name and LCI data that can be used in the calc function to perform LCA calculation.
    '''
    xl = pd.ExcelFile(lci_file)
    sheet_names = xl.sheet_names

    lci_mapping = dict()
    for sheet in sheet_names:
        df = pd.read_excel(lci_file, sheet_name=sheet)
        # df = format_input(df)
        lci_mapping.update({sheet: df})

    return lci_mapping

def allocation(df, basis='mass'):
    '''
    Calcuates process-level allocation raio

    Parameters:
        df: the original LCI dataframe that contains inputs and outputs
        basis: the basis for process-level allocation. Must be one of the following: "mass", "energy", or "value".
    '''
    products = df[df['Type'].isin(['Main Product', 'Co-product'])].copy()
    products = products.rename(columns={"Amount": "Input Amount"})

    if basis == 'mass':
        products['Primary Unit'] = 'kg'
    elif basis == 'energy':
        products['Primary Unit'] = 'mmbtu'

    products['Amount'] = products.apply(unit_conversion, axis=1)
    ratio = products.loc[products['Type']=='Main Product', 'Amount'].sum()/products['Amount'].sum()

    allocated = df[~df['Type'].isin(['Main Product', 'Co-product'])].copy()

    # allocated['Ratio'] = allocated
    allocated['Amount'] = allocated['Amount'] * allocated['Product train'].map({'Both': ratio, 'Co-product': 0, 'Main product': 1}) 
    allocated = allocated[allocated['Amount']>0]

    return pd.concat([allocated, df[df['Type'].isin(['Main Product'])]], ignore_index=True)


# def calc(sheet_names, step_mapping):
def calc(lci_mapping, coprod='displacement', basis='mass'):
    '''
    lci_mapping: a dictionary containing the sheet names and original LCI data table.
    coprod: coproduct handling method. Must be one of the following: "displacement", "process allocation", and "system allocation".
    basis: the basis for allocation methods. Must be one of the following: "mass", "energy", or "value".
    '''

    sheet_names = list(lci_mapping.keys())
    step_mapping = {sheet.lower(): format_input(df) for sheet, df in lci_mapping.items()}

    if coprod = "process allocation":
        step_mapping = {sheet: allocation(df, basis) for sheet, df in step_mapping.items()}


    lcis = process(step_mapping)

    overall_lci = lcis[sheet_names[-1].lower()]    # Assuming the final product is always in the last worksheet TODO: Improve this.
    # overall_lci = overall_lci[overall_lci['Type']=='Input'].copy()
    # overall_lci['ID'] = overall_lci.apply(
    #     # lambda a: a['Resource'] if (pd.isna(a['End Use']))|(a['Resource'] == 'Electricity') else a['Resource']+'_'+a['End Use'], axis=1
    #     lambda a: a['Resource'] if pd.isna(a['End Use']) else a['Resource']+'_'+a['End Use'], axis=1
    # )
    overall_lci["End Use"] = overall_lci["End Use"].fillna("")
    overall_lci["ID"] = overall_lci.apply(
        # lambda a: a['Resource'] if (pd.isna(a['End Use']))|(a['Resource'] == 'Electricity') else a['Resource']+'_'+a['End Use'], axis=1
        # lambda a: a['Resource'] if pd.isna(a['End Use']) else a['Resource']+'_'+a['End Use'], axis=1
        lambda a: a["Resource"]
        if a["End Use"] == ""
        else a["Resource"] + "_" + a["End Use"],
        axis=1,
    )
    overall_lci.loc[overall_lci["Type"].str.contains("Co-product"), "Amount"] = overall_lci.loc[overall_lci["Type"].str.contains("Co-product"), "Amount"] * -1

    res = calculate_lca(overall_lci)
    # res.loc[res['Category']!='Co-Product', 'Category'] = res.loc[res['Category']!='Co-Product', 'Resource'].map(category)
    res['Resource'] = res['Resource'].str.title()
    res.loc[res["Type"].str.contains("Co-product"), "Category"] = "Co-product Credits"
    res['Resource'] = res['Resource'].str.replace('Wwt', 'WWT').str.replace('Fgd', 'FGD')

    return res
