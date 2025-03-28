from pathlib import Path
from typing import List

import geopandas as gpd
from shapely.geometry import shape, box

import configparser
from datetime import datetime
from core.downloader import Downloader
from core.pixc_rasterizer import Rasterizer
from core.swot_raster import SwotCollection

DEFAULT_VARIABLES = [
    'sig0', 
    'coherent_power', 
    'incidence', 
    'gamma_tot', 
    'gamma_SNR', 
    'gamma_est', 
    'power_plus_y', 
    'power_minus_y',  
    'interf_real', 
    'interf_imag', 
    'height', 
    'classification', 
    'bright_land_flag'
    ]


class SwotProject():
    """
    SwotProject class to manage the SWOT project
    Can be used to download data, process data, and plot data
    """
    def __init__(
        self, 
        param_dict: dict | configparser.ConfigParser
        ) -> None:
        """Initialize the SwotProject class

        Args:
            param_dict (dict or configparser.ConfigParser): dictionary with the parameters of the project
                it should contain the following keys:
                   - project (str): string with the name of the project
                   - workspace (Path): string with the path to the workspace
                   - data_path (Path): string with the path to the data folder
                   - CRS (str): string with the CRS of the project
                   - first_time (str): string with the first date in the format 'YYYY-MM-DD'
                   - last_time (str): string with the last date in the format 'YYYY-MM-DD'
                   - aoi (str): string with the name of the AOI file path
                   - aoi_crs (str, optional): string with the CRS of the AOI. Defaults to None.
                   - passes (list, optional): list of SWOT passes to download. Defaults to None.
                   - tile_names_selection (List[str], optional): list of tile names to select. Defaults to None.
                   - list_dry_dates (List[str], optional): list of dry dates to select. Defaults to None.
                   - list_flood_dates (List[str], optional): list of flood dates to select. Defaults to None.
                   - nodes (int, optional): number of nodes to use for parallel download. Defaults to 4.
                   - do_download (bool, optional): flag to download the data. Defaults to False.
                   - download_type (str, optional): type of download. Defaults to 'PIXC'.
                   - variables (List[str], optional): list of variables to download. Defaults to DEFAULT_VARIABLES.
                   - pixel_resolution (float, optional): pixel resolution of the raster. Defaults to 10.
                   - gdal_grid_options (dict, optional): dictionary with the gdal_grid options. Defaults to dict().
                   - gdal_merge_options (dict, optional): dictionary with the gdal_merge options. Defaults to dict().
                   - GDAL_NUM_THREADS (int, optional): number of threads to use in GDAL. Defaults to 4.
                   - GDAL_CACHEMAX (int, optional): maximum cache size for GDAL. Defaults to 1024.
                   - do_make_gpkg (bool, optional): flag to make the geopackage. Defaults to False.
                   - do_make_tiff (bool, optional): flag to make the tiff files. Defaults to False.
        """
        if isinstance(param_dict, configparser.ConfigParser):
            try:
                gdal_grid_options = dict(param_dict["GDAL_GRID_OPTIONS"])
            except KeyError:
                gdal_grid_options = dict()
            try:
                gdal_merge_options = dict(param_dict["GDAL_MERGE_OPTIONS"])
            except KeyError:
                gdal_merge_options = dict()
            param_dict = dict(param_dict["CONFIG"])
            param_dict['gdal_grid_options'] = gdal_grid_options
            param_dict['gdal_merge_options'] = gdal_merge_options
            param_dict['workspace'] = Path(param_dict['workspace'])
            param_dict['data_path'] = Path(param_dict['data_path'])
            param_dict['aoi'] = Path(param_dict['aoi'])
            if 'passes' in param_dict.keys():
                param_dict['passes'] = list(map(int, param_dict['passes'][1:-1].split(',')))
            if 'variables' in param_dict.keys():
                param_dict['variables'] = list(map(str, param_dict['variables'][1:-1].split(',')))
                param_dict['variables'] = [var.strip() for var in param_dict['variables']]
            if 'do_download' in param_dict.keys():
                param_dict['do_download'] = param_dict['do_download'] == 'True'
            if 'do_make_gpkg' in param_dict.keys():
                param_dict['do_make_gpkg'] = param_dict['do_make_gpkg'] == 'True'
            if 'do_make_tiff' in param_dict.keys():
                param_dict['do_make_tiff'] = param_dict['do_make_tiff'] == 'True'
            if 'tile_names_selection' in param_dict.keys():
                lst_tile = list()
                for tile_str in param_dict['tile_names_selection'][1:-1].split('], ['):
                    lst = [str(i).strip() for i in tile_str.replace('[','').replace(']','').split(',')]
                    lst_tile.append(lst)
                param_dict['tile_names_selection'] = lst_tile
            if 'list_dry_dates' in param_dict.keys():
                param_dict['list_dry_dates'] = list(map(str, param_dict['list_dry_dates'][1:-1].split(',')))
                param_dict["list_dry_dates"] = [date.strip() for date in param_dict["list_dry_dates"]]
            if 'list_flood_dates' in param_dict.keys():
                param_dict['list_flood_dates'] = list(map(str, param_dict['list_flood_dates'][1:-1].split(',')))
                param_dict['list_flood_dates'] = [date.strip() for date in param_dict['list_flood_dates']]
            if 'floodmask_path' in param_dict.keys():
                param_dict['floodmask_path'] = Path(param_dict['floodmask_path'])
            if 'controlmask_path' in param_dict.keys():
                param_dict['controlmask_path'] = Path(param_dict['controlmask_path'])
            if 'esa_worldcover_path' in param_dict.keys():
                param_dict['esa_worldcover_path'] = Path(param_dict['esa_worldcover_path'])
            

        for key in ['project', 'workspace', 'data_path', 'crs', 'first_time', 'last_time', "aoi"]:
            if key not in param_dict.keys():
                raise KeyError(f"Key {key} not found in param_dict")
        
        # mandatory parameters
        self.project : str =  param_dict.get('project')
        self.workspace : Path = param_dict.get('workspace')
        self.data_path : Path = param_dict.get('data_path')
        self.CRS : str = param_dict.get('crs')
        self.first_time : str = param_dict.get('first_time')
        self.last_time : str = param_dict.get('last_time')
        
        # optional parameters
        self.variables : List[str] = param_dict.get('variables', DEFAULT_VARIABLES)
        self.tile_names_selection : List[str] = param_dict.get('tile_names_selection', list())
        self.list_dry_dates : List[str] = param_dict.get('list_dry_dates', list())
        self.list_flood_dates : List[str] = param_dict.get('list_flood_dates', list())
        self.floodmask_path: Path = param_dict.get('floodmask_path', None)
        self.controlmask_path: Path = param_dict.get('controlmask_path', None)
        self.ESA_WC_PATH: Path = param_dict.get('esa_worldcover_path', None)
        do_download : bool = param_dict.get('do_download', False)
        download_type : str = param_dict.get('download_type', 'PIXC')
        passes : List[int] = param_dict.get('passes', None)
        nodes : int = param_dict.get('nodes', 4)
        gdal_grid_options : dict = param_dict.get('gdal_grid_options',dict())
        gdal_merge_options : dict = param_dict.get('gdal_merge_options',dict())
        GDAL_NUM_THREADS : int = param_dict.get('gdal_num_threads',4)
        GDAL_CACHEMAX : int = param_dict.get('gdal_cachemax', 1024)
        do_make_gpkg : bool = param_dict.get('do_make_gpkg', False)
        do_make_tiff : bool = param_dict.get('do_make_tiff', False)
        pixel_resolution : float = param_dict.get('pixel_resolution', 10)
        
        self.swot_collection : SwotCollection = None

        # initialize the paths
        self.define_paths()
        self.check_paths()
        
        # open the AOI
        self.open_aoi(param_dict.get('aoi'), aoi_crs=param_dict.get('aoi_crs', None))
        
        # open masks
        self.floodmask = None
        self.controlmask = None
        if self.floodmask_path is not None:
            self.floodmask = gpd.read_file(self.floodmask_path)
        if self.controlmask_path is not None:
            self.controlmask = gpd.read_file(self.controlmask_path)
            
        # initialize the Downloader and Rasterizer
        self.Downloader = Downloader(
            download_path=self.SWOT_PATH,
            first_time=self.first_time,
            last_time=self.last_time,
            AOI=self.AOI,
            do_download=do_download,
            download_type=download_type,
            passes=passes,
            nodes=nodes,
            )
        
        self.Rasterizer = Rasterizer(
            SWOT_PATH=self.SWOT_PATH,
            AUX_PATH=self.AUX_PATH,
            PATH_GPKG=self.PATH_GPKG,
            TIFF_PATH=self.TIFF_PATH,
            first_time=self.first_time,
            last_time=self.last_time,
            AOI=self.AOI,
            CRS=self.CRS,
            variables=self.variables,
            tile_names_selection= self.tile_names_selection,
            pixel_resolution = pixel_resolution,
            gdal_grid_options=gdal_grid_options,
            gdal_merge_options=gdal_merge_options,
            GDAL_NUM_THREADS=GDAL_NUM_THREADS,
            GDAL_CACHEMAX=GDAL_CACHEMAX,
            do_make_gpkg=do_make_gpkg,
            do_make_tiff=do_make_tiff
        )
        
    def __repr__(self):
        """Representation of the SWOT_PROJECT object"""
        text = f"Class SWOT_PROJECT():"
        for key, item in self.__dict__.items():
            if key == 'Downloader':
                text += f"\n\t{key}: Downloader object"
                for k, i in self.Downloader.__dict__.items():
                    if k == 'results':
                        if i is not None:
                            text += f"\n\t\t{k}: {len(i)} granules"
                        if self.Downloader.passes is not None:
                            text += f" within {self.Downloader.passes} passes"
                    elif self.Downloader.results is not None and k == "passes":
                        pass
                    else:
                        text += f"\n\t\t{k}: {i}"
            elif key == 'Rasterizer':
                text += f"\n\t{key}: Rasterizer object"
                for k, i in self.Rasterizer.__dict__.items():
                    if k == 'AOI':
                        text += f"\n\t\t{k}: {i.geometry[0]}"
                    elif key == 'meta_swot':
                        text += f"\n\t\t{k}: {type(i)}"
                    else:
                        text += f"\n\t\t{k}: {i}"
            elif key == 'AOI':
                text += f"\n\t{key}: {item.geometry[0]}"
            else:
                text += f"\n\t{key}: {item}"
        return text
               
    def check_paths(self):
        """check if the paths exist and create them if they don't
        """
        if self.data_path.joinpath('SWOT').exists() is False:
            self.data_path.joinpath('SWOT').mkdir()
        if self.workspace.exists() is False:
            self.workspace.mkdir()
        if self.data_path.exists() is False:
            self.data_path.mkdir()
        if self.AUX_PATH.exists() is False:
            self.AUX_PATH.mkdir()
        if self.SWOT_PATH.exists() is False:
            self.SWOT_PATH.mkdir()
        if self.PATH_GPKG.exists() is False:
            self.PATH_GPKG.mkdir()
        if self.TIFF_PATH.exists() is False:
            self.TIFF_PATH.mkdir()
        for variable in self.variables:
            variable_path = self.TIFF_PATH.joinpath(variable)
            if variable_path.exists() is False:
                variable_path.mkdir()
        if self.PLOT_PATH.exists() is False:
            self.PLOT_PATH.mkdir()

    def define_paths(self):
        """define the paths of the project
        """
        self.PROJECT_PATH : Path = self.workspace.joinpath(self.project)
        self.SWOT_PATH : Path = self.data_path.joinpath('SWOT', self.project)
        self.AUX_PATH : Path = self.PROJECT_PATH.joinpath('aux_data')
        self.PATH_GPKG : Path = self.PROJECT_PATH.joinpath('gpkg_combined')
        self.TIFF_PATH : Path = self.PROJECT_PATH.joinpath('rasters')
        self.PLOT_PATH : Path = self.PROJECT_PATH.joinpath('plots')
        
    def open_aoi(self, aoi: str, aoi_crs: str=None):
        """open the AOI file and set the BBOX

        Args:
            aoi (str): string with the name of the AOI file path
            aoi_crs (str): string with the CRS of the AOI. Defaults to None.
        """
        if aoi_crs is None:
            aoi_crs = self.CRS
        
        AOI_PATH : Path = self.AUX_PATH.joinpath(aoi)
        if AOI_PATH.suffix in ['.shp', '.geojson', '.gpkg', '.kml', '.json']:
            if AOI_PATH.suffix == '.gpkg':
                self.AOI : gpd.GeoDataFrame = gpd.read_file(AOI_PATH).to_crs(aoi_crs)
            else:
                self.AOI : gpd.GeoDataFrame = gpd.read_file(AOI_PATH, crs=aoi_crs)
        elif isinstance(aoi, dict):
            self.AOI : gpd.GeoDataFrame = gpd.GeoDataFrame(index=[0], geometry=[shape(aoi)], crs=aoi_crs)
        
        self.AOI = self.AOI.to_crs(self.CRS)
        self.BBOX = box(
            self.AOI.bounds['minx'][0],
            self.AOI.bounds['miny'][0],
            self.AOI.bounds['maxx'][0],
            self.AOI.bounds['maxy'][0]
            )
    
    def find_raster(self):
        """find the raster files in the project
        """
        self.rasters_list = list(self.TIFF_PATH.glob('*.tif'))
        
    def select_date(self, date: str):
        """select a date in the project raster_list

        Args:
            date (str): string with the date in the format 'YYYY-MM-DD'
        """
        date = datetime.strptime(date, '%Y-%m-%d').strftime('%Y%m%d')
        return [raster for raster in self.rasters_list if date in raster.name]

    def select_dates(self, dates_list: List[str]):
        """select a list of dates in the project raster_list

        Args:
            dates_list (List[str]): list of strings with the dates in the format 'YYYY-MM-DD'
        """
        lists = [self.select_date(date) for date in dates_list]
        return list(set([item for sublist in lists for item in sublist]))
    
    def create_collection(self):
        """create the SWOT_COLLECTION object"""
        if len(self.list_flood_dates) == 0:
            raise ValueError("No flood dates selected, please add dates before creating the collection")
        if len(self.list_dry_dates) == 0:
            raise ValueError("No dry dates selected, please add dates before creating the collection")
        
        list_flood_paths = self.select_dates(self.list_flood_dates)
        list_dry_paths = self.select_dates(self.list_dry_dates)
        
        dict_collection = {
            "swot_flood_paths": list_flood_paths,
            "swot_dry_paths": list_dry_paths,
            "variables": self.variables,
            "AOI": self.AOI,
            "raster_crs": self.CRS,    
            "floodmask":self.floodmask,
            "controlmask":self.controlmask,
            "ESA_WC_PATH":self.ESA_WC_PATH,
        }
        self.swot_collection = SwotCollection(**dict_collection)
        self.swot_collection.open_rasters()
