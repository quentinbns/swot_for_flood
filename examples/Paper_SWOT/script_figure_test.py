import os
print(os.system('ulimit -a'))
os.environ['PROJ_LIB'] = '/data/home/globc/bonassies/.conda/envs/conda3.10/share/proj'
os.sys.path.append('/data/scratch/globc/bonassies/workspace/swot_for_flood')
from shapely.geometry import shape, box
import numpy as np
import geopandas as gpd
import matplotlib
import matplotlib.colors
import matplotlib.cm as cm
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
import rasterio as rio
from rasterio import mask as rmask
from rasterio.plot import show
import datetime
import glob
from scipy.ndimage import binary_dilation, binary_erosion, binary_fill_holes
from skimage.filters.rank import majority
from skimage import morphology
from auxiliary.cbar_ESA_WC import *
from auxiliary.cbar_SWOT import *
from auxiliary.plot_variables import *
from auxiliary.tools import *

import psutil
from eomaps import Maps

cmap_ESAWC, normalizer_ESAWC, boundaries_ESAWC, ticks_ESAWC, tick_labels_ESAWC, values_ESAWC = defined_ESAWC_cmap()
cmap_SWOT, normalizer_SWOT, boundaries_SWOT, ticks_SWOT, tick_labels_SWOT, values_SWOT = defined_SWOT_cmap()

#compute xy position from transform and data
def get_xy_from_transform(transform, data):
    x = np.arange(data.shape[1]) * transform[0] + transform[2]
    y = np.arange(data.shape[0]) * transform[4] + transform[5]
    return x, y

def pretreat_data(data, size):
    data = np.where(data == 0, np.nan, data)
    data = np.where(data == -9999, np.nan, data)
    data = (data - np.nanmin(data))/(np.nanmax(data) - np.nanmin(data))
    data = majority(data, morphology.disk(size)) / 255
    data = np.where(data == 0, np.nan, data)
    data = np.where(data == -9999, np.nan, data)
    return data

