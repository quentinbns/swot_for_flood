# os.environ['PROJ_LIB'] = '/data/home/globc/bonassies/.conda/envs/conda3.10/share/proj'
from pathlib import Path
import earthaccess
import geopandas as gpd
from shapely.geometry import box
import concurrent.futures

class Downloader():
    """ Utility class to download data from the Earth Engine API.
    """
    def __init__(self, download_path: Path, first_time: str, last_time: str, AOI: gpd.GeoDataFrame, passes: list=None, nodes:int=4):
        """_summary_

        Args:
            first_date (str): _description_
            last_date (str): _description_
            AOI (gpd.GeoDataFrame): _description_
            passes (list, optional): _description_. Defaults to None.
            nodes (int, optional): _description_. Defaults to 4.
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
        
    def search_data(self, short_name):
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
        """_summary_
        """
        self.search_data('SWOT_L2_HR_PIXC_2.0')
    
    def search_LakeSP(self):
        """_summary_
        """
        self.search_data('SWOT_L2_HR_LakeSP_2.0')
    
    def search_Nodes(self):
        """_summary_
        """
        self.search_data('SWOT_L2_HR_Nodes_2.0')

    def download(self, item):
        """_summary_

        Args:
            item (_type_): _description_
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
        """_summary_

        Raises:
            Exception: _description_
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
        """_summary_

        Raises:
            Exception: _description_
        """
        if self.results is None:
            raise Exception('No data to download')
        
        for item in self.results:
            self.download(item)
        
        