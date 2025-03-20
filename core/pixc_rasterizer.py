from typing import List
from pathlib import Path
from datetime import datetime
import pandas as pd
import geopandas as gpd
import numpy as np
import os
import xarray as xr
from auxiliary.tools import interf_coh, noise_to_pixc_index # tools is a module in the auxiliary package of the swot_for_flood package


class Rasterizer():
    """ Utility class to rasterize the SWOT PIXC data
    """
    def __init__(
        self,
        SWOT_PATH:Path,
        AUX_PATH:Path,
        PATH_GPKG:Path,
        TIFF_PATH:Path,
        first_time:str,
        last_time:str,
        AOI: gpd.GeoDataFrame,
        CRS:str,
        variables:List[str],
        tile_names_selection:List[str]=list(),
        gdal_grid_options:dict=dict(),
        gdal_merge_options:dict=dict(),
        GDAL_NUM_THREADS:int=4,
        GDAL_CACHEMAX:int=1024,
        do_make_gpkg:bool=False,
        do_make_tiff:bool=False,
    )-> None:
        """Initialize the Rasterizer class
        
        Args:
            SWOT_PATH (Path): path to the SWOT data
            AUX_PATH (Path): path to the auxiliary data
            PATH_GPKG (Path): path to the geopackage
            TIFF_PATH (Path): path to the tiff files
            first_time (str): string with the first date in the format 'YYYY-MM-DD'
            last_time (str): string with the last date in the format 'YYYY-MM-DD'
            AOI (gpd.GeoDataFrame): geodataframe with the AOI
            CRS (str): EPSG code of the projection
            variables (List[str]): list of variables to rasterize
            tile_names_selection (List[str], optional): list of tile names to select. Defaults to list().
            gdal_grid_options (dict, optional): dictionary with the gdal_grid options. Defaults to dict().
            gdal_merge_options (dict, optional): dictionary with the gdal_merge options. Defaults to dict().
            GDAL_NUM_THREADS (int, optional): number of threads to use. Defaults to 4.
            GDAL_CACHEMAX (int, optional): maximum cache size. Defaults to 1024.
            do_make_gpkg (bool, optional): flag to make the geopackage. Defaults to False.
            do_make_tiff (bool, optional): flag to make the tiff files. Defaults
        """
        self.SWOT_PATH : Path = SWOT_PATH
        self.AUX_PATH : Path = AUX_PATH
        self.PATH_GPKG : Path = PATH_GPKG
        self.TIFF_PATH : Path = TIFF_PATH
        self.first_time : datetime = datetime.strptime(first_time, '%Y-%m-%d')
        self.last_time : datetime = datetime.strptime(last_time, '%Y-%m-%d')
        self.AOI : gpd.GeoDataFrame = AOI
        self.CRS : str = CRS
        self.variables : List[str] = variables
        self.tile_names_selection: List[str] = tile_names_selection
        self.gdal_grid_options : dict = gdal_grid_options
        self.gdal_merge_options : dict = gdal_merge_options
        self.GDAL_NUM_THREADS : int = GDAL_NUM_THREADS
        self.GDAL_CACHEMAX : int = GDAL_CACHEMAX
        
        # create the list of tile names if not provided
        if self.tile_names_selection is None:
            self.SWOT_PATH.name
            list_tile = [name.name for name in self.SWOT_PATH.glob(f'*PIXC*.nc')]
            tiles = [name.split('_')[5] + "_" + name.split('_')[6] for name in list_tile]
            tiles = list(set(tiles))
            passes = list(set([name.split('_')[0] for name in tiles]))
            self.tile_names_selection = []
            for pass_num in passes:
                sublist_tile = [name for name in tiles if pass_num in name]
                self.tile_names_selection.append(sublist_tile)
        else:
            self.tile_names_selection = tile_names_selection
    
        self.find_number_pixels()
        self.find_pixc()
        
        if do_make_gpkg:
            self.picx_to_gpkg()
            
        if do_make_tiff:
            self.gpkg_to_tiff()
    
    def __repr__(self) -> str:
        """Representation of the Rasterizer object"""
        text = f"Class Rasterizer():"
        for key, item in self.__dict__.items():
            if key == 'AOI':
                text += f"\n\t{key}: {item.geometry[0]}"
            elif key == 'meta_swot':
                text += f"\n\t{key}: {type(item)}"
            else:
                text += f"\n\t{key}: {item}"
        return text

    def find_pixc(self) -> None:
        """Find the pixc files for the given pass
        """
        list_time = [name.name.split('_')[7] for name in self.SWOT_PATH.glob(f'*PIXC*.nc')]
        if len(list_time) == 0:
            print(ValueError("No pixc files found, please check the SWOT_PATH of download the data"))
            return
        
        self.list_time_select = sorted(list(set(
            [
                time.split('T')[0] for time in list_time \
                    if datetime.strptime(time, '%Y%m%dT%H%M%S') > self.first_time 
                    and datetime.strptime(time, '%Y%m%dT%H%M%S') < self.last_time
                ]
            )))
        
        self.list_pixc = [list(self.SWOT_PATH.glob(f'*PIXC*{time}*.nc')) for time in self.list_time_select]
        
        self.meta_swot = xr.open_dataset(self.list_pixc[0][1])
    
    def find_number_pixels(self) -> None:
        """Find the number of pixels in the SWOT data
        """
        self.ulx, self.uly, self.lrx, self.lry = self.AOI.total_bounds
        
        self.nrow = np.ceil((self.lrx - self.ulx) / 10)
        self.ncol = np.ceil((self.lry - self.uly) / 10)
        
        self.psx = (self.lrx - self.ulx) / self.ncol
        self.psy = (self.lry - self.uly) / self.nrow
    
    def pixc_to_gpkg(self) -> None:
        """Rasterize the SWOT data
        """
        if self.list_pixc is None:
            raise ValueError("No pixc files found, please the find_pixc() method")
        
        print(">>> Converting the SWOT PIXC netcdf to geopackage")
        
        # loop over the tiles to make list of pixc per tile
        list_pixc_per_tile = []
        for tile_names in self.tile_names_selection:
            for lst in self.list_pixc:
                list_pixc = [pixc for pixc in lst if tile_names[0] in pixc.name]
                list_pixc_per_tile.append(list_pixc)
        
        
        # loop over the list of pixc per tile to make on gpkg of selected variables per tile combining all the pixc
        for list_pixc_item in list_pixc_per_tile:
            print(">>> Working on :")
            SWOT_im_list = []
            for tile in list_pixc_item:
                print('\t', tile.name)
                
                SWOT_im = xr.open_dataset(tile, group='pixel_cloud', engine='netcdf4')
                SWOT_noise_im = xr.open_dataset(tile, group='noise', engine='netcdf4')
                meta_im = xr.open_dataset(tile)
                
                classif_im = SWOT_im.classification.values
                darkwater_filter = (classif_im != 5)
                
                interf = SWOT_im.interferogram.values[:,0] + 1j * SWOT_im.interferogram.values[:,1]
                gamma_tot = interf_coh(interf, SWOT_im.power_plus_y.values, SWOT_im.power_minus_y.values)
                
                num_azimuth_looks = SWOT_im.num_azimuth_looks
                azimuth_offset = SWOT_im.azimuth_offset
                azimuth_index = SWOT_im.azimuth_index.astype(np.int32).to_numpy()
                noise_plus_y = SWOT_noise_im.noise_plus_y.to_numpy()
                noise_minus_y = SWOT_noise_im.noise_minus_y.to_numpy()
                noise_index = azimuth_index * num_azimuth_looks + azimuth_offset
                
                noise_to_pixc = noise_to_pixc_index(noise_index.astype(np.int32), noise_plus_y.astype(np.float32), noise_minus_y.astype(np.float32))
                noise_plus_y_pixc = noise_to_pixc[0]
                noise_minus_y_pixc = noise_to_pixc[1]
                SNR_plus_y =(SWOT_im.power_plus_y - noise_plus_y_pixc) / noise_plus_y_pixc
                SNR_minus_y =(SWOT_im.power_minus_y - noise_minus_y_pixc) / noise_minus_y_pixc
                
                gamma_SNR = 1 / np.sqrt((1+(1/SNR_plus_y))*(1+(1/SNR_minus_y))) # Discussion Pierre Dubois
                gamma_est = gamma_tot / gamma_SNR
                
                data = {}
                for var in self.variables:
                    if var == 'gamma_tot':
                        data[var] = gamma_tot[darkwater_filter]
                    elif var == 'gamma_SNR':
                        data[var] = gamma_SNR[darkwater_filter]
                    elif var == 'gamma_est':
                        data[var] = gamma_est[darkwater_filter]
                    elif var == 'interf_real':
                        data[var] =SWOT_im.interferogram.values[:,0][darkwater_filter]
                    elif var == 'interf_imag':
                        data[var] = SWOT_im.interferogram.values[:,1][darkwater_filter]
                    elif var == 'incidence':
                        data[var] = SWOT_im.inc.values.astype('float32')[darkwater_filter]
                    elif var in ['classification', 'bright_land_flag']:
                        data[var] = SWOT_im[var].values.astype('int32')[darkwater_filter]
                    else:
                        data[var] = SWOT_im[var].values.astype('float32')[darkwater_filter]
                data['latitude'] = SWOT_im.latitude.values.astype('float32')[darkwater_filter]
                data['longitude'] = SWOT_im.longitude.values.astype('float32')[darkwater_filter]
                data['polarization'] = meta_im.polarization
                data['tile_name'] = meta_im.tile_name
                data['time_coverage_start'] = meta_im.time_coverage_start
                
                SWOT_im = gpd.GeoDataFrame(
                    data = data,
                    geometry=gpd.points_from_xy(
                        SWOT_im.longitude.values[darkwater_filter],
                        SWOT_im.latitude.values[darkwater_filter]
                        )
                    )
                SWOT_im = SWOT_im[SWOT_im.geometry.within(self.AOI.to_crs(epsg=4326))]
                SWOT_im = SWOT_im.set_crs(epsg=4326)
                SWOT_im = SWOT_im.to_crs(epsg=self.CRS)
                SWOT_im = SWOT_im.dropna(subset=['latitude', 'longitude'])
                
                SWOT_im_list.append(SWOT_im)
            
            if len(SWOT_im_list) > 0:
                SWOT_combined = pd.concat(SWOT_im_list, ignore_index=True)
                SWOT_combined = SWOT_combined.drop_duplicates(subset=['latitude', 'longitude'], keep='first')
            else:
                SWOT_combined = SWOT_im_list[0]    
            
            SWOT_combined.to_file(self.PATH_GPKG.join(f"SWOT_epsg{self.CRS}_{tile.name.split('_')[7]}.gpkg"), driver='GPKG')
    
    def gpkg_to_tiff(self) -> None:
        """Rasterize the SWOT data into tiff files
        """
        list_gpkg = self.PATH_GPKG.glob("*.gpkg")
        if len(list(list_gpkg)) == 0:
            raise ValueError("No geopackage files found, please generate them with picx_to_gpkg() method or check the PATH_GPKG")
        
        print(">>> Converting the SWOT geopackage to tiff")
        
        list_gpkg = [val for val in list_gpkg if val.name.split('_')[-1].split('T')[0] in self.list_time_select]
        list_gpkg.sort()
        list_tiff = []

        print('>>> Generate tiff for every variables')
        for gdf_path in list_gpkg[::-1]:
            print("Working on ", gdf_path)
            tiff_gpkg = []
            for var in self.variables:
                print(">>> Generate tiff for ", var)
                tif_output = self.TIFF_PATH.join(var, f"{gdf_path.name.split('.')[0]}_{var}.tif")
                tiff_gpkg.append(tif_output)
                # GDAL Grid algorithm that perform IDW interpolation
                # clip the output to the polygon of poly_cut.gpkg, fid = 1 using -clipsrcwhere -clipsrc and -clipsrclayer option
                power = self.gdal_grid_options.get('power', 2.)
                smoothing = self.gdal_grid_options.get('smoothing', 1.)
                radius = self.gdal_grid_options.get('radius', 50.)
                max_points = self.gdal_grid_options.get('max_points', 20.)
                nodata = self.gdal_grid_options.get('nodata', -9999.)
                cmd = f"gdal_grid -a invdistnn:power={power}:smoothing={smoothing}:radius={radius}:max_points={max_points}:nodata={nodata} -txe {self.ulx} {self.lrx} -tye {self.lry} {self.uly} -outsize {self.nrow} {self.ncol} -zfield {var} -of GTiff -ot Float32 {gdf_path} {tif_output} --config GDAL_NUM_THREADS {int(self.GDAL_NUM_THREADS)} --config GDAL_CACHEMAX {int(self.GDAL_CACHEMAX)}"
                
                print(cmd)
                os.system(cmd)
            list_tiff.append(tiff_gpkg)
            
        list_tiff = list_tiff[::-1]
        print('>>> Generate combined tiff')
        for list_var_tiff, gpkg in zip(list_tiff, list_gpkg):
            print("Working on ", gpkg)
            print("file to treat:", list_var_tiff)
            
            output = os.path.join(self.TIFF_PATH, f"{gpkg.name.split('.')[0]}_combined.tif")
            nodata = self.gdal_merge_options.get('nodata', int(-9999))
            nodata_str = str(self.gdal_merge_options.get('nodata', int(-9999))) + " "
            type_tiff = self.gdal_merge_options.get('type', 'Float32')
            
            cmd = f'gdal_merge.py -v -init "{nodata_str*len(self.variables)}" -ps {self.psx} {self.psy} -pct -o {output} -separate -of GTiff -ot {type_tiff} -n {nodata} {" ".join(list_var_tiff)}'
            
            print(cmd)
            os.system(cmd)
    
    def gdalwarp_raster_to_swot_bbox_and_size(self, raster:Path, raster_crs:int, interp:str=None) -> None:
        """Convert the auxiliary raster to tiff with the same resolution  and bounding box as the SWOT tiff
        
        Args:
            raster (Path): path to the raster file to convert
            raster_crs (int): EPSG code of the raster
            interp (str, optional): interpolation method for gdalwarp. Defaults to None.
        """
        print(">>> Converting the AUXILARY rasters to tiff")
        output = self.AUX_PATH.join(raster.name.split('.')[0] + f"_epsg{self.CRS}_nrow{self.nrow}_ncol{self.ncol}.tif")
        
        if interp is None:
            interp = "bilinear"
            if "wc" in raster.name.lower() or "worldcover" in raster.name.lower():
                interp = "near"
        
        cmd = f"gdalwarp -s_srs EPSG:{raster_crs} -t_srs EPSG:{self.CRS} -te {self.ulx} {self.lrx} {self.uly} {self.lry} -ts {self.nrow} {self.ncol} -r {interp} -of GTiff {raster} {output}"
        
        print(cmd)
        os.system(cmd)