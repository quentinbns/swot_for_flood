from pathlib import Path

import geopandas as gpd
from shapely.geometry import shape, box

from core.downloader import Downloader

class SWOT_PROJECT():
    """
    TODO: Add description
    """
    def __init__(
        self, 
        project: str, 
        workspace: Path, 
        data_path: Path, 
        CRS: str, 
        first_time: str, 
        last_time: str, 
        aoi: str, 
        download : bool = False,
        download_type: str = 'PIXC',
        variables: list = [
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
            ],
        aoi_crs: str=None, 
        passes:list=None, 
        nodes:int=4
        ) -> None:
        """_summary_

        Args:
            project (str): string with the name of the project
            workspace (Path): string with the path to the workspace
            data_path (Path): string with the path to the data folder
            CRS (str): string with the CRS of the project
            first_time (str): string with the first date in the format 'YYYY-MM-DD'
            last_time (str): string with the last date in the format 'YYYY-MM-DD'
            aoi (str): string with the name of the AOI file path
            aoi_crs (str, optional): string with the CRS of the AOI. Defaults to None.
            passes (list, optional): list of SWOT passes to download. Defaults to None.
            nodes (int, optional): number of nodes to use for parallel download. Defaults to 4.
        """
        self.project : str =  project
        self.workspace : Path = workspace
        self.data_path : Path = data_path
        self.CRS : str = CRS
        self.first_time : str = first_time
        self.last_time : str = last_time
        self.variables : list = variables

        self.define_paths()
        self.check_paths()
        self.open_aoi(aoi, aoi_crs)
        
        self.Downloader = Downloader(
            download_path=self.SWOT_PATH,
            first_time=self.first_time,
            last_time=self.last_time,
            AOI=self.AOI,
            do_download=download,
            download_type=download_type,
            passes=passes,
            nodes=nodes,
            )
               
    def check_paths(self):
        """_summary_
        """
        if self.workspace.exists() is False:
            self.workspace.mkdir()
        if self.data_path.exists() is False:
            self.data_path.mkdir()
        if self.AUX_PATH.exists() is False:
            self.AUX_PATH.mkdir()
        if self.SWOT_PATH.exists() is False:
            self.SWOT_PATH.mkdir()
        if self.S6_PATH.exists() is False:
            self.S6_PATH.mkdir()
        if self.S1_PATH.exists() is False:
            self.S1_PATH.mkdir()
        if self.S2_PATH.exists() is False:
            self.S2_PATH.mkdir()
        if self.S3_PATH.exists() is False:
            self.S3_PATH.mkdir()
        if self.JASON_PATH.exists() is False:
            self.JASON_PATH.mkdir()
        if self.FABDEM_PATH.exists() is False:
            self.FABDEM_PATH.mkdir()
        if self.INSITU_PATH.exists() is False:
            self.INSITU_PATH.mkdir
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
        self.S6_PATH : Path = self.data_path.joinpath('S6', self.project)
        self.S1_PATH : Path = self.data_path.joinpath('S1', self.project)
        self.S2_PATH : Path = self.data_path.joinpath('S2', self.project)
        self.S3_PATH : Path = self.data_path.joinpath('S3', self.project)
        self.JASON_PATH : Path = self.data_path.joinpath('JASON', self.project)
        self.FABDEM_PATH : Path = self.data_path.joinpath('FABDEM', self.project)
        self.INSITU_PATH : Path = self.data_path.joinpath('insitu', self.project)
        self.PATH_GPKG : Path = self.PROJECT_PATH.joinpath('gpkg_combined')
        self.TIFF_PATH : Path = self.PROJECT_PATH.joinpath('rasters')
        self.PLOT_PATH : Path = self.PROJECT_PATH.joinpath('plots')
        
    def open_aoi(self, aoi: str, aoi_crs: str=None):
        """_summary_

        Args:
            aoi (str): _description_
            aoi_crs (str): _description_
        """
        if aoi_crs is None:
            aoi_crs = self.CRS
        
        AOI_PATH : Path = self.AUX_PATH.joinpath(aoi)
        if AOI_PATH.suffix in ['.shp', '.geojson', '.gpkg', '.kml', '.json']:
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
    
            