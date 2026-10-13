import urllib.parse as url_p
from astroquery.vizier import Vizier as viz
import pandas as pd

def get_data_3_types(sample_size_per=50):
    v = viz(row_limit=sample_size_per)
    
    print("Getting Eclipse Binaries")

    #J/AJ/151/68/catalog, kepler eclipsing binary catalog
    eclipse_binary = v.get_catalogs("J/AJ/151/68/catalog")[0].to_pandas()
    data_eclipse_binary = eclipse_binary[["KIC"]].rename(columns={"KIC": "kic_id"})
    data_eclipse_binary["label"] = 0

    print("Getting quiet stars")

    #V/133/kic, kelpler input catalog, main sequence starts
    quiets = v.get_catalogs("V/133/kic")[0].to_pandas()
    data_quiets =  quiets[["KIC"]].rename(columns={"KIC": "kic_id"})
    data_quiets["label"] = 1
   
    print("Getting pulsating stars")    
    
    #J/ApJS/211/2, pulsating start catalog, added other one since I was getting empty table issue
    pulsator_table = v.get_catalogs("J/MNRAS/414/792")
    if len(pulsator_table) == 0:
        pulsator_table = v.get_catalogs("J/ApJS/211/2")
    pulsators = pulsator_table[0].to_pandas()
    data_pulsators = pulsators[["KIC"]].rename(columns={"KIC": "kic_id"})
    data_pulsators["label"] = 2
    
    full_data = pd.concat([data_eclipse_binary, data_quiets, data_pulsators], ignore_index=True)
    #set random_state= if you want reproducable results
    return full_data.sample(frac=1.0).reset_index(drop=True)


data = get_data_3_types(50)
print(f"total data points: {len(data)}")
print(data["label"].value_counts())
filename = "data/ids_with_label.csv"
data.to_csv(filename, index=False)