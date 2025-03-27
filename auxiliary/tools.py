
# Contains the functions that are used in the main script
# These functions are tools for the main script and plotting functions
import numpy as np
import numba as nb
import re
from collections import defaultdict

def power_to_db(power):
    '''Convert power to dB'''
    return 10 * np.log10(power)

# coh = abs(ifgram) / np.sqrt(power_plus_y * power_minus_y)
def interf_coh(ifgram, power_plus_y, power_minus_y):
    '''Calculate the coherence of the interferogram'''
    return np.abs(ifgram) / np.sqrt(power_plus_y * power_minus_y)

def toslant(pixc, key='height'):
    '''Convert the pixel coordinates to slant range'''
    az = pixc.azimuth_index.astype(int)
    rng = pixc.range_index.astype(int)
    out = np.zeros((pixc.interferogram_size_azimuth + 1, pixc.interferogram_size_range + 1)) + np.nan
    # handle complex interferogram
    if key=='interferogram':
        out = out.astype('complex64')
        var = pixc[key][:,0] + 1j * pixc[key][:,1]
    else:
        var = pixc[key]
    out[az, rng] = var
    return out

@nb.njit('float32[:,:](int32[:], float32[:], float32[:])', parallel=True)
def noise_to_pixc_index(noise_index, noise_plus_y, noise_minus_y):
    '''Convert the noise index to the pixel coordinates'''
    noise_plus_y_pixc = np.zeros(noise_index.shape, dtype=np.float32)
    noise_minus_y_pixc = np.zeros(noise_index.shape, dtype=np.float32)
    for idx in np.unique(noise_index):
        noise_plus_y_pixc [noise_index == idx] = noise_plus_y[idx]
        noise_minus_y_pixc[noise_index == idx] = noise_minus_y[idx]
    
    # combine the two arrays
    noise_to_pixc = np.vstack((noise_plus_y_pixc, noise_minus_y_pixc))
    return noise_to_pixc

def parse_version(filename):
    """Extrait les composants de la version depuis le nom du fichier."""
    match = re.match(r"([PD])([IGO])([A-Z])(\d+)_(\d+)\.nc", filename)
    if match:
        return match.groups()  # (P/D, I/G/O, Major, Minor, Counter)
    return None

def filter_versions(filenames):
    """Filtre les versions selon les règles demandées."""
    versions = [parse_version(f) for f in filenames]
    versions = [v for v in versions if v]  # Enlever None

    # Convertir minor et counter en entiers
    versions = [(p, f, major, int(minor), int(counter)) for p, f, major, minor, counter in versions]

    # Grouper par major version
    grouped = defaultdict(list)
    for v in versions:
        grouped[v[2]].append(v)
    
    # Trouver la dernière major version (ordre alphabétique)
    last_major = max(grouped.keys())

    # Filtrer uniquement les versions de cette major
    filtered = grouped[last_major]

    # Trier selon fidélité (G > I > O)
    fidelity_order = {"G": 3, "I": 2, "O": 1}
    filtered.sort(key=lambda v: fidelity_order[v[1]], reverse=True)
    best_fidelity = filtered[0][1]
    filtered = [v for v in filtered if v[1] == best_fidelity]

    # Garder le plus grand numéro de version mineure
    max_minor = max(v[3] for v in filtered)
    filtered = [v for v in filtered if v[3] == max_minor]

    # Garder le plus grand compteur
    max_counter = max(v[4] for v in filtered)
    final_versions = [v for v in filtered if v[4] == max_counter]

    # Reformer les noms de fichiers
    return [f"{p}{f}{last_major}{m}_{str(c).zfill(2)}.nc" for p, f, _, m, c in final_versions]