if __name__ == '__main__':
    #############################################
    # Set the workspace
    data_path = "/data/scratch/globc/bonassies/data"
    workspace_path = "/data/scratch/globc/bonassies/workspace/swot_for_flood/examples"
    project =  'Paper_SWOT'
    EMSR692 = "EMSR_692"

    PROJECT_PATH = os.path.join(workspace_path, project)
    FIGS_FOLDER = os.path.join(PROJECT_PATH, 'Figs')

    EMSR692_PATH = os.path.join(workspace_path, EMSR692)
    EMSR692_raster_PATH = os.path.join(EMSR692_PATH, 'rasters')
    EMSR692_aux_PATH = os.path.join(EMSR692_PATH, 'aux_data')
    
    
    #############################################
    # Set the AOI
    ####
    file = os.path.join(EMSR692_aux_PATH, 'EMSR692_aois_V2.gpkg')
    bbox_EMSR692 = gpd.read_file(file)
    aoi2_EMSR692 = box(bbox_EMSR692.bounds['minx'][0], bbox_EMSR692.bounds['miny'][0], bbox_EMSR692.bounds['maxx'][0], bbox_EMSR692.bounds['maxy'][0])

    
    #############################################
    # Loading Aux Data

    # ------------------------------------------------
    # EMSR692
    # ------------------------------------------------
    EMSR692_list_var = ['sig0', 'coherent_power', 'incidence', 'gamma_tot', 'gamma_SNR', 'gamma_est', 'power_plus_y', 'power_minus_y',  'interf_real', 'interf_imag', 'height', 'classification', 'bright_land_flag']
    EPSG_32634 = "EPSG:32634" # EMSR692

    # Delineation
    EMSR692_TotalFlood_file = os.path.join(EMSR692_aux_PATH, "FM_watermask.gpkg")
    EMSR692_ControlArea_file = os.path.join(EMSR692_aux_PATH, "ControlArea_32634.gpkg")

    # ESA World Cover
    EMSR692_ESA_WC_file = os.path.join(EMSR692_aux_PATH, "ESA_WC_cut_V2_32634_nrow5624_ncol4610.tif")
    EMSR692_ESA_WC_file = os.path.join(EMSR692_aux_PATH, "ESA_WC_cut_V2_32634_nrow5720_ncol5917.tif")

    #FABDEM
    EMSR692_DEM = os.path.join(EMSR692_aux_PATH, "FABDEM_fusion_cut_v2_32634_10m.tif")

    # Open files
    EMSR692_mask_flooded = gpd.read_file(EMSR692_TotalFlood_file)
    EMSR692_mask_flooded = EMSR692_mask_flooded.to_crs(EPSG_32634)

    EMSR692_mask_control = gpd.read_file(EMSR692_ControlArea_file)
    EMSR692_mask_control = EMSR692_mask_control.to_crs(EPSG_32634)

    EMSR692_mask_WC = rio.open(EMSR692_ESA_WC_file, crs=EPSG_32634)
    EMSR692_mask_WC_resample, EMSR692_transform = rmask.mask(EMSR692_mask_WC, EMSR692_mask_flooded.geometry, crop=True)


    EMSR692_DEM = rio.open(EMSR692_DEM, crs=EPSG_32634)
    EMSR692_DEM_FloodArea = EMSR692_DEM.read(1, out_shape=EMSR692_mask_WC_resample[0].shape)

    # is forest
    EMSR692_forest_mask = ~(EMSR692_mask_WC_resample == 10)
    # is urban
    EMSR692_urban_mask = ~(EMSR692_mask_WC_resample == 50)
    # is not open water, not forest, not urban
    EMSR692_open_mask = ~(EMSR692_forest_mask & EMSR692_urban_mask & ~(EMSR692_mask_WC_resample == 80))
    
    #############################################
    # Set dates of interest
    EMSR692_list_dry_dates = [
        "20240410",
        "20240703",
        "20240501"
        ]
    EMSR692_list_flooded_dates = [
        "20230915T202311",
        # "20230915T070816"
        ]
    
    EMSR692_list_raster = glob.glob(os.path.join(EMSR692_raster_PATH, '*.tif'))
    EMSR692_list_raster.sort()

    EMSR692_glob_dry_rasters = [glob.glob(os.path.join(EMSR692_raster_PATH, f'*{dry_date}*.tif') )[0] for dry_date in EMSR692_list_dry_dates]
    EMSR692_glob_flooded_rasters = [glob.glob(os.path.join(EMSR692_raster_PATH, f'*{flooded_date}*.tif') )[0] for flooded_date in EMSR692_list_flooded_dates]

    EMSR692_label_flooded_date = [datetime.datetime.strptime(flooded_date.split('T')[0],'%Y%m%d') for flooded_date in EMSR692_list_flooded_dates]
    EMSR692_label_dry_date = [datetime.datetime.strptime(flooded_date,'%Y%m%d') for flooded_date in EMSR692_list_dry_dates]
    
    #############################################
    # Opening rasters
    EMSR692_dry_rasters = [rio.open(raster) for raster in EMSR692_glob_dry_rasters]
    EMSR692_flooded_rasters = [rio.open(raster) for raster in EMSR692_glob_flooded_rasters]

    EMSR692_FloodedArea_dry_rasters_masked = [rmask.mask(raster, EMSR692_mask_flooded.geometry, crop=True)[0] for raster in EMSR692_dry_rasters]
    EMSR692_FloodedArea_flooded_raster_masked = [rmask.mask(raster, EMSR692_mask_flooded.geometry, crop=True)[0] for raster in EMSR692_flooded_rasters]

    EMSR692_ControlArea_dry_rasters_masked = [rmask.mask(raster, EMSR692_mask_control.geometry, crop=True)[0] for raster in EMSR692_dry_rasters]
    EMSR692_ControlArea_flooded_raster_masked = [rmask.mask(raster, EMSR692_mask_control.geometry, crop=True)[0] for raster in EMSR692_flooded_rasters]

    # ------------------------------------------------
    # EMSR692
    # ------------------------------------------------
    # Load the dry rasters
    EMSR692_FloodArea_sig0_rasters        = np.array([raster[EMSR692_list_var.index('sig0')] for raster in EMSR692_FloodedArea_dry_rasters_masked])
    EMSR692_FloodArea_coh_rasters         = np.array([raster[EMSR692_list_var.index('coherent_power')] for raster in EMSR692_FloodedArea_dry_rasters_masked])
    EMSR692_FloodArea_gamma_tot_rasters   = np.array([raster[EMSR692_list_var.index('gamma_tot')] for raster in EMSR692_FloodedArea_dry_rasters_masked])
    EMSR692_FloodArea_gamma_SNR_rasters   = np.array([raster[EMSR692_list_var.index('gamma_SNR')] for raster in EMSR692_FloodedArea_dry_rasters_masked])
    EMSR692_FloodArea_height_rasters      = np.array([raster[EMSR692_list_var.index('height')] for raster in EMSR692_FloodedArea_dry_rasters_masked])


    EMSR692_FloodArea_sig0_rasters = np.where(EMSR692_FloodArea_sig0_rasters == -9999, np.nan, EMSR692_FloodArea_sig0_rasters)
    EMSR692_FloodArea_coh_rasters  = np.where(EMSR692_FloodArea_coh_rasters == -9999,  np.nan, EMSR692_FloodArea_coh_rasters)
    EMSR692_FloodArea_gamma_tot_rasters = np.where(EMSR692_FloodArea_gamma_tot_rasters == -9999, np.nan, EMSR692_FloodArea_gamma_tot_rasters)
    EMSR692_FloodArea_gamma_SNR_rasters = np.where(EMSR692_FloodArea_gamma_SNR_rasters == -9999, np.nan, EMSR692_FloodArea_gamma_SNR_rasters)
    EMSR692_FloodArea_height_rasters = np.where(EMSR692_FloodArea_height_rasters == -9999, np.nan, EMSR692_FloodArea_height_rasters)

    EMSR692_FloodArea_sig0_rasters = np.where(EMSR692_FloodArea_sig0_rasters == 0, np.nan, EMSR692_FloodArea_sig0_rasters)
    EMSR692_FloodArea_coh_rasters  = np.where(EMSR692_FloodArea_coh_rasters == 0,  np.nan, EMSR692_FloodArea_coh_rasters)
    EMSR692_FloodArea_gamma_tot_rasters = np.where(EMSR692_FloodArea_gamma_tot_rasters == 0, np.nan, EMSR692_FloodArea_gamma_tot_rasters)
    EMSR692_FloodArea_gamma_SNR_rasters = np.where(EMSR692_FloodArea_gamma_SNR_rasters == 0, np.nan, EMSR692_FloodArea_gamma_SNR_rasters)
    EMSR692_FloodArea_height_rasters = np.where(EMSR692_FloodArea_height_rasters == 0, np.nan, EMSR692_FloodArea_height_rasters)

    EMSR692_FloodArea_mean_dry_sig0 = np.nanmean(EMSR692_FloodArea_sig0_rasters, axis=0)
    EMSR692_FloodArea_mean_dry_coh  = np.nanmean(EMSR692_FloodArea_coh_rasters, axis=0)
    EMSR692_FloodArea_mean_dry_gamma_tot = np.nanmean(EMSR692_FloodArea_gamma_tot_rasters, axis=0)
    EMSR692_FloodArea_mean_dry_gamma_SNR = np.nanmean(EMSR692_FloodArea_gamma_SNR_rasters, axis=0)
    EMSR692_FloodArea_mean_dry_height = np.nanmean(EMSR692_FloodArea_height_rasters, axis=0)
    EMSR692_FloodArea_mean_dry_gamma_est = EMSR692_FloodArea_mean_dry_gamma_tot / EMSR692_FloodArea_mean_dry_gamma_SNR


    EMSR692_ControlArea_sig0_rasters        = np.array([raster[EMSR692_list_var.index('sig0')] for raster in EMSR692_ControlArea_dry_rasters_masked])
    EMSR692_ControlArea_coh_rasters         = np.array([raster[EMSR692_list_var.index('coherent_power')] for raster in EMSR692_ControlArea_dry_rasters_masked])
    EMSR692_ControlArea_gamma_tot_rasters   = np.array([raster[EMSR692_list_var.index('gamma_tot')] for raster in EMSR692_ControlArea_dry_rasters_masked])
    EMSR692_ControlArea_gamma_SNR_rasters   = np.array([raster[EMSR692_list_var.index('gamma_SNR')] for raster in EMSR692_ControlArea_dry_rasters_masked])
    EMSR692_ControlArea_height_rasters      = np.array([raster[EMSR692_list_var.index('height')] for raster in EMSR692_ControlArea_dry_rasters_masked])


    EMSR692_ControlArea_sig0_rasters = np.where(EMSR692_ControlArea_sig0_rasters == -9999, np.nan, EMSR692_ControlArea_sig0_rasters)
    EMSR692_ControlArea_coh_rasters  = np.where(EMSR692_ControlArea_coh_rasters == -9999,  np.nan, EMSR692_ControlArea_coh_rasters)
    EMSR692_ControlArea_gamma_tot_rasters = np.where(EMSR692_ControlArea_gamma_tot_rasters == -9999, np.nan, EMSR692_ControlArea_gamma_tot_rasters)
    EMSR692_ControlArea_gamma_SNR_rasters = np.where(EMSR692_ControlArea_gamma_SNR_rasters == -9999, np.nan, EMSR692_ControlArea_gamma_SNR_rasters)
    EMSR692_ControlArea_height_rasters = np.where(EMSR692_ControlArea_height_rasters == -9999, np.nan, EMSR692_ControlArea_height_rasters)

    EMSR692_ControlArea_sig0_rasters = np.where(EMSR692_ControlArea_sig0_rasters == 0, np.nan, EMSR692_ControlArea_sig0_rasters)
    EMSR692_ControlArea_coh_rasters  = np.where(EMSR692_ControlArea_coh_rasters == 0,  np.nan, EMSR692_ControlArea_coh_rasters)
    EMSR692_ControlArea_gamma_tot_rasters = np.where(EMSR692_ControlArea_gamma_tot_rasters == 0, np.nan, EMSR692_ControlArea_gamma_tot_rasters)
    EMSR692_ControlArea_gamma_SNR_rasters = np.where(EMSR692_ControlArea_gamma_SNR_rasters == 0, np.nan, EMSR692_ControlArea_gamma_SNR_rasters)
    EMSR692_ControlArea_height_rasters = np.where(EMSR692_ControlArea_height_rasters == 0, np.nan, EMSR692_ControlArea_height_rasters)

    EMSR692_ControlArea_mean_dry_sig0 = np.nanmean(EMSR692_ControlArea_sig0_rasters, axis=0)
    EMSR692_ControlArea_mean_dry_coh  = np.nanmean(EMSR692_ControlArea_coh_rasters, axis=0)
    EMSR692_ControlArea_mean_dry_gamma_tot = np.nanmean(EMSR692_ControlArea_gamma_tot_rasters, axis=0)
    EMSR692_ControlArea_mean_dry_gamma_SNR = np.nanmean(EMSR692_ControlArea_gamma_SNR_rasters, axis=0)
    EMSR692_ControlArea_mean_dry_height = np.nanmean(EMSR692_ControlArea_height_rasters, axis=0)
    EMSR692_ControlArea_mean_dry_gamma_est = EMSR692_ControlArea_mean_dry_gamma_tot / EMSR692_ControlArea_mean_dry_gamma_SNR


    # Load the flooded raster
    EMSR692_FloodArea_flooded_sig0         = np.array([raster[EMSR692_list_var.index('sig0')] for raster in EMSR692_FloodedArea_flooded_raster_masked])
    EMSR692_FloodArea_flooded_coh          = np.array([raster[EMSR692_list_var.index('coherent_power')] for raster in EMSR692_FloodedArea_flooded_raster_masked])
    EMSR692_FloodArea_flooded_gamma_tot    = np.array([raster[EMSR692_list_var.index('gamma_tot')] for raster in EMSR692_FloodedArea_flooded_raster_masked])
    EMSR692_FloodArea_flooded_gamma_SNR    = np.array([raster[EMSR692_list_var.index('gamma_SNR')] for raster in EMSR692_FloodedArea_flooded_raster_masked])
    EMSR692_FloodArea_flooded_height       = np.array([raster[EMSR692_list_var.index('height')] for raster in EMSR692_FloodedArea_flooded_raster_masked])

    EMSR692_FloodArea_flooded_sig0 = np.where(EMSR692_FloodArea_flooded_sig0 == -9999, np.nan, EMSR692_FloodArea_flooded_sig0)
    EMSR692_FloodArea_flooded_coh  = np.where(EMSR692_FloodArea_flooded_coh == -9999, np.nan,EMSR692_FloodArea_flooded_coh)
    EMSR692_FloodArea_flooded_gamma_tot = np.where(EMSR692_FloodArea_flooded_gamma_tot == -9999, np.nan, EMSR692_FloodArea_flooded_gamma_tot)
    EMSR692_FloodArea_flooded_gamma_SNR = np.where(EMSR692_FloodArea_flooded_gamma_SNR == -9999, np.nan, EMSR692_FloodArea_flooded_gamma_SNR)
    EMSR692_FloodArea_flooded_height = np.where(EMSR692_FloodArea_flooded_height == -9999, np.nan, EMSR692_FloodArea_flooded_height)

    EMSR692_FloodArea_flooded_sig0 = np.where(EMSR692_FloodArea_flooded_sig0 == 0, np.nan, EMSR692_FloodArea_flooded_sig0)
    EMSR692_FloodArea_flooded_coh  = np.where(EMSR692_FloodArea_flooded_coh == 0, np.nan, EMSR692_FloodArea_flooded_coh)
    EMSR692_FloodArea_flooded_gamma_tot = np.where(EMSR692_FloodArea_flooded_gamma_tot == 0, np.nan, EMSR692_FloodArea_flooded_gamma_tot)
    EMSR692_FloodArea_flooded_gamma_SNR = np.where(EMSR692_FloodArea_flooded_gamma_SNR == 0, np.nan, EMSR692_FloodArea_flooded_gamma_SNR)
    EMSR692_FloodArea_flooded_height = np.where(EMSR692_FloodArea_flooded_height == 0, np.nan, EMSR692_FloodArea_flooded_height)

    EMSR692_FloodArea_flooded_gamma_est = EMSR692_FloodArea_flooded_gamma_tot / EMSR692_FloodArea_flooded_gamma_SNR
    EMSR692_FloodArea_flooded_sig0 = np.log10(EMSR692_FloodArea_flooded_sig0) * 10
    EMSR692_FloodArea_mean_dry_sig0 = np.log10(EMSR692_FloodArea_mean_dry_sig0) * 10
    EMSR692_FloodArea_flooded_coh = np.log10(EMSR692_FloodArea_flooded_coh) * 10
    EMSR692_FloodArea_mean_dry_coh = np.log10(EMSR692_FloodArea_mean_dry_coh) * 10

    EMSR692_ControlArea_flooded_sig0         = np.array([raster[EMSR692_list_var.index('sig0')] for raster in EMSR692_ControlArea_flooded_raster_masked])
    EMSR692_ControlArea_flooded_coh          = np.array([raster[EMSR692_list_var.index('coherent_power')] for raster in EMSR692_ControlArea_flooded_raster_masked])
    EMSR692_ControlArea_flooded_gamma_tot    = np.array([raster[EMSR692_list_var.index('gamma_tot')] for raster in EMSR692_ControlArea_flooded_raster_masked])
    EMSR692_ControlArea_flooded_gamma_SNR    = np.array([raster[EMSR692_list_var.index('gamma_SNR')] for raster in EMSR692_ControlArea_flooded_raster_masked])
    EMSR692_ControlArea_flooded_height       = np.array([raster[EMSR692_list_var.index('height')] for raster in EMSR692_ControlArea_flooded_raster_masked])

    EMSR692_ControlArea_flooded_sig0 = np.where(EMSR692_ControlArea_flooded_sig0 == -9999, np.nan, EMSR692_ControlArea_flooded_sig0)
    EMSR692_ControlArea_flooded_coh  = np.where(EMSR692_ControlArea_flooded_coh == -9999, np.nan,EMSR692_ControlArea_flooded_coh)
    EMSR692_ControlArea_flooded_gamma_tot = np.where(EMSR692_ControlArea_flooded_gamma_tot == -9999, np.nan, EMSR692_ControlArea_flooded_gamma_tot)
    EMSR692_ControlArea_flooded_gamma_SNR = np.where(EMSR692_ControlArea_flooded_gamma_SNR == -9999, np.nan, EMSR692_ControlArea_flooded_gamma_SNR)
    EMSR692_ControlArea_flooded_height = np.where(EMSR692_ControlArea_flooded_height == -9999, np.nan, EMSR692_ControlArea_flooded_height)

    EMSR692_ControlArea_flooded_sig0 = np.where(EMSR692_ControlArea_flooded_sig0 == 0, np.nan, EMSR692_ControlArea_flooded_sig0)
    EMSR692_ControlArea_flooded_coh  = np.where(EMSR692_ControlArea_flooded_coh == 0, np.nan, EMSR692_ControlArea_flooded_coh)
    EMSR692_ControlArea_flooded_gamma_tot = np.where(EMSR692_ControlArea_flooded_gamma_tot == 0, np.nan, EMSR692_ControlArea_flooded_gamma_tot)
    EMSR692_ControlArea_flooded_gamma_SNR = np.where(EMSR692_ControlArea_flooded_gamma_SNR == 0, np.nan, EMSR692_ControlArea_flooded_gamma_SNR)
    EMSR692_ControlArea_flooded_height = np.where(EMSR692_ControlArea_flooded_height == 0, np.nan, EMSR692_ControlArea_flooded_height)

    EMSR692_ControlArea_flooded_gamma_est = EMSR692_ControlArea_flooded_gamma_tot / EMSR692_ControlArea_flooded_gamma_SNR
    EMSR692_ControlArea_flooded_sig0 = np.log10(EMSR692_ControlArea_flooded_sig0) * 10
    EMSR692_ControlArea_mean_dry_sig0 = np.log10(EMSR692_ControlArea_mean_dry_sig0) * 10
    EMSR692_ControlArea_flooded_coh = np.log10(EMSR692_ControlArea_flooded_coh) * 10
    EMSR692_ControlArea_mean_dry_coh = np.log10(EMSR692_ControlArea_mean_dry_coh) * 10

    # apply WC mask
    EMSR692_forest_flooded_sig0 = np.where(EMSR692_forest_mask, np.nan, EMSR692_FloodArea_flooded_sig0)
    EMSR692_forest_flooded_coh = np.where(EMSR692_forest_mask, np.nan, EMSR692_FloodArea_flooded_coh)
    EMSR692_forest_flooded_gamma_tot = np.where(EMSR692_forest_mask, np.nan, EMSR692_FloodArea_flooded_gamma_tot)
    EMSR692_forest_flooded_gamma_SNR = np.where(EMSR692_forest_mask, np.nan, EMSR692_FloodArea_flooded_gamma_SNR)
    EMSR692_forest_flooded_gamma_est = np.where(EMSR692_forest_mask, np.nan, EMSR692_FloodArea_flooded_gamma_est)
    EMSR692_forest_flooded_height = np.where(EMSR692_forest_mask, np.nan, EMSR692_FloodArea_flooded_height)

    EMSR692_forest_mean_dry_sig0 = np.where(EMSR692_forest_mask, np.nan, EMSR692_FloodArea_mean_dry_sig0)
    EMSR692_forest_mean_dry_coh = np.where(EMSR692_forest_mask, np.nan, EMSR692_FloodArea_mean_dry_coh)
    EMSR692_forest_mean_dry_gamma_tot = np.where(EMSR692_forest_mask, np.nan, EMSR692_FloodArea_mean_dry_gamma_tot)
    EMSR692_forest_mean_dry_gamma_SNR = np.where(EMSR692_forest_mask, np.nan, EMSR692_FloodArea_mean_dry_gamma_SNR)
    EMSR692_forest_mean_dry_gamma_est = np.where(EMSR692_forest_mask, np.nan, EMSR692_FloodArea_mean_dry_gamma_est)
    EMSR692_forest_mean_dry_height = np.where(EMSR692_forest_mask, np.nan, EMSR692_FloodArea_mean_dry_height)

    # apply WC mask
    EMSR692_urban_flooded_sig0 = np.where(EMSR692_urban_mask, np.nan, EMSR692_FloodArea_flooded_sig0)
    EMSR692_urban_flooded_coh = np.where(EMSR692_urban_mask, np.nan, EMSR692_FloodArea_flooded_coh)
    EMSR692_urban_flooded_gamma_tot = np.where(EMSR692_urban_mask, np.nan, EMSR692_FloodArea_flooded_gamma_tot)
    EMSR692_urban_flooded_gamma_SNR = np.where(EMSR692_urban_mask, np.nan, EMSR692_FloodArea_flooded_gamma_SNR)
    EMSR692_urban_flooded_gamma_est = np.where(EMSR692_urban_mask, np.nan, EMSR692_FloodArea_flooded_gamma_est)
    EMSR692_urban_flooded_height = np.where(EMSR692_urban_mask, np.nan, EMSR692_FloodArea_flooded_height)

    EMSR692_urban_mean_dry_sig0 = np.where(EMSR692_urban_mask, np.nan, EMSR692_FloodArea_mean_dry_sig0)
    EMSR692_urban_mean_dry_coh = np.where(EMSR692_urban_mask, np.nan, EMSR692_FloodArea_mean_dry_coh)
    EMSR692_urban_mean_dry_gamma_tot = np.where(EMSR692_urban_mask, np.nan, EMSR692_FloodArea_mean_dry_gamma_tot)
    EMSR692_urban_mean_dry_gamma_SNR = np.where(EMSR692_urban_mask, np.nan, EMSR692_FloodArea_mean_dry_gamma_SNR)
    EMSR692_urban_mean_dry_gamma_est = np.where(EMSR692_urban_mask, np.nan, EMSR692_FloodArea_mean_dry_gamma_est)
    EMSR692_urban_mean_dry_height = np.where(EMSR692_urban_mask, np.nan, EMSR692_FloodArea_mean_dry_height)

    # apply WC mask
    EMSR692_open_flooded_sig0 = np.where(EMSR692_open_mask, np.nan, EMSR692_FloodArea_flooded_sig0)
    EMSR692_open_flooded_coh = np.where(EMSR692_open_mask, np.nan, EMSR692_FloodArea_flooded_coh)
    EMSR692_open_flooded_gamma_tot = np.where(EMSR692_open_mask, np.nan, EMSR692_FloodArea_flooded_gamma_tot)
    EMSR692_open_flooded_gamma_SNR = np.where(EMSR692_open_mask, np.nan, EMSR692_FloodArea_flooded_gamma_SNR)
    EMSR692_open_flooded_gamma_est = np.where(EMSR692_open_mask, np.nan, EMSR692_FloodArea_flooded_gamma_est)
    EMSR692_open_flooded_height = np.where(EMSR692_open_mask, np.nan, EMSR692_FloodArea_flooded_height)

    EMSR692_open_mean_dry_sig0 = np.where(EMSR692_open_mask, np.nan, EMSR692_FloodArea_mean_dry_sig0)
    EMSR692_open_mean_dry_coh = np.where(EMSR692_open_mask, np.nan, EMSR692_FloodArea_mean_dry_coh)
    EMSR692_open_mean_dry_gamma_tot = np.where(EMSR692_open_mask, np.nan, EMSR692_FloodArea_mean_dry_gamma_tot)
    EMSR692_open_mean_dry_gamma_SNR = np.where(EMSR692_open_mask, np.nan, EMSR692_FloodArea_mean_dry_gamma_SNR)
    EMSR692_open_mean_dry_gamma_est = np.where(EMSR692_open_mask, np.nan, EMSR692_FloodArea_mean_dry_gamma_est)
    EMSR692_open_mean_dry_height = np.where(EMSR692_open_mask, np.nan, EMSR692_FloodArea_mean_dry_height)
    
    
    #############################################
    # Pretreat for plotting
    print("opening flooded")
    EMSR692_flooded_rasters = [rio.open(f) for f in EMSR692_glob_flooded_rasters]
    print("opening dry")
    EMSR692_dry_rasters = [rio.open(f) for f in EMSR692_glob_dry_rasters]
    print(EMSR692_flooded_rasters)

    print(psutil.virtual_memory().available * 100 / psutil.virtual_memory().total)

    print("reading flooded")
    EMSR692_flooded_gamma_tot = [reader.read(EMSR692_list_var.index('gamma_tot')+1) for reader in EMSR692_flooded_rasters]
    print("reading dry")
    EMSR692_dry_gamma_tot = [reader.read(EMSR692_list_var.index('gamma_tot')+1) for reader in EMSR692_dry_rasters]


    print("Memory available:", psutil.virtual_memory().available * 100 / psutil.virtual_memory().total)

    print("treat flooded")
    EMSR692_flooded_gamma_tot = np.where(EMSR692_flooded_gamma_tot == 0, np.nan, EMSR692_flooded_gamma_tot)
    EMSR692_flooded_gamma_tot = np.where(EMSR692_flooded_gamma_tot == -9999, np.nan, EMSR692_flooded_gamma_tot)

    print("Memory available:", psutil.virtual_memory().available * 100 / psutil.virtual_memory().total)

    print("treat dry")
    print("Memory available:", psutil.virtual_memory().available * 100 / psutil.virtual_memory().total)
    for i in range(len(EMSR692_dry_gamma_tot)):
        EMSR692_dry_gamma_tot[i] = np.where(EMSR692_dry_gamma_tot[i] == 0, np.nan, EMSR692_dry_gamma_tot[i])
        EMSR692_dry_gamma_tot[i] = np.where(EMSR692_dry_gamma_tot[i] == -9999, np.nan, EMSR692_dry_gamma_tot[i])
        print("Memory available:", psutil.virtual_memory().available * 100 / psutil.virtual_memory().total)
        print(np.unique(EMSR692_dry_gamma_tot[i]))
    
    np.save('badeguy.npy', EMSR692_dry_gamma_tot)
    
    print("mean dry", flush=True)
    print("Memory available:", psutil.virtual_memory().available * 100 / psutil.virtual_memory().total)
    EMSR692_dry_mean_gamma_tot = np.nanmean(EMSR692_dry_gamma_tot, axis=0)
    del EMSR692_dry_gamma_tot

    print("WC open and treat", flush=True)
    print(1)
    EMSR_WC = rio.open(EMSR692_ESA_WC_file, crs=EPSG_32634)
    print(2)
    print(EMSR_WC, flush=True)
    EMSR_WC_trfm = EMSR_WC.transform
    EMSR_WC = EMSR_WC.read(1)
    print(EMSR_WC.shape, flush=True)
    print(EMSR_WC_trfm, flush=True)

    all_EMSR692_forest_mask = (EMSR_WC == 10)
    print(np.unique(all_EMSR692_forest_mask), flush=True)
    all_EMSR692_urban_mask = (EMSR_WC == 50)
    print(np.unique(all_EMSR692_urban_mask), flush=True)
    all_EMSR692_open_mask = (~all_EMSR692_forest_mask & ~all_EMSR692_urban_mask & ~(EMSR_WC == 80))
    print(np.unique(all_EMSR692_open_mask), flush=True)

    del EMSR_WC

    print("mask data flooded", flush=True)
    EMSR692_flooded_gamma_tot_urban = np.where(all_EMSR692_urban_mask, EMSR692_flooded_gamma_tot[0], np.nan)
    EMSR692_flooded_gamma_tot_forest = np.where(all_EMSR692_forest_mask, EMSR692_flooded_gamma_tot[0], np.nan)
    EMSR692_flooded_gamma_tot_open = np.where(all_EMSR692_open_mask, EMSR692_flooded_gamma_tot[0], np.nan)

    print("mask data dry")
    EMSR692_dry_mean_gamma_tot_urban = np.where(all_EMSR692_urban_mask, EMSR692_dry_mean_gamma_tot, np.nan)
    EMSR692_dry_mean_gamma_tot_forest = np.where(all_EMSR692_forest_mask, EMSR692_dry_mean_gamma_tot, np.nan)
    EMSR692_dry_mean_gamma_tot_open = np.where(all_EMSR692_open_mask, EMSR692_dry_mean_gamma_tot, np.nan)


    print("Memory available:", psutil.virtual_memory().available * 100 / psutil.virtual_memory().total)
    
    #############################################
    # Plotting

    fig, axs = plt.subplots(3, 3, figsize=(10, 10))
    index_raster = 0

    diff_open = EMSR692_flooded_gamma_tot_open[index_raster] - EMSR692_dry_mean_gamma_tot_open
    # axs[2, 0].hist(EMSR692_open_mean_dry_gamma_tot.flatten(), bins=100, alpha=0.5, label='Dry mean', color='red', range=(0,1))
    # axs[2, 0].axvline(np.nanmedian(EMSR692_open_mean_dry_gamma_tot), color='red', linestyle='dashed', linewidth=1)
    axs[2, 0].hist(diff_open.flatten(), bins=100, alpha=0.5, label=f'difference {EMSR692_label_flooded_date[index_raster].strftime("%d-%m-%Y")} - dry mean', color='green', range=(-1,1))
    axs[2, 0].axvline(np.nanmedian(diff_open), color='green', linestyle='dashed', linewidth=1)
    axs[2, 0].axvline(0.15, color='black', linewidth=1)
    # axs[2, 0].axvline(-0.2, color='black', linewidth=1)
    axs[2, 0].plot([],[], color='grey', linestyle='dashed', linewidth=1, label='Medians')
    axs[2, 0].plot([],[], color='black', linewidth=1, label='Threshold')
    # axs[2, 0].legend()
    axs[2, 0].set_xlabel(LABEL_GAMMA_TOT)
    axs[2, 0].set_title('Open Areas')

    diff_forest = EMSR692_flooded_gamma_tot_forest[index_raster] - EMSR692_dry_mean_gamma_tot_forest
    # axs[2, 1].hist(EMSR692_forest_mean_dry_gamma_tot.flatten(), bins=100, alpha=0.5, label='Dry', color='red', range=(0,1))
    # axs[2, 1].axvline(np.nanmedian(EMSR692_forest_mean_dry_gamma_tot), color='red', linestyle='dashed', linewidth=1)
    axs[2, 1].hist(diff_forest.flatten(), bins=100, alpha=0.5, label=f'Flooded', color='green', range=(-1,1))
    axs[2, 1].axvline(np.nanmedian(diff_forest), color='green', linestyle='dashed', linewidth=1)
    axs[2, 1].axvline(0.15, color='black', linewidth=1)
    axs[2, 1].set_xlabel(LABEL_GAMMA_TOT)
    axs[2, 1].set_title('Forest Areas')

    diff_urban = EMSR692_flooded_gamma_tot_urban[index_raster] - EMSR692_dry_mean_gamma_tot_urban
    axs[2, 2].hist(diff_urban.flatten(), bins=100, alpha=0.5, label='Difference between dry and flooded', color='green', range=(-1,1))
    axs[2, 2].axvline(np.nanmedian(diff_urban), color='green', linestyle='dashed', linewidth=1)
    axs[2, 2].axvline(-0.1, color='black', linewidth=1)
    axs[2, 2].plot([],[], color='black', linewidth=1, label='Threshold')
    axs[2, 2].set_xlabel(LABEL_GAMMA_TOT)
    axs[2, 2].set_title('Urban Areas')

    axs[0, 0].set_visible(False)
    axs[0, 1].set_visible(False)
    axs[0, 2].set_visible(False)
    axs[1, 0].set_visible(False)
    axs[1, 1].set_visible(False)
    axs[1, 2].set_visible(False)


    gs = axs[0, 0].get_gridspec()
    for axx in axs[:2,:].flatten():
        axx.remove()

    ############################################################################################################
    # Base Maps
    m = Maps(crs=EPSG_32634,f=fig, ax=(3, 3, (1, 6)))

    xmin, ymin, xmax, ymax = aoi2_EMSR692.bounds
    buffer = 0.0

    m.set_extent(extents=[xmin-buffer, xmax+buffer, ymin-buffer, ymax+buffer], crs=4326)
    g = m.add_gridlines(lw=0.25, alpha=0.5, zorder=0)
    gl = g.add_labels(fontsize=8, every = 2)
    c = m.add_compass(style='compass', pos=(0.9, 0.85), scale=7)
    # sc = m.add_scalebar()


    ############################################################################################################
    # S2 DATA
    # m_bkg = m.new_layer()
    # file = '/data/scratch/globc/bonassies/workspace/swot_for_flood/examples/Paper_SWOT/S2A/S2A_merged_32722_20240506T131349.tif'
    # S2_file = rio.open(file)
    # S2_trfm = S2_file.transform
    # show(S2_file,transform=S2_trfm, ax=m_bkg.ax)


    ############################################################################################################
    # Flood MASK
    m_data = m.new_layer()

    mask_open = diff_open > 0.15
    mask_forest = diff_forest > 0.15
    mask_urban = diff_urban < -0.1
    global_mask = (mask_open | mask_forest | mask_urban )*1.

    # global_mask[global_mask == 0] = np.nan
    # x, y = get_xy_from_transform(EMSR692_WC_tfrm, global_mask)
    x, y = get_xy_from_transform(EMSR692_transform, global_mask)

    mask_holes = (global_mask == 0)*1

    # footprint = morphology.disk(2)
    # res = morphology.white_tophat(global_mask[0], footprint) 
    # mask_intersection = binary_erosion(global_mask[0] - res, structure=morphology.disk(2)).astype(float)
    # mask_intersection = binary_dilation(mask_intersection,structure=morphology.disk(2)).astype(float)
    # mask_intersection = np.where(mask_holes == 1, np.nan, mask_intersection)
    # print(mask_intersection.shape, x.shape, y.shape)

    global_mask[global_mask==0] = np.nan

    m_data.set_data(EMSR692_flooded_gamma_tot[index_raster].T, x, y, crs=EPSG_32634, parameter=LABEL_GAMMA_TOT)
    m_data.set_shape.raster()

    m_data.plot_map(vmin=0, vmax=1, cmap='magma')

    m_data.savefig('/data/scratch/globc/bonassies/workspace/swot_for_flood/examples/Paper_SWOT/Figs/EMSR692_gamma_tot.png', dpi=300)


    ############################################################################################################
    # SNR MASK
    # m_mask = m.new_layer()
    # mask_SNR = EMSR692_open_flooded_gamma_SNR[index_raster]<0.5
    # mask_SNR = mask_SNR*1.
    # mask_SNR[mask_SNR == 0] = np.nan
    # print(np.unique(mask_SNR))
    # m_mask.set_data(mask_SNR.T, x,y, crs=EPSG_32634, parameter=LABEL_GAMMA_TOT)
    # m_mask.plot_map(cmap='autumn', alpha=1)

    # m_mask.show()