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
        searched_star = lk.search_lightcurve(kic_id, mission="Kepler", author="Kepler")
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