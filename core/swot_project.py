from pathlib import Path

import geopandas as gpd
from shapely.geometry import shape, box

from core.downloader import Downloader

class SWOT_PROJECT():
    """
    TODO: Add description
    """
    def __init__(self, project: str, workspace: Path, data_path: Path, CRS: str, first_time: str, last_time: str, aoi: str, aoi_crs: str=None, passes:list=None, nodes:int=4):
        """_summary_

        Args:
            project (str): _description_
            workspace (Path): _description_
            data_path (Path): _description_
            CRS (str): _description_
            aoi (str): _description_
        """
        self.project : str =  project
        self.workspace : Path = workspace
        self.data_path : Path = data_path
        self.CRS : str = CRS
        self.first_time : str = first_time
        self.last_time : str = last_time

        self.define_paths()
        self.open_aoi(aoi, aoi_crs)
        
        self.Downloader = Downloader(download_path=self.SWOT_PATH, first_time=self.first_time, last_time=self.last_time, AOI=self.AOI, passes=passes, nodes=nodes)
        
        
    def define_paths(self):
        """_summary_
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
    
            