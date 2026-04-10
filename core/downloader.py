# os.environ['PROJ_LIB'] = '/data/home/globc/bonassies/.conda/envs/conda3.10/share/proj'
from pathlib import Path
from typing import List
import earthaccess
import geopandas as gpd
from shapely.geometry import box
import concurrent.futures
from datetime import datetime

class Downloader():
    """ Utility class to download data from the Earth Engine API.
    """
    def __init__(
        self, 
        download_path: Path, 
        first_time: str, 
        last_time: str, 
        AOI: gpd.GeoDataFrame, 
        do_download: bool = False,
        download_type:str="PIXC",
        passes: list=None, 
        nodes:int=4,
        studied_time:List[str]=list(),
        )-> None:
        """Initialize the Downloader class

        Args:
            first_date (str): string with the first date in the format 'YYYY-MM-DD'
            last_date (str): string with the last date in the format 'YYYY-MM-DD'
            AOI (gpd.GeoDataFrame): GeoDataFrame of the Area of interest
            do_download (bool, optional): if True, download the data automatically. Defaults to False.
            download_type (str, optional): type of data to download. Defaults to "PIXC".
            passes (list, optional): list of SWOT passes to download. Defaults to None.
            nodes (int, optional): number of nodes to use for parallel download. Defaults to 4.
            studied_time (List[str], optional): list of dates to download. Defaults to [].
        """
        self.download_path = download_path
        self.download_type = download_type
        self.passes = passes
        self.first_time = first_time
        self.last_time = last_time
        self.studied_time = studied_time
        AOI = AOI.to_crs(4326)
        self.BBOX = box(
            AOI.bounds['minx'][0],
            AOI.bounds['miny'][0],
            AOI.bounds['maxx'][0],
            AOI.bounds['maxy'][0]
            )
        self.nodes = nodes
        
        self.results = None
        
        if do_download:
            self.automatic_download()
        else:
            print('No automatic download, please use the Downloader object to download the data', flush=True)
        
    def __repr__(self):
        """Representation of the Downloader object"""
        text = f"Class Downloader():"
        for key, item in self.__dict__.items():
            if key == 'results':
                if item is not None:
                    text += f"\n\t{key}: {len(item)} granules"
                if self.passes is not None:
                    text += f" within {self.passes} passes"
            elif self.results is not None and key == "passes":
                pass
            else:
                text += f"\n\t{key}: {item}"
        return text
    
    def search_data(self, short_name:str, only_studied=False):
        """main function to search data from the Earth Engine API
        
        Args:
            short_name (str): Shhort name of the SWOT data product to search
        
        Raises:
            Exception: login failed, please check your credentials of the earthaccess module
        """
        try:
            earthaccess.login()
        except Exception as e:
            print('Error: login failed', flush=True)
            raise e
        
        results = earthaccess.search_data(
            short_name=short_name,
            temporal=(self.first_time, self.last_time),
            bounding_box=self.BBOX.bounds
            )
        print(f"Found {len(results)} granules", flush=True)
        
        if self.passes is not None:
            for res in results:
                if res['umm']['SpatialExtent']['HorizontalSpatialDomain']['Track']['Passes'][0]['Pass'] not in self.passes:
                    results.remove(res)
            print(f"Found {len(results)} granules within {self.passes} passes", flush=True)
        if only_studied:
            tmp_results = []
            if len(self.studied_time) > 0:
                for res in results:
                    time_res = datetime.strptime(res['umm']['TemporalExtent']['RangeDateTime']['BeginningDateTime'].split('T')[0], "%Y-%m-%d").date()
                    studied_time = [datetime.strptime(date, "%Y-%m-%d").date() for date in self.studied_time]
                    if (time_res in studied_time):
                        tmp_results.append(res)
                        # print(f"Removing {time_res} from results", flush=True)
                    # else:
                    #     print(f"Keeping {time_res} in results", flush=True)
                results = tmp_results.copy()
            print(f"Found {len(results)} granules within only studied dates", flush=True)
        
        self.results = results
    
    def search_PIXC(self, only_studied=False):
        """search for SWOT_L2_HR_PIXC_2.0 data
        """
        self.search_data('SWOT_L2_HR_PIXC_D', only_studied)
        # self.search_data('SWOT_L2_HR_PIXC_2.0', only_studied)
        
    def search_PIXCVec(self, only_studied=False):
        """search for SWOT_L2_HR_PIXCVec_2.0 data
        """
        # self.search_data('SWOT_L2_HR_PIXCVec_D', only_studied)
        self.search_data('SWOT_L2_HR_PIXCVec_2.0', only_studied)
    
    def search_LakeSP(self, only_studied=False):
        """search for SWOT_L2_HR_LakeSP_2.0 data
        """
        # self.search_data('SWOT_L2_HR_LakeSP_D', only_studied)
        self.search_data('SWOT_L2_HR_LakeSP_2.0', only_studied)
    
    def search_RiverSP(self, only_studied=False):
        """search for SWOT_L2_HR_RiverSP_D data
        """
        self.search_data('SWOT_L2_HR_RiverSP_D', only_studied)
    
    def search_Nodes(self, only_studied=False):
        """search for SWOT_L2_HR_RiverSP_node_2.0 data
        """
        # self.search_data('SWOT_L2_HR_RiverSP_D', only_studied)
        self.search_data('SWOT_L2_HR_RiverSP_node_2.0', only_studied)
    
    def search_Reachs(self, only_studied=False):
        """search for SWOT_L2_HR_RiverSP_reach_2.0 data
        """
        # self.search_data('SWOT_L2_HR_RiverSP_D', only_studied)
        self.search_data('SWOT_L2_HR_RiverSP_reach_2.0', only_studied)
    
    def automatic_download(self, only_studied=False):
        """automatic download of the data from the search results
        
        Raises:
            Exception: Unknown download type
        """
        match self.download_type:
            case 'PIXC':
                self.search_PIXC(only_studied)
            case 'LakeSP':
                self.search_LakeSP(only_studied)
            case 'Nodes':
                # self.search_Nodes(only_studied)
                self.search_RiverSP(only_studied)
            case 'Reaches':
                # self.search_Reachs(only_studied)
                self.search_RiverSP(only_studied)
            case _:
                raise Exception('Unknown download type')
        self.download_pool()

    def download(self, item:earthaccess.results.DataGranule):
        """download a single item from the Earth Engine API

        Args:
            item (earthaccess.results.DataGranule): item from the search results
        """
        if 'PIXC' in item['meta']['native-id']:
            path_file = self.download_path.joinpath(item['meta']['native-id'] +".nc")
        if 'LakeSP' in item['meta']['native-id'] or "RiverSP" in item['meta']['native-id']:
            path_file = self.download_path.joinpath(item['meta']['native-id'] +".zip")
        if not path_file.exists():
            earthaccess.download(item, self.download_path)
        else:
            print(f"File {item['meta']['native-id']} already exists", flush=True)
            
    def download_pool(self):
        """download all the data from the search results in parallel

        Raises:
            Exception: no data to download, please search data first
        """
        if self.results is None:
            raise Exception('No data to download, please search data first')
        
        # Create a ThreadPoolExecutor with parallel processes
        with concurrent.futures.ThreadPoolExecutor(max_workers=int(self.nodes)) as executor:
            # Submit the download tasks to the executor
            futures = [executor.submit(self.download, item) for item in self.results]
            
            # Wait for all tasks to complete
            concurrent.futures.wait(futures)
        # kill the thread pool
        concurrent.futures.thread._threads_queues.clear()
        
    def download_granules(self):
        """download all the data from the search results in series

        Raises:
            Exception: no data to download, please search data first
        """
        if self.results is None:
            raise Exception('No data to download')
        
        for item in self.results:
            self.download(item)
        
        