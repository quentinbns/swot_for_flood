from pathlib import Path
from typing import List, Tuple
from datetime import datetime
import numpy as np
import geopandas as gdp
import rioxarray as rxr
import xarray as xr
from shapely.geometry import LineString
import seaborn as sns
import matplotlib.pyplot as plt
from scipy.ndimage import binary_dilation, binary_erosion
from skimage import morphology
from skimage.filters.rank import majority
from auxiliary.tools import ufunc_where, power_to_db

CONDITIONS_WORLDCOVER = {
    "urban": 50,
    "forest": 10,
    "permanent_water": 80
}

class SwotRaster():
    """Class to handle SWOT Raster data"""
    def __init__(
        self,
        path_to_swot_raster:Path,
        variables: List[str],
        AOI: gdp.GeoDataFrame,
        floodmask:gdp.GeoDataFrame=None,
        controlmask:gdp.GeoDataFrame=None,
        ESA_WC_PATH:Path=None,
        raster_crs:str='EPSG:4326'
        ) -> None:
        self.PATH_TO_SWOT_RASTER = path_to_swot_raster
        self.variables = variables
        self.AOI = AOI
        self.raster_crs = raster_crs
        self.controlmask = controlmask
        self.floodmask = floodmask
        self.ESA_WC_PATH = ESA_WC_PATH
        
        self.time = datetime.strptime(self.PATH_TO_SWOT_RASTER.name.split('_')[-2], "%Y%m%dT%H%M%S")
        
        self.SWOT_RASTER : xr.DataArray = None
        self.SWOT_CONTROL_MASK : xr.DataArray = None
        self.SWOT_FLOOD_MASK : xr.DataArray = None
        self.ESA_WC : xr.DataArray = None
        self.ESA_WC_CONTROL : xr.DataArray = None
        self.ESA_WC_FLOOD : xr.DataArray = None
        self.MASK_HOLES : xr.DataArray = None
        self.MASK_HOLES_CONTROL : xr.DataArray = None
        self.MASK_HOLES_FLOOD : xr.DataArray = None
        self.mask_urban_global : xr.DataArray = None
        self.mask_forest_global : xr.DataArray = None
        self.mask_open_global : xr.DataArray = None
        self.mask_urban_control : xr.DataArray = None
        self.mask_forest_control : xr.DataArray = None
        self.mask_open_control : xr.DataArray = None
        self.mask_urban_flood : xr.DataArray = None
        self.mask_forest_flood : xr.DataArray = None
        self.mask_open_flood : xr.DataArray = None

    
    def __getattribute__(self, name):
        """ Get the attribute of the class """
        if name in super(SwotRaster, self).__getattribute__("variables"):
            return super(SwotRaster, self).__getattribute__("get_swot_variable")(name)
        return super(SwotRaster, self).__getattribute__(name)
    
    def read_raster(self):
        """ Read the raster data and pretreat it"""
        self.read_swot_raster()
        self.clip_swot_raster()
    
        self.read_worldcover()
        self.clip_worldcover()
        self.make_mask_worldcover()
    
    def pretreat_raster(self):
        """ Pretreat the raster data by putting nodata values to nan and 0 values """
        self.MASK_HOLES = np.logical_or(self.SWOT_RASTER[self.variables[0]] == -9999, self.SWOT_RASTER[self.variables[0]] == 0)
        self.SWOT_RASTER = self.SWOT_RASTER.where(self.SWOT_RASTER != -9999)
        self.SWOT_RASTER = self.SWOT_RASTER.where(self.SWOT_RASTER != 0)
        
    def normalize_raster(self, data, size):
        """ Normalize the raster data by using the majority filter """
        values = self.SWOT_RASTER[data].values
        values = (values - np.nanmin(values))/(np.nanmax(values) - np.nanmin(values))
        values = majority(values, morphology.disk(size)) / 255
        values = np.where(values == 0, np.nan, values)
        values = np.where(values == -9999, np.nan, values)
        
        self.SWOT_RASTER[data].values = values
    
    def read_swot_raster(self):
        """ Read the SWOT raster data and pretreat it
        """
        self.SWOT_RASTER = rxr.open_rasterio(self.PATH_TO_SWOT_RASTER, chunks=500, variable=self.variables, band_as_variable=True, nodata=-9999)
        self.SWOT_RASTER.rio.write_crs(self.raster_crs, inplace=True)
        
        # Rename the bands
        dict_name = {}
        for length in range(len(self.variables)):
            name_band = "band_" + str(length + 1)
            dict_name[name_band] = self.variables[length]
        self.SWOT_RASTER = self.SWOT_RASTER.rename(dict_name)
        
        # remove nodata values
        self.pretreat_raster()
        
        # add time as a dimension
        self.SWOT_RASTER = self.SWOT_RASTER.expand_dims(time=[self.time])
           
    def clip_swot_raster(self):
        """ Clip the SWOT raster data to the AOI """
        self.SWOT_CONTROL_MASK : xr.DataArray = None
        self.SWOT_FLOOD_MASK : xr.DataArray = None
        if self.controlmask is not None:
            self.controlmask = self.controlmask.to_crs(self.raster_crs)
            self.SWOT_CONTROL_MASK = self.SWOT_RASTER.rio.clip(self.controlmask.geometry)
            self.MASK_HOLES_CONTROL = self.MASK_HOLES.rio.clip(self.controlmask.geometry)
        if self.floodmask is not None:
            self.floodmask = self.floodmask.to_crs(self.raster_crs)
            self.SWOT_FLOOD_MASK = self.SWOT_RASTER.rio.clip(self.floodmask.geometry)
            self.MASK_HOLES_FLOOD = self.MASK_HOLES.rio.clip(self.floodmask.geometry)
    
    def clip_worldcover(self):
        """ Clip the world cover data to the AOI """
        self.ESA_WC_CONTROL = None
        self.ESA_WC_FLOOD = None
        if self.controlmask is not None:
            self.controlmask = self.controlmask.to_crs(self.raster_crs)
            self.ESA_WC_CONTROL = self.ESA_WC.rio.clip(self.controlmask.geometry)
        if self.floodmask is not None:
            self.floodmask = self.floodmask.to_crs(self.raster_crs)
            self.ESA_WC_FLOOD = self.ESA_WC.rio.clip(self.floodmask.geometry)
    
    def get_swot_variable(self, variable:str):
        """ Get the SWOT variable from the SWOT Raster data
        
        Args:
            variable (str): the variable to get from the SWOT Raster data
            
        Returns:
            xarray.DataArray: the variable from the SWOT Raster data
        """
        if variable not in self.variables:
            raise ValueError(f"Variable {variable} not in the list of variables")
        return self.SWOT_RASTER[variable]
        
    def read_worldcover(self):
        """ Read the world cover data and pretreat it
        """
        if self.ESA_WC_PATH is None:
            raise ValueError("No path to the world cover data")
        self.ESA_WC = rxr.open_rasterio(self.ESA_WC_PATH, band_as_variable=True, chunks=500)
        self.ESA_WC.rio.write_crs(self.raster_crs, inplace=True)
    
    @staticmethod
    def check_dims(data1, data2):
        """ Check if the dimensions of two data are the same
        
        Args:
            data1 (xarray.DataArray): the first data
            data2 (xarray.DataArray): the second data
            
        Returns:
            bool: True if the dimensions are the same, False otherwise
        """
        if data1.sizes["x"] != data2.sizes["x"]:
            print(f"Dimension x of data1: {data1.sizes['x']} and dimension x of data2: {data2.sizes['x']}")
            return False
        if data1.sizes["y"] != data2.sizes["y"]:
            print(f"Dimension y of data1: {data1.sizes['y']} and dimension y of data2: {data2.sizes['y']}")
            return False
        return True
    
    @staticmethod
    def mask_worldcover(WC_array:xr.Dataset, SWOT_array:xr.Dataset)->Tuple[xr.Dataset, xr.Dataset, xr.Dataset]:
        """ Mask SWOT data with the world cover data """
        condition_urban = WC_array['band_1'].values == CONDITIONS_WORLDCOVER["urban"]
        condition_forest = WC_array['band_1'].values == CONDITIONS_WORLDCOVER["forest"]
        condition_permanent_water = WC_array['band_1'].values == CONDITIONS_WORLDCOVER["permanent_water"]
        condition_open = np.logical_and(~ condition_forest,
            np.logical_and(
                ~ condition_urban,
                ~ condition_permanent_water)
            )
        SWOT_urban = xr.apply_ufunc(ufunc_where, SWOT_array, condition_urban, dask='parallelized')
        SWOT_forest = xr.apply_ufunc(ufunc_where, SWOT_array, condition_forest, dask='parallelized')
        SWOT_open = xr.apply_ufunc(ufunc_where, SWOT_array, condition_open, dask='parallelized')
        return SWOT_urban, SWOT_forest, SWOT_open
    
    def make_mask_worldcover(self):
        """ Make the mask of the world cover data
        """
        if not self.check_dims(self.ESA_WC, self.SWOT_RASTER):
            raise ValueError("[GLOBAL MASK] The shape of the SWOT Raster and the World Cover data are not the same")
        
        if not self.check_dims(self.ESA_WC_CONTROL, self.SWOT_CONTROL_MASK):
            raise ValueError("[CONTROL MASK] The shape of the SWOT Raster and the World Cover data are not the same")
        
        if not self.check_dims(self.ESA_WC_FLOOD, self.SWOT_FLOOD_MASK):
            raise ValueError("[FLOOD MASK] The shape of the SWOT Raster and the World Cover data are not the same")
        
        self.mask_urban_global, self.mask_forest_global, self.mask_open_global = self.mask_worldcover(self.ESA_WC, self.SWOT_RASTER)
        self.mask_urban_control, self.mask_forest_control, self.mask_open_control = self.mask_worldcover(self.ESA_WC_CONTROL, self.SWOT_CONTROL_MASK)
        self.mask_urban_flood, self.mask_forest_flood, self.mask_open_flood = self.mask_worldcover(self.ESA_WC_FLOOD, self.SWOT_FLOOD_MASK)
        
        
