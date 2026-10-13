from concurrent.futures import ThreadPoolExecutor
import lightkurve as lk
import numpy as np
import pandas as pd

#Constants to play around with in the data, I guess I could also just make this a param.  
SIGMA = 5
WINDOW_LENGTH = 101

def process_star(row, bin_count=1000):
    kic_id = int(row["kic_id"])
    label = int(row["label"])
    
    try:
        pass
        searched_star = lk.search_lightcurve(f"KIC {kic_id}", mission="Kepler", author="Kepler")
        if len(searched_star) == 0:
            return None
        
        lightcurve = searched_star[0].download()
        if lightcurve is None:
            return None
        lightcurve_clean = lightcurve.remove_nans().remove_outliers(sigma=SIGMA)
        lightcurve_flattened = lightcurve_clean.flatten(WINDOW_LENGTH)

        periodogram = lightcurve_flattened.to_periodogram(method="lombscargle")
        ideal = periodogram.period_at_max_power
        lightcurve_folded = lightcurve_flattened.fold(ideal)        
        
        lightcurve_binned = lightcurve_folded.bin(bins=bin_count)
        flux = lightcurve_binned.flux.value
        
        NaNs = np.isnan(flux)
        if np.all(NaNs):
            return None
        if np.any(NaNs):
            flux[NaNs] = np.interp(np.flatnonzero(NaNs), np.flatnonzero(~NaNs), flux[~NaNs])
        
        flux = (flux - np.mean(flux)) / np.std(flux)
        return (flux, label, kic_id)
    except Exception:
        return None
    
def process_stars_into_npy(csv_path="data/ids_with_label.csv", max_threads=6):
    stars = pd.read_csv(csv_path)
    print(f"{len(stars)} stars from file {csv_path}")
    
    x_list, y_list = [], []
    completed = 0
    
    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        rows = [row for _, row in stars.iterrows()]
        results = list(executor.map(process_star, rows))
    
    for result in results:
        if result is not None:
            flux, label, kic_id = result
            x_list.append(flux)
            y_list.append(label)
            completed += 1
            print(f"Processed star- KIC: {kic_id}, label: {label}")
            
    x = np.expand_dims(np.array(x_list), axis=1)
    y = np.array(y_list)
    np.save("data/X_lightcurves.npy", x)
    np.save("data/y_labels.npy", y)
    
    print(f"processing complete, loaded {completed} / {len(stars)} stars properly")
    print(f"saved data/X_lightcurves.npy {x.shape}, data/y_labels.npy {y.shape}")

process_stars_into_npy()