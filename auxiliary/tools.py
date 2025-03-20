
# Contains the functions that are used in the main script
# These functions are tools for the main script and plotting functions
import numpy as np
import numba as nb

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