class SwotMean():
    """ Class to calculate the mean of the SWOT Raster data for multiple dates """
    def __init__(
        self, 
        swot_paths:List[Path|str],
        variables: List[str],
        AOI: gdp.GeoDataFrame,
        floodmask:gdp.GeoDataFrame=None,
        controlmask:gdp.GeoDataFrame=None,
        ESA_WC_PATH:Path=None,
        raster_crs:str='EPSG:4326'
        ) -> None:
        self.swot_paths = swot_paths
        self.variables = variables
        self.AOI = AOI
        self.raster_crs = raster_crs
        self.controlmask = controlmask
        self.floodmask = floodmask
        self.ESA_WC_PATH = ESA_WC_PATH
        
        self.swot_dates = [None for _ in self.swot_paths]
        self.swot_rasters = [None for _ in self.swot_paths]
        self.swot_mean = None
        
        self.find_swot_rasters()
    
    def __getattribute__(self, name:str):
        """ Get the attribute of the class """
        if name in super(SwotMean, self).__getattribute__("variables"):
            return super(SwotMean, self).__getattribute__("get_swot_variable")(name)
        return super(SwotMean, self).__getattribute__(name)
    
    def get_swot_variable(self, variable:str):
        """ Get the SWOT variable from the SWOT Raster data
        
        Args:
            variable (str): the variable to get from the SWOT Raster data
            
        Returns:
            xarray.DataArray: the variable from the SWOT Raster data
        """
        if variable not in self.variables:
            raise ValueError(f"Variable {variable} not in the list of variables")
        return self.swot_mean[variable]
    
    def find_swot_rasters(self):
        """ Find the SWOT Raster data """
        for raster_path in self.swot_paths:
            if not Path(raster_path).exists():
                raise ValueError(f"Path {raster_path} does not exist")
        
        self.swot_dates = [raster.name.split('_')[-2] for raster in self.swot_paths]
        self.swot_dates = [datetime.strptime(date, "%Y%m%dT%H%M%S") for date in self.swot_dates] 
    
    def open_rasters(self):
        """ Open the SWOT Raster data """
        dict_swot_param = {
            "path_to_swot_raster": None,
            "variables": self.variables,
            "AOI": self.AOI,
            "floodmask": self.floodmask,
            "controlmask": self.controlmask,
            "ESA_WC_PATH": self.ESA_WC_PATH,
            "raster_crs": self.raster_crs,
        }
        for ii, swot_raster_path in enumerate(self.swot_paths):
            print(f"Opening SWOT raster at time: {self.swot_dates[ii]}")
            dict_swot_param["path_to_swot_raster"] = swot_raster_path
            self.swot_rasters[ii] = SwotRaster(**dict_swot_param)
            self.swot_rasters[ii].read_raster()
            if ii == 0:
                self.ESA_WC = self.swot_rasters[ii].ESA_WC
                self.ESA_WC_CONTROL = self.swot_rasters[ii].ESA_WC_CONTROL
                self.ESA_WC_FLOOD = self.swot_rasters[ii].ESA_WC_FLOOD

        self.concat_rasters()
    
    def concat_rasters(self):
        """ Fusion the SWOT Rasters data """
        self.swot_rasters = xr.concat([raster.SWOT_RASTER for raster in self.swot_rasters], dim='time')
        
    def compute_mean(self):
        """ Create a mean of the SWOT Rasters data """
        self.swot_mean = self.swot_rasters.mean(dim='time')
        self.holes_mean = self.swot_mean[self.variables[0]] == np.nan
        
        self.controlmask = self.controlmask.to_crs(self.raster_crs)
        self.floodmask = self.floodmask.to_crs(self.raster_crs)
        
        self.swot_mean_control = self.swot_mean.rio.clip(self.controlmask.geometry)
        self.swot_mean_flood = self.swot_mean.rio.clip(self.floodmask.geometry)
        self.holes_mean_control = self.holes_mean.rio.clip(self.controlmask.geometry)
        self.holes_mean_flood = self.holes_mean.rio.clip(self.floodmask.geometry)
        self.make_mask_worldcover()
        
    def make_mask_worldcover(self):
        """ Make the mask of the world cover data """
        self.mask_urban_global, self.mask_forest_global, self.mask_open_global = SwotRaster.mask_worldcover(self.ESA_WC, self.swot_mean)
        self.mask_urban_control, self.mask_forest_control, self.mask_open_control = SwotRaster.mask_worldcover(self.ESA_WC_CONTROL, self.swot_mean_control)
        self.mask_urban_flood, self.mask_forest_flood, self.mask_open_flood = SwotRaster.mask_worldcover(self.ESA_WC_FLOOD, self.swot_mean_flood)
        

