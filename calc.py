import pandas as pd
# from lookup_table import lookup_table
from utils import process, format_input, calculate_lca

category = pd.read_csv("category.csv", index_col=0, header=0).squeeze()

def calc(lci_file):
    xl = pd.ExcelFile(lci_file)
    sheet_names = xl.sheet_names

    step_mapping = dict()
    for sheet in sheet_names:
        df = pd.read_excel(lci_file, sheet_name=sheet)
        df = format_input(df)
        step_mapping.update({sheet.lower(): df})

    res = process(step_mapping)

    overall_lci = res[sheet_names[-1].lower()]    # Assuming the final product is always in the last worksheet TODO: Improve this.
    overall_lci = overall_lci[overall_lci['Type']=='Input'].copy()
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

    res = calculate_lca(overall_lci)
    res.loc[res['Category']!='Co-Product', 'Category'] = res.loc[res['Category']!='Co-Product', 'Resource'].map(category)
    res['Resource'] = res['Resource'].str.title()
    res['Resource'] = res['Resource'].str.replace('Wwt', 'WWT').str.replace('Fgd', 'FGD')

    return res
