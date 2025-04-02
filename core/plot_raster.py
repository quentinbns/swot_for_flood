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
from scipy.ndimage import binary_dilation, binary_erosion
from skimage import morphology

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
            1: 'red',        # urban
            2: 'forestgreen',      # forest
            3: 'cornflowerblue',       # open
            }
        color_labels = {
            1: 'Flooded urban',
            2: 'Flooded forest',
            3: 'Flooded open',
            }
        if add_uncertainty:
            color_dict_uncertainty = { 
                11: 'rosybrown',     # urban potential dark water
                12: 'yellowgreen',      # forest potential dark water
                13: 'darkcyan',     # open potential dark water
                21: 'darkred',    # urban low SNR
                22: 'darkgreen',    # forest low SNR
                23: 'darkblue',      # open low SNR
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
        
        return cmap, color_labels
    
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
        extents = [poly.bounds[0], poly.bounds[2], poly.bounds[1], poly.bounds[3]]
        
        map_obj = Maps(crs=self.CRS, f=fig, ax=ax)
        map_obj.set_extent(extents=extents, crs=self.CRS)
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
        add_xlabel:bool=True,
        add_ylabel:bool=True,
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
        
        if add_xlabel:
            ax.set_xlabel(label_data)
        
        if add_ylabel:
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
        data = self.swot_collection.get_variable(variable, "control", "swot")
        data_mean = self.swot_collection.get_variable(variable, "control", "mean")
        label_data = self.get_label(variable)
        
        # get the data on the requested time
        data = data.sel(time=time_selection)
        if data['time'].size > 1:
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
        
        str_time = data['time'].dt.strftime("%Y-%m-%d %H:%M").values
        if data['time'].size > 1:
            str_time = str_time[0]
        axs[1].set_title(f"{label_data} - {str_time}")
        
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
            ax.set_title(title)
        
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
        thresholds:float|dict=0.8,
        add_uncertainty:bool=False,
        threshold_SNR:float=0.5,
        comparing_raster_Path:Path=None,
        add_classif_score:bool=True,
        title:str=None,
        dpi:int=300,
        add_bkg:bool=False,
        add_legend:bool=True,
        **kwargs
    ) -> Tuple[plt.Figure, plt.Axes]:
        """ Plot the map of the variable with the mask of the thresholds
        
        Args:
            variable (str): the variable to plot
            data_area (str): the area to plot ('global', 'control', 'flood')
            data_type (str): the type of data to plot ('swot', 'mean', 'diff')
            time_selection (str): the time selection to plot. Default is None.
            thresholds (float|dict|List[float]): the threshold to mask the data. Can be a float for a global threshold or a dictionary containing values for each pixel class. Default is 0.8.
            add_uncertainty (bool): Add the classification for SNR/dark water. Default is False.
            threshold_SNR (float): The threshold to mask the SNR data. Default is 0.5.
            comparing_raster_Path (Path): the path to the raster to compare with. Default is None.
            add_classif_score (bool): Add the classification score. Default is True.
            title (str): The title of the plot. Default is None.
            dpi (int): The dpi of the plot to save. Default is 300.
            add_bkg (bool): Add a background map (OpenStreetMap). Default is False.
            add_legend (bool): Add a legend to the plot. Default is True.
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
        if variable not in self.swot_collection.variables:
            raise ValueError(f"The variable {variable} is not in the collection")

        if isinstance(thresholds, float):
            thresholds = {
                "open": thresholds,
                "forest": thresholds,
                "urban": thresholds
            }
        elif isinstance(thresholds, dict):
            if "open" not in thresholds:
                thresholds["open"] = 0.8
            if "forest" not in thresholds:
                thresholds["forest"] = 0.8
            if "urban" not in thresholds:
                thresholds["urban"] = 0.8
        else:
            raise ValueError("The thresholds must be a float or a dictionary")

        data_urban = self.swot_collection.get_variable(variable, data_area, data_type, 'urban')
        data_forest = self.swot_collection.get_variable(variable, data_area, data_type, 'forest')
        data_open = self.swot_collection.get_variable(variable, data_area, data_type, 'open')
        data_glob = self.swot_collection.get_variable(variable, data_area, data_type, None)

        label_data = self.get_label(variable)

        if add_uncertainty:
            data_SNR_urban =  self.swot_collection.get_variable("gamma_SNR", data_area, data_type, 'urban')
            data_SNR_forest = self.swot_collection.get_variable("gamma_SNR", data_area, data_type, 'forest')
            data_SNR_open =   self.swot_collection.get_variable("gamma_SNR", data_area, data_type, 'open')
            
            data_SNR_urban =  data_SNR_urban.rio.clip(self.swot_collection.floodmask.geometry, drop=False)
            data_SNR_forest = data_SNR_forest.rio.clip(self.swot_collection.floodmask.geometry, drop=False)
            data_SNR_open =   data_SNR_open.rio.clip(self.swot_collection.floodmask.geometry, drop=False)
            
            data_flood_urban = data_urban.rio.clip(self.swot_collection.floodmask.geometry, drop=False)
            data_flood_forest = data_forest.rio.clip(self.swot_collection.floodmask.geometry, drop=False)
            data_flood_open = data_open.rio.clip(self.swot_collection.floodmask.geometry, drop=False)

        # Get the data on the requested time
        if time_selection is not None:
            data_urban = data_urban.sel(time=time_selection)
            data_forest = data_forest.sel(time=time_selection)
            data_open = data_open.sel(time=time_selection)
            data_glob = data_glob.sel(time=time_selection)
            if add_uncertainty:
                data_SNR_urban = data_SNR_urban.sel(time=time_selection)
                data_SNR_forest = data_SNR_forest.sel(time=time_selection)
                data_SNR_open = data_SNR_open.sel(time=time_selection)
                data_flood_urban = data_flood_urban.sel(time=time_selection)
                data_flood_forest = data_flood_forest.sel(time=time_selection)
                data_flood_open = data_flood_open.sel(time=time_selection)
        else:
            data_urban = data_urban.isel(time=0)
            data_forest = data_forest.isel(time=0)
            data_open = data_open.isel(time=0)
            data_glob = data_glob.isel(time=0)
            if add_uncertainty:
                data_SNR_urban = data_SNR_urban.isel(time=0)
                data_SNR_forest = data_SNR_forest.isel(time=0)
                data_SNR_open = data_SNR_open.isel(time=0)
                data_flood_urban = data_flood_urban.isel(time=0)
                data_flood_forest = data_flood_forest.isel(time=0)
                data_flood_open = data_flood_open.isel(time=0)
        holes_mask = np.isnan(data_glob.values) * 1

        if thresholds['urban'] > 0:
            mask_urban = np.where(data_urban.values > thresholds['urban'], 1, 0)
        else:
            mask_urban = np.where(data_urban.values < thresholds['urban'], 1, 0)
        if thresholds['forest'] > 0:
            mask_forest = np.where(data_forest.values > thresholds['forest'], 2, 0)
        else:
            mask_forest = np.where(data_forest.values < thresholds['forest'], 2, 0)
        if thresholds['open'] > 0:
            mask_open = np.where(data_open.values > thresholds['open'], 3, 0)
        else:
            mask_open = np.where(data_open.values < thresholds['open'], 3, 0)
        mask = mask_urban + mask_forest + mask_open

        if add_uncertainty:
            mask_SNR_urban = np.where(data_SNR_urban.values < threshold_SNR, 11, 0)
            if variable == "gamma_tot":
                mask_darkwater_urban = np.where(data_flood_urban.values < 0.2, 21, 0)
            mask_SNR_forest = np.where(data_SNR_forest.values < threshold_SNR, 12, 0)
            if variable == "gamma_tot":
                mask_darkwater_forest = np.where(data_flood_forest.values < 0.2, 22, 0)
            mask_SNR_open = np.where(data_SNR_open.values < threshold_SNR, 13, 0)
            if variable == "gamma_tot":
                mask_darkwater_open = np.where(data_flood_open.values < 0.2, 23, 0)
            mask_SNR = mask_SNR_urban + mask_SNR_forest + mask_SNR_open
            if variable == "gamma_tot":
                mask_darkwater = mask_darkwater_urban + mask_darkwater_forest + mask_darkwater_open
            
        global_mask = mask
        if add_uncertainty:
            global_mask[mask_SNR != 0] = mask_SNR[mask_SNR != 0]
            if variable == "gamma_tot":
                global_mask[mask_darkwater != 0] = mask_darkwater[mask_darkwater != 0]

        clean_mask = (global_mask != 0) * 1
        
        # cleaning mask
        footprint = morphology.disk(2)
        res = morphology.white_tophat(clean_mask, footprint)
        clean_mask = np.where(res == 1, 0, clean_mask)
        clean_mask = binary_erosion(clean_mask, structure=morphology.disk(2)).astype(float)
        clean_mask = binary_dilation(clean_mask,structure=morphology.disk(2)).astype(float)
        
        global_mask = np.where(clean_mask == 1, global_mask, 0)
        
        # set mask within a data copy for geolocation
        data = data_urban.copy()
        data.values = global_mask

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
            classif = self.swot_collection.get_variable("classification", data_area, "swot", None)
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

        map_obj = Maps(crs=self.CRS, ax=(3,3,(1,6)), figsize=(10, 10))
        
        # Get extent of the data
        match data_area:
            case "global":
                poly = self.BBOX
            case "control":
                poly = self.swot_collection.controlmask
            case "flood":
                poly = self.swot_collection.floodmask
        extents = [poly.bounds[0], poly.bounds[2], poly.bounds[1], poly.bounds[3]]
        map_obj.set_extent(extents=extents, crs=self.CRS)

        g = map_obj.add_gridlines(lw=0.25, alpha=0.5, zorder=0)
        gl = g.add_labels(where="blr",fontsize=8, every = 2)
        c = map_obj.add_compass(style='compass', pos=(0.9, 0.85), scale=7)

        if title is not None:
            map_obj.add_title(title, y=1)
        else:    
            time_str = data['time'].dt.strftime("%Y-%m-%d %H:%M").values
            if data['time'].size > 1:
                time_str = time_str[0]
            map_obj.add_title(f"{label_data} - {time_str}", y=1)

        if add_bkg:
            m_bkg = map_obj.new_layer()
            m_bkg.add_wms.OpenStreetMap.add_layer.default()


        m_data = map_obj.new_layer()
        m_data.set_data(data, x="x", y="y", crs=self.CRS, parameter=label_data)
        m_data.set_shape.raster()

        m_data.plot_map(cmap=cmap.to_matplotlib(), norm=matplotlib.colors.Normalize(vmin=0, vmax=255), vmin=0, vmax=255, **kwargs)

        if add_classif_score:
            m_data.text(0.01, 0.02, f"F1-score[classification, current mask]: {f1_score_classification:.2f}", fontsize=10, color='black', ha='left', va='center', transform=m_data.ax.transAxes)
        if comparing_raster_Path is not None:
            m_data.text(0.01, 0.07, f"F1-score[FloodML, current mask]: {f1_score_compared:.2f}", fontsize=10, color='black', ha='left', va='center', transform=m_data.ax.transAxes)
            if add_classif_score:
                m_data.text(0.01, 0.12, f"F1-score[FloodML, classification]: {f1_score_classif_compared:.2f}", fontsize=10, color='black', ha='left', va='center', transform=m_data.ax.transAxes)

        # add legend for the flood mask
        if add_legend:
            aaxx = map_obj.ax
            l1 = mpatches.Patch(color='red', label=color_labels[1])
            l2 = mpatches.Patch(color='forestgreen', label=color_labels[2])
            l3 = mpatches.Patch(color='cornflowerblue', label=color_labels[3])
            if add_uncertainty:
                l11 = mpatches.Patch(color='rosybrown', label=color_labels[11])
                l12 = mpatches.Patch(color='yellowgreen', label=color_labels[12])
                l13 = mpatches.Patch(color='darkcyan', label=color_labels[13])
                l21 = mpatches.Patch(color='darkred', label=color_labels[21])
                l22 = mpatches.Patch(color='darkgreen', label=color_labels[22])
                l23 = mpatches.Patch(color='darkblue', label=color_labels[23])
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
        
        
