# os.environ['PROJ_LIB'] = '/data/home/globc/bonassies/.conda/envs/conda3.10/share/proj'
from pathlib import Path
import earthaccess
import geopandas as gpd
from shapely.geometry import box
import concurrent.futures

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
        nodes:int=4
        )-> None:
        """Initialize the Downloader class

        Args:
            first_date (str): string with the first date in the format 'YYYY-MM-DD'
            last_date (str): string with the last date in the format 'YYYY-MM-DD'
            AOI (gpd.GeoDataFrame): GeoDataFrame of the Area of interest
            passes (list, optional): list of SWOT passes to download. Defaults to None.
            nodes (int, optional): number of nodes to use for parallel download. Defaults to 4.
        """
        self.download_path = download_path
        self.first_time = first_time
        self.last_time = last_time
        AOI = AOI.to_crs(4326)
        self.BBOX = box(
            AOI.bounds['minx'][0],
            AOI.bounds['miny'][0],
            AOI.bounds['maxx'][0],
            AOI.bounds['maxy'][0]
            )
        self.nodes = nodes
        
        self.results = None
        self.passes = passes
        
        self.download_type = download_type
        
        if do_download:
            self.automatic_download()
        else:
            print('No automatic download, please use the Downloader object to download the data')
        
    def search_data(self, short_name:str):
        """main function to search data from the Earth Engine API
        
        Args:
            short_name (str): Shhort name of the SWOT data product to search
        
        Raises:
            Exception: login failed, please check your credentials of the earthaccess module
        """
        try:
            earthaccess.login()
        except Exception as e:
            print('Error: login failed')
            raise e
        
        results = earthaccess.search_data(
            short_name=short_name,
            temporal=(self.first_time, self.last_time),
            bounding_box=self.BBOX.bounds
            )
        print(f"Found {len(results)} granules")
        
        if self.passes is not None:
            for res in results:
                if res['umm']['SpatialExtent']['HorizontalSpatialDomain']['Track']['Passes'][0]['Pass'] not in self.passes:
                    results.remove(res)
            print(f"Found {len(results)} granules within {self.passes} passes")
        
        self.results = results
    
    def search_PIXC(self):
        """search for SWOT_L2_HR_PIXC_2.0 data
        """
        self.search_data('SWOT_L2_HR_PIXC_2.0')
    
    def search_LakeSP(self):
        """search for SWOT_L2_HR_LakeSP_2.0 data
        """
        self.search_data('SWOT_L2_HR_LakeSP_2.0')
    
    def search_Nodes(self):
        """search for SWOT_L2_HR_Nodes_2.0 data
        """
        self.search_data('SWOT_L2_HR_Nodes_2.0')
    
    def automatic_download(self):
        """automatic download of the data from the search results
        
        Raises:
            Exception: Unknown download type
        """
        match self.download_type:
            case 'PIXC':
                self.search_PIXC()
            case 'LakeSP':
                self.search_LakeSP()
            case 'Nodes':
                self.search_Nodes()
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
        if 'LakeSP' in item['meta']['native-id'] or "Nodes" in item['meta']['native-id']:
            path_file = self.download_path.joinpath(item['meta']['native-id'] +".zip")
        if not path_file.exists():
            earthaccess.download(item, self.download_path)
        else:
            print(f"File {item['meta']['native-id']} already exists")
            
    def download_pool(self):
        """download all the data from the search results in parallel

        Raises:
            Exception: no data to download, please search data first
        """
        if self.results is None:
            raise Exception('No data to download, please search data first')
        
        # Create a ThreadPoolExecutor with parallel processes
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.nodes) as executor:
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
        
        