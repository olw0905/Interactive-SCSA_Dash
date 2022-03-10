import pandas as pd
# from lookup_table import lookup_table
from utils import unit_conversion, convert_transport_lci, step_processing, used_other_process, process, format_input, calculate_lca, lookup_table

category = pd.read_csv("category.csv", index_col=0, header=0).squeeze()

def calc(lci_file):
    lci_feedstock = pd.read_excel(lci_file, sheet_name='Feedstock harvest')
    lci_feedstock = format_input(lci_feedstock)

    lci_preprocessing = pd.read_excel(lci_file, sheet_name='Preprocessing')
    lci_preprocessing = format_input(lci_preprocessing)

    lci_fuel = pd.read_excel(lci_file, sheet_name='Fuel Production')
    lci_fuel = format_input(lci_fuel)

    step_mapping = {'feedstock harvest': lci_feedstock, 'preprocessing': lci_preprocessing, 'fuel production': lci_fuel}
    res = process(step_mapping)

    overall_lci = res['fuel production']
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
