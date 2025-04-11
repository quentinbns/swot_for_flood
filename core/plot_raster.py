""" 
Contains classes and functions for plotting the raster data
Uses the SWOT_RASTER, SWOT_COLLECTION and SWOT_MEAN classes as input data

Displaying maps uses EOmaps packages
Histograms and scatter plots use seaborn and/or matplotlib
"""
import os
from typing import Tuple, List
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import patches as mpatches
from matplotlib import patheffects
import seaborn as sns
from eomaps import Maps
from cmap import Colormap
import rioxarray as rxr
from rasterio import features
from shapely import geometry
import geopandas as gpd

from time import time

from core.swot_project import SwotProject
from core.swot_raster import SwotCollection
from auxiliary.cbar_ESA_WC import *
from auxiliary.cbar_SWOT import *
from auxiliary.plot_variables import *

class PlotRaster():
    """ Uses the SWOT_RASTER, SWOT_COLLECTION or SWOT_MEAN classes as input data to plot the raster data """
    def __init__(self, project:SwotProject, save_fig:bool=True, show_fig:bool=False):
        """ Initialize the class with the project data """
        self.project = project
        
        # Fast access to the project data
        self.BBOX = project.BBOX
        self.CRS = project.CRS
        self.swot_collection : SwotCollection = project.swot_collection
        self.PATH_TO_SAVE : Path = project.PLOT_PATH
        
        self.define_plot_directories()
        
        # Save and show the figure
        self.save_fig = save_fig
        self.show_fig = show_fig
    
    def define_plot_directories(self):
        """ Define the directories to save the plots """
        if not self.PATH_TO_SAVE.exists():
            self.PATH_TO_SAVE.mkdir(parents=True)
        if not (self.PATH_TO_SAVE / "maps").exists():
            (self.PATH_TO_SAVE / "maps").mkdir()
        if not (self.PATH_TO_SAVE / "histograms").exists():
            (self.PATH_TO_SAVE / "histograms").mkdir()
        if not (self.PATH_TO_SAVE / "scatter").exists():
            (self.PATH_TO_SAVE / "scatter").mkdir()
    
    @staticmethod
    def get_label(variable:str)->str:
        """ Get the label of the variable """
        match variable:
            case "height":
                return LABEL_PCOH
            case "coherent_power":
                return LABEL_PCOH
            case "sig0":
                return LABEL_SIG0
            case "gamma_est":
                return LABEL_GAMMA_EST
            case "gamma_tot":
                return LABEL_GAMMA_TOT
            case "gamma_SNR":
                return LABEL_GAMMA_SNR
            case "incidence":
                return 'Incidence angle [deg]'
            case _:
                return variable
    
    @staticmethod
    def select_color_world_cover(color:str, world_cover_selection:str)->str:
        """ Select the color of the histogram based on the world cover selection """
        match world_cover_selection:
            case "forest": 
                color = '#00a000'
            case "urban":
                color = '#c31400'
            case "open":
                color = '#ffb400'
            case _:
                color = color
        return color
    
    @staticmethod
    def get_floodmask_colormap(add_uncertainty:bool=False) -> Tuple[Colormap, dict]:
        """ Get the colormap and the color labels for mask data
        
        Args:
            add_uncertainty (bool): Add the uncertainty in the colormap. Default is False.
        Returns:
            Tuple[Colormap, dict]: The colormap and the color labels
        """ 
        
        color_dict = {
            # 1: 'red',        # urban
            # 2: 'forestgreen',      # forest
            # 3: 'cornflowerblue',       # open
            1: 'darkred',   
            2: 'darkgreen', 
            3: 'darkblue',  
            }
        color_labels = {
            1: 'Flooded urban',
            2: 'Flooded forest',
            3: 'Flooded open',
            }
        if add_uncertainty:
            color_dict_uncertainty = { 
                11: 'red',        # urban
                12: 'limegreen',      # forest
                13: 'cornflowerblue',       # open
                # 11: 'darkred',     # urban potential dark water
                # 12: 'darkgreen',      # forest potential dark water
                # 13: 'darkblue',     # open potential dark water
                21: 'dimgrey',    # urban low SNR
                22: 'grey',    # forest low SNR
                23: 'darkgrey',      # open low SNR
                # 11: 'rosybrown',     # urban potential dark water
                # 12: 'yellowgreen',      # forest potential dark water
                # 13: 'darkcyan',     # open potential dark water
                # 21: 'darkred',    # urban low SNR
                # 22: 'darkgreen',    # forest low SNR
                # 23: 'darkblue',      # open low SNR
                }
            color_labels_uncertainty = {
                11: 'urban potential dark water',
                12: 'forest potential dark water',
                13: 'open potential dark water',
                21: 'urban low SNR',
                22: 'forest low SNR',
                23: 'open low SNR',
            }
            color_dict.update(color_dict_uncertainty)
            color_labels.update(color_labels_uncertainty)

        # make cmap
        range_color = np.linspace(0, 255, 255)
        range_color = ["black" for _ in range_color.tolist()]
        for key, value in color_dict.items():
            range_color[key] = value
        cmap = Colormap(range_color)
        
        return cmap.to_matplotlib(), color_labels
    
    @staticmethod
    def f1_score(true, pred):
        """ Compute the F1 score """
        # remove NaN values
        true = true[~np.isnan(true)].flatten()
        pred = pred[~np.isnan(pred)].flatten()        
        true.astype(int)
        pred.astype(int)
        
        TP_scale = np.sum(np.logical_and(true == 1, pred == 1))
        FP_scale = np.sum(np.logical_and(true == 0, pred == 1))
        FN_scale = np.sum(np.logical_and(true == 1, pred == 0))
        if TP_scale == np.nan:
            TP_scale = 0
        if FP_scale == np.nan:
            FP_scale = 0
        if FN_scale == np.nan:
            FN_scale = 0
        if TP_scale + FP_scale == 0:
            precision = 0
        else:
            precision = TP_scale / (TP_scale + FP_scale)
        if TP_scale + FN_scale == 0:
            recall = 0
        else:
            recall = TP_scale / (TP_scale + FN_scale)
        if precision + recall == 0:
            f1 = 0
        else:
            f1 = 2 * ((precision * recall) / (precision + recall))
        return f1
    
    def add_missing_values(self, data_type:str, data_area:str, map_obj:Maps, time_selection:str) -> Maps:
        """ Add the missing values to the data
        Args:
            data_type (str): the type of data to add the missing values
            data_area (str): the area of the data to add the missing values
            map_obj (Maps): the map object to add the missing values
            time_selection (str): the time selection to add the missing values
        Returns:
            Maps: the map object with the missing values added
            handle (mpatches.Patch): the handle of the missing values
        """
        mask_holes = self.swot_collection.get_holes_mask(data_area, data_type)
        try:
            mask_holes = mask_holes.sel(time=time_selection)
        except:
            print("Warning: The mask holes does not have a time dimension or an empty time dimension")
            pass
    
        try:
            mask_holes = mask_holes.isel(time=0)
        except:
            print("Warning: The mask holes does not have a time dimension or an empty time dimension")
            pass
        
        m_mask = map_obj.new_layer()
        shapes = features.shapes(mask_holes.values.astype(np.uint8), transform=mask_holes.rio.transform())
        geo_list = []
        for poly, val in shapes:
            if val == 0:
                continue
            geo_list.append(geometry.shape(poly))
        gpd_mask = gpd.GeoDataFrame(geometry=geo_list, crs=self.CRS)
        # gpd_mask.plot(ax=m_mask.ax, color='black', edgecolor='none', linewidth=0.0001, hatch='////', alpha=0.1, zorder=0)  
        gpd_mask.plot(ax=m_mask.ax, color='black', alpha=1, zorder=0)  
        
        # handle = mpatches.Patch(facecolor='none', edgecolor='black', hatch='////', label='No Data or discarded data')
        handle = mpatches.Patch(facecolor='black', edgecolor='none', label='No Data or discarded data')
        
        return m_mask, handle    
        
    def plot_all_rasters(
        self, 
        variable:str,
        cmap:str='viridis',
        vmin:float=None,
        vmax:float=None,       
        ) -> Tuple[plt.Figure, plt.Axes]:
        """ Uses the raster data to plot all the rasters in a single figure
        
        Args:
            variable (str): the variable to plot
            cmap (str): the colormap to use. Default is 'viridis'.
            vmin (float): the minimum value of the colormap. Default is None.
            vmax (float): the maximum value of the colormap. Default is None.
        Returns:
            Tuple[plt.Figure, plt.Axes]: The figure and axes of the plot
        """
        import rasterio as rio
        from rasterio.plot import show
        from datetime import datetime
        
        if variable not in self.swot_collection.variables:
            raise ValueError(f"The variable {variable} is not in the collection")
        
        # Get the list of rasters paths
        self.project.find_raster()
        list_rasters = self.project.rasters_list
        list_rasters.sort()
        
        index_variable = self.swot_collection.variables.index(variable) + 1
        
        ncols = 3
        nrows = int(np.ceil(len(list_rasters) / ncols))
        if ncols * nrows < len(list_rasters):
            nrows += 1
        fig, axs = plt.subplots(nrows, ncols, figsize=(5*ncols, 5*nrows))
                
        for i, raster in enumerate(list_rasters):
            raster = rio.open(raster)
            time_str = datetime.strptime(raster.name.split("_")[-2], "%Y%m%dT%H%M%S")
            data = raster.read(index_variable)
            trfm = raster.transform
            ax = axs[i // ncols, i % ncols]
            show(data, transform=trfm, ax=ax, cmap=cmap, vmin=vmin, vmax=vmax)
            ax.set_title(time_str.strftime("%Y-%m-%d %H:%M"))
        
        for i in range(len(list_rasters), nrows * ncols):
            fig.delaxes(axs[i // ncols, i % ncols])
            
        fig.tight_layout()
        
        if self.save_fig:
            title_str = f"all_rasters_{variable}"
            path = self.PATH_TO_SAVE.joinpath("maps", title_str + ".png")
            fig.savefig(path, dpi=300)
        
        if self.show_fig:
            fig.show()
        return fig, axs
           
    def plot_auxiliary_data(
        self,
        path_to_raster:Path,
        data_area:str="global",
        is_multiband:bool=False,
        is_worldcover:bool=False,
        make_mask=False,
        mask_value:int=0,
        vmin:float=None,
        vmax:float=None,
        cmap:str='grey',
        title:str=None,
        fig:plt.Figure=None,
        ax:plt.Axes=None,
        dpi:int=300,
        add_bkg:bool=False,
        add_cbar:bool=True
    ) -> Tuple[plt.Figure, plt.Axes]:
        """ Plot the auxiliary data
        
        Args:
            path_to_raster (Path): the path to the raster to plot
            data_area (str): the area to plot ('global', 'control', 'flood')
            is_multiband (bool): If True, the raster is a multiband raster. Default is False.
            is_worldcover (bool): If True, the raster is a world cover raster. Default is False.
            vmin (float): The minimum value of the colormap. Default is None.
            vmax (float): The maximum value of the colormap. Default is None.
            cmap (str): The colormap to use. Default is 'grey'.
            title (str): The title of the plot. Default is None.
            fig (plt.Figure): The figure to plot on. Default is None.
            ax (plt.Axes): The axes to plot on. Default is None.
            dpi (int): The dpi of the plot to save. Default is 300.
            add_bkg (bool): Add a background map (OpenStreetMap). Default is False.
            add_cbar (bool): Add a colorbar. Default is True.
        Returns:
            Tuple[plt.Figure, plt.Axes]: The figure and axes of the plot
        """
        import rasterio as rio
        from rasterio.plot import show
        import matplotlib.patches as mpatches
        
        if not path_to_raster.exists():
            raise ValueError(f"The path {path_to_raster} does not exist")
        
        if fig is None:
            map_obj = Maps(crs=self.CRS, figsize=(10, 10))
            fig = map_obj.f
            ax = map_obj.f.axes
        else:
            map_obj = Maps(crs=self.CRS, ax=ax, f=fig)
        
        # get data
        data = rxr.open_rasterio(path_to_raster)
        
        if not is_multiband:
            data = data.sel(band=1)
        
        if is_worldcover:
            data = data.where(data != 255)
            cmap_ESAWC, normalizer_ESAWC, boundaries_ESAWC, ticks_ESAWC, tick_labels_ESAWC, values_ESAWC = defined_ESAWC_cmap()
            cmap = cmap_ESAWC
            vmin = 0
            vmax = 255
        
        # get the data on the requested time
        if "time" in data.dims:
            if data.time.size > 1:
                print(f"Warning: {data['time'].size} time steps selected. Only the first one will be used.")
            data = data.isel(time=0)
        
        if is_multiband:
            data = rio.open(path_to_raster)
            trfm = data.transform
            
        if make_mask:
            data.values = np.where(data.values == mask_value, 1, 0)
            
        # Get extent of the data
        match data_area:
            case "global":
                poly = self.BBOX
                extents = [poly.bounds[0], poly.bounds[2], poly.bounds[1], poly.bounds[3]]
            case "control":
                poly = self.swot_collection.controlmask
                extents = [poly.bounds["minx"], poly.bounds["maxx"], poly.bounds["miny"], poly.bounds["maxy"]]
            case "flood":
                poly = self.swot_collection.floodmask
                extents = [poly.bounds["minx"], poly.bounds["maxx"], poly.bounds["miny"], poly.bounds["maxy"]]
        
        # set extent and crs
        map_obj.set_extent(extents=extents, crs=self.CRS)

        g = map_obj.add_gridlines(lw=0.25, alpha=0.5, zorder=0)
        gl = g.add_labels(where="blr",fontsize=8, every = 2)
        # c = map_obj.add_compass(style='compass', pos=(0.9, 0.85), scale=7)

        # add title
        if title is not None:
            map_obj.add_title(title, y=1)
        else:
            if 'time' in data.dims:
                time_str = data['time'].dt.strftime("%Y-%m-%d %H:%M").values
                if data['time'].size > 1:
                    time_str = time_str[0]
                map_obj.add_title(f"Auxiliary data - {time_str}", y=1)
            else:
                map_obj.add_title(f"Auxiliary data - {path_to_raster.stem}", y=1)
            
        # add background
        if add_bkg:
            m_bkg = map_obj.new_layer()
            m_bkg.add_wms.OpenStreetMap.add_layer.default()
        
        # add data
        m_data = map_obj.new_layer()
        if not is_multiband:
            m_data.set_data(data, x="x", y="y", crs=self.CRS)
            m_data.set_shape.raster()
            m_data.plot_map(cmap=cmap, vmin=vmin, vmax=vmax)
        else:
            show(data, ax=m_data.ax, transform=trfm)
            
        if add_cbar and not is_multiband:
            if not is_worldcover:
                m_data.add_colorbar(label=data.name, hist_size=0, shrink=0.5, pad=0.05)
            else:
                aaxx = map_obj.ax
                ll = []
                for value, label in zip(values_ESAWC, tick_labels_ESAWC):
                    ll.append(mpatches.Patch(color=cmap_ESAWC(value), label=label))
                
                aaxx.legend(handles=ll, fontsize=10, loc="upper left", handlelength=1, handleheight=1)
                
        if self.save_fig:
            name_stripped = '_'.join(path_to_raster.stem.split(" "))
            name_stripped = name_stripped.replace("-", "").replace("(", "").replace(")", "").replace(':', "")
            if 'time' in data.dims:
                time_str = data['time'].dt.strftime("%Y%m%dT%H%M%S").values
                if data['time'].size > 1:
                    time_str = time_str[0]
                title_str = title if title is not None else f"auxiliary_data_{name_stripped}_{time_str}"
            else:
                title_str = title if title is not None else f"auxiliary_data_{name_stripped}"
            path = self.PATH_TO_SAVE.joinpath("maps", title_str + ".png")
            m_data.savefig(path, dpi=dpi)
            
        if self.show_fig:
            m_data.show()
            
        return map_obj.f, map_obj.f.axes
         
    def plot_classification(
        self,
        data_area:str="global",
        time_selection=None,
        title=None,
        add_legend:bool=False,
        dpi:int=300,
        show_fig:bool=None,
        save_fig:bool=None,
        fig:plt.Figure=None,
        ax:plt.Axes=None,
        **kwargs
    ) -> Tuple[plt.Figure, plt.Axes]:
        """ Plot the classification map
        Args:
            data_area (str): the area to plot ('global', 'control', 'flood')
            time_selection (str): the time selection to plot. Default is None.
            title (str): The title of the plot. Default is None.
            add_legend (bool): Add a legend to the plot. Default is False.
            dpi (int): The dpi of the plot to save. Default is 300.
            show_fig (bool): Show the figure. Default is False.
            save_fig (bool): Save the figure. Default is False.
            fig (plt.Figure): The figure to plot on. Default is None.
            ax (plt.Axes): The axes to plot on. Default is None.
            **kwargs: Additional arguments to pass to the plotting function
        Returns:
            Tuple[plt.Figure, plt.Axes]: The figure and axes of the plot
        """
        
        data = self.swot_collection.get_variable("classification", data_area, "swot", None).copy()
        label_data = self.get_label("classification")
        if data['time'].size > 1:
            print(f"Warning: {data['time'].size} time steps selected. Only the first one will be used.")
        if time_selection is not None:
            data = data.sel(time=time_selection)
        data = data.isel(time=0)
        
        if save_fig is None:
            save_fig = self.save_fig
        if show_fig is None:
            show_fig = self.show_fig
            
        if fig is None:
            map_obj = Maps(crs=self.CRS, figsize=(10, 10))
            fig = map_obj.f
            ax = map_obj.ax
        else:
            map_obj = Maps(crs=self.CRS, f=fig, ax=ax)
            
        # get extent of the data
        match data_area:
            case "global":
                poly = self.BBOX
                extents = [poly.bounds[0], poly.bounds[2], poly.bounds[1], poly.bounds[3]]
            case "control":
                poly = self.swot_collection.controlmask
                extents = [poly.bounds["minx"], poly.bounds["maxx"], poly.bounds["miny"], poly.bounds["maxy"]]
            case "flood":
                poly = self.swot_collection.floodmask
                extents = [poly.bounds["minx"], poly.bounds["maxx"], poly.bounds["miny"], poly.bounds["maxy"]]
        
        # create map
        
        map_obj.set_extent(extents=extents, crs=self.CRS)
        g = map_obj.add_gridlines(lw=0.25, alpha=0.5, zorder=0)
        gl = g.add_labels(where="blr",fontsize=8, every = 2)
        # c = map_obj.add_compass(style='compass', pos=(0.9, 0.85), scale=7)
        
        if title is not None:
            map_obj.add_title(title, y=1)
        else:    
            time_str = data['time'].dt.strftime("%Y-%m-%d %H:%M").values
            if data['time'].size > 1:
                time_str = time_str[0]
            map_obj.add_title(f"{label_data} - {time_str}", y=1)
            
        map_obj.set_data(data, x="x", y="y", crs=self.CRS, parameter=label_data)
        map_obj.set_shape.raster()
        
        cmap_SWOT, normalizer_SWOT, _, _, tick_labels_SWOT, values_SWOT = defined_SWOT_cmap()
        map_obj.plot_map(cmap=cmap_SWOT, norm=normalizer_SWOT, vmin=0, vmax=255, **kwargs)
        
        if add_legend:
            aaxx = map_obj.ax
            ll = []
            for value, label in zip(values_SWOT, tick_labels_SWOT):
                ll.append(mpatches.Patch(color=cmap_SWOT(value), label=label))
            
            aaxx.legend(handles=ll, fontsize=10, loc="lower right", handlelength=1, handleheight=1)
            
        if save_fig:
            time_str = data['time'].dt.strftime("%Y%m%dT%H%M%S").values
            if data['time'].size > 1:
                time_str = time_str[0]
            title_str = title if title is not None else f"classification_{data_area}_{time_str}"
            path = self.PATH_TO_SAVE.joinpath("maps", title_str + ".png")
            fig.savefig(path, dpi=dpi)
        
        if show_fig:
            fig.show()
            
        return map_obj.f, map_obj.ax
        
    def plot_map(
        self,
        variable:str,
        data_area:str="global",
        data_type:str="swot",
        world_cover_selection:str=None,
        time_selection:str=None,
        fig:plt.Figure=None,
        ax:plt.Axes=None,
        title:str=None,
        dpi:int=300,
        cmap:str='viridis',
        vmin:float=None,
        vmax:float=None,
        add_bkg:bool=True,
        add_cbar:bool=True,
        save_fig:bool=None,
        show_fig:bool=None,
        figsize:Tuple[int, int]=(10, 10),
        **kwargs
        ) -> Tuple[plt.Figure, plt.Axes]:
        """ Plot the map of the variable 
        
        Args:
            data_type (str): 
            variable (str): the variable to plot
            data_area (str): the area to plot ('global', 'control', 'flood')
            data_type (str): the type of data to plot ('swot', 'mean', 'diff')
            world_cover_selection (str): the world cover selection to plot (None, "open", "forest", "urban"). Default is None.
            time_selection (str): the time selection to plot. Default is None.
            title (str): The title of the plot. Default is None.
            fig (plt.Figure): The figure to plot on. Default is None.
            ax (plt.Axes): The axes to plot on. Default is None.
            dpi (int): The dpi of the plot to save. Default is 300.
            cmap (str): The colormap to use. Default is 'viridis'.
            vmin (float): The minimum value of the colormap. Default is None.
            vmax (float): The maximum value of the colormap. Default is None.
            add_bkg (bool): Add a background map (OpenStreetMap). Default is True.
            add_cbar (bool): Add a colorbar. Default is True.
            **kwargs: Additional arguments to pass to the plotting function
        Returns:
            Tuple[plt.Figure, plt.Axes]: The figure and axes of the plot
        """
        if variable is None:
            raise ValueError("The variable must be given")
        if variable not in self.swot_collection.variables:
            raise ValueError(f"The variable {variable} is not in the collection")
        
        if save_fig is None:
            save_fig = self.save_fig
        if show_fig is None:
            show_fig = self.show_fig
        
        # Get the data
        data = self.swot_collection.get_variable(variable, data_area, data_type, world_cover_selection).copy()
        label_data = self.get_label(variable)
        
        # Get the data on the requested time
        if "time" in data.dims:
            if time_selection is not None:
                data = data.sel(time=time_selection)
            if data['time'].size > 1:
                print(f"Warning: {data['time'].size} time steps selected. Only the first one will be used.")
            data = data.isel(time=0)
        
        # Get extent of the data
        match data_area:
            case "global":
                poly = self.BBOX
                extents = [poly.bounds[0], poly.bounds[2], poly.bounds[1], poly.bounds[3]]
            case "control":
                poly = self.swot_collection.controlmask.to_crs(self.CRS)
                extents = [poly.bounds["minx"], poly.bounds["maxx"], poly.bounds["miny"], poly.bounds["maxy"]]
            case "flood":
                poly = self.swot_collection.floodmask.to_crs(self.CRS)
                extents = [poly.bounds["minx"], poly.bounds["maxx"], poly.bounds["miny"], poly.bounds["maxy"]]
        
        map_obj = Maps(crs=self.CRS, f=fig, ax=ax, figsize=figsize)
        map_obj.set_extent(extents=extents, crs=self.CRS)
        g = map_obj.add_gridlines(lw=0.25, alpha=0.5, zorder=0)
        gl = g.add_labels(where="blr",fontsize=8, every = 2)
        # c = map_obj.add_compass(style='compass', pos=(0.9, 0.85), scale=7)
        
        if title is not None:
            map_obj.add_title(title, y=1, fontsize=14)
        else:    
            try:
                time_str = data['time'].dt.strftime("%Y-%m-%d %H:%M").values
                if data['time'].size > 1:
                    time_str = time_str[0]
            except:
                time_str = "mean"
            if world_cover_selection is not None:
                label_data += f" - {world_cover_selection} areas"
            map_obj.add_title(f"{label_data} - {time_str}", y=1, fontsize=14)
        
        if add_bkg:
            m_bkg = map_obj.new_layer()
            m_bkg.add_wms.OpenStreetMap.add_layer.default()
        
        # Adding missing values
        m_mask, handle = self.add_missing_values(data_type, data_area, map_obj, time_selection)
        
        m_data = map_obj.new_layer()
        m_data.set_data(data, x="x", y="y", crs=self.CRS, parameter=label_data)
        m_data.set_shape.raster()

        m_data.plot_map(vmin=vmin, vmax=vmax, cmap=cmap, **kwargs)
        if add_cbar:
            m_data.add_colorbar()
            map_obj.ax.legend(handles=[handle], loc='lower left', fontsize=10, handlelength=2, handleheight=1)
        
        if save_fig:
            time_str = data['time'].dt.strftime("%Y%m%dT%H%M%S").values
            if data['time'].size > 1:
                time_str = time_str[0]
                
            filename = f"{variable}_{data_area}_{data_type}_{time_str}"
            if world_cover_selection is not None:
                filename += f"_{world_cover_selection}"
                
            path = self.PATH_TO_SAVE.joinpath("maps", filename + ".png")
            m_data.savefig(path, dpi=dpi)
            
        if show_fig:
            m_data.show()
            
        return map_obj.f, map_obj.f.axes
    
    def plot_histogram(
        self,
        variable:str,
        data_area:str="global",
        data_type:str="swot",
        world_cover_selection:str=None,
        time_selection:str=None,
        add_mean:bool=True,
        fig:plt.Figure=None,
        ax:plt.Axes=None,
        title:str=None,
        set_title:bool=True,
        dpi:int=300,
        bins:int=100,
        range_hist:List[float]=None,
        color:str='blue',
        use_seaborn:bool=True,
        save_fig:bool=None,
        show_fig:bool=None,
        add_xlabel:bool=True,
        add_ylabel:bool=True,
        y_text:float=0.24,
        y_text_mean:float=0.05,
        ha:str='left',
        va:str='top',
        ha_mean:str='right',
        **kwargs
        ) -> Tuple[plt.Figure, plt.Axes]:
        """ Plot the histogram of the variable
        
        Args:
            variable (str): the variable to plot
            data_area (str): the area to plot ('global', 'control', 'flood')
            data_type (str): the type of data to plot ('swot', 'mean', 'diff')
            world_cover_selection (str): the world cover selection to plot (None, "open", "forest", "urban"). Default is None.
            time_selection (str): the time selection to plot. Default is None.
            add_mean (bool): Add the histogram of the mean data (in grey color). Default is True.
            title (str): The title of the plot. Default is None.
            set_title (bool): Set the title of the plot. Default is True.
            fig (plt.Figure): The figure to plot on. Default is None.
            ax (plt.Axes): The axes to plot on. Default is None.
            dpi (int): The dpi of the plot to save. Default is 300.
            bins (int): The number of bins in the histogram. Default is 100.
            color (str): The color of the histogram. Default is 'blue'.
            use_seaborn (bool): Use seaborn to plot the histogram else use matplotlib. Default is True.
            **kwargs: Additional arguments to pass to the plotting function
        Returns:
            Tuple[plt.Figure, plt.Axes]: The figure and axes of the plot
        """
        if variable is None:
            raise ValueError("The variable must be given")
        if variable not in self.swot_collection.variables:
            raise ValueError(f"The variable {variable} is not in the collection")
        
        if save_fig is None:
            save_fig = self.save_fig
        if show_fig is None:
            show_fig = self.show_fig
        
        if data_type == "diff" or data_type == "mean":
            add_mean = False
            print("Warning: The mean data will not be plotted in the histogram with diff or mean data type")
        
        # Get the data
        data = self.swot_collection.get_variable(variable, data_area, data_type, world_cover_selection).copy()
        label_data = self.get_label(variable)
        
        # Get the data on the requested time
        if "time" in data.dims:
            if time_selection is not None:
                data = data.sel(time=time_selection)
                if data['time'].size > 1:
                    print(f"Warning: {data['time'].size} time steps selected. Only the first one will be used.")
            data = data.isel(time=0)
        # Set specific color if world_cover_selection is given
        color = self.select_color_world_cover(color, world_cover_selection)
            
        # Plot the histogram
        if fig is None:
            fig, ax = plt.subplots()
        if use_seaborn:
            if range_hist is not None:
                sns.histplot(data.values.flatten(), element='step',binrange=range_hist, bins=bins, color=color, ax=ax, alpha=0.7, **kwargs)
            else:
                sns.histplot(data.values.flatten(), element='step', bins=bins, color=color, ax=ax, alpha=0.7, **kwargs)
        else:
            if range_hist is not None:
                ax.hist(data.values.flatten(), bins=bins, color=color, alpha=0.5, range=range_hist, **kwargs)
            else:
                ax.hist(data.values.flatten(), bins=bins, color=color, alpha=0.5, **kwargs)
            median_data = np.nanmean(data.values.flatten())
        ax.axvline(median_data, color=color, linestyle='dashed', linewidth=1)
        ax.text(median_data, y_text, f"Median: {median_data:.2f}", color=color, rotation=90, ha=ha, va=va, transform=ax.get_xaxis_transform(),
                    path_effects=[patheffects.withStroke(linewidth=3, foreground='w')])
        
        if add_mean:
            mean_data = self.swot_collection.get_variable(variable, data_area, "mean", world_cover_selection).copy()
            if use_seaborn:
                if range_hist is not None:
                    sns.histplot(mean_data.values.flatten(), element='step', binrange=range_hist, bins=bins, color='grey', alpha=0.5, ax=ax, **kwargs)
                else:
                    sns.histplot(mean_data.values.flatten(), element='step', bins=bins, color='grey', alpha=0.5, ax=ax, **kwargs)
            else:
                if range_hist is not None:
                    ax.hist(mean_data.values.flatten(), bins=bins, color='grey', alpha=0.5, range=range_hist, **kwargs)
                else:
                    ax.hist(mean_data.values.flatten(), bins=bins, color='grey', alpha=0.5, **kwargs)
            median_mean = np.nanmean(mean_data.values.flatten())
            ax.axvline(median_mean, color='grey', linestyle='dashed', linewidth=1)
            ax.text(median_mean, y_text_mean, f"Median: {median_mean:.2f}", color='grey', rotation=90, ha=ha_mean, transform=ax.get_xaxis_transform(),
                    path_effects=[patheffects.withStroke(linewidth=3, foreground='w')])
        
        if add_xlabel:
            ax.set_xlabel(label_data)
        
        if add_ylabel:
            ax.set_ylabel("Frequency")
        
        if set_title:
            if title is not None:
                ax.set_title(title, fontsize=14)
            else:
                time_str = data['time'].dt.strftime("%Y-%m-%d %H:%M").values
                if data['time'].size > 1:
                    time_str = time_str[0]
                if world_cover_selection is not None:
                    label_data += f" - {world_cover_selection} areas"
                ax.set_title(f"{label_data} - {time_str}", fontsize=14)
        
        if save_fig:
            time_str = data['time'].dt.strftime("%Y%m%dT%H%M%S").values
            if data['time'].size > 1:
                time_str = time_str[0]
            title_str = title if title is not None else f"{variable}_{data_area}_{data_type}_{time_str}"
            if world_cover_selection is not None:
                title_str += f"_{world_cover_selection}"
            path = self.PATH_TO_SAVE.joinpath("histograms", title_str + ".png")
            fig.savefig(path, dpi=dpi)
            
        if show_fig:
            fig.show()
        
        return fig, ax
    
    def plot_all_histograms(
        self,
        variable:str,
        data_area:str="global",
        data_type:str="swot",
        time_selection:str=None,
        bins:int=100,
        range_hist:Tuple[float]=None,
        title:str=None,
        dpi:int=300,
        use_seaborn:bool=True,
        **kwargs
        ) -> Tuple[plt.Figure, plt.Axes]:
        """ Create a new figure to plot the histogram of the variable with the three histograms
        
        Args:
            variable (str): the variable to plot
            data_area (str): the area to plot ('global', 'control', 'flood')
            data_type (str): the type of data to plot ('swot', 'mean', 'diff')
            time_selection (str): the time selection to plot. Default is None.
            bins (int): The number of bins in the histogram. Default is 100.
            range_hist (Tuple(float)): The range of the histogram. Default is None.
            title (str): The title of the plot. Default is None.
            dpi (int): The dpi of the plot to save. Default is 300.
            use_seaborn (bool): Use seaborn to plot the histogram else use matplotlib. Default is True.
            **kwargs: Additional arguments to pass to the plotting function
        Returns:
            Tuple[plt.Figure, plt.Axes]: The figure and axes of the plot
        """
        if variable is None:
            raise ValueError("The variable must be given")
        if variable not in self.swot_collection.variables:
            raise ValueError(f"The variable {variable} is not in the collection")
        

        fig, axs = plt.subplots(1, 3, figsize=(15, 5))
        list_hist = [
            variable,           
            data_area,          
            data_type,          
            None,               
            time_selection,     
            True,
            fig,                
            axs[0],          
            title,              
            True,              
            dpi,                
            bins,  
            range_hist,  
            None,           
            use_seaborn,        
            False,              
            False               
        ]

        list_hist[3] = "open"
        list_hist[7] = axs[0]
        list_hist[8] = "Open areas"
        self.plot_histogram(*list_hist, **kwargs)
        list_hist[3] = "forest"
        list_hist[7] = axs[1]
        list_hist[8] = "Forest areas"
        self.plot_histogram(*list_hist, **kwargs)
        list_hist[3] = "urban"
        list_hist[7] = axs[2]
        list_hist[8] = "Urban areas"
        self.plot_histogram(*list_hist, **kwargs)
        
        fig.tight_layout()
        
        if self.save_fig:
            try:
                time_str = self.swot_collection.get_variable(variable, data_area, data_type, None)['time'].dt.strftime("%Y%m%dT%H%M%S").values
                time_str = time_str.tolist()[0]
            except:
                time_str = "mean"
            title_str = title if title is not None else f"all_hist_{variable}_{data_area}_{data_type}_{time_str}"
            path = self.PATH_TO_SAVE.joinpath("histograms", title_str + ".png")
            fig.savefig(path, dpi=dpi)
        
        if self.show_fig:
            fig.show()
        
        return fig, axs
        
    def plot_map_with_histogram(
        self,
        variable:str,
        data_area:str="global",
        data_type:str="swot",
        world_cover_mask:List[str]=list(),
        time_selection:str=None,
        title:str=None,
        dpi:int=300,
        cmap:str='viridis',
        vmin:float=None,
        vmax:float=None,
        add_bkg:bool=True,
        add_cbar:bool=True,
        bins:int=100,
        use_seaborn:bool=True,
        **kwargs
        ) -> Tuple[plt.Figure, plt.Axes]:
        """ Create a new figure to plot the map of the variable with the histograms of the world cover selection
        
        Args:
            variable (str): the variable to plot
            data_area (str): the area to plot ('global', 'control', 'flood')
            data_type (str): the type of data to plot ('swot', 'mean', 'diff')
            world_cover_mask (str): the world cover selection to mask (list(), list("open", "forest", "urban")). Default is None.
            time_selection (str): the time selection to plot. Default is None.
            title (str): The title of the plot. Default is None.
            dpi (int): The dpi of the plot to save. Default is 300.
            cmap (str): The colormap to use. Default is 'viridis'.
            vmin (float): The minimum value of the colormap. Default is None.
            vmax (float): The maximum value of the colormap. Default is None.
            add_bkg (bool): Add a background map (OpenStreetMap). Default is True.
            add_cbar (bool): Add a colorbar. Default is True.
            bins (int): The number of bins in the histogram. Default is 100.
            use_seaborn (bool): Use seaborn to plot the histogram else use matplotlib. Default is True.
            **kwargs: Additional arguments to pass to the plotting function
        Returns:
            Tuple[plt.Figure, plt.Axes]: The figure and axes of the plot
        """
        if variable is None:
            raise ValueError("The variable must be given")
        if variable not in self.swot_collection.variables:
            raise ValueError(f"The variable {variable} is not in the collection")
        if len(world_cover_mask) > 3:
            raise ValueError("The world cover mask must have a maximum of 3 elements")
        
        ncols = 3 - len(world_cover_mask)
        if ncols == 0:
            raise ValueError("The world cover mask must have at least one element")
        fig, axs = plt.subplots(3, ncols, figsize=(15, 15))

        range_hist = None
        if vmin is not None and vmax is not None:
            range_hist = (vmin, vmax)
        else:
            print("Warning: The vmin and vmax values are not set. The histogram will be plotted with the default values.")
            
        list_hist = [
            variable,           
            data_area,          
            data_type,          
            None,               
            time_selection,     
            True,
            fig,                
            axs[0, 0],          
            title,              
            True,              
            dpi,                
            bins,  
            range_hist,             
            use_seaborn,        
            False,              
            False               
        ]

        n = 0
        if "open" not in world_cover_mask:
            list_hist[3] = "open"
            list_hist[7] = axs[2, n]
            n += 1
            list_hist[8] = "Open areas"
            self.plot_histogram(*list_hist, **kwargs)
        if "forest" not in world_cover_mask:
            list_hist[3] = "forest"
            list_hist[7] = axs[2, n]
            n += 1
            list_hist[8] = "Forest areas"
            self.plot_histogram(*list_hist, **kwargs)
        if "urban" not in world_cover_mask:
            list_hist[3] = "urban"
            list_hist[7] = axs[2, n]
            list_hist[8] = "Urban areas"
            self.plot_histogram(*list_hist, **kwargs)
        
        fig.tight_layout()
        
        # remove unused axes for plotting the map
        for i in range(ncols):
            axs[0, i].set_visible(False)
            axs[1, i].set_visible(False)
            
                        
        # create place for the map
        gs = axs[0, 0].get_gridspec()
        for axx in axs[:2,:].flatten():
            axx.remove()
        
        fig, axs = self.plot_map(
            variable=variable,
            data_area=data_area,
            data_type=data_type,
            world_cover_selection=None,
            time_selection=time_selection,
            fig=fig,
            ax=(3, ncols, (1, ncols*2)),
            title=title,
            dpi=dpi,
            cmap=cmap,
            vmin=vmin,
            vmax=vmax,
            add_bkg=add_bkg,
            add_cbar=add_cbar,
            save_fig=False,
            show_fig=False,
            **kwargs
            )

        if self.save_fig:
            try:
                time_str = self.swot_collection.get_variable(variable, data_area, data_type, None)['time'].dt.strftime("%Y%m%dT%H%M%S").values
                time_str = time_str.tolist()[0]
            except:
                time_str = "mean"
            title_str = title if title is not None else f"maps_with_hist_{variable}_{data_area}_{data_type}_{time_str}"
            path = self.PATH_TO_SAVE.joinpath("maps", title_str + ".png")
            fig.savefig(path, dpi=dpi)
        
        if self.show_fig:
            fig.show()
        
        return fig, axs
    
    def plot_control_maps_and_histograms(
        self,
        variable:str,
        time_selection:str=None,
        y_label:str=None,
        title:str=None,
        dpi:int=300,
        cmap:str='magma',
        vmin:float=None,
        vmax:float=None,
        fig:plt.Figure=None,
        axs:plt.Axes=None,
    ) -> Tuple[plt.Figure, plt.Axes]:
        """ Plot the control maps and histograms of the variable
        
        Args:
            variable (str): the variable to plot
            time_selection (str): the time selection to plot. Default is None.
            title (str): The title of the plot. Default is None.
            dpi (int): The dpi of the plot to save. Default is 300.
            cmap (str): The colormap to use. Default is 'magma'.
            vmin (float): The minimum value of the colormap. Default is None.
            vmax (float): The maximum value of the colormap. Default is None.
            fig (plt.Figure): The figure to plot on. Default is None.
            axs (plt.Axes): The axes to plot on (3 align). Default is None.
        Returns:
            Tuple[plt.Figure, plt.Axes]: The figure and axes of the plot
        """
        if variable not in self.swot_collection.variables:
            raise ValueError(f"The variable {variable} is not in the collection")
        
        if fig is None:
            fig, axs = plt.subplots(1, 3, figsize=(15, 5), )
            
            # adjust the subplots for the colorbar
            fig.subplots_adjust(right=0.9)
            
        # get data
        data = self.swot_collection.get_variable(variable, "control", "swot").copy()
        data_mean = self.swot_collection.get_variable(variable, "control", "mean").copy()
        label_data = self.get_label(variable)
        
        # get the data on the requested time
        data = data.sel(time=time_selection)
        if data['time'].size > 1:
            print(f"Warning: {data['time'].size} time steps selected. Only the first one will be used.")
        data = data.isel(time=0)
        
        #create mask were data and data_mean are not nan
        mask = ~np.isnan(data.values) & ~np.isnan(data_mean.values)
        data = data.where(mask)
        data_mean = data_mean.where(mask)
            
        im = data_mean.plot.imshow(ax=axs[0], cmap=cmap, vmin=vmin, vmax=vmax, add_colorbar=False, add_labels=False)
        axs[0].set_title(f"{label_data} - Mean data")
        
        data.plot.imshow(ax=axs[1], cmap=cmap, vmin=vmin, vmax=vmax, add_colorbar=False, add_labels=False)
        
        axs[0].get_xaxis().set_visible(False)
        if y_label is not None:
            axs[0].set_ylabel(y_label, fontsize=12, fontweight='bold')
            # remove ticks labels
            axs[0].get_yaxis().set_tick_params(labelsize=0)
        else:
            axs[0].get_yaxis().set_visible(False)
        
        axs[1].get_xaxis().set_visible(False)
        axs[1].get_yaxis().set_visible(False)
        
        # add ax for colorbar
        cax = fig.add_axes([0.92, 0.1, 0.02, 0.8])
        cbar = fig.colorbar(im, cax=cax)
        cbar.set_label(label_data)
        
        if 'time' in data.dims:
            str_time = data['time'].dt.strftime("%Y-%m-%d %H:%M").values
            if data['time'].size > 1:
                str_time = str_time[0]
        
            axs[1].set_title(f"{label_data} - {str_time}", fontsize=14)
        else:
            axs[1].set_title(f"{label_data}", fontsize=14)
        
        self.plot_histogram(
            variable=variable,
            data_area="control",
            data_type="swot",
            time_selection=time_selection,
            add_mean=True,
            fig=fig,
            ax=axs[2],
            title="",
            dpi=dpi,
            bins=100,
            color='blue',
            use_seaborn=False,
            save_fig=False,
            show_fig=False,
            add_ylabel=False
        )
        
        if title is not None:
            fig.suptitle(title)
        
        if self.save_fig:
            time_str = data['time'].dt.strftime("%Y%m%dT%H%M%S").values
            if data['time'].size > 1:
                time_str = time_str[0]
            title_str = title if title is not None else f"control_maps_and_hist_{variable}_{time_str}"
            path = self.PATH_TO_SAVE.joinpath("maps", title_str + ".png")
            fig.savefig(path, dpi=dpi)
            
        if self.show_fig:
            fig.show()
            
        return fig, axs
            
    def plot_mean_hist_computation(
        self,
        variable:str,
        title:str=None,
        dpi:int=300,
        bins=100,
        hist_range:Tuple[float, float]=None,
        fig:plt.Figure=None,
        ax:plt.Axes=None,
        add_legend:bool=True
    ) -> Tuple[plt.Figure, plt.Axes]:
        """ Plot the histograms of the mean data and the difference between the mean and the swot data
        
        Args:
            variable (str): the variable to plot
            title (str): The title of the plot. Default is None.
            dpi (int): The dpi of the plot to save. Default is 300.
            bins (int): The number of bins in the histogram. Default is 100.
            range (Tuple[float, float]): The range of the histogram. Default is None.
            fig (plt.Figure): The figure to plot on. Default is None.
            ax (plt.Axes): The axes to plot on. Default is None.
            add_legend (bool): Add a legend to the plot. Default is True.
        Returns:
            Tuple[plt.Figure, plt.Axes]: The figure and axes of the plot
        """
        mean_obj = self.swot_collection.swot_mean
        if variable not in mean_obj.variables:
            raise ValueError(f"The variable {variable} is not in the mean object")
        
        if fig is None:
            fig, ax = plt.subplots(1, 1, figsize=(5, 5))
            
        # get data
        data_mean = mean_obj.swot_mean[variable]
        data_dates = mean_obj.swot_rasters[variable]
        
        
        no_range = False
        if range is None:
            no_range = True
            hist_range = (data_mean.values.min(), data_mean.values.max())
        
        ax.hist(data_mean.values.flatten(), bins=bins, color="grey", alpha=0.5, histtype='stepfilled', label="Mean data", range=hist_range)
        
        for i in range(data_dates['time'].size):
            data = data_dates.isel(time=i)
            data = data.values.flatten()
            date_str = data_dates['time'].dt.strftime("%Y-%m-%d %H:%M").values[i]
            if no_range:
                hist_range = (min(hist_range[0], data.min()), max(hist_range[1], data.max()))
            ax.hist(data, bins=bins, alpha=0.5, histtype='step', label=f"{date_str}", range=hist_range)
        
        ax.set_xlabel(self.get_label(variable))
        ax.set_ylabel("Frequency")
        
        if range is not None:
            ax.set_xlim(hist_range)
            
        if add_legend:
            ax.legend(fontsize=11)
        
        if title is not None:
            ax.set_title(title, fontsize=14)
        
        if self.save_fig:
            time_str = data_dates['time'].dt.strftime("%Y%m%dT%H%M%S").values
            if data_dates['time'].size > 1:
                time_str = time_str[0]
            title_str = title if title is not None else f"mean_hist_computation_{variable}_{time_str}"
            path = self.PATH_TO_SAVE.joinpath("histograms", title_str + ".png")
            fig.savefig(path, dpi=dpi)
        
        if self.show_fig:
            fig.show()
        
        return fig, ax
    
    def plot_map_mask(
        self,
        variable:str,
        data_area:str="global",
        data_type:str="swot",
        time_selection:str=None,
        add_uncertainty:bool=False,
        comparing_raster_Path:Path=None,
        add_classif_score:bool=True,
        title:str=None,
        dpi:int=300,
        add_bkg:bool=False,
        add_legend:bool=True,
        extents:List[float]=None,
        fig:plt.Figure=None,
        ax:plt.Axes=None,
        figsize:Tuple[float, float]=(10, 10),
        **kwargs
    ) -> Tuple[plt.Figure, plt.Axes]:
        """ Plot the map of the variable with the mask of the thresholds
        
        Args:
            variable (str): the variable to plot
            data_area (str): the area to plot ('global', 'control', 'flood')
            data_type (str): the type of data to plot ('swot', 'mean', 'diff')
            time_selection (str): the time selection to plot. Default is None.
            add_uncertainty (bool): Add the classification for SNR/dark water. Default is False.
            comparing_raster_Path (Path): the path to the raster to compare with. Default is None.
            add_classif_score (bool): Add the classification score. Default is True.
            title (str): The title of the plot. Default is None.
            dpi (int): The dpi of the plot to save. Default is 300.
            add_bkg (bool): Add a background map (OpenStreetMap). Default is False.
            add_legend (bool): Add a legend to the plot. Default is True.
            extents (List[float]): The extents of the map. Default is None.
            fig (plt.Figure): The figure to plot on. Default is None.
            ax (plt.Axes): The axes to plot on. Default is None.
            **kwargs: Additional arguments to pass to the plotting function
        Returns:
            Tuple[plt.Figure, plt.Axes]: The figure and axes of the plot
            
        Thresholds example: Default thresholds = 0.8 for all classes.
            If negative value, take the start of the range
            If positive value, take the end of the range 
            thresholds = 0.8
            thresholds = {
                "open": 0.75,
                "forest": 0.8,
                "urban": -0.15
            }
        """
        if variable is None:
            raise ValueError("The variable must be given")
        if variable not in self.swot_collection.variables and variable != "merged":
            raise ValueError(f"The variable {variable} is not in the collection")

        label_data = self.get_label(variable) if variable != "merged" else "Merged flood mask"
        holes_mask = self.swot_collection.get_holes_mask(data_area, data_type)
        holes_mask = holes_mask.isel(time=0)
        
        data = self.swot_collection.get_floodmask_from_variable(variable, data_type, data_area)
        if data is None:
            raise ValueError(f"The variable {variable} is not in the collection, please use create_flood_mask() method in the swot_collection object.")
        
        # get flood cmap and labels
        cmap, color_labels = self.get_floodmask_colormap(add_uncertainty)

        if comparing_raster_Path is not None:
            comparing_raster = rxr.open_rasterio(comparing_raster_Path)
            mask_compared = np.where(comparing_raster.values == 1, 1., 0.)[0]
            mask_compared[holes_mask] = np.nan
            mask_data = (data.values != 0) * 1.
            mask_data[holes_mask] = np.nan
            
            #remove nan values
            mask_compared = mask_compared[~np.isnan(mask_compared)]
            mask_data = mask_data[~np.isnan(mask_data)]
            
            # compute f1 score
            f1_score_compared = self.f1_score(mask_compared.flatten(), mask_data.flatten())
            print(f"f1 score with compared data: {f1_score_compared}")

        if add_classif_score:
            classif = self.swot_collection.get_variable("classification", data_area, "swot", None).copy()
            if time_selection  is not None:
                classif = classif.sel(time=time_selection)
            else: 
                classif = classif.isel(time=0)
            # selection classif == 3 - 4 - 5
            mask_classif = np.logical_and(classif.values >= 3, classif.values <= 5)
            mask_classif = np.where(mask_classif, 1., 0.)
            mask_data = (data.values != 0) * 1.
            
            #remove nan values
            mask_classif = np.where(holes_mask, np.nan, mask_classif)
            mask_data = np.where(holes_mask, np.nan, mask_data)
            mask_classif = mask_classif[~np.isnan(mask_classif)]
            mask_data = mask_data[~np.isnan(mask_data)]
            
            # compute f1 score
            f1_score_classification = self.f1_score(mask_classif.flatten(), mask_data.flatten())
            print(f"f1 score with classification data: {f1_score_classification}")
            if comparing_raster_Path is not None:
                mask_compared = np.where(comparing_raster.values == 1, 1., 0.)[0]
                mask_compared= np.where(holes_mask, np.nan, mask_compared)
                mask_classif = mask_classif[~np.isnan(mask_classif)]
                mask_compared = mask_compared[~np.isnan(mask_compared)]
                f1_score_classif_compared = self.f1_score(mask_classif.flatten(), mask_compared.flatten())
                print(f"f1 score with compared data and classification: {f1_score_classif_compared}")

        data.values = data.values.astype(float)
        data.values[holes_mask] = np.nan
        data.values[data.values==0] = np.nan

        if fig is None:
            map_obj = Maps(crs=self.CRS, ax=(1,1,1), figsize=figsize)
        else:
            map_obj = Maps(crs=self.CRS, ax=ax, f=fig)
        
        # Get extent of the data
        if extents is None:
            match data_area:
                case "global":
                    poly = self.BBOX
                    extents = [poly.bounds[0], poly.bounds[2], poly.bounds[1], poly.bounds[3]]
                case "control":
                    poly = self.swot_collection.controlmask
                    extents = [poly.bounds["minx"], poly.bounds["maxx"], poly.bounds["miny"], poly.bounds["maxy"]]
                case "flood":
                    poly = self.swot_collection.floodmask
                    extents = [poly.bounds["minx"], poly.bounds["maxx"], poly.bounds["miny"], poly.bounds["maxy"]]
            crs_extents = self.CRS
        else:
            crs_extents = 4326
        map_obj.set_extent(extents=extents, crs=crs_extents)

        g = map_obj.add_gridlines(lw=0.25, alpha=0.5, zorder=0)
        gl = g.add_labels(where="blr",fontsize=8, every = 2)
        # c = map_obj.add_compass(style='compass', pos=(0.9, 0.85), scale=7)

        if title is not None:
            map_obj.add_title(title, y=1, fontsize=14)
        else:    
            time_str = data['time'].dt.strftime("%Y-%m-%d %H:%M").values
            if data['time'].size > 1:
                time_str = time_str[0]
            map_obj.add_title(f"{label_data} - {time_str}", y=1, fontsize=14)

        if add_bkg:
            m_bkg = map_obj.new_layer()
            m_bkg.add_wms.OpenStreetMap.add_layer.default()


        # Adding missing values
        m_mask, handle = self.add_missing_values(data_type, data_area, map_obj, time_selection)
        
        m_data = map_obj.new_layer()
        m_data.set_data(data, x="x", y="y", crs=self.CRS, parameter=label_data)
        m_data.set_shape.raster()

        m_data.plot_map(cmap=cmap, norm=matplotlib.colors.Normalize(vmin=0, vmax=255), vmin=0, vmax=255, **kwargs)

        if add_classif_score:
            m_data.text(0.01, 0.02, f"F1-score[classification, current mask]: {f1_score_classification:.2f}", fontsize=10, color='black', ha='left', va='center', transform=m_data.ax.transAxes, **{'path_effects': [patheffects.withStroke(linewidth=3, foreground='w')]})
        if comparing_raster_Path is not None:
            m_data.text(0.01, 0.07, f"F1-score[FloodML, current mask]: {f1_score_compared:.2f}", fontsize=10, color='black', ha='left', va='center', transform=m_data.ax.transAxes, **{'path_effects': [patheffects.withStroke(linewidth=3, foreground='w')]})
            if add_classif_score:
                m_data.text(0.01, 0.12, f"F1-score[FloodML, classification]: {f1_score_classif_compared:.2f}", fontsize=10, color='black', ha='left', va='center', transform=m_data.ax.transAxes, **{'path_effects': [patheffects.withStroke(linewidth=3, foreground='w')]})

        # add legend for the flood mask
        if add_legend:
            aaxx = map_obj.ax
            l1 = mpatches.Patch(color=cmap(1), label=color_labels[1])
            l2 = mpatches.Patch(color=cmap(2), label=color_labels[2])
            l3 = mpatches.Patch(color=cmap(3), label=color_labels[3])
            if add_uncertainty:
                l11 = mpatches.Patch(color=cmap(11), label=color_labels[11])
                l12 = mpatches.Patch(color=cmap(12), label=color_labels[12])
                l13 = mpatches.Patch(color=cmap(13), label=color_labels[13])
                l21 = mpatches.Patch(color=cmap(21), label=color_labels[21])
                l22 = mpatches.Patch(color=cmap(22), label=color_labels[22])
                l23 = mpatches.Patch(color=cmap(23), label=color_labels[23])
                aaxx.legend(handles=[l1, l2, l3, l11, l12, l13, l21, l22, l23],loc="lower center", fontsize=10, ncols=3, bbox_to_anchor=(0.5, -0.2), handlelength=1, handleheight=1)
            else:
                aaxx.legend(handles=[l1, l2, l3], fontsize=10,loc="lower center",ncols=3, bbox_to_anchor=(0.5, -.2), handlelength=1, handleheight=1)

        if self.save_fig:
            time_str = data['time'].dt.strftime("%Y%m%dT%H%M%S").values
            if data['time'].size > 1:
                time_str = time_str[0]
            title_str = title if title is not None else f"floodmask_{variable}_{data_area}_{data_type}_{time_str}"
            path = self.PATH_TO_SAVE.joinpath("maps", title_str + ".png")
            m_data.savefig(path, dpi=dpi)

        if self.show_fig:
            m_data.show()

        return map_obj.f, map_obj.f.axes
       