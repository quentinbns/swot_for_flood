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
from matplotlib import patheffects
import seaborn as sns
from eomaps import Maps
from cmap import Colormap

from time import time

from core.swot_project import SwotProject
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
        self.swot_collection = project.swot_collection
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
    
    def get_label(self, variable:str)->str:
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
    
    def select_color_world_cover(self, color:str, world_cover_selection:str)->str:
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
        set_tight_layout:bool=True,
        save_fig:bool=None,
        show_fig:bool=None,
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
        data = self.swot_collection.get_variable(variable, data_area, data_type, world_cover_selection)
        label_data = self.get_label(variable)
        
        # Get the data on the requested time
        data = data.sel(time=time_selection)
        
        # Get extent of the data
        match data_area:
            case "global":
                poly = self.BBOX
            case "control":
                poly = self.swot_collection.controlmask
            case "flood":
                poly = self.swot_collection.floodmask
        extends = [poly.bounds[0], poly.bounds[2], poly.bounds[1], poly.bounds[3]]
        
        map_obj = Maps(crs=self.CRS, f=fig, ax=ax)
        map_obj.set_extent(extents=extends, crs=self.CRS)
        g = map_obj.add_gridlines(lw=0.25, alpha=0.5, zorder=0)
        gl = g.add_labels(where="blr",fontsize=8, every = 2)
        c = map_obj.add_compass(style='compass', pos=(0.9, 0.85), scale=7)
        
        if title is not None:
            map_obj.add_title(title, y=1)
        else:    
            time_str = data['time'].dt.strftime("%Y-%m-%d %H:%M").values
            if data['time'].size > 1:
                time_str = time_str[0]
            if world_cover_selection is not None:
                label_data += f" - {world_cover_selection} areas"
            map_obj.add_title(f"{label_data} - {time_str}", y=1)
        
        if add_bkg:
            m_bkg = map_obj.new_layer()
            m_bkg.add_wms.OpenStreetMap.add_layer.default()
        
        m_data = map_obj.new_layer()
        m_data.set_data(data, x="x", y="y", crs=self.CRS, parameter=label_data)
        m_data.set_shape.raster()

        m_data.plot_map(vmin=vmin, vmax=vmax, cmap=cmap, **kwargs)
        if add_cbar:
            m_data.add_colorbar()
        
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
        color:str='blue',
        use_seaborn:bool=True,
        save_fig:bool=None,
        show_fig:bool=None,
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
            
        # Get the data
        data = self.swot_collection.get_variable(variable, data_area, data_type, world_cover_selection)
        label_data = self.get_label(variable)
        
        # Get the data on the requested time
        if time_selection is not None:
            data = data.sel(time=time_selection)
        else:
            data = data.isel(time=0)
        
        # Set specific color if world_cover_selection is given
        color = self.select_color_world_cover(color, world_cover_selection)
            
        # Plot the histogram
        if fig is None:
            fig, ax = plt.subplots()
        if use_seaborn:
            sns.histplot(data.values.flatten(), element='step', bins=bins, color=color, ax=ax, alpha=0.7, **kwargs)
        else:
            ax.hist(data.values.flatten(), bins=bins, color=color, alpha=0.5, **kwargs)
        median_data = np.nanmean(data.values.flatten())
        ax.axvline(median_data, color=color, linestyle='dashed', linewidth=1)
        ax.text(median_data, 0.24, f"Median: {median_data:.2f}", color=color, rotation=90, ha='left', va='top', transform=ax.get_xaxis_transform(),
                    path_effects=[patheffects.withStroke(linewidth=3, foreground='w')])
        
        if add_mean:
            mean_data = self.swot_collection.get_variable(variable, data_area, "mean", world_cover_selection)
            if use_seaborn:
                sns.histplot(mean_data.values.flatten(), element='step', bins=bins, color='grey', alpha=0.5, ax=ax, **kwargs)
            else:
                ax.hist(mean_data.values.flatten(), bins=bins, color='grey', alpha=0.5, **kwargs)
            median_mean = np.nanmean(mean_data.values.flatten())
            ax.axvline(median_mean, color='grey', linestyle='dashed', linewidth=1)
            ax.text(median_mean, 0.05, f"Median: {median_mean:.2f}", color='grey', rotation=90, ha='right', transform=ax.get_xaxis_transform(),
                    path_effects=[patheffects.withStroke(linewidth=3, foreground='w')])
        
        ax.set_xlabel(label_data)
        ax.set_ylabel("Frequency")
        
        if set_title:
            if title is not None:
                ax.set_title(title)
            else:
                time_str = data['time'].dt.strftime("%Y-%m-%d %H:%M").values
                if data['time'].size > 1:
                    time_str = time_str[0]
                if world_cover_selection is not None:
                    label_data += f" - {world_cover_selection} areas"
                ax.set_title(f"{label_data} - {time_str}")
        
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
        if len(world_cover_mask) == 3:
            raise ValueError("The world cover mask must have at least one element")
        
        fig, axs = plt.subplots(3, 3 - len(world_cover_mask), figsize=(15, 15))

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
        axs[0, 0].set_visible(False)
        axs[0, 1].set_visible(False)
        axs[0, 2].set_visible(False)
        axs[1, 0].set_visible(False)
        axs[1, 1].set_visible(False)
        axs[1, 2].set_visible(False)
                        
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
            ax=(3, 3, (1, 6)),
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
            time_str = self.swot_collection.get_variable(variable, data_area, data_type, None)['time'].dt.strftime("%Y%m%dT%H%M%S").values
            if self.swot_collection.get_variable(variable, data_area, data_type, None)['time'].size > 1:
                time_str = time_str[0]
            title_str = title if title is not None else f"maps_with_hist_{variable}_{data_area}_{data_type}_{time_str}"
            path = self.PATH_TO_SAVE.joinpath("maps", title_str + ".png")
            fig.savefig(path, dpi=dpi)
        
        if self.show_fig:
            fig.show()
        
        return fig, axs