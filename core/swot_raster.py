from pathlib import Path
from typing import List
import geopandas as gdp
import rioxarray as rxr
import xarray as xr
from datetime import datetime
import numpy as np
from skimage.filters.rank import majority
from skimage import morphology
from time import time

CONDITIONS_WORLDCOVER = {
    "urban": 50,
    "forest": 10,
    "permament_water": 80
}

class SWOT_RASTER():
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
        
        self.SWOT_RASTER = None

    
    def __getattribute__(self, name):
        """ Get the attribute of the class """
        if name in super(SWOT_RASTER, self).__getattribute__("variables"):
            return super(SWOT_RASTER, self).__getattribute__("get_swot_variable")(name)
        return super(SWOT_RASTER, self).__getattribute__(name)
    
    def read_raster(self):
        """ Read the raster data and pretreat it"""
        self.read_swot_raster()
        self.clip_swot_raster()
    
        self.read_worldcover()
        self.clip_worldcover()
        self.make_mask_worldcover()
    
    def pretreat_raster(self):
        """ Pretreat the raster data by putting nodata values to nan and 0 values """
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
        self.SWOT_RASTER = rxr.open_rasterio(self.PATH_TO_SWOT_RASTER, chunks="auto", variable=self.variables, band_as_variable=True, nodata=-9999)
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
        self.SWOT_CONTROL_MASK = None
        self.SWOT_FLOOD_MASK = None
        if self.controlmask is not None:
            self.SWOT_CONTROL_MASK = self.SWOT_RASTER.rio.clip(self.controlmask.geometry)
        if self.floodmask is not None:
            self.SWOT_FLOOD_MASK = self.SWOT_RASTER.rio.clip(self.floodmask.geometry)
    
    def clip_worldcover(self):
        """ Clip the world cover data to the AOI """
        self.ESA_WC_CONTROL = None
        self.ESA_WC_FLOOD = None
        if self.controlmask is not None:
            self.ESA_WC_CONTROL = self.ESA_WC.rio.clip(self.controlmask.geometry)
        if self.floodmask is not None:
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
        self.ESA_WC = rxr.open_rasterio(self.ESA_WC_PATH, band_as_variable=True, chunks="auto")
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
    def mask_worldcover(WC_array, SWOT_array):
        """ Mask SWOT data with the world cover data """
        condition_urban = WC_array['band_1'].values == CONDITIONS_WORLDCOVER["urban"]
        condition_forest = WC_array['band_1'].values == CONDITIONS_WORLDCOVER["forest"]
        condition_permament_water = WC_array['band_1'].values == CONDITIONS_WORLDCOVER["permament_water"]
        condition_open = np.logical_and(
            ~ condition_forest,
            ~ condition_urban,
            ~ condition_permament_water
            )
        SWOT_urban = SWOT_array.where(condition_urban)
        SWOT_forest = SWOT_array.where(condition_forest)
        SWOT_open = SWOT_array.where(condition_open)
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
        
        
class SWOT_MEAN():
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
        
        self.swot_dates = [None for raster in self.swot_paths]
        self.swot_rasters = [None for raster in self.swot_paths]
        self.swot_mean = None
        
        self.find_swot_rasters()
    
    def __getattribute__(self, name):
        """ Get the attribute of the class """
        if name in super(SWOT_MEAN, self).__getattribute__("variables"):
            return super(SWOT_MEAN, self).__getattribute__("get_swot_variable")(name)
        return super(SWOT_MEAN, self).__getattribute__(name)
    
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
            self.swot_rasters[ii] = SWOT_RASTER(**dict_swot_param)
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
        
        self.swot_mean_control = self.swot_mean.rio.clip(self.controlmask.geometry)
        self.swot_mean_flood = self.swot_mean.rio.clip(self.floodmask.geometry)
        self.make_mask_worldcover()
    
    @staticmethod
    def mask_worldcover(WC_array, SWOT_array):
        """ Mask SWOT data with the world cover data """
        condition_urban = WC_array['band_1'].values == CONDITIONS_WORLDCOVER["urban"]
        condition_forest = WC_array['band_1'].values == CONDITIONS_WORLDCOVER["forest"]
        condition_permament_water = WC_array['band_1'].values == CONDITIONS_WORLDCOVER["permament_water"]
        condition_open = np.logical_and(
            ~ condition_forest,
            ~ condition_urban,
            ~ condition_permament_water
            )
        SWOT_urban = SWOT_array.where(condition_urban)
        SWOT_forest = SWOT_array.where(condition_forest)
        SWOT_open = SWOT_array.where(condition_open)
        return SWOT_urban, SWOT_forest, SWOT_open
        
    def make_mask_worldcover(self):
        """ Make the mask of the world cover data """
        self.mask_urban_global, self.mask_forest_global, self.mask_open_global = self.mask_worldcover(self.ESA_WC, self.swot_mean)
        self.mask_urban_control, self.mask_forest_control, self.mask_open_control = self.mask_worldcover(self.ESA_WC_CONTROL, self.swot_mean_control)
        self.mask_urban_flood, self.mask_forest_flood, self.mask_open_flood = self.mask_worldcover(self.ESA_WC_FLOOD, self.swot_mean_flood)
        

class SWOT_COLLECTION():
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
        
        self.swot_flood_dates = [None for _ in self.swot_flood_paths]
        self.swot_dry_dates = [None for _ in self.swot_dry_paths]
        self.swot_flood_rasters = [None for _ in self.swot_flood_paths]
        self.swot_dry_rasters = [None for _ in self.swot_dry_paths]
        self.swot_mean = None
        
        self.find_swot_rasters()
        
    @staticmethod
    def find_swot_paths(paths):
        """ Find the SWOT Raster data """
        for raster_path in paths:
            if not Path(raster_path).exists():
                raise ValueError(f"Path {raster_path} does not exist")
        
        swot_dates = [raster.name.split('_')[-2] for raster in paths]
        swot_dates = [datetime.strptime(date, "%Y%m%dT%H%M%S") for date in swot_dates] 
        
        return swot_dates
    
    def find_swot_rasters(self):
        """ Find the SWOT Raster data """
        self.swot_flood_dates = self.find_swot_paths(self.swot_flood_paths)
        self.swot_dry_dates = self.find_swot_paths(self.swot_dry_paths)
    
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
            self.swot_flood_rasters[ii] = SWOT_RASTER(**dict_swot_param)
            self.swot_flood_rasters[ii].read_raster()
            if ii == 0:
                self.ESA_WC = self.swot_flood_rasters[ii].ESA_WC
                self.ESA_WC_CONTROL = self.swot_flood_rasters[ii].ESA_WC_CONTROL
                self.ESA_WC_FLOOD = self.swot_flood_rasters[ii].ESA_WC_FLOOD
        
        self.swot_mean = SWOT_MEAN(self.swot_dry_paths, self.variables, self.AOI, self.floodmask, self.controlmask, self.ESA_WC_PATH, self.raster_crs)
        self.swot_mean.open_rasters()
        self.swot_mean.compute_mean()
        