class SwotCollection():
    """ Class to handle multiple SWOT Raster data and calculate the mean """
    def __init__(
        self,
        swot_flood_paths:List[Path|str],
        swot_dry_paths:List[Path|str],
        variables: List[str],
        AOI: gdp.GeoDataFrame,
        floodmask:gdp.GeoDataFrame=None,
        controlmask:gdp.GeoDataFrame=None,
        ESA_WC_PATH:Path=None,
        raster_crs:str='EPSG:4326'
        ) -> None:
        self.swot_flood_paths = swot_flood_paths
        self.swot_dry_paths = swot_dry_paths
        self.variables = variables
        self.AOI = AOI
        self.raster_crs = raster_crs
        self.controlmask = controlmask
        self.floodmask = floodmask
        
        self.ESA_WC_PATH = ESA_WC_PATH
        self.ESA_WC : xr.DataArray = None
        self.ESA_WC_CONTROL : xr.DataArray = None
        self.ESA_WC_FLOOD : xr.DataArray = None
        
        self.swot_flood_dates : List[datetime] = [None for _ in self.swot_flood_paths]
        self.swot_dry_dates : List[datetime] = [None for _ in self.swot_dry_paths]
        self.swot_flood_rasters : List[SwotRaster] = [None for _ in self.swot_flood_paths]
        self.swot_dry_rasters : List[SwotRaster] = [None for _ in self.swot_dry_paths]
        self.swot_mean : SwotMean = None
        
        self.sig0_floodmask_diff : xr.DataArray = None
        self.sig0_floodmask_mean : xr.DataArray = None
        self.sig0_floodmask_swot : xr.DataArray = None
        self.sig0_floodmask_flood_diff : xr.DataArray = None
        self.sig0_floodmask_flood_mean : xr.DataArray = None
        self.sig0_floodmask_flood_swot : xr.DataArray = None
        
        self.coherent_power_floodmask_diff : xr.DataArray = None
        self.coherent_power_floodmask_mean : xr.DataArray = None
        self.coherent_power_floodmask_swot : xr.DataArray = None
        self.coherent_power_floodmask_flood_diff : xr.DataArray = None
        self.coherent_power_floodmask_flood_mean : xr.DataArray = None
        self.coherent_power_floodmask_flood_swot : xr.DataArray = None
        
        self.gamma_tot_floodmask_diff : xr.DataArray = None
        self.gamma_tot_floodmask_mean : xr.DataArray = None
        self.gamma_tot_floodmask_swot : xr.DataArray = None
        self.gamma_tot_floodmask_flood_diff : xr.DataArray = None
        self.gamma_tot_floodmask_flood_mean : xr.DataArray = None
        self.gamma_tot_floodmask_flood_swot : xr.DataArray = None
        
        self.swot_mask_holes : xr.DataArray = None
        self.swot_mask_holes_control : xr.DataArray = None
        self.swot_mask_holes_flood : xr.DataArray = None
        self.swot_flood_rasters_control : xr.DataArray = None
        self.swot_flood_rasters_flood : xr.DataArray = None
        self.swot_flood_urban_flood : xr.DataArray = None
        self.swot_flood_forest_flood : xr.DataArray = None
        self.swot_flood_open_flood : xr.DataArray = None
        self.swot_flood_urban_control : xr.DataArray = None
        self.swot_flood_forest_control : xr.DataArray = None
        self.swot_flood_open_control : xr.DataArray = None
        self.swot_flood_urban_global : xr.DataArray = None
        self.swot_flood_forest_global : xr.DataArray = None
        self.swot_flood_open_global : xr.DataArray = None
        self.swot_diff : xr.DataArray = None
        self.swot_diff_control : xr.DataArray = None
        self.swot_diff_flood : xr.DataArray = None
        self.mask_urban_diff_global : xr.DataArray = None
        self.mask_forest_diff_global : xr.DataArray = None
        self.mask_open_diff_global : xr.DataArray = None
        self.mask_urban_diff_control : xr.DataArray = None
        self.mask_forest_diff_control : xr.DataArray = None
        self.mask_open_diff_control : xr.DataArray = None
        self.mask_urban_diff_flood : xr.DataArray = None
        self.mask_forest_diff_flood : xr.DataArray = None
        self.mask_open_diff_flood : xr.DataArray = None
        
        self.find_swot_rasters()
        
    @staticmethod
    def find_swot_paths(paths:List[Path])->List[datetime]:
        """ Find the SWOT Raster data """
        for raster_path in paths:
            if not Path(raster_path).exists():
                raise ValueError(f"Path {raster_path} does not exist")
        
        swot_dates = [raster.name.split('_')[-2] for raster in paths]
        swot_dates = [datetime.strptime(date, "%Y%m%dT%H%M%S") for date in swot_dates] 
        
        return swot_dates
    
    def concat_flood_rasters(self):
        """ Concatenate the flood SWOT Raster data """
        self.swot_mask_holes = xr.concat([raster.MASK_HOLES for raster in self.swot_flood_rasters], dim='time')
        self.swot_mask_holes_control = xr.concat([raster.MASK_HOLES_CONTROL for raster in self.swot_flood_rasters], dim='time')
        self.swot_mask_holes_flood = xr.concat([raster.MASK_HOLES_FLOOD for raster in self.swot_flood_rasters], dim='time')
        self.swot_flood_rasters_control = xr.concat([raster.SWOT_CONTROL_MASK for raster in self.swot_flood_rasters], dim='time')
        self.swot_flood_rasters_flood = xr.concat([raster.SWOT_FLOOD_MASK for raster in self.swot_flood_rasters], dim='time')
        self.swot_flood_urban_flood = xr.concat([raster.mask_urban_flood for raster in self.swot_flood_rasters], dim='time')
        self.swot_flood_forest_flood = xr.concat([raster.mask_forest_flood for raster in self.swot_flood_rasters], dim='time')
        self.swot_flood_open_flood = xr.concat([raster.mask_open_flood for raster in self.swot_flood_rasters], dim='time')
        self.swot_flood_urban_control = xr.concat([raster.mask_urban_control for raster in self.swot_flood_rasters], dim='time')
        self.swot_flood_forest_control = xr.concat([raster.mask_forest_control for raster in self.swot_flood_rasters], dim='time')
        self.swot_flood_open_control = xr.concat([raster.mask_open_control for raster in self.swot_flood_rasters], dim='time')
        self.swot_flood_urban_global = xr.concat([raster.mask_urban_global for raster in self.swot_flood_rasters], dim='time')
        self.swot_flood_forest_global = xr.concat([raster.mask_forest_global for raster in self.swot_flood_rasters], dim='time')
        self.swot_flood_open_global = xr.concat([raster.mask_open_global for raster in self.swot_flood_rasters], dim='time')
        self.swot_flood_rasters = xr.concat([raster.SWOT_RASTER for raster in self.swot_flood_rasters], dim='time')
        
    def __select_global_types(self, variable:str, data_type:str, world_cover_selection:str):
        """ Select the global types of the SWOT Raster data """
        match data_type:
            case 'swot':
                match world_cover_selection:
                    case 'urban':
                        return self.swot_flood_urban_global[variable]
                    case 'forest':
                        return self.swot_flood_forest_global[variable]
                    case 'open':
                        return self.swot_flood_open_global[variable]
                    case _:
                        return self.swot_flood_rasters[variable]
                    
            case 'mean':
                match world_cover_selection:
                    case 'urban':
                        return self.swot_mean.mask_urban_global[variable]
                    case 'forest':
                        return self.swot_mean.mask_forest_global[variable]
                    case 'open':
                        return self.swot_mean.mask_open_global[variable]
                    case _:
                        return self.swot_mean.swot_mean[variable]
                    
            case 'diff':
                match world_cover_selection:
                    case 'urban':
                        return self.mask_urban_diff_global[variable]
                    case 'forest':
                        return self.mask_forest_diff_global[variable]
                    case 'open':
                        return self.mask_open_diff_global[variable]
                    case _:
                        return self.swot_diff[variable]
                
            case _:
                raise ValueError(f"Data type {data_type} not in the list of types")
            
    def __select_control_types(self, variable:str, data_type:str, world_cover_selection:str):
        """ Select the control types of the SWOT Raster data """
        match data_type:
            case 'swot':
                match world_cover_selection:
                    case 'urban':
                        return self.swot_flood_urban_control[variable]
                    case 'forest':
                        return self.swot_flood_forest_control[variable]
                    case 'open':
                        return self.swot_flood_open_control[variable]
                    case _:
                        return self.swot_flood_rasters_control[variable]
                    
            case 'mean':
                match world_cover_selection:
                    case 'urban':
                        return self.swot_mean.mask_urban_control[variable]
                    case 'forest':
                        return self.swot_mean.mask_forest_control[variable]
                    case 'open':
                        return self.swot_mean.mask_open_control[variable]
                    case _:
                        return self.swot_mean.swot_mean_control[variable]
                    
            case 'diff':
                match world_cover_selection:
                    case 'urban':
                        return self.mask_urban_diff_control[variable]
                    case 'forest':
                        return self.mask_forest_diff_control[variable]
                    case 'open':
                        return self.mask_open_diff_control[variable]
                    case _:
                        return self.swot_diff_control[variable]
                
            case _:
                raise ValueError(f"Data type {data_type} not in the list of types")
    
    def __select_flood_types(self, variable:str, data_type:str, world_cover_selection:str):
        """ Select the flood types of the SWOT Raster data """
        match data_type:
            case 'swot':
                match world_cover_selection:
                    case 'urban':
                        return self.swot_flood_urban_flood[variable]
                    case 'forest':
                        return self.swot_flood_forest_flood[variable]
                    case 'open':
                        return self.swot_flood_open_flood[variable]
                    case _:
                        return self.swot_flood_rasters_flood[variable]
                    
            case 'mean':
                match world_cover_selection:
                    case 'urban':
                        return self.swot_mean.mask_urban_flood[variable]
                    case 'forest':
                        return self.swot_mean.mask_forest_flood[variable]
                    case 'open':
                        return self.swot_mean.mask_open_flood[variable]
                    case _:
                        return self.swot_mean.swot_mean_flood[variable]
                    
            case 'diff':
                match world_cover_selection:
                    case 'urban':
                        return self.mask_urban_diff_flood[variable]
                    case 'forest':
                        return self.mask_forest_diff_flood[variable]
                    case 'open':
                        return self.mask_open_diff_flood[variable]
                    case _:
                        return self.swot_diff_flood[variable]
                
            case _:
                raise ValueError(f"Data type {data_type} not in the list of types")
      
    def __set_gamma_tot_floodmask(self, data_type:str, data_area:str, data:xr.DataArray) -> None:
        """ Set the gamma_tot flood mask
        
        Args:
            data_type (str): the type of data to set the flood mask
            data_area (str): the area to set the flood mask
            data (xarray.DataArray): the data to set the flood mask
        """
        match data_area:
            case 'global':
                if data_type == "swot":
                    self.__setattr__("gamma_tot_floodmask_swot", data)
                elif data_type == "mean":
                    self.__setattr__("gamma_tot_floodmask_mean", data)
                elif data_type == "diff":
                    self.__setattr__("gamma_tot_floodmask_diff", data)
            case 'flood':
                if data_type == "swot":
                    self.__setattr__("gamma_tot_floodmask_flood_swot", data)
                elif data_type == "mean":
                    self.__setattr__("gamma_tot_floodmask_flood_mean", data)
                elif data_type == "diff":
                    self.__setattr__("gamma_tot_floodmask_flood_diff", data)
            case 'control':
                raise NotImplementedError("Control flood mask not implemented")
            case _:
                raise ValueError(f"Data area {data_area} not in the list of areas")
    
    def __set_sig0_floodmask(self, data_type:str, data_area:str, data:xr.DataArray) -> None:
        """ Set the sig0 flood mask
        
        Args:
            data_type (str): the type of data to set the flood mask
            data_area (str): the area to set the flood mask
            data (xarray.DataArray): the data to set the flood mask
        """
        match data_area:
            case 'global':
                if data_type == "swot":
                    self.__setattr__("sig0_floodmask_swot", data)
                elif data_type == "mean":
                    self.__setattr__("sig0_floodmask_mean", data)
                elif data_type == "diff":
                    self.__setattr__("sig0_floodmask_diff", data)
            case 'flood':
                if data_type == "swot":
                    self.__setattr__("sig0_floodmask_flood_swot", data)
                elif data_type == "mean":
                    self.__setattr__("sig0_floodmask_flood_mean", data)
                elif data_type == "diff":
                    self.__setattr__("sig0_floodmask_flood_diff", data)
            case 'control':
                raise NotImplementedError("Control flood mask not implemented")
            case _:
                raise ValueError(f"Data area {data_area} not in the list of areas")
    
    def __set_coherent_power_floodmask(self, data_type:str, data_area:str, data:xr.DataArray) -> None:
        """ Set the coherent power flood mask
        
        Args:
            data_type (str): the type of data to set the flood mask
            data_area (str): the area to set the flood mask
            data (xarray.DataArray): the data to set the flood mask
        """
        match data_area:
            case 'global':
                if data_type == "swot":
                    self.__setattr__("coherent_power_floodmask_swot", data)
                elif data_type == "mean":
                    self.__setattr__("coherent_power_floodmask_mean", data)
                elif data_type == "diff":
                    self.__setattr__("coherent_power_floodmask_diff", data)
            case 'flood':
                if data_type == "swot":
                    self.__setattr__("coherent_power_floodmask_flood_swot", data)
                elif data_type == "mean":
                    self.__setattr__("coherent_power_floodmask_flood_mean", data)
                elif data_type == "diff":
                    self.__setattr__("coherent_power_floodmask_flood_diff", data)
            case 'control':
                raise NotImplementedError("Control flood mask not implemented")
            case _:
                raise ValueError(f"Data area {data_area} not in the list of areas")
    
    def set_floodmask_from_variable(
        self,
        variable:str,
        data_type:str,
        data_area:str,
        data:xr.DataArray
        ) -> None:
        """ Set the flood mask per variable
        
        Args:
            variable (str): the variable to set the flood mask
            data_type (str): the type of data to set the flood mask
            data_area (str): the area to set the flood mask
            data (xarray.DataArray): the data to set the flood mask
        """
        match variable:
            case 'gamma_tot':
                self.__set_gamma_tot_floodmask(data_type, data_area, data)
            case 'sig0':
                self.__set_sig0_floodmask(data_type, data_area, data)
            case 'coherent_power':
                self.__set_coherent_power_floodmask(data_type, data_area, data)
            case _:
                raise ValueError(f"Variable {variable} not in the list of variables")
        
    def __get_gamma_tot_floodmask(
        self,
        data_type:str,
        data_area:str
        ) -> xr.DataArray:
        """ Get the gamma_tot flood mask
        
        Args:
            variable (str): the variable to get the flood mask
            data_type (str): the type of data to get the flood mask
            data_area (str): the area to get the flood mask
            
        Returns:
            xarray.DataArray: the gamma_tot flood mask
        """
        match data_area:
            case 'global':
                if data_type == "swot":
                    return self.gamma_tot_floodmask_swot
                elif data_type == "mean":
                    return self.gamma_tot_floodmask_mean
                elif data_type == "diff":
                    return self.gamma_tot_floodmask_diff
            case 'flood':
                if data_type == "swot":
                    return self.gamma_tot_floodmask_flood_swot
                elif data_type == "mean":
                    return self.gamma_tot_floodmask_flood_mean
                elif data_type == "diff":
                    return self.gamma_tot_floodmask_flood_diff
            case 'control':
                raise NotImplementedError("Control flood mask not implemented")
            case _:
                raise ValueError(f"Data area {data_area} not in the list of areas")
            
    def __get_sig0_floodmask(
        self,
        data_type:str,
        data_area:str
        ) -> xr.DataArray:
        """ Get the sig0 flood mask
        
        Args:
            variable (str): the variable to get the flood mask
            data_type (str): the type of data to get the flood mask
            data_area (str): the area to get the flood mask
            
        Returns:
            xarray.DataArray: the sig0 flood mask
        """
        match data_area:
            case 'global':
                if data_type == "swot":
                    return self.sig0_floodmask_swot
                elif data_type == "mean":
                    return self.sig0_floodmask_mean
                elif data_type == "diff":
                    return self.sig0_floodmask_diff
            case 'flood':
                if data_type == "swot":
                    return self.sig0_floodmask_flood_swot
                elif data_type == "mean":
                    return self.sig0_floodmask_flood_mean
                elif data_type == "diff":
                    return self.sig0_floodmask_flood_diff
            case 'control':
                raise NotImplementedError("Control flood mask not implemented")
            case _:
                raise ValueError(f"Data area {data_area} not in the list of areas")
            
    def __get_coherent_power_floodmask(
        self,
        data_type:str,
        data_area:str
        ) -> xr.DataArray:
        """ Get the coherent power flood mask
        
        Args:
            variable (str): the variable to get the flood mask
            data_type (str): the type of data to get the flood mask
            data_area (str): the area to get the flood mask
            
        Returns:
            xarray.DataArray: the coherent power flood mask
        """
        match data_area:
            case 'global':
                if data_type == "swot":
                    return self.coherent_power_floodmask_swot
                elif data_type == "mean":
                    return self.coherent_power_floodmask_mean
                elif data_type == "diff":
                    return self.coherent_power_floodmask_diff
            case 'flood':
                if data_type == "swot":
                    return self.coherent_power_floodmask_flood_swot
                elif data_type == "mean":
                    return self.coherent_power_floodmask_flood_mean
                elif data_type == "diff":
                    return self.coherent_power_floodmask_flood_diff
            case 'control':
                raise NotImplementedError("Control flood mask not implemented")
            case _:
                raise ValueError(f"Data area {data_area} not in the list of areas")
            
    def get_floodmask_from_variable(
        self,
        variable:str,
        data_type:str,
        data_area:str
        ) -> xr.DataArray:
        """ Get the flood mask per variable

        Args:
            variable (str): the variable to get the flood mask
            data_type (str): the type of data to get the flood mask
            data_area (str): the area to get the flood mask
            
        Returns:
            xarray.DataArray: the flood mask per variable
        """
        match variable:
            case "gamma_tot":
                return self.__get_gamma_tot_floodmask(data_type, data_area)
            case "sig0":
                return self.__get_sig0_floodmask(data_type, data_area)
            case "coherent_power":
                return self.__get_coherent_power_floodmask(data_type, data_area)
            case "merged":
                return self.merged_floodmask
            case _:
                raise ValueError(f"Variable {variable} not in the list of variables")
    
    def get_intersections(self, variable, ln, SNR_th=0.5):
        clean_dry = np.where(self.swot_mean.swot_mean.gamma_SNR.values > SNR_th, self.swot_mean.swot_mean[variable].values, np.nan)
        clean_flooded = np.where(self.swot_flood_rasters.gamma_SNR.values > SNR_th, self.swot_flood_rasters[variable].values, np.nan)
        
        fig, ax = plt.subplots(1,1)
        sns.kdeplot(clean_dry.flatten(), ax=ax)
        ln = sns.kdeplot(clean_flooded.flatten(), ax=ax)
        plt.close(fig)
        
        f_ln = [[x,y] for x, y in zip(ln.lines[0].get_xdata(), ln.lines[0].get_ydata())]
        f_ln = np.array(f_ln)
        g_ln = [[x,y] for x, y in zip(ln.lines[1].get_xdata(), ln.lines[1].get_ydata())]
        g_ln = np.array(g_ln)
        
        f = LineString(f_ln)
        g = LineString(g_ln)
        intersection = f.intersection(g)
        
        x, y = [], []
        if intersection.geom_type == 'Point':
            x.append(intersection.x)
            y.append(intersection.y)
        elif intersection.geom_type == 'MultiPoint':
            for geo in intersection.geoms:
                x.append(geo.x)
                y.append(geo.y)
                
        return x, y
    
    def get_holes_mask(self, data_area:str="global", data_type:str="swot")->xr.DataArray:
        """ get tjhe holes mask from the SWOT Raster data 
        
        Args:
            data_area (str): the area to get the data (global, control or flood)
            data_type (str): the type of data to get (swot, mean, diff)
            
        Returns:
            xarray.DataArray: the holes mask from the SWOT Raster data
        """
        match data_area:
            case 'global':
                match data_type:
                    case 'swot':
                        return self.swot_mask_holes
                    case 'mean':
                        return self.swot_mean.holes_mean
                    case 'diff':
                        val = self.swot_mask_holes.copy()
                        condi = np.logical_or(self.swot_mean.holes_mean.values, self.swot_mask_holes.values)
                        val.values = np.where(condi, 1, 0)
                        return val
                    case _:
                        raise ValueError(f"Data type {data_type} not in the list of types")
            case 'control':
                match data_type:
                    case 'swot':
                        return self.swot_mask_holes_control
                    case 'mean':
                        return self.swot_mean.holes_mean_control
                    case 'diff':
                        val = self.swot_mask_holes_control.copy()
                        condi = np.logical_or(self.swot_mean.holes_mean_control.values, self.swot_mask_holes_control.values)
                        val.values = np.where(condi, 1, 0)
                        return val
                    case _:
                        raise ValueError(f"Data type {data_type} not in the list of types")
            case 'flood':
                match data_type:
                    case 'swot':
                        return self.swot_mask_holes_flood
                    case 'mean':
                        return self.swot_mean.holes_mean_flood
                    case 'diff':
                        val = self.swot_mask_holes_flood.copy()
                        condi = np.logical_or(self.swot_mean.holes_mean_flood.values, self.swot_mask_holes_flood.values)
                        val.values = np.where(condi, 1, 0)
                        return val
                    case _:
                        raise ValueError(f"Data type {data_type} not in the list of types")
            case _:
                raise ValueError(f"Data area {data_area} not in the list of areas")
    
    def save_tiff(self, variable:str, is_mask:bool=True, make_binary:bool=False, remove_lowcoh:bool=True, data_area:str="global", data_type:str="swot", world_cover_selection:str=None, path:Path=None, time_selection:str=None)->None:
        """ Save the variable to a tiff file
        
        Args:
            variable (str): the variable to save
            is_mask (bool): if the variable is a mask
            make_binary (bool): if the water mask is save as a binary variable
            remove_lowcoh (bool): if True, the low coherence is removed when make_binary is True else, only low_SNR is remove from mask
            data_area (str): the area to save the data (global, control or flood)
            data_type (str): the type of data to save (swot, mean, diff)
            world_cover_selection (str): the world cover selection to save the data (None, urban, forest, open)
            path (Path): the path to save the tiff file
            time_selection (str): the time selection to save the data (None, date)
        """
        if path is None:
            raise ValueError("Path is None")
        if not isinstance(path, Path):
            raise ValueError("Path is not a Path object")
        if not path.parent.exists():
            raise ValueError(f"Path {path} does not exist")
        if is_mask:
            data = self.get_floodmask_from_variable(variable, data_type, data_area)
            if make_binary:
                if remove_lowcoh:
                    condition = np.logical_and(data.values != 0, data.values < 10) * 1.
                else:
                    condition = np.logical_and(data.values != 0, data.values < 20) * 1.
                data.values = np.where(condition, 1, 0)
        else:
            data = self.get_variable(variable, data_area, data_type, world_cover_selection)
        
        data.values = np.where(data.values == np.nan, -9999, data.values)
        
        if data is None:
            raise ValueError(f"Data is None")
        
        if time_selection is not None:
            if "time" in data.dims:
                data = data.sel(time=time_selection)
            else:
                print("Time selection is not possible with this variable")
                
        data.rio.to_raster(path, driver="GTiff", nodata=-9999, dtype="float32")
    
    def get_variable(self, variable:str, data_area:str="global", data_type:str="swot", world_cover_selection:str=None)->xr.DataArray:
        """ Get the variable from the SWOT Raster data
        
        Args:
            variable (str): the variable to get from the SWOT Raster data
            data_area (str): the area to get the data (global, control or flood)
            data_type (str): the type of data to get (swot, mean, diff)
            world_cover_selection (str): the world cover selection to get the data (None, urban, forest, open)
            
        Returns:
            xarray.DataArray: the variable from the SWOT Raster data
        """
        if variable not in self.variables:
            raise ValueError(f"Variable {variable} not in the list of variables")
        match data_area:
            case 'global':
                data = self.__select_global_types(variable, data_type, world_cover_selection).copy()
            case 'control':
                data = self.__select_control_types(variable, data_type, world_cover_selection).copy()
            case 'flood':
                data = self.__select_flood_types(variable, data_type, world_cover_selection).copy()
            case _:
                raise ValueError(f"Data area {data_area} not in the list of areas")
        if variable == "sig0" or variable == "coherent_power":
            data = power_to_db(data)
        return data
                
    def open_rasters(self):
        """ Open both flood and dry SWOT Raster data """
        dict_swot_param = {
            "path_to_swot_raster": None,
            "variables": self.variables,
            "AOI": self.AOI,
            "floodmask": self.floodmask,
            "controlmask": self.controlmask,
            "ESA_WC_PATH": self.ESA_WC_PATH,
            "raster_crs": self.raster_crs,
        }
        for ii, swot_raster_path in enumerate(self.swot_flood_paths):
            print(f"Opening SWOT raster at time: {self.swot_flood_dates[ii]}")
            dict_swot_param["path_to_swot_raster"] = swot_raster_path
            self.swot_flood_rasters[ii] = SwotRaster(**dict_swot_param)
            self.swot_flood_rasters[ii].read_raster()
            if ii == 0:
                self.ESA_WC = self.swot_flood_rasters[ii].ESA_WC
                self.ESA_WC_CONTROL = self.swot_flood_rasters[ii].ESA_WC_CONTROL
                self.ESA_WC_FLOOD = self.swot_flood_rasters[ii].ESA_WC_FLOOD
        self.concat_flood_rasters()
        
        self.swot_mean = SwotMean(self.swot_dry_paths, self.variables, self.AOI, self.floodmask, self.controlmask, self.ESA_WC_PATH, self.raster_crs)
        self.swot_mean.open_rasters()
        self.swot_mean.compute_mean()
        
        self.compute_difference()
        
    def find_swot_rasters(self):
        """ Find the SWOT Raster data """
        self.swot_flood_dates = self.find_swot_paths(self.swot_flood_paths)
        self.swot_dry_dates = self.find_swot_paths(self.swot_dry_paths)
    
    def make_mask_worldcover(self):
        """ mask the world cover data """
        self.mask_urban_diff_global, self.mask_forest_diff_global, self.mask_open_diff_global = SwotRaster.mask_worldcover(self.ESA_WC, self.swot_diff)
        self.mask_urban_diff_control, self.mask_forest_diff_control, self.mask_open_diff_control = SwotRaster.mask_worldcover(self.ESA_WC_CONTROL, self.swot_diff_control)
        self.mask_urban_diff_flood, self.mask_forest_diff_flood, self.mask_open_diff_flood = SwotRaster.mask_worldcover(self.ESA_WC_FLOOD, self.swot_diff_flood)
    
    def compute_difference(self):
        """ Compute the difference between the flood and dry mean SWOT raster data and make the ESA world cover mask"""
        self.swot_diff = self.swot_flood_rasters - self.swot_mean.swot_mean
        self.swot_diff_control = self.swot_flood_rasters_control - self.swot_mean.swot_mean_control
        self.swot_diff_flood = self.swot_flood_rasters_flood - self.swot_mean.swot_mean_flood
        self.make_mask_worldcover()
    
    def merge_flood_masks(self, data_area:str="global", data_type:str="swot", filter_variable:str=None) -> None:
        """ Merge the flood masks
        Args:
            data_area (str): the area to get the data (global, control or flood)
            data_type (str): the type of data to get (swot, mean, diff)
        """
        gamma_floodmask = None
        sig0_floodmask = None
        coherent_power_floodmask = None
        match data_area:
            case 'global':
                if data_type == "swot":
                    if "gamma_tot" != filter_variable:
                        gamma_floodmask = self.get_floodmask_from_variable("gamma_tot", "swot", "global")
                    if "sig0" != filter_variable:
                        sig0_floodmask = self.get_floodmask_from_variable("sig0", "swot", "global")
                    if "coherent_power" != filter_variable:
                        coherent_power_floodmask = self.get_floodmask_from_variable("coherent_power", "swot", "global")
                elif data_type == "mean":
                    if "gamma_tot" != filter_variable:
                        gamma_floodmask = self.get_floodmask_from_variable("gamma_tot", "mean", "global")
                    if "sig0" != filter_variable:
                        sig0_floodmask = self.get_floodmask_from_variable("sig0", "mean", "global")
                    if "coherent_power" != filter_variable:
                        coherent_power_floodmask = self.get_floodmask_from_variable("coherent_power", "mean", "global")
                elif data_type == "diff":
                    if "gamma_tot" != filter_variable:
                        gamma_floodmask = self.get_floodmask_from_variable("gamma_tot", "diff", "global")
                    if "sig0" != filter_variable:
                        sig0_floodmask = self.get_floodmask_from_variable("sig0", "diff", "global")
                    if "coherent_power" != filter_variable:
                        coherent_power_floodmask = self.get_floodmask_from_variable("coherent_power", "diff", "global")
            case 'flood':
                if data_type == "swot":
                    if "gamma_tot" != filter_variable:
                        gamma_floodmask = self.get_floodmask_from_variable("gamma_tot", "swot", "flood")
                    if "sig0" != filter_variable:
                        sig0_floodmask = self.get_floodmask_from_variable("sig0", "swot", "flood")
                    if "coherent_power" != filter_variable:
                        coherent_power_floodmask = self.get_floodmask_from_variable("coherent_power", "swot", "flood")
                elif data_type == "mean":
                    if "gamma_tot" != filter_variable:
                        gamma_floodmask = self.get_floodmask_from_variable("gamma_tot", "mean", "flood")
                    if "sig0" != filter_variable:
                        sig0_floodmask = self.get_floodmask_from_variable("sig0", "mean", "flood")
                    if "coherent_power" != filter_variable:
                        coherent_power_floodmask = self.get_floodmask_from_variable("coherent_power", "mean", "flood")
                elif data_type == "diff":
                    if "gamma_tot" != filter_variable:
                        gamma_floodmask = self.get_floodmask_from_variable("gamma_tot", "diff", "flood")
                    if "sig0" != filter_variable:
                        sig0_floodmask = self.get_floodmask_from_variable("sig0", "diff", "flood")
                    if "coherent_power" != filter_variable:
                        coherent_power_floodmask = self.get_floodmask_from_variable("coherent_power", "diff", "flood")
            case 'control':
                raise NotImplementedError("Control flood mask not implemented")
            case _:
                raise ValueError(f"Data area {data_area} != the list of areas")
            
        condi_gamma = (gamma_floodmask is None and "gamma_tot" != filter_variable)
        condi_sig0 = (sig0_floodmask is None and "sig0" != filter_variable)
        condi_coherent = (coherent_power_floodmask is None and "coherent_power" != filter_variable)
        if  condi_gamma or condi_sig0 or condi_coherent:
            raise ValueError("One or more flood masks are not set. Please create them before merging.")
        
        list_to_merge = [gamma_floodmask, sig0_floodmask, coherent_power_floodmask]
        # remove None
        list_to_merge = [x for x in list_to_merge if x is not None]
        
        for i in range(len(list_to_merge) - 1):
            merge = np.where(list_to_merge[i].values == list_to_merge[i + 1].values, list_to_merge[i].values, np.nan)
        if filter_variable is not None:
            merge = np.where(merge == list_to_merge[-1].values, merge, np.nan)
        
        self.merged_floodmask = gamma_floodmask.copy()
        self.merged_floodmask.values = merge
            
    def create_flood_mask(
        self,
        variable:str,
        data_area:str="global",
        data_type:str="swot",
        thresholds:dict|float=0.8,
        open_diff:bool=False,
        forest_diff:bool=False,
        urban_diff:bool=False,
        time_selection:List[str]=None,
        add_uncertainty:bool=False,
        threshold_SNR:float=0.5,
        threshold_gamma:float=0.1,
        disk_size:int=3
        ) -> None:
        if variable not in ['gamma_tot', 'sig0', 'coherent_power']:
            raise ValueError(f"Variable {variable} not implemented for flood mask computation")
        
        if isinstance(thresholds, float):
            thresholds = {
                "open": thresholds,
                "forest": thresholds,
                "urban": thresholds
            }
        elif isinstance(thresholds, dict):
            if "open" not in thresholds:
                thresholds["open"] = 0.8
            if "forest" not in thresholds:
                thresholds["forest"] = 0.8
            if "urban" not in thresholds:
                thresholds["urban"] = 0.8
        else:
            raise ValueError("The thresholds must be a float or a dictionary")
        
        if urban_diff:
            data_urban = self.get_variable(variable, data_area, "diff", 'urban')
        else:
            data_urban = self.get_variable(variable, data_area, data_type, 'urban')
            
        if forest_diff:
            data_forest = self.get_variable(variable, data_area, "diff", 'forest')
        else:
            data_forest = self.get_variable(variable, data_area, data_type, 'forest')
        if open_diff:
            data_open = self.get_variable(variable, data_area, "diff", 'open')
        else:
            data_open = self.get_variable(variable, data_area, data_type, 'open')
        data_glob = self.get_variable(variable, data_area, data_type, None)


        if add_uncertainty:
            data_SNR_urban =  self.get_variable("gamma_SNR", data_area, "swot", 'urban')
            data_SNR_forest = self.get_variable("gamma_SNR", data_area, "swot", 'forest')
            data_SNR_open =   self.get_variable("gamma_SNR", data_area, "swot", 'open')
            
            data_urban_gamma_tot =  self.get_variable("gamma_tot", data_area, data_type, 'urban')
            data_forest_gamma_tot = self.get_variable("gamma_tot", data_area, data_type, 'forest')
            data_open_gamma_tot =   self.get_variable("gamma_tot", data_area, data_type, 'open')
            
            self.floodmask = self.floodmask.to_crs(self.raster_crs)
            data_SNR_urban =  data_SNR_urban.rio.clip(self.floodmask.geometry, drop=False)
            data_SNR_forest = data_SNR_forest.rio.clip(self.floodmask.geometry, drop=False)
            data_SNR_open =   data_SNR_open.rio.clip(self.floodmask.geometry, drop=False)
            
            data_flood_urban = data_urban_gamma_tot.rio.clip(self.floodmask.geometry, drop=False)
            data_flood_forest = data_forest_gamma_tot.rio.clip(self.floodmask.geometry, drop=False)
            data_flood_open = data_open_gamma_tot.rio.clip(self.floodmask.geometry, drop=False)

        # Get the data on the requested time
        if "time" in data_glob.dims:
            if time_selection is not None:
                data_urban = data_urban.sel(time=time_selection)
                data_forest = data_forest.sel(time=time_selection)
                data_open = data_open.sel(time=time_selection)
                data_glob = data_glob.sel(time=time_selection)
                if add_uncertainty:
                    data_SNR_urban = data_SNR_urban.sel(time=time_selection)
                    data_SNR_forest = data_SNR_forest.sel(time=time_selection)
                    data_SNR_open = data_SNR_open.sel(time=time_selection)
                    data_flood_urban = data_flood_urban.sel(time=time_selection)
                    data_flood_forest = data_flood_forest.sel(time=time_selection)
                    data_flood_open = data_flood_open.sel(time=time_selection)
            data_urban = data_urban.isel(time=0)
            data_forest = data_forest.isel(time=0)
            data_open = data_open.isel(time=0)
            data_glob = data_glob.isel(time=0)
            if add_uncertainty:
                data_SNR_urban = data_SNR_urban.isel(time=0)
                data_SNR_forest = data_SNR_forest.isel(time=0)
                data_SNR_open = data_SNR_open.isel(time=0)
                data_flood_urban = data_flood_urban.isel(time=0)
                data_flood_forest = data_flood_forest.isel(time=0)
                data_flood_open = data_flood_open.isel(time=0)

        if data_type == "diff":
            from skimage.filters import gaussian
            # smooth data with gaussian filter
            gaussian_urban = gaussian(data_urban.values, sigma=1)
            gaussian_forest = gaussian(data_forest.values, sigma=1)
            gaussian_open = gaussian(data_open.values, sigma=1)
            
            data_urban.values = gaussian_urban
            data_forest.values = gaussian_forest
            data_open.values = gaussian_open
            
        if data_type == "swot" and not urban_diff:
            thresholds_apply = abs(thresholds['urban'])
        else:
            thresholds_apply = thresholds['urban']
        if thresholds['urban'] > 0:
            mask_urban = np.where(data_urban.values > thresholds_apply, 1, 0)
        else:
            mask_urban = np.where(data_urban.values < thresholds_apply, 1, 0)
        if data_type == "swot" and not forest_diff:
            thresholds_apply = abs(thresholds['forest'])
        else:
            thresholds_apply = thresholds['forest']
        if thresholds['forest'] > 0:
            mask_forest = np.where(data_forest.values > thresholds_apply, 2, 0)
        else:
            mask_forest = np.where(data_forest.values < thresholds_apply, 2, 0)
        if data_type == "swot" and not open_diff:
            thresholds_apply = abs(thresholds['open'])
        else:
            thresholds_apply = thresholds['open']
        if thresholds['open'] > 0:
            mask_open = np.where(data_open.values > thresholds_apply, 3, 0)
        else:
            mask_open = np.where(data_open.values < thresholds_apply, 3, 0)
        mask = mask_urban + mask_forest + mask_open

        if add_uncertainty:
            if variable == "gamma_tot":
                mask_darkwater_urban = np.where(data_flood_urban.values < threshold_gamma, 11, 0)
                mask_darkwater_forest = np.where(data_flood_forest.values < threshold_gamma, 12, 0)
                mask_darkwater_open = np.where(data_flood_open.values < threshold_gamma, 13, 0)
                mask_darkwater = mask_darkwater_urban + mask_darkwater_forest + mask_darkwater_open
                
            mask_SNR_urban = np.where(data_SNR_urban.values < threshold_SNR, 21, 0)
            mask_SNR_forest = np.where(data_SNR_forest.values < threshold_SNR, 22, 0)
            mask_SNR_open = np.where(data_SNR_open.values < threshold_SNR, 23, 0)
            mask_SNR = mask_SNR_urban + mask_SNR_forest + mask_SNR_open
            
        global_mask = mask
        if add_uncertainty:
            global_mask[mask_SNR != 0] = mask_SNR[mask_SNR != 0]
            if variable == "gamma_tot":
                condition = np.logical_and(mask_SNR == 0, mask_darkwater != 0)
                global_mask[condition] = mask_darkwater[condition]
        
        # majority filter
        footprint = morphology.disk(disk_size)
        global_mask = majority(global_mask.astype(np.uint8), footprint=footprint)
        global_mask = global_mask.astype(float)

        clean_mask = (global_mask != 0) * 1
        
        # cleaning mask
        res = morphology.white_tophat(clean_mask, footprint)
        clean_mask = np.where(res == 1, 0, clean_mask)
        clean_mask = binary_erosion(clean_mask, structure=footprint).astype(float)
        clean_mask = binary_dilation(clean_mask,structure=footprint).astype(float)
        
        global_mask = np.where(clean_mask == 1, global_mask, 0)
        
        # set mask within a data copy for geolocation
        data = data_urban.copy()
        data.values = global_mask
        
        self.set_floodmask_from_variable(variable, data_type, data_area, data)
        
    def pretreat_data_for_score(
        self, 
        variable, 
        compared_raster_path:Path | str, 
        data_area:str="flood",
        data_type:str="swot",
        time_selection:str=None,
        water_value=1,
        nan_value:float=np.nan
    ) -> Tuple[np.ndarray, np.ndarray]:
        """ Pretreat the data for the critical success index
        
        Args:
            variable (str): the variable to compute the critical success index
            compared_raster_path (Path | str): the path to the compared raster data or "classification" to use the classification data
            data_area (str): the area to get the data (global, control or flood). Default is flood
            data_type (str): the type of data to get (swot, mean, diff). Default is swot
            time_selection (str): the time selection to get the data. Default is None
            water_value (int): the value of water in the compared raster data. Default is 1
            nan_value (float): the value of nan in the compared raster data. Default is np.nan
        
        Returns:
            Tuple[np.ndarray, np.ndarray]: the SWOT Raster data and the compared raster data
        """
        def classif_filter(data):
            condition_classification = data.values >= 3 # Every water class
            return condition_classification
    
        if variable is None:
            raise ValueError("The variable must be given")
        if variable not in self.variables and variable != "merged":
            raise ValueError(f"The variable {variable} is not in the collection")
        holes_mask = self.get_holes_mask(data_area, data_type)
        holes_mask = holes_mask.isel(time=0)
        
        if variable != "classification":
            data = self.get_floodmask_from_variable(variable, data_type, data_area)
            if "time" in data.dims:
                data = data.sel(time=time_selection)
                if data.time.values.size > 1:
                    data = data.isel(time=0)
            
            if data is None:
                raise ValueError(f"The variable {variable} is not in the collection, please use create_flood_mask() method in the swot_collection object.")
            
            mask_data = np.logical_and(data.values != 0, data.values < 20) * 1. # discard dry and low SNR data
        
        else:
            data = self.get_variable(variable, data_area, data_type)
            if "time" in data.dims:
                data = data.sel(time=time_selection)
                if data.time.values.size > 1:
                    data = data.isel(time=0)
            mask_data = (classif_filter(data) * 1.)
            mask_data = mask_data[0]
        
        if data_area == "flood":
            esa_wc = self.ESA_WC_FLOOD
        elif data_area == "control":
            esa_wc = self.ESA_WC_CONTROL
        elif data_area == "global":
            esa_wc = self.ESA_WC
        permanent_water = np.where(esa_wc['band_1'].values == CONDITIONS_WORLDCOVER['permanent_water'], 1, 0)
        
        # read the compared raster data
        if isinstance(compared_raster_path, Path):
            comparing_raster = rxr.open_rasterio(compared_raster_path)
            if data_area == "flood":
                comparing_raster = comparing_raster.rio.clip(self.floodmask.geometry)
            elif data_area == "control":
                comparing_raster = comparing_raster.rio.clip(self.controlmask.geometry)
            mask_compared = np.where(comparing_raster.values == water_value, 1., 0.)[0]
            holes_compared = np.where(comparing_raster.values == nan_value, 1., 0.)[0]
        else:
            comparing_raster = self.get_variable(compared_raster_path, data_area, data_type)
            if "time" in comparing_raster.dims:
                comparing_raster = comparing_raster.sel(time=time_selection)
                if comparing_raster.time.values.size > 1:
                    comparing_raster = comparing_raster.isel(time=0)
            
            mask_compared = np.where(classif_filter(comparing_raster), 1., 0.)[0]
            holes_compared = holes_mask
        
        # removing holes from SWOT
        mask_compared[holes_mask == 1] = np.nan
        mask_data[holes_mask == 1] = np.nan
        
        # removing holes from compared raster
        mask_compared[holes_compared == 1] = np.nan
        mask_data[holes_compared == 1] = np.nan
        
        # removing permanent water
        mask_compared[permanent_water == 1] = np.nan
        mask_data[permanent_water == 1] = np.nan
        
        return mask_data, mask_compared
        
    def compute_scores(
        self, 
        variable, 
        compared_raster_path:Path | str, 
        data_area:str="flood",
        data_type:str="swot",
        time_selection:str=None,
        water_value=1,
        nan_value:float=np.nan
        ) -> Tuple[float, float, float]:
        """ Compute the critical success index, F1-score and Cohen’s kappa index between the SWOT Raster data and the compared raster data
        
        Args:
            variable (str): the variable to compute the critical success index
            compared_raster_path (Path | str): the path to the compared raster data or "classification" to use the classification data
            data_area (str): the area to get the data (global, control or flood). Default is flood
            data_type (str): the type of data to get (swot, mean, diff). Default is swot
            time_selection (str): the time selection to get the data. Default is None
            water_value (int): the value of water in the compared raster data. Default is 1
        
        Returns:
            Tuple[float, float, float]: the critical success index, F1-score and Cohen’s kappa index
        """
        mask_data, mask_compared = self.pretreat_data_for_score(
            variable, 
            compared_raster_path, 
            data_area, 
            data_type, 
            time_selection, 
            water_value, 
            nan_value
            )
        
        if np.count_nonzero(~np.isnan(mask_compared)) != np.count_nonzero(~np.isnan(mask_data)):
            print("WARNING: The compared raster and the SWOT Raster data have not the same non-nan number of pixels")
        
        # compute TP, FP, TN, FN
        true = mask_compared
        pred = mask_data
        
        contingency_map = np.ones(true.shape) * np.nan
        contingency_map[np.logical_and(true == 1, pred == 1)] = 1 #'TP'
        contingency_map[np.logical_and(true == 0, pred == 0)] = 0 #'TN'
        contingency_map[np.logical_and(true == 0, pred == 1)] = 2 #'FP'
        contingency_map[np.logical_and(true == 1, pred == 0)] = 3 #'FN'
        
        TP_scale = np.nansum(contingency_map == 1)
        TN_scale = np.nansum(contingency_map == 0)
        FP_scale = np.nansum(contingency_map == 2)
        FN_scale = np.nansum(contingency_map == 3)
        total = TP_scale + FP_scale + TN_scale + FN_scale
        if total != (~np.isnan(true)).flatten().sum():
            print("WARNING: The sum of TP, FP, TN and FN is not equal to the number of non-nan pixels in the compared raster data")
            
            
        # compute precision and recall
        if TP_scale + FP_scale == 0:
            precision = 0
        else:
            precision = TP_scale / (TP_scale + FP_scale)
        if TP_scale + FN_scale == 0:
            recall = 0
        else:
            recall = TP_scale / (TP_scale + FN_scale)
            
        # compute F1-score
        if precision + recall == 0:
            f1_score = 0
        else:
            f1_score = 2 * (precision * recall) / (precision + recall)
            
        # compute critical success index (CSI)
        if TP_scale + FP_scale + FN_scale == 0:
            CSI = 0
        else:
            CSI = TP_scale / (TP_scale + FP_scale + FN_scale)
            
        # compute Cohen’s kappa index
        total = (TP_scale + FP_scale + FN_scale + TN_scale)
        po = (TP_scale + TN_scale) / total
        pe = ((TP_scale + FN_scale) / total) * ((TP_scale + FP_scale) / total)
        
        if ((1 - pe) == 0):
            kappa = 0
        else:
            kappa = (po - pe) / (1 - pe)
            
        return CSI, f1_score, kappa