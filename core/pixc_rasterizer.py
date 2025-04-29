from typing import List
from pathlib import Path
from datetime import datetime
import pandas as pd
import geopandas as gpd
import numpy as np
import os
import xarray as xr
import re
from auxiliary.tools import interf_coh, noise_to_pixc_index, filter_versions # tools is a module in the auxiliary package of the swot_for_flood package

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
        studied_time:List[str]=list(),
        tile_names_selection:List[str]=list(),
        pixel_resolution:float=10,
        gdal_grid_options:dict=dict(),
        gdal_merge_options:dict=dict(),
        GDAL_NUM_THREADS:int=4,
        GDAL_CACHEMAX:int=1024,
        do_make_gpkg:bool=False,
        do_make_tiff:bool=False,
        make_space:bool=False,
        add_darkwater_filter:bool=False
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
            pixel_resolution (float, optional): resolution of the pixel. Defaults to 10.
            gdal_grid_options (dict, optional): dictionary with the gdal_grid options. Defaults to dict().
            gdal_merge_options (dict, optional): dictionary with the gdal_merge options. Defaults to dict().
            GDAL_NUM_THREADS (int, optional): number of threads to use. Defaults to 4.
            GDAL_CACHEMAX (int, optional): maximum cache size. Defaults to 1024.
            do_make_gpkg (bool, optional): flag to make the geopackage. Defaults to False.
            do_make_tiff (bool, optional): flag to make the tiff files. Defaults
            make_space (bool, optional): flag to remove the geopackage and tiff files. Defaults to False.
            add_darkwater_filter (bool, optional): flag to add the dark water into discarding pixel filter. Defaults to False.
        """
        self.SWOT_PATH : Path = SWOT_PATH
        self.AUX_PATH : Path = AUX_PATH
        self.PATH_GPKG : Path = PATH_GPKG
        self.TIFF_PATH : Path = TIFF_PATH
        self.first_time : datetime = datetime.strptime(first_time, '%Y-%m-%d')
        self.last_time : datetime = datetime.strptime(last_time, '%Y-%m-%d')
        self.studied_time : List[datetime] = [datetime.strptime(time, '%Y-%m-%d') for time in studied_time]
        self.AOI : gpd.GeoDataFrame = AOI
        self.CRS : str = CRS
        self.variables : List[str] = variables
        self.tile_names_selection: List[str] = tile_names_selection
        self.pixel_resolution : float = pixel_resolution
        self.gdal_grid_options : dict = gdal_grid_options
        self.gdal_merge_options : dict = gdal_merge_options
        self.GDAL_NUM_THREADS : int = GDAL_NUM_THREADS
        self.GDAL_CACHEMAX : int = GDAL_CACHEMAX
        self.make_space : bool = make_space
        self.add_darkwater_filter : bool = add_darkwater_filter
        
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
            self.pixc_to_gpkg()
            
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

    def find_pixc(self, studied=False) -> None:
        """Find the pixc files for the given pass
        """
        list_time = [name.name.split('_')[7] for name in self.SWOT_PATH.glob(f'*PIXC*.nc')]
        if len(list_time) == 0:
            print(ValueError("No pixc files found, please check the SWOT_PATH of download the data"), flush=True)
            return
        
        if not studied:
            self.list_time_select = sorted(list(set(
                [
                    time.split('T')[0] for time in list_time \
                        if datetime.strptime(time, '%Y%m%dT%H%M%S') > self.first_time 
                        and datetime.strptime(time, '%Y%m%dT%H%M%S') < self.last_time
                    ]
                )))
        else:
            self.list_time_select = sorted(list(set(
                [
                    time.split('T')[0] for time in list_time \
                        if datetime.strptime(time.split('T')[0], '%Y%m%d') in self.studied_time
                    ]
                )))
        self.list_pixc = [list(self.SWOT_PATH.glob(f'*PIXC*{time}*.nc')) for time in self.list_time_select]
        
        self.meta_swot = xr.open_dataset(self.list_pixc[0][0])
    
    def find_number_pixels(self) -> None:
        """Find the number of pixels in the SWOT data
        """
        self.ulx, self.uly, self.lrx, self.lry = self.AOI.total_bounds
        
        self.ncol = np.ceil((self.lrx - self.ulx) / self.pixel_resolution)
        self.nrow = np.ceil((self.lry - self.uly) / self.pixel_resolution)
        
        self.psx = (self.lrx - self.ulx) / self.ncol
        self.psy = (self.lry - self.uly) / self.nrow
    
    def pixc_to_gpkg(self) -> None:
        """Rasterize the SWOT data
        """
        if self.list_pixc is None:
            raise ValueError("No pixc files found, please the find_pixc() method")
        
        print(">>> Converting the SWOT PIXC netcdf to geopackage", flush=True)
        
        # loop over the tiles to make list of pixc per tile
        list_pixc_per_tile = []
        for tile_lst in self.tile_names_selection:
            for pixcs in self.list_pixc:
                decomposed_pixc = ['_'.join(str(pixc.name).split('_')[5:7]) for pixc in pixcs]
                # check if element in decomposed_pixc is in tile_lst
                first_selection = np.isin(decomposed_pixc, tile_lst)
                kept_pixcs = np.array(pixcs)[first_selection].tolist()

                if kept_pixcs != []:
                    versions = filter_versions(np.unique(['_'.join(str(pixc.name).split('_')[-2:]) for pixc in kept_pixcs]))
                    for version in versions:
                        pattern = re.compile(f'.*_{version}')
                        list_pixc_per_tile.append([pixc for pixc in kept_pixcs if pattern.match(str(pixc.name))])
            
        print(list_pixc_per_tile)        
        # loop over the list of pixc per tile to make on gpkg of selected variables per tile combining all the pixc
        for list_pixc_item in list_pixc_per_tile:
            print(">>> Working on :", flush=True)
            SWOT_im_list = []
            for tile in list_pixc_item:
                print('\t', tile.name)
                
                SWOT_im = xr.open_dataset(tile, group='pixel_cloud', engine='netcdf4')
                SWOT_noise_im = xr.open_dataset(tile, group='noise', engine='netcdf4')
                meta_im = xr.open_dataset(tile)
                
                quality_flag = (SWOT_im.interferogram_qual.values == 524288) # Bit value 19 (2^19) => Specular ringing quality flag
                print("Specular Ringing:", np.unique(quality_flag, return_counts=True), flush=True)
                quality_flag_cl = np.logical_or(SWOT_im.classification.values == 6, SWOT_im.classification.values == 7) # Classification of low coherent pixels
                print("Low Coherent:", np.unique(quality_flag_cl, return_counts=True), flush=True)
                
                # Discard low coherent pixels with Specular ringing
                quality_flag = np.where(quality_flag_cl, quality_flag, False)
                print("Pixel discarded:", np.unique(quality_flag, return_counts=True), flush=True)
                quality_flag = ~ quality_flag
                
                darkwater_filter = (SWOT_im.classification.values != 5) # Dark water classification value
                if self.add_darkwater_filter: # if True, discard dark water pixels
                    quality_flag = np.logical_or(quality_flag, darkwater_filter)
                
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
                        data[var] = gamma_tot[quality_flag]
                    elif var == 'gamma_SNR':
                        data[var] = gamma_SNR[quality_flag]
                    elif var == 'gamma_est':
                        data[var] = gamma_est[quality_flag]
                    elif var == 'interf_real':
                        data[var] =SWOT_im.interferogram.values[:,0][quality_flag]
                    elif var == 'interf_imag':
                        data[var] = SWOT_im.interferogram.values[:,1][quality_flag]
                    elif var == 'incidence':
                        data[var] = SWOT_im.inc.values.astype('float32')[quality_flag]
                    elif var in ['classification', 'bright_land_flag']:
                        data[var] = SWOT_im[var].values.astype('int32')[quality_flag]
                    else:
                        data[var] = SWOT_im[var].values.astype('float32')[quality_flag]
                data['latitude'] = SWOT_im.latitude.values.astype('float32')[quality_flag]
                data['longitude'] = SWOT_im.longitude.values.astype('float32')[quality_flag]
                data['polarization'] = meta_im.polarization
                data['tile_name'] = meta_im.tile_name
                data['time_coverage_start'] = meta_im.time_coverage_start
                
                SWOT_im = gpd.GeoDataFrame(
                    data = data,
                    geometry=gpd.points_from_xy(
                        SWOT_im.longitude.values[quality_flag],
                        SWOT_im.latitude.values[quality_flag]
                        ),
                    crs='EPSG:4326'
                    )
                aoi = gpd.GeoDataFrame(geometry=self.AOI.to_crs(4326).geometry, crs='EPSG:4326')
                SWOT_im = SWOT_im.sjoin(aoi, predicate='within')
                SWOT_im = SWOT_im.to_crs(epsg=self.CRS)
                SWOT_im = SWOT_im.dropna(subset=['latitude', 'longitude'])
                
                SWOT_im_list.append(SWOT_im)
            if len(SWOT_im_list) > 0:
                SWOT_combined = pd.concat(SWOT_im_list, ignore_index=True)
                SWOT_combined = SWOT_combined.drop_duplicates(subset=['latitude', 'longitude'], keep='first')
            else:
                SWOT_combined = SWOT_im_list[0]    
            
            SWOT_combined.to_file(self.PATH_GPKG.joinpath(f"SWOT_epsg{self.CRS}_{tile.name.split('_')[7]}.gpkg"), driver='GPKG')
    
    def gpkg_to_tiff(self) -> None:
        """Rasterize the SWOT data into tiff files
        """
        list_gpkg = list(self.PATH_GPKG.glob('*.gpkg'))
        if len(list_gpkg) == 0:
            raise ValueError("No geopackage files found, please generate them with picx_to_gpkg() method or check the PATH_GPKG")
        
        print(">>> Converting the SWOT geopackage to tiff", flush=True)
        
        list_gpkg = [val for val in list_gpkg if val.name.split('_')[-1].split('T')[0] in self.list_time_select]
        list_gpkg.sort()
        list_tiff = []

        print('>>> Generate tiff for every variables')
        for gdf_path in list_gpkg[::-1]:
            print("Working on ", gdf_path, flush=True)
            tiff_gpkg = []
            for var in self.variables:
                print(">>> Generate tiff for ", var, flush=True)
                tif_output = str(self.TIFF_PATH.joinpath(var, f"{gdf_path.name.split('.')[0]}_{var}.tif"))
                if os.path.exists(tif_output):
                    print(f"\t>>> File {tif_output} already exists, deleting file")
                    os.remove(tif_output)
                tiff_gpkg.append(tif_output)
                # GDAL Grid algorithm that perform IDW interpolation
                # clip the output to the polygon of poly_cut.gpkg, fid = 1 using -clipsrcwhere -clipsrc and -clipsrclayer option
                power = self.gdal_grid_options.get('power', 2.)
                smoothing = self.gdal_grid_options.get('smoothing', 1.)
                radius = self.gdal_grid_options.get('radius', 50.)
                max_points = self.gdal_grid_options.get('max_points', 20.)
                nodata = self.gdal_grid_options.get('nodata', -9999.)
                cmd = f"gdal_grid -a invdistnn:power={power}:smoothing={smoothing}:radius={radius}:max_points={max_points}:nodata={nodata} -txe {self.ulx} {self.lrx} -tye {self.lry} {self.uly} -outsize {self.ncol} {self.nrow} -zfield {var} -of GTiff -ot Float32 {gdf_path} {tif_output} --config GDAL_NUM_THREADS {int(self.GDAL_NUM_THREADS)} --config GDAL_CACHEMAX {int(self.GDAL_CACHEMAX)}"
                
                print(cmd, flush=True)
                os.system(cmd)
            list_tiff.append(tiff_gpkg)
        
        if self.make_space:
            print('>>> Removing the geopackage files', flush=True)
            self.remove_gpkg()
        
        list_tiff = list_tiff[::-1]
        print('>>> Generate combined tiff', flush=True)
        for list_var_tiff, gpkg in zip(list_tiff, list_gpkg):
            print("Working on ", gpkg, flush=True)
            print("file to treat:", list_var_tiff, flush=True)
            
            output = str(self.TIFF_PATH.joinpath(f"{gpkg.name.split('.')[0]}_combined.tif"))
            nodata = self.gdal_merge_options.get('nodata', int(-9999))
            nodata_str = str(self.gdal_merge_options.get('nodata', int(-9999))) + " "
            type_tiff = self.gdal_merge_options.get('type', 'Float32')
            
            cmd = f'gdal_merge.py -v -init "{nodata_str*len(self.variables)}" -ps {self.psx} {self.psy} -pct -o {output} -separate -of GTiff -ot {type_tiff} -n {nodata} {" ".join(list_var_tiff)}'
            
            print(cmd, flush=True)
            os.system(cmd)
            
        if self.make_space:
            print('>>> Removing the sub-tiff files', flush=True)
            self.remove_tiff()
    
    def remove_gpkg(self):
        """Remove the geopackage files
        """
        files = list(self.PATH_GPKG.glob('*.gpkg'))
        for file in files:
            os.remove(file)
        os.rmdir(self.PATH_GPKG)
    
    def remove_tiff(self):
        """ Remove the tiff sub-files
        """
        for var in self.variables:
            files = list(self.TIFF_PATH.joinpath(var).glob('*.tif'))
            for file in files:
                os.remove(file)
            os.rmdir(self.TIFF_PATH.joinpath(var))

    def gdalwarp_raster_to_swot_bbox_and_size(self, raster:Path, raster_crs:int, interp:str=None, ncol=None, nrow=None) -> None:
        """Convert the auxiliary raster to tiff with the same resolution  and bounding box as the SWOT tiff
        
        Args:
            raster (Path): path to the raster file to convert
            raster_crs (int): EPSG code of the raster
            interp (str, optional): interpolation method for gdalwarp. Defaults to None.
        """
        if ncol is None:
            ncol = self.ncol
        if nrow is None:
            nrow = self.nrow
        print(">>> Converting the AUXILARY rasters to tiff", flush=True)
        output = self.AUX_PATH.joinpath(raster.name.split('.')[0] + f"_nrow{int(nrow)}_ncol{int(ncol)}.tif")
        
        if interp is None:
            interp = "bilinear"
            if "wc" in raster.name.lower() or "worldcover" in raster.name.lower():
                interp = "near"
        
        cmd = f"gdalwarp -s_srs EPSG:{raster_crs} -t_srs EPSG:{self.CRS} -te {self.ulx} {self.uly} {self.lrx} {self.lry} -ts {ncol} {nrow} -r {interp} -of GTiff {raster} {output}"
        
        print(cmd, flush=True)
        os.system(cmd)