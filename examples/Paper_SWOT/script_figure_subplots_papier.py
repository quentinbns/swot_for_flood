import os
os.sys.path.append('/data/scratch/globc/bonassies/workspace/swot_for_flood')
import geopandas as gpd
import configparser
from pathlib import Path
from matplotlib import pyplot as plt
import seaborn as sns
from cmap import Colormap

from core.swot_project import SwotProject
from core.plot_raster import PlotRaster
import cartopy
from matplotlib import patches as mpatches
from matplotlib.lines import Line2D
from matplotlib import patheffects

from time import time

def plot_combine_mask(Chinon_plot:PlotRaster, PortoAlegre_plot:PlotRaster, Ohio_plot:PlotRaster, EMSR692_plot:PlotRaster):
    start = time()
    print("Plotting water mask", flush=True)
    fig, ax = plt.subplots(2, 2, figsize=(25,20))
    fig.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05, hspace=0.1, wspace=0.1)

    ax[0,0].remove()
    ax[0,1].remove()
    ax[1,0].remove()
    ax[1,1].remove()

    Chinon_plot.swot_collection.merge_flood_masks(data_area="global", data_type="swot", filter_variable="sig0")
    PortoAlegre_plot.swot_collection.merge_flood_masks(data_area="global", data_type="swot", filter_variable="sig0")
    Ohio_plot.swot_collection.merge_flood_masks(data_area="global", data_type="swot", filter_variable="coherent_power")
    EMSR692_plot.swot_collection.merge_flood_masks(data_area="global", data_type="swot")

    ####################
    # Chinon
    Chinon_plot.plot_map_mask(
        variable="merged",
        data_area="global",
        data_type="swot",
        time_selection="2024-03-31",
        title="[a]",
        comparing_raster_Path=Chinon_plot.project.AUX_PATH.joinpath("FM_30TYT_20240331T174856_S1_132_POST_nrow1496_ncol2635.tif"),
        add_scores=False,
        add_bkg=False,
        add_legend=False,
        ax=(2,2,1),
        fig=fig
        )

    ####################
    # Porto Alegre
    PortoAlegre_plot.plot_map_mask(
        variable="merged", 
        data_area="global", #global or flood or control
        data_type="swot", #swot
        time_selection="2024-05-06",
        title="[b]",
        comparing_raster_Path=PortoAlegre_plot.project.AUX_PATH.joinpath("FloodMask_nrow4248_ncol8052.tif"),
        add_scores=False,
        add_bkg=False,
        add_legend=False,
        ax=(2,2,2),
        fig=fig
        )

    ####################
    # Ohio
    Ohio_plot.plot_map_mask(
        variable="merged",
        data_area="global",
        data_type="swot",
        time_selection="2025-02-20",
        comparing_raster_Path=Ohio_plot.project.AUX_PATH.joinpath("FM_20250222T000000_S1_POST_fusion_cut_32616_nrow3646_ncol6003.tif"),
        title="[c]",
        add_scores=False,
        add_bkg=False,
        add_legend=False,
        ax=(2,2,3),
        fig=fig
        )

    ####################
    # Greece
    fig, ax = EMSR692_plot.plot_map_mask(
        variable="merged",
        data_area="global",
        data_type="swot",
        time_selection="2023-09-15",
        title="[d]",
        comparing_raster_Path=EMSR692_plot.project.AUX_PATH.joinpath("FM_34SEJ_20230915_CUT_nrow5720_ncol5917.tif"),
        add_scores=False,
        add_bkg=False,
        add_legend=False,
        ax=(2,2,4),
        fig=fig
        )

    ax[0].add_patch(
        mpatches.Rectangle(
            xy=(0.28, 47.1),  # lower left corner
            width=0.03,  # width of rectangle
            height=0.05,  # height of rectangle
            linewidth=2,
            linestyle='--',
            edgecolor="red",
            fill=False,
            transform=cartopy.crs.PlateCarree()._as_mpl_transform(ax[0]),
        )
    )
    ax[0].text(
        s="A",
        x=0.284, 
        y=47.1,
        transform=cartopy.crs.PlateCarree()._as_mpl_transform(ax[0]),
        fontsize=25,
        color="red",
        ha='center',
        va='center',
        **{'path_effects': [patheffects.withStroke(linewidth=3, foreground='w')]}
    )
        
    # plot in porto alegre [-51.2, -51.1, -29.8, -29.7] and [-51.25, -51.1, -30, -29.85] rectangle
    ax[1].text(
        s="Zoom [a]",
        x=-51.19, 
        y=-29.8,
        fontsize=25,
        color="red",
        transform=cartopy.crs.PlateCarree()._as_mpl_transform(ax[1]),
        **{'path_effects': [patheffects.withStroke(linewidth=3, foreground='w')]}
    )
    ax[1].add_patch(
        mpatches.Rectangle(
            xy=(-51.2, -29.8),  # lower left corner
            width=0.1,  # width of rectangle
            height=0.1,  # height of rectangle
            linewidth=2,
            color="red",
            linestyle='--',
            edgecolor="red",
            fill=False,
            transform=cartopy.crs.PlateCarree()._as_mpl_transform(ax[1]),
        )
    )
    ax[1].text(
        s="Zoom [b]",
        x=-51.24, 
        y=-30,
        fontsize=25,
        color="red",
        transform=cartopy.crs.PlateCarree()._as_mpl_transform(ax[1]),
        **{'path_effects': [patheffects.withStroke(linewidth=3, foreground='w')]}
    )
    
    ax[1].add_patch(
        mpatches.Rectangle(
            xy=(-51.25, -30),  # lower left corner
            width=0.15,  # width of rectangle
            height=0.15,  # height of rectangle
            linewidth=2,
            color="red",
            linestyle='--',
            edgecolor="red",
            fill=False,
            transform=cartopy.crs.PlateCarree()._as_mpl_transform(ax[1]),
        )
    )

    # Plot wet-snow rectangle in Ohio
    ax[2].text(
            s="B",
            x=-87.015, 
            y=37.97,
            transform=cartopy.crs.PlateCarree()._as_mpl_transform(ax[2]),
            fontsize=25,
            color="purple",
            ha='center',
            va='center',
            **{'path_effects': [patheffects.withStroke(linewidth=3, foreground='w')]}
        )
    ax[2].add_patch(
        mpatches.Rectangle(
            xy=(-87.01, 37.97),  # lower left corner
            width=0.055,  # width of rectangle
            height=0.08,  # height of rectangle
            linewidth=2,
            linestyle='--',
            edgecolor="purple",
            fill=False,
            transform=cartopy.crs.PlateCarree()._as_mpl_transform(ax[2]),
        )
    )

    ax[2].text(
            s="B'",
            x=-86.915, 
            y=37.82,
            transform=cartopy.crs.PlateCarree()._as_mpl_transform(ax[2]),
            fontsize=25,
            color="purple",
            ha='center',
            va='center',
            **{'path_effects': [patheffects.withStroke(linewidth=3, foreground='w')]}
        )
    ax[2].add_patch(
        mpatches.Rectangle(
            xy=(-86.92, 37.82),  # lower left corner
            width=0.1,  # width of rectangle
            height=0.06,  # height of rectangle
            linewidth=2,
            linestyle='--',
            edgecolor="purple",
            fill=False,
            transform=cartopy.crs.PlateCarree()._as_mpl_transform(ax[2]),
        )
    )
    
    # plot in greece [21.94, 22.15, 39.47, 39.59] rectangle
    ax[-1].text(
        s="Zoom [c]",
        x=21.95, 
        y=39.47,
        color="red",
        fontsize=25,
        transform=cartopy.crs.PlateCarree()._as_mpl_transform(ax[-1]),
        **{'path_effects': [patheffects.withStroke(linewidth=3, foreground='w')]}
    )
    ax[-1].add_patch(
        mpatches.Rectangle(
            xy=(21.94, 39.47),  # lower left corner
            width=0.21,  # width of rectangle
            height=0.12,  # height of rectangle
            linewidth=2,
            color="red",
            linestyle='--',
            edgecolor="red",
            fill=False,
            transform=cartopy.crs.PlateCarree()._as_mpl_transform(ax[-1]),
        )
    )
    # Add arrow for Nadir direction
    # Chinon : East > West
    # Porto Alegre : West > East
    # Ohio : East > West
    # Greece : West > East
    add_arrow_range(ax[0],  "Chinon")
    add_arrow_range(ax[1],  "PortoAlegre")
    add_arrow_range(ax[2],  "Ohio")
    add_arrow_range(ax[3], "Greece")
    
    # cmap, color_labels = EMSR692_plot.get_floodmask_colormap(True)
    # l1 = mpatches.Patch(color=cmap(1), label=color_labels[1])
    # l2 = mpatches.Patch(color=cmap(2), label=color_labels[2])
    # l3 = mpatches.Patch(color=cmap(3), label=color_labels[3])
    # l11 = mpatches.Patch(color=cmap(11), label=color_labels[11])
    # l12 = mpatches.Patch(color=cmap(12), label=color_labels[12])
    # l13 = mpatches.Patch(color=cmap(13), label=color_labels[13])
    # l21 = mpatches.Patch(color=cmap(21), label=color_labels[21])
    # l22 = mpatches.Patch(color=cmap(22), label=color_labels[22])
    # l23 = mpatches.Patch(color=cmap(23), label=color_labels[23])
    # ax[-2].legend(handles=[l1, l2, l3, l11, l12, l13, l21, l22, l23],loc="lower left", fontsize=18, ncols=3, bbox_to_anchor=(0.,-0.25), handlelength=1, handleheight=1)

    # Save figure
    fig.savefig(
        f"/data/scratch/globc/bonassies/workspace/swot_for_flood/examples/Paper_SWOT/Figs/merged_mask_maps_compile.pdf",
        dpi=300,
    )
    fig.savefig(
        f"/data/scratch/globc/bonassies/workspace/swot_for_flood/examples/Paper_SWOT/Figs/merged_mask_maps_compile.png",
        dpi=300,
    )
    
    plt.close("all")
    print("Elapsed time: ", round(time() - start, 2), "s for merged mask maps", flush=True)
    
    
    print("Plotting zoom maps masks", flush=True)
    fig, ax = plt.subplots(1, 3, figsize=(30,10))
    fig.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05, hspace=0.1, wspace=0.1)

    ax[0].remove()
    ax[1].remove()
    ax[2].remove()

    ####################
    # Porto Alegre - Zoom 1
    PortoAlegre_plot.plot_map_mask(
        variable="merged", 
        data_area="global", #global or flood or control
        data_type="swot", #swot
        time_selection="2024-05-06",
        title="Zoom [a]",
        comparing_raster_Path=PortoAlegre_plot.project.AUX_PATH.joinpath("FloodMask_nrow4248_ncol8052.tif"),
        add_scores=False,
        add_bkg=False,
        add_legend=False,
        ax=(1,3,1),
        fig=fig,
        extents=[-51.2, -51.1, -29.8, -29.7] # North Porto Alegre
        )

    # Porto Alegre - Zoom 2
    PortoAlegre_plot.plot_map_mask(
        variable="merged", 
        data_area="global", #global or flood or control
        data_type="swot", #swot
        time_selection="2024-05-06",
        title="Zoom [b]",
        comparing_raster_Path=PortoAlegre_plot.project.AUX_PATH.joinpath("FloodMask_nrow4248_ncol8052.tif"),
        add_scores=False,
        add_bkg=False,
        add_legend=False,
        ax=(1,3,2),
        fig=fig,
        extents=[-51.25, -51.1, -30, -29.85] # South Porto Alegre
        )

    ####################
    # Greece - Zoom 1
    fig, ax = EMSR692_plot.plot_map_mask(
        variable="merged",
        data_area="global",
        data_type="swot",
        time_selection="2023-09-15",
        title="Zoom [c]",
        comparing_raster_Path=EMSR692_plot.project.AUX_PATH.joinpath("FM_34SEJ_20230915_CUT_nrow5720_ncol5917.tif"),
        add_scores=False,
        add_bkg=False,
        add_legend=False,
        ax=(1,3,3),
        fig=fig,
        extents=[21.94, 22.15, 39.47, 39.59] # Zoom on Metamorfosis village and neighbourhood
        )

    cmap, color_labels = EMSR692_plot.get_floodmask_colormap(True)
    l1 = mpatches.Patch(color=cmap(1), label=color_labels[1])
    l2 = mpatches.Patch(color=cmap(2), label=color_labels[2])
    l3 = mpatches.Patch(color=cmap(3), label=color_labels[3])
    l11 = mpatches.Patch(color=cmap(11), label=color_labels[11])
    l12 = mpatches.Patch(color=cmap(12), label=color_labels[12])
    l13 = mpatches.Patch(color=cmap(13), label=color_labels[13])
    l21 = mpatches.Patch(color=cmap(21), label=color_labels[21])
    l22 = mpatches.Patch(color=cmap(22), label=color_labels[22])
    l23 = mpatches.Patch(color=cmap(23), label=color_labels[23])
    ax[-1].legend(handles=[l1, l2, l3, l11, l12, l13, l21, l22, l23],loc="lower left", fontsize=18, ncols=3, bbox_to_anchor=(-0.1,-0.25), handlelength=1, handleheight=1)

    # Save figure
    fig.savefig(
        f"/data/scratch/globc/bonassies/workspace/swot_for_flood/examples/Paper_SWOT/Figs/merged_mask_maps_compile_zoom.pdf",
        dpi=300,
    )

    fig.savefig(
        f"/data/scratch/globc/bonassies/workspace/swot_for_flood/examples/Paper_SWOT/Figs/merged_mask_maps_compile_zoom.png",
        dpi=300,
    )
    plt.close("all")
    print("Elapsed time: ", round(time() - start, 2), "s for mask maps zoom", flush=True)

def add_arrow_range(ax, test_case):
    match test_case:
        case "Greece":
            ax.annotate(
                "",
                xy=(0.05, 1.07),  # position of the arrow
                xytext=(0.15, 1.1),  # position of the text
                size=20,
                xycoords="axes fraction",
                textcoords="axes fraction",
                arrowprops=dict(
                    arrowstyle="->",
                    color="black",
                    lw=2,
                )   
            )
            ax.annotate("Near Range", xy=(0.1, 1.02), xytext=(0.1, 1.02), xycoords="axes fraction", textcoords="axes fraction", fontsize=20, ha="center", va="center")

            ax.annotate(
                "",
                xy=(0.95, -0.07),  # position of the text
                xytext=(0.85, -.1),  # position of the arrow
                size=20,
                xycoords="axes fraction",
                textcoords="axes fraction",
                arrowprops=dict(
                    arrowstyle="->",
                    color="black",
                    lw=2,
                )   
            )
            ax.annotate("Far Range", xy=(0.9, -.04), xytext=(0.9, -.04), xycoords="axes fraction", textcoords="axes fraction", fontsize=20, ha="center", va="center")

        case "Ohio":
            ax.annotate(
                "",
                xy=(0.95, -0.1),  # position of the text
                xytext=(0.85, -.07),  # position of the arrow
                size=20,
                xycoords="axes fraction",
                textcoords="axes fraction",
                arrowprops=dict(
                    arrowstyle="->",
                    color="black",
                    lw=2,
                )   
            )
            ax.annotate("Near Range", xy=(0.9, -.04), xytext=(0.9, -.04), xycoords="axes fraction", textcoords="axes fraction", fontsize=20, ha="center", va="center")

            ax.annotate(
                "",
                xy=(0.05, 1.1),  # position of the arrow
                xytext=(0.15, 1.07),  # position of the text
                size=20,
                xycoords="axes fraction",
                textcoords="axes fraction",
                arrowprops=dict(
                    arrowstyle="->",
                    color="black",
                    lw=2,
                )   
            )
            ax.annotate("Far Range", xy=(0.1, 1.02), xytext=(0.1, 1.02), xycoords="axes fraction", textcoords="axes fraction", fontsize=20, ha="center", va="center")

        case "Chinon":
            ax.annotate(
                "",
                xy=(0.95, -0.1),  # position of the text
                xytext=(0.85, -.07),  # position of the arrow
                size=20,
                xycoords="axes fraction",
                textcoords="axes fraction",
                arrowprops=dict(
                    arrowstyle="->",
                    color="black",
                    lw=2,
                )   
            )
            ax.annotate("Near Range", xy=(0.9, -.04), xytext=(0.9, -.04), xycoords="axes fraction", textcoords="axes fraction", fontsize=20, ha="center", va="center")

            ax.annotate(
                "",
                xy=(0.05, 1.1),  # position of the arrow
                xytext=(0.15, 1.07),  # position of the text
                size=20,
                xycoords="axes fraction",
                textcoords="axes fraction",
                arrowprops=dict(
                    arrowstyle="->",
                    color="black",
                    lw=2,
                )   
            )
            ax.annotate("Far Range", xy=(0.1, 1.02), xytext=(0.1, 1.02), xycoords="axes fraction", textcoords="axes fraction", fontsize=20, ha="center", va="center")

        case "PortoAlegre":
            ax.annotate(
                "",
                xy=(0.05, 1.1),  # position of the arrow
                xytext=(0.15, 1.07),  # position of the text
                size=20,
                xycoords="axes fraction",
                textcoords="axes fraction",
                arrowprops=dict(
                    arrowstyle="->",
                    color="black",
                    lw=2,
                )   
            )
            ax.annotate("Near Range", xy=(0.1, 1.02), xytext=(0.1, 1.02), xycoords="axes fraction", textcoords="axes fraction", fontsize=20, ha="center", va="center")

            ax.annotate(
                "",
                xy=(0.95, -0.1),  # position of the text
                xytext=(0.85, -.07),  # position of the arrow
                size=20,
                xycoords="axes fraction",
                textcoords="axes fraction",
                arrowprops=dict(
                    arrowstyle="->",
                    color="black",
                    lw=2,
                )   
            )
            ax.annotate("Far Range", xy=(0.9, -.04), xytext=(0.9, -.04), xycoords="axes fraction", textcoords="axes fraction", fontsize=20, ha="center", va="center")

def plot_polygons(plot_obj,ax):
    # polygon_control = plot_obj.swot_collection.controlmask
    polygon_flood = plot_obj.swot_collection.floodmask
    # set crs to WGS84
    # polygon_control = polygon_control.to_crs(4326)
    polygon_flood = polygon_flood.to_crs(4326)
    # plot the polygons
    # polygon_control.plot(ax=ax, color="none", edgecolor="black", linewidth=1)
    polygon_flood.plot(ax=ax, color='blue', alpha=0.5, linewidth=1)     
 
def main(variable, S1_S2, ESA_WC, CLASSIF, MEAN, HISTO, WATER_MASK, ZOOM_MASK, MAPS, COMPARE_MASKS, SAVE_MASKS, Chinon_plot:PlotRaster, PortoAlegre_plot:PlotRaster, Ohio_plot:PlotRaster, EMSR692_plot:PlotRaster):
    print("-"*30)
    print("Do S1_S2: ", S1_S2)
    print("Do ESA_WC: ", ESA_WC)
    print("Do CLASSIF: ", CLASSIF)
    print("Do MEAN: ", MEAN)
    print("Do HISTO: ", HISTO)
    print("Do WATER_MASK: ", WATER_MASK)
    print("Do ZOOM_MASK: ", ZOOM_MASK)
    print("Do MAPS: ", MAPS)
    print("Do COMPARE_MASKS: ", COMPARE_MASKS)
    print("Do SAVE_MASKS: ", SAVE_MASKS)
    
    if variable == "sig0":
        vmin=-20.
        vmax=40.
        cmap="viridis"
        Ohio_thresholds={"urban":-0, "forest":5.5, "open":9.5}
        PA_thresholds={"urban":-0, "forest":5, "open":10}
        PA_urban_diff=False
        Greece_thresholds={"urban":8, "forest":7, "open":9}
        Greece_urban_diff=True
        Chinon_thresholds={"urban":-0, "forest":10, "open":10}
        
    elif variable == "coherent_power":
        vmin=45.
        vmax=85.
        cmap="plasma"
        Ohio_thresholds={"urban":-0, "forest":62.5, "open":65}
        Ohio_threshold_gamma = 0.5
        PA_thresholds={"urban":-0, "forest":62, "open":70}
        PA_urban_diff=False
        Greece_thresholds={"urban":70, "forest":65, "open":65}
        Greece_urban_diff=False
        Chinon_thresholds={"urban":-0, "forest":64, "open":64}
        
    elif variable == "gamma_tot":
        vmin=0.
        vmax=1.
        cmap=Colormap("seaborn:mako").to_matplotlib()
        Ohio_thresholds={"urban":-0, "forest":0.7, "open":0.85}
        PA_thresholds={"urban":-0.1, "forest":0.65, "open":0.8} # swot with urban diff
        PA_urban_diff=True
        Greece_thresholds={"urban":0.9, "forest":0.85, "open":0.9}
        Greece_urban_diff=False
        Chinon_thresholds={"urban":-0, "forest":0.725, "open":0.725}
        
    print("Variable: ", variable)
    print("plot range: ", vmin, vmax)
    print("Colormap: ", "seaborn:mako" if not isinstance(cmap, str) else cmap)
        
    start000 = time()
    print("Start", flush=True)
    
    ########################################################################################################################
    #### S1 and S2 plots
    ########################################################################################################################
    if S1_S2:
        start = time()
        print("Plotting S1 and S2 images", flush=True)
        fig, ax = plt.subplots(2, 2, figsize=(12, 8), dpi=300,
                                subplot_kw={'projection': (cartopy.crs.PlateCarree())})
        ax[0, 0].remove()
        ax[0, 1].remove()
        ax[1, 0].remove()
        ax[1, 1].remove()

        path_aux_Ohio = Ohio_project.AUX_PATH.joinpath("FM_20250222T000000_S1_POST_fusion_cut_32616_nrow3646_ncol6003.tif")
        path_aux_Chinon = Chinon_project.AUX_PATH.joinpath("FM_30TYT_20240331T174856_S1_132_POST_nrow1493_ncol2633.tif")
        path_aux_PortAlegre = PortoAlegre_project.AUX_PATH.joinpath("S2A_merged_32722_20240506T131349.tif")
        path_aux_EMSR692 = EMSR692_project.AUX_PATH.joinpath("FM_34SEJ_20230915_CUT_nrow5720_ncol5917.tif")
        title_aux_Chinon =     "[a]" #   "FloodML mask from Sentinel-1 image (2024-03-31 17:48)"
        title_aux_PortAlegre = "[b]" #   "Sentinel-2A RGB image (2024-05-06 13:13)"
        title_aux_Ohio =       "[c]" #   "FloodML mask from Sentinel-1 image (2025-02-22 23:48)"
        title_aux_EMSR692 =    "[d]" #   "FloodML mask from Sentine-2A image (2023-09-15 09:20)"

        Chinon_plot.plot_auxiliary_data(
            path_to_raster=path_aux_Chinon,
            title=title_aux_Chinon,
            is_multiband=False,
            is_worldcover=False,
            vmin=0,
            vmax=1,
            fig=fig,
            ax=(2,2,1),
            add_cbar=False
        )

        PortoAlegre_plot.plot_auxiliary_data(
            path_to_raster=path_aux_PortAlegre,
            title=title_aux_PortAlegre,
            is_multiband=True, 
            is_worldcover=False,
            fig=fig,
            ax=(2,2,2),
            add_cbar=False
        )

        Ohio_plot.plot_auxiliary_data(
            path_to_raster=path_aux_Ohio,
            title=title_aux_Ohio,
            is_multiband=False,
            is_worldcover=False,
            vmin=0,
            vmax=1,
            fig=fig,
            ax=(2,2,3),
            add_cbar=False
        )

        _, ax = EMSR692_plot.plot_auxiliary_data(
            path_to_raster=path_aux_EMSR692,
            title=title_aux_EMSR692,
            is_multiband=False,
            is_worldcover=False,
            make_mask = True,
            mask_value = 1,
            vmin=0,
            vmax=1,
            fig=fig,
            ax=(2,2,4),
            add_cbar=False
        )

        fig.savefig(
            "/data/scratch/globc/bonassies/workspace/swot_for_flood/examples/Paper_SWOT/Figs/S1_S2_compile.pdf",
            dpi=300,
            bbox_inches='tight'
        )
        fig.savefig(
            "/data/scratch/globc/bonassies/workspace/swot_for_flood/examples/Paper_SWOT/Figs/S1_S2_compile.png",
            dpi=300,
            bbox_inches='tight'
        )
        plt.close("all")
        print("Elapsed time: ", round(time() - start, 2), "s for S1 and S2 images", flush=True)
    ########################################################################################################################
    #### ESA World Cover plots
    ########################################################################################################################
    if ESA_WC:
        start = time()
        print("Plotting ESA World Cover images", flush=True)
        fig, ax = plt.subplots(2, 2, figsize=(12, 8), dpi=300,
                            subplot_kw={'projection': (cartopy.crs.PlateCarree())})
        ax[0, 0].remove()
        ax[0, 1].remove()
        ax[1, 0].remove()
        ax[1, 1].remove()

        path_aux_Ohio = Ohio_project.AUX_PATH.joinpath("ESA_WC_Fusion_cut_32616_nrow3646_ncol6003.tif")
        path_aux_Chinon = Chinon_project.AUX_PATH.joinpath("ESA_WorldCover_10m_merged_32630_clip.tif")
        path_aux_PortAlegre = PortoAlegre_project.AUX_PATH.joinpath("ESA_WorldCover_10m_merged_32722_clip.tif")
        path_aux_EMSR692 = EMSR692_project.AUX_PATH.joinpath("ESA_WC_cut_V2_32634_nrow5720_ncol5917.tif")
        title_aux_Chinon =     "[a]" #   "FloodML mask from Sentinel-1 image (2024-03-31 17:48)"
        title_aux_PortAlegre = "[b]" #   "Sentinel-2A RGB image (2024-05-06 13:13)"
        title_aux_Ohio =       "[c]" #   "FloodML mask from Sentinel-1 image (2025-02-22 23:48)"
        title_aux_EMSR692 =    "[d]" #   "FloodML mask from Sentine-2A image (2023-09-15 09:20)"

        Chinon_plot.plot_auxiliary_data(
            path_to_raster=path_aux_Chinon,
            title=title_aux_Chinon,
            is_multiband=False,
            is_worldcover=True,
            fig=fig,
            ax=(2,2,1),
            add_cbar=False
        )

        PortoAlegre_plot.plot_auxiliary_data(
            path_to_raster=path_aux_PortAlegre,
            title=title_aux_PortAlegre,
            is_multiband=False, 
            is_worldcover=True,
            fig=fig,
            ax=(2,2,2),
            add_cbar=True
        )

        Ohio_plot.plot_auxiliary_data(
            path_to_raster=path_aux_Ohio,
            title=title_aux_Ohio,
            is_multiband=False,
            is_worldcover=True,
            fig=fig,
            ax=(2,2,3),
            add_cbar=False
        )

        _, ax = EMSR692_plot.plot_auxiliary_data(
            path_to_raster=path_aux_EMSR692,
            title=title_aux_EMSR692,
            is_multiband=False,
            is_worldcover=True,
            fig=fig,
            ax=(2,2,4),
            add_cbar=False
        )

        plot_polygons(Chinon_plot, ax[0])
        plot_polygons(PortoAlegre_plot, ax[1])
        plot_polygons(Ohio_plot, ax[2])
        plot_polygons(EMSR692_plot, ax[3])

        handles = [
            Line2D([0], [0], linestyle='none', mfc='blue', mec='blue', alpha=0.5, marker='s', label='flood mask'),
            # Line2D([0], [0], linestyle='-', color='black', mfc='none', mec='none', marker='s', label='control mask'),
        ]
        ax[0].legend(handles=handles, loc="upper right", fontsize=14)

        fig.savefig(
            "/data/scratch/globc/bonassies/workspace/swot_for_flood/examples/Paper_SWOT/Figs/ESA_WC_compile.pdf",
            dpi=300,
        )
        fig.savefig(
            "/data/scratch/globc/bonassies/workspace/swot_for_flood/examples/Paper_SWOT/Figs/ESA_WC_compile.png",
            dpi=300,
        )
        plt.close("all")
        print("Elapsed time: ", round(time() - start, 2), "s for ESA World Cover images", flush=True)
    ########################################################################################################################
    #### SWOT CLASSIFICATION
    ########################################################################################################################
    if CLASSIF:
        start = time()
        print("Plotting SWOT classification images", flush=True)
        fig, ax = plt.subplots(2, 2, figsize=(12, 8), dpi=300,
                            subplot_kw={'projection': (cartopy.crs.PlateCarree())})
        ax[0, 0].remove()
        ax[0, 1].remove()
        ax[1, 0].remove()
        ax[1, 1].remove()

        title_aux_Chinon =     "[a]" #   "FloodML mask from Sentinel-1 image (2024-03-31 17:48)"
        title_aux_PortAlegre = "[b]" #   "Sentinel-2A RGB image (2024-05-06 13:13)"
        title_aux_Ohio =       "[c]" #   "FloodML mask from Sentinel-1 image (2025-02-22 23:48)"
        title_aux_EMSR692 =    "[d]" #   "FloodML mask from Sentine-2A image (2023-09-15 09:20)"

        Chinon_plot.plot_classification(
            data_area="global",
            time_selection='2024-03-31',
            title=title_aux_Chinon,
            show_fig=False,
            save_fig=False,
            add_legend=False,
            fig=fig,
            ax=(2,2,1),
        )

        PortoAlegre_plot.plot_classification(
            data_area="global",
            time_selection='2024-05-06',
            title=title_aux_PortAlegre,
            show_fig=False,
            save_fig=False,
            add_legend=True,
            fig=fig,
            ax=(2,2,2),
        )

        Ohio_plot.plot_classification(
            data_area="global",
            time_selection='2025-02-20',
            title=title_aux_Ohio,
            show_fig=False,
            save_fig=False,
            add_legend=False,
            fig=fig,
            ax=(2,2,3),
        )

        _, ax = EMSR692_plot.plot_classification(
            data_area="global",
            time_selection='2023-09-15',
            title=title_aux_EMSR692,
            show_fig=False,
            save_fig=False,
            add_legend=False,
            fig=fig,
            ax=(2,2,4),
        )

        fig.savefig(
            "/data/scratch/globc/bonassies/workspace/swot_for_flood/examples/Paper_SWOT/Figs/SWOT_classification_compile.pdf",
            dpi=300,
        )
        fig.savefig(
            "/data/scratch/globc/bonassies/workspace/swot_for_flood/examples/Paper_SWOT/Figs/SWOT_classification_compile.png",
            dpi=300,
        )
        print("Elapsed time: ", round(time() - start, 2), "s for SWOT classification", flush=True)
    ########################################################################################################################
    #### MEAN PLOT
    ########################################################################################################################
    if MEAN:
        start = time()
        print("Plotting mean images", flush=True)
        fig, ax = plt.subplots(2, 2, figsize=(15,10))

        title_aux_Chinon =     "[a]" #   "FloodML mask from Sentinel-1 image (2024-03-31 17:48)"
        title_aux_PortAlegre = "[b]" #   "Sentinel-2A RGB image (2024-05-06 13:13)"
        title_aux_Ohio =       "[c]" #   "FloodML mask from Sentinel-1 image (2025-02-22 23:48)"
        title_aux_EMSR692 =    "[d]" #   "FloodML mask from Sentine-2A image (2023-09-15 09:20)"

        Chinon_plot.plot_mean_hist_computation(
            variable=variable,
            title=title_aux_Chinon,
            fig=fig,
            hist_range=(vmin, vmax),
            ax=ax[0,0],
        )
        PortoAlegre_plot.plot_mean_hist_computation(
            variable=variable,
            title=title_aux_PortAlegre,
            fig=fig,
            hist_range=(vmin, vmax),
            ax=ax[0,1],
        )
        Ohio_plot.plot_mean_hist_computation(
            variable=variable,
            title=title_aux_Ohio,
            fig=fig,
            hist_range=(vmin, vmax),
            ax=ax[1,0],
        )
        _, ax = EMSR692_plot.plot_mean_hist_computation(
            variable=variable,
            title=title_aux_EMSR692,
            fig=fig,
            hist_range=(vmin, vmax),
            ax=ax[1,1],
        )
        fig.tight_layout()
        fig.savefig(
            f"/data/scratch/globc/bonassies/workspace/swot_for_flood/examples/Paper_SWOT/Figs/mean_computation_{variable}_compile.pdf",
            dpi=300,
        )
        fig.savefig(
            f"/data/scratch/globc/bonassies/workspace/swot_for_flood/examples/Paper_SWOT/Figs/mean_computation_{variable}_compile.png",
            dpi=300,
        )
        plt.close("all")
        print("Elapsed time: ", round(time() - start, 2), "s for mean histo", flush=True)
        start = time()
        
        fig, ax = plt.subplots(2 , 2, figsize=(25,20))

        ax[0,0].remove()
        ax[0,1].remove()
        ax[1,0].remove()
        ax[1,1].remove()

        ####################
        # Chinon
        Chinon_plot.plot_map(
            variable=variable,
            data_area="global",
            data_type="mean",
            world_cover_selection=None,
            time_selection="2024-03-31",
            cmap=cmap,
            vmin=vmin,
            vmax=vmax,
            add_bkg=False,
            title="[a]",
            ax=(2,2,1),
            fig=fig
            )

        ####################
        # Porto Alegre
        PortoAlegre_plot.plot_map(
            variable=variable,
            data_area="global",
            data_type="mean",
            world_cover_selection=None,
            time_selection="2024-05-06",
            cmap=cmap,
            vmin=vmin,
            vmax=vmax,
            add_bkg=False,
            title="[b]",
            ax=(2,2,2),
            fig=fig
        )

        ####################
        # Ohio
        Ohio_plot.plot_map(
            variable=variable,
            data_area="global",
            data_type="mean",
            world_cover_selection=None,
            time_selection="2025-02-20",
            cmap=cmap,
            vmin=vmin,
            vmax=vmax,
            add_bkg=False,
            title="[c]",
            ax=(2,2,3),
            fig=fig
        )

        ####################
        # Greece
        fig, ax = EMSR692_plot.plot_map(
            variable=variable,
            data_area="global",
            data_type="mean",
            world_cover_selection=None,
            time_selection="2023-09-15",
            cmap=cmap,
            vmin=vmin,
            vmax=vmax,
            add_bkg=False,
            title="[d]",
            ax=(2,2,4),
            fig=fig
        )

        # Add arrow for Nadir direction
        # Chinon : East > West
        # Porto Alegre : West > East
        # Ohio : East > West
        # Greece : West > East
        add_arrow_range(ax[0],  "Chinon")
        add_arrow_range(ax[4],  "PortoAlegre")
        add_arrow_range(ax[8],  "Ohio")
        add_arrow_range(ax[12], "Greece")
        
        ax[0].add_patch(
            mpatches.Rectangle(
                xy=(0.28, 47.1),  # lower left corner
                width=0.03,  # width of rectangle
                height=0.05,  # height of rectangle
                linewidth=2,
                linestyle='--',
                edgecolor="red",
                fill=False,
                transform=cartopy.crs.PlateCarree()._as_mpl_transform(ax[0]),
            )
        )
        ax[0].text(
            s="A",
            x=0.284, 
            y=47.1,
            transform=cartopy.crs.PlateCarree()._as_mpl_transform(ax[0]),
            fontsize=25,
            color="red",
            ha='center',
            va='center',
            **{'path_effects': [patheffects.withStroke(linewidth=3, foreground='w')]}
        )
        # Plot wet-snow rectangle in Ohio
        ax[8].text(
                s="B",
                x=-87.015, 
                y=37.97,
                transform=cartopy.crs.PlateCarree()._as_mpl_transform(ax[8]),
                fontsize=25,
                color="purple",
                ha='center',
                va='center',
                **{'path_effects': [patheffects.withStroke(linewidth=3, foreground='w')]}
            )
        ax[8].add_patch(
            mpatches.Rectangle(
                xy=(-87.01, 37.97),  # lower left corner
                width=0.055,  # width of rectangle
                height=0.08,  # height of rectangle
                linewidth=2,
                linestyle='--',
                edgecolor="purple",
                fill=False,
                transform=cartopy.crs.PlateCarree()._as_mpl_transform(ax[8]),
            )
        )

        ax[8].text(
                s="B'",
                x=-86.915, 
                y=37.82,
                transform=cartopy.crs.PlateCarree()._as_mpl_transform(ax[8]),
                fontsize=25,
                color="purple",
                ha='center',
                va='center',
                **{'path_effects': [patheffects.withStroke(linewidth=3, foreground='w')]}
            )
        ax[8].add_patch(
            mpatches.Rectangle(
                xy=(-86.92, 37.82),  # lower left corner
                width=0.1,  # width of rectangle
                height=0.06,  # height of rectangle
                linewidth=2,
                linestyle='--',
                edgecolor="purple",
                fill=False,
                transform=cartopy.crs.PlateCarree()._as_mpl_transform(ax[8]),
            )
        )
        
        # Save figure
        fig.savefig(
            f"/data/scratch/globc/bonassies/workspace/swot_for_flood/examples/Paper_SWOT/Figs/maps_mean_{variable}_compile.pdf",
            dpi=300,
        )
        fig.savefig(
            f"/data/scratch/globc/bonassies/workspace/swot_for_flood/examples/Paper_SWOT/Figs/maps_mean_{variable}_compile.png",
            dpi=300,
        )
        print("Elapsed time: ", round(time() - start, 2), "s for mean maps", flush=True)
    #########################################################################################################################
    #### HISTOGRAMS
    #########################################################################################################################
    if HISTO:
        start = time()
        print("Plotting histograms", flush=True)
        fig, ax = plt.subplots(4, 3, figsize=(15,10))

        ax[0,0].set_ylabel("Porto Alegre, Brazil\nEMSN 192", fontsize=14, fontweight='bold')
        ax[1,0].set_ylabel("Farkadona, Greece\nEMSR 692", fontsize=14, fontweight='bold')
        ax[2,0].set_ylabel("Chinon, France", fontsize=14, fontweight='bold')
        ax[3,0].set_ylabel("Owensboro, USA\nOhio River", fontsize=14, fontweight='bold')

        y_text = 0.95

        ####################
        # Porto Alegre
        PortoAlegre_plot.plot_histogram(
            variable=variable,
            data_area="flood",
            data_type="swot",
            world_cover_selection="open",
            time_selection='2024-05-06',
            range_hist=(vmin, vmax),
            use_seaborn=False,
            add_ylabel=False,
            add_xlabel=True,
            title="[a]",
            fig=fig,
            ax=ax[0,0],
            y_text=y_text
        )
        ax[0,0].axvline(PA_thresholds["open"], color='red', linestyle=':', label='Threshold')
        ax[0,0].legend(handles=[
            Line2D([0], [0], color='red', linestyle=':', label='Thresholds'),
            Line2D([0], [0], color='grey', linestyle='--', label='Medians'),
            ], fontsize=12)
        PortoAlegre_plot.plot_histogram(
            variable=variable,
            data_area="flood",
            data_type="swot",
            world_cover_selection="forest",
            time_selection='2024-05-06',
            range_hist=(vmin, vmax),
            use_seaborn=False,
            title="[b]",
            add_ylabel=False,
            add_xlabel=True,
            fig=fig,
            ax=ax[0,1],
            y_text=y_text
        )
        
        ax[0,1].axvline(PA_thresholds["forest"], color='red', linestyle=':', label='Threshold')
        PortoAlegre_plot.plot_histogram(
            variable=variable,
            data_area="flood",
            data_type="swot",
            world_cover_selection="urban",
            time_selection='2024-05-06',
            range_hist=(vmin, vmax),
            use_seaborn=False,
            title="[c]",
            add_ylabel=False,
            add_xlabel=True,
            fig=fig,
            ax=ax[0,2],
            y_text=y_text,
            ha="right",
            va="top",
            ha_mean="left",
        )
        if not PA_urban_diff and PA_thresholds["urban"] > 0:
            ax[0,2].axvline(PA_thresholds["urban"], color='red', linestyle=':', label='Threshold')
            
        ####################
        # Greece
        EMSR692_plot.plot_histogram(
            variable=variable,
            data_area="flood",
            data_type="swot",
            world_cover_selection="open",
            time_selection='2023-09-15',
            range_hist=(vmin, vmax),
            use_seaborn=False,
            add_ylabel=False,
            add_xlabel=True,
            title="[d]",
            fig=fig,
            ax=ax[1,0],
            y_text=y_text
        )
        ax[1,0].axvline(Greece_thresholds["open"], color='red', linestyle=':', label='Threshold')
        EMSR692_plot.plot_histogram(
            variable=variable,
            data_area="flood",
            data_type="swot",
            world_cover_selection="forest",
            time_selection='2023-09-15',
            range_hist=(vmin, vmax),
            title="[e]",
            use_seaborn=False,
            add_ylabel=False,
            add_xlabel=True,
            fig=fig,
            ax=ax[1,1],
            y_text=y_text
        )
        ax[1,1].axvline(Greece_thresholds["forest"], color='red', linestyle=':', label='Threshold')
        EMSR692_plot.plot_histogram(
            variable=variable,
            data_area="flood",
            data_type="swot",
            world_cover_selection="urban",
            time_selection='2023-09-15',
            range_hist=(vmin, vmax),
            title="[f]",
            use_seaborn=False,
            add_ylabel=False,
            add_xlabel=True,
            fig=fig,
            ax=ax[1,2],
            y_text=y_text
        )
        if not Greece_urban_diff:
            ax[1,2].axvline(Greece_thresholds["urban"], color='red', linestyle=':', label='Threshold')

        ####################
        # Chinon
        Chinon_plot.plot_histogram(
            variable=variable,
            data_area="flood",
            data_type="swot",
            world_cover_selection="open",
            time_selection='2024-03-31',
            range_hist=(vmin, vmax),
            use_seaborn=False,
            add_ylabel=False,
            add_xlabel=True,
            title="[g]",
            fig=fig,
            ax=ax[2,0],
            y_text=y_text
        )
        ax[2,0].axvline(Chinon_thresholds["open"], color='red', linestyle=':', label='Threshold')
        
        Chinon_plot.plot_histogram(
            variable=variable,
            data_area="flood",
            data_type="swot",
            world_cover_selection="forest",
            time_selection='2024-03-31',
            range_hist=(vmin, vmax),
            use_seaborn=False,
            title="[h]",
            add_ylabel=False,
            add_xlabel=True,
            fig=fig,
            ax=ax[2,1],
            y_text=y_text
        )
        ax[2,1].axvline(Chinon_thresholds["forest"], color='red', linestyle=':', label='Threshold')
        ax[2,2].remove() # no urban in Chinon

        ####################
        # Ohio
        Ohio_plot.plot_histogram(
            variable=variable,
            data_area="flood",
            data_type="swot",
            world_cover_selection="open",
            time_selection='2025-02-20',
            range_hist=(vmin, vmax),
            use_seaborn=False,
            add_ylabel=False,
            add_xlabel=True,
            title="[i]",
            fig=fig,
            ax=ax[3,0],
            y_text=y_text
        )
        ax[3,0].axvline(Ohio_thresholds["open"], color='red', linestyle=':', label='Threshold')
        Ohio_plot.plot_histogram(
            variable=variable,
            data_area="flood",
            data_type="swot",
            world_cover_selection="forest",
            time_selection='2025-02-20',
            range_hist=(vmin, vmax),
            title="[j]",
            use_seaborn=False,
            add_ylabel=False,
            add_xlabel=True,
            fig=fig,
            ax=ax[3,1],
            y_text=y_text
        )
        ax[3,1].axvline(Ohio_thresholds["forest"], color='red', linestyle=':', label='Threshold')
        ax[3,2].remove() # no urban in Ohio
        
        # Create a table with the median values
        table_data = [
            ["Event", "Open", "Forest", "Urban"],
            ["Porto Alegre: Dry mean", round(PortoAlegre_plot.median_mean_open, 2), round(PortoAlegre_plot.median_mean_forest, 2), round(PortoAlegre_plot.median_mean_urban, 2)],
            ["Porto Alegre: 2024-05-06", round(PortoAlegre_plot.median_open, 2), round(PortoAlegre_plot.median_forest, 2), round(PortoAlegre_plot.median_urban, 2)],
            ["Greece: Dry mean", round(EMSR692_plot.median_mean_open, 2), round(EMSR692_plot.median_mean_forest, 2), round(EMSR692_plot.median_mean_urban, 2)],
            ["Greece: 2023-09-15", round(EMSR692_plot.median_open, 2), round(EMSR692_plot.median_forest, 2), round(EMSR692_plot.median_urban, 2)],
            ["Chinon: Dry mean", round(Chinon_plot.median_mean_open, 2), round(Chinon_plot.median_mean_forest, 2), ""],
            ["Chinon: 2024-03-31", round(Chinon_plot.median_open, 2), round(Chinon_plot.median_forest, 2), ""],
            ["Ohio: Dry mean", round(Ohio_plot.median_mean_open, 2), round(Ohio_plot.median_mean_forest, 2), ""],
            ["Ohio: 2025-02-20", round(Ohio_plot.median_open, 2), round(Ohio_plot.median_forest, 2), ""],
        ]
        # table_data = [
        #     ["Event", "Open\nareas", "Forest\nareas", "Urban\nareas"],
        #     ["Porto Alegre", f"> {PA_thresholds["open"]}", f"> {PA_thresholds["forest"]}", f"> {PA_thresholds["urban"]}" if not PA_urban_diff else f"$\Delta_{"mean"}$ < {PA_thresholds["urban"]}"],
        #     ["Greece", f"> {Greece_thresholds["open"]}", f"> {Greece_thresholds["forest"]}", f"> {Greece_thresholds["urban"]}" if not Greece_urban_diff else f"$\Delta_{"mean"}$ > {Greece_thresholds["urban"]}"],
        #     ["Chinon", f"> {Chinon_thresholds["open"]}", f"> {Chinon_thresholds["forest"]}", ""],
        #     ["Ohio", f"> {Ohio_thresholds["open"]}", f"> {Ohio_thresholds["forest"]}", ""],
        # ]
        # Add the table to the figure
        print("4, 3, (8, 11)", flush=True)
        table = fig.add_subplot(4, 3, (9, 12))
        table.axis("off")
        table.axis("tight")
        table.axis("equal")
        table.set_title("Median values", fontsize=16, fontweight='bold')
        the_table = table.table(cellText=table_data, colLabels=None, cellLoc="center", loc="center", colWidths=[0.55, 0.15, 0.15, 0.15])
        the_table.scale(1, 1.65)
        the_table.auto_set_font_size(False)
        the_table.set_fontsize(12)
        
        
        # Save figure
        fig.tight_layout()
        fig.savefig(
            f"/data/scratch/globc/bonassies/workspace/swot_for_flood/examples/Paper_SWOT/Figs/histo_{variable}_compile.pdf",
            dpi=300,
        )
        fig.savefig(
            f"/data/scratch/globc/bonassies/workspace/swot_for_flood/examples/Paper_SWOT/Figs/histo_{variable}_compile.png",
            dpi=300,
        )
        plt.close("all")
        print("Elapsed time: ", round(time() - start, 2), "s for histograms", flush=True)
    #########################################################################################################################
    #### MAPS variables
    #########################################################################################################################
    if MAPS:
        start = time()
        print("Plotting variable maps", flush=True)
        fig, ax = plt.subplots(2 , 2, figsize=(25,20))

        ax[0,0].remove()
        ax[0,1].remove()
        ax[1,0].remove()
        ax[1,1].remove()

        ####################
        # Chinon
        Chinon_plot.plot_map(
            variable=variable,
            data_area="global",
            data_type="swot",
            world_cover_selection=None,
            time_selection="2024-03-31",
            cmap=cmap,
            vmin=vmin,
            vmax=vmax,
            add_bkg=False,
            add_cbar=True,
            add_legend=False,
            title="[a]",
            ax=(2,2,1),
            fig=fig
            )

        ####################
        # Porto Alegre
        PortoAlegre_plot.plot_map(
            variable=variable,
            data_area="global",
            data_type="swot",
            world_cover_selection=None,
            time_selection="2024-05-06",
            cmap=cmap,
            vmin=vmin,
            vmax=vmax,
            add_bkg=False,
            add_cbar=True,
            add_legend=False,
            title="[b]",
            ax=(2,2,2),
            fig=fig
        )

        ####################
        # Ohio
        Ohio_plot.plot_map(
            variable=variable,
            data_area="global",
            data_type="swot",
            world_cover_selection=None,
            time_selection="2025-02-20",
            cmap=cmap,
            vmin=vmin,
            vmax=vmax,
            add_bkg=False,
            add_cbar=True,
            add_legend=False,
            title="[c]",
            ax=(2,2,3),
            fig=fig
        )

        ####################
        # Greece
        fig, ax = EMSR692_plot.plot_map(
            variable=variable,
            data_area="global",
            data_type="swot",
            world_cover_selection=None,
            time_selection="2023-09-15",
            cmap=cmap,
            vmin=vmin,
            vmax=vmax,
            add_bkg=False,
            add_cbar=True,
            add_legend=False,
            title="[d]",
            ax=(2,2,4),
            fig=fig
        )

        # Add arrow for Nadir direction
        # Chinon : East > West
        # Porto Alegre : West > East
        # Ohio : East > West
        # Greece : West > East
        add_arrow_range(ax[0],  "Chinon")
        add_arrow_range(ax[4],  "PortoAlegre")
        add_arrow_range(ax[8],  "Ohio")
        add_arrow_range(ax[12], "Greece")

        ax[0].add_patch(
            mpatches.Rectangle(
                xy=(0.28, 47.1),  # lower left corner
                width=0.03,  # width of rectangle
                height=0.05,  # height of rectangle
                linewidth=2,
                linestyle='--',
                edgecolor="red",
                fill=False,
                transform=cartopy.crs.PlateCarree()._as_mpl_transform(ax[0]),
            )
        )
        ax[0].text(
            s="A",
            x=0.284, 
            y=47.1,
            transform=cartopy.crs.PlateCarree()._as_mpl_transform(ax[0]),
            fontsize=25,
            color="red",
            ha='center',
            va='center',
            **{'path_effects': [patheffects.withStroke(linewidth=3, foreground='w')]}
        )
        # Plot wet-snow rectangle in Ohio
        ax[8].text(
                s="B",
                x=-87.015, 
                y=37.97,
                transform=cartopy.crs.PlateCarree()._as_mpl_transform(ax[8]),
                fontsize=25,
                color="purple",
                ha='center',
                va='center',
                **{'path_effects': [patheffects.withStroke(linewidth=3, foreground='w')]}
            )
        ax[8].add_patch(
            mpatches.Rectangle(
                xy=(-87.01, 37.97),  # lower left corner
                width=0.055,  # width of rectangle
                height=0.08,  # height of rectangle
                linewidth=2,
                linestyle='--',
                edgecolor="purple",
                fill=False,
                transform=cartopy.crs.PlateCarree()._as_mpl_transform(ax[8]),
            )
        )

        ax[8].text(
                s="B'",
                x=-86.915, 
                y=37.82,
                transform=cartopy.crs.PlateCarree()._as_mpl_transform(ax[8]),
                fontsize=25,
                color="purple",
                ha='center',
                va='center',
                **{'path_effects': [patheffects.withStroke(linewidth=3, foreground='w')]}
            )
        ax[8].add_patch(
            mpatches.Rectangle(
                xy=(-86.92, 37.82),  # lower left corner
                width=0.1,  # width of rectangle
                height=0.06,  # height of rectangle
                linewidth=2,
                linestyle='--',
                edgecolor="purple",
                fill=False,
                transform=cartopy.crs.PlateCarree()._as_mpl_transform(ax[8]),
            )
        )
        

        # Save figure
        fig.savefig(
            f"/data/scratch/globc/bonassies/workspace/swot_for_flood/examples/Paper_SWOT/Figs/maps_{variable}_compile.pdf",
            dpi=300,
        )
        fig.savefig(
            f"/data/scratch/globc/bonassies/workspace/swot_for_flood/examples/Paper_SWOT/Figs/maps_{variable}_compile.png",
            dpi=300,
        )
        plt.close("all")
        print("Elapsed time: ", round(time() - start, 2), "s for variable maps", flush=True)
    #########################################################################################################################
    #### WATER MASK
    #########################################################################################################################
    if WATER_MASK:
        start = time()
        print("Plotting water mask", flush=True)
        fig, ax = plt.subplots(2, 2, figsize=(25,20))
        fig.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05, hspace=0.1, wspace=0.1)

        ax[0,0].remove()
        ax[0,1].remove()
        ax[1,0].remove()
        ax[1,1].remove()


        ####################
        # Chinon
        Chinon_plot.swot_collection.create_flood_mask(
            variable=variable,
            data_area="global",
            data_type="swot",
            thresholds=Chinon_thresholds,
            time_selection="2024-03-31",
            add_uncertainty=True,
            threshold_gamma=0.5,
            threshold_SNR=0.5,
            )
        Chinon_plot.plot_map_mask(
            variable=variable,
            data_area="global",
            data_type="swot",
            time_selection="2024-03-31",
            title="[a]",
            comparing_raster_Path=Chinon_plot.project.AUX_PATH.joinpath("FM_30TYT_20240331T174856_S1_132_POST_nrow1496_ncol2635.tif"),
            add_scores=False,
            add_bkg=False,
            add_legend=False,
            ax=(2,2,1),
            fig=fig
            )

        ####################
        # Porto Alegre
        PortoAlegre_plot.swot_collection.create_flood_mask(
            variable=variable,
            data_area="global",
            data_type="swot",
            thresholds=PA_thresholds,
            time_selection="2024-05-06",
            urban_diff=PA_urban_diff,
            add_uncertainty=True,
            threshold_gamma=0.5,
            threshold_SNR=0.5,
            )
        PortoAlegre_plot.plot_map_mask(
            variable=variable, 
            data_area="global", #global or flood or control
            data_type="swot", #swot
            time_selection="2024-05-06",
            title="[b]",
            comparing_raster_Path=PortoAlegre_plot.project.AUX_PATH.joinpath("FloodMask_nrow4248_ncol8052.tif"),
            add_scores=False,
            add_bkg=False,
            add_legend=False,
            ax=(2,2,2),
            fig=fig
            )

        ####################
        # Ohio
        Ohio_plot.swot_collection.create_flood_mask(
            variable=variable,
            data_area="global",
            data_type="swot",
            thresholds=Ohio_thresholds,
            time_selection="2025-02-20",
            add_uncertainty=True,
            threshold_gamma=0.5,
            threshold_SNR=0.5,
            )
            
        Ohio_plot.plot_map_mask(
            variable=variable,
            data_area="global",
            data_type="swot",
            time_selection="2025-02-20",
            comparing_raster_Path=Ohio_plot.project.AUX_PATH.joinpath("FM_20250222T000000_S1_POST_fusion_cut_32616_nrow3646_ncol6003.tif"),
            title="[c]",
            add_scores=False,
            add_bkg=False,
            add_legend=False,
            ax=(2,2,3),
            fig=fig
            )

        ####################
        # Greece
        EMSR692_plot.swot_collection.create_flood_mask(
            variable=variable,
            data_area="global",
            data_type="swot",
            thresholds=Greece_thresholds,
            time_selection="2023-09-15",
            add_uncertainty=True,
            urban_diff=Greece_urban_diff,
            threshold_gamma=0.5,
            threshold_SNR=0.5,
            )
            
        fig, ax = EMSR692_plot.plot_map_mask(
            variable=variable,
            data_area="global",
            data_type="swot",
            time_selection="2023-09-15",
            title="[d]",
            comparing_raster_Path=EMSR692_plot.project.AUX_PATH.joinpath("FM_34SEJ_20230915_CUT_nrow5720_ncol5917.tif"),
            add_scores=False,
            add_bkg=False,
            add_legend=False,
            ax=(2,2,4),
            fig=fig
            )
        ax[0].add_patch(
            mpatches.Rectangle(
                xy=(0.28, 47.1),  # lower left corner
                width=0.03,  # width of rectangle
                height=0.05,  # height of rectangle
                linewidth=2,
                linestyle='--',
                edgecolor="red",
                fill=False,
                transform=cartopy.crs.PlateCarree()._as_mpl_transform(ax[0]),
            )
        )
        ax[0].text(
            s="A",
            x=0.284, 
            y=47.1,
            transform=cartopy.crs.PlateCarree()._as_mpl_transform(ax[0]),
            fontsize=25,
            color="red",
            ha='center',
            va='center',
            **{'path_effects': [patheffects.withStroke(linewidth=3, foreground='w')]}
        )
            
        # plot in porto alegre [-51.2, -51.1, -29.8, -29.7] and [-51.25, -51.1, -30, -29.85] rectangle
        ax[1].text(
            s="Zoom [a]",
            x=-51.19, 
            y=-29.8,
            fontsize=25,
            color="red",
            transform=cartopy.crs.PlateCarree()._as_mpl_transform(ax[1]),
            **{'path_effects': [patheffects.withStroke(linewidth=3, foreground='w')]}
        )
        ax[1].add_patch(
            mpatches.Rectangle(
                xy=(-51.2, -29.8),  # lower left corner
                width=0.1,  # width of rectangle
                height=0.1,  # height of rectangle
                linewidth=2,
                color="red",
                linestyle='--',
                edgecolor="red",
                fill=False,
                transform=cartopy.crs.PlateCarree()._as_mpl_transform(ax[1]),
            )
        )
        ax[1].text(
            s="Zoom [b]",
            x=-51.24, 
            y=-30,
            fontsize=25,
            color="red",
            transform=cartopy.crs.PlateCarree()._as_mpl_transform(ax[1]),
            **{'path_effects': [patheffects.withStroke(linewidth=3, foreground='w')]}
        )
        
        ax[1].add_patch(
            mpatches.Rectangle(
                xy=(-51.25, -30),  # lower left corner
                width=0.15,  # width of rectangle
                height=0.15,  # height of rectangle
                linewidth=2,
                color="red",
                linestyle='--',
                edgecolor="red",
                fill=False,
                transform=cartopy.crs.PlateCarree()._as_mpl_transform(ax[1]),
            )
        )

        # Plot wet-snow rectangle in Ohio
        ax[2].text(
                s="B",
                x=-87.015, 
                y=37.97,
                transform=cartopy.crs.PlateCarree()._as_mpl_transform(ax[2]),
                fontsize=25,
                color="purple",
                ha='center',
                va='center',
                **{'path_effects': [patheffects.withStroke(linewidth=3, foreground='w')]}
            )
        ax[2].add_patch(
            mpatches.Rectangle(
                xy=(-87.01, 37.97),  # lower left corner
                width=0.055,  # width of rectangle
                height=0.08,  # height of rectangle
                linewidth=2,
                linestyle='--',
                edgecolor="purple",
                fill=False,
                transform=cartopy.crs.PlateCarree()._as_mpl_transform(ax[2]),
            )
        )

        ax[2].text(
                s="B'",
                x=-86.915, 
                y=37.82,
                transform=cartopy.crs.PlateCarree()._as_mpl_transform(ax[2]),
                fontsize=25,
                color="purple",
                ha='center',
                va='center',
                **{'path_effects': [patheffects.withStroke(linewidth=3, foreground='w')]}
            )
        ax[2].add_patch(
            mpatches.Rectangle(
                xy=(-86.92, 37.82),  # lower left corner
                width=0.1,  # width of rectangle
                height=0.06,  # height of rectangle
                linewidth=2,
                linestyle='--',
                edgecolor="purple",
                fill=False,
                transform=cartopy.crs.PlateCarree()._as_mpl_transform(ax[2]),
            )
        )
        
        # plot in greece [21.94, 22.15, 39.47, 39.59] rectangle
        ax[-1].text(
            s="Zoom [c]",
            x=21.95, 
            y=39.47,
            color="red",
            fontsize=25,
            transform=cartopy.crs.PlateCarree()._as_mpl_transform(ax[-1]),
            **{'path_effects': [patheffects.withStroke(linewidth=3, foreground='w')]}
        )
        ax[-1].add_patch(
            mpatches.Rectangle(
                xy=(21.94, 39.47),  # lower left corner
                width=0.21,  # width of rectangle
                height=0.12,  # height of rectangle
                linewidth=2,
                color="red",
                linestyle='--',
                edgecolor="red",
                fill=False,
                transform=cartopy.crs.PlateCarree()._as_mpl_transform(ax[-1]),
            )
        )
        # Add arrow for Nadir direction
        # Chinon : East > West
        # Porto Alegre : West > East
        # Ohio : East > West
        # Greece : West > East
        add_arrow_range(ax[0],  "Chinon")
        add_arrow_range(ax[1],  "PortoAlegre")
        add_arrow_range(ax[2],  "Ohio")
        add_arrow_range(ax[3], "Greece")
        
        # cmap, color_labels = EMSR692_plot.get_floodmask_colormap(True)
        # l1 = mpatches.Patch(color=cmap(1), label=color_labels[1])
        # l2 = mpatches.Patch(color=cmap(2), label=color_labels[2])
        # l3 = mpatches.Patch(color=cmap(3), label=color_labels[3])
        # l11 = mpatches.Patch(color=cmap(11), label=color_labels[11])
        # l12 = mpatches.Patch(color=cmap(12), label=color_labels[12])
        # l13 = mpatches.Patch(color=cmap(13), label=color_labels[13])
        # l21 = mpatches.Patch(color=cmap(21), label=color_labels[21])
        # l22 = mpatches.Patch(color=cmap(22), label=color_labels[22])
        # l23 = mpatches.Patch(color=cmap(23), label=color_labels[23])
        # ax[-2].legend(handles=[l1, l2, l3, l11, l12, l13, l21, l22, l23],loc="lower left", fontsize=18, ncols=3, bbox_to_anchor=(0.,-0.25), handlelength=1, handleheight=1)

        # Save figure
        fig.savefig(
            f"/data/scratch/globc/bonassies/workspace/swot_for_flood/examples/Paper_SWOT/Figs/mask_{variable}_maps_compile.pdf",
            dpi=300,
        )
        fig.savefig(
            f"/data/scratch/globc/bonassies/workspace/swot_for_flood/examples/Paper_SWOT/Figs/mask_{variable}_maps_compile.png",
            dpi=300,
        )
        
        plt.close("all")
        print("Elapsed time: ", round(time() - start, 2), "s for mask maps", flush=True)
    ############################################################################################################################
    #### ZOOM MAPS MASKS
    ############################################################################################################################
    if ZOOM_MASK:
        start = time()
        print("Plotting zoom maps masks", flush=True)
        fig, ax = plt.subplots(1, 3, figsize=(30,10))
        fig.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05, hspace=0.1, wspace=0.1)

        ax[0].remove()
        ax[1].remove()
        ax[2].remove()

        ####################
        # Porto Alegre - Zoom 1
        PortoAlegre_plot.swot_collection.create_flood_mask(
            variable=variable,
            data_area="global",
            data_type="swot",
            thresholds=PA_thresholds,
            time_selection="2024-05-06",
            urban_diff=PA_urban_diff,
            add_uncertainty=True,
            threshold_gamma=0.5,
            threshold_SNR=0.5,
            )
        PortoAlegre_plot.plot_map_mask(
            variable=variable, 
            data_area="global", #global or flood or control
            data_type="swot", #swot
            time_selection="2024-05-06",
            title="Zoom [a]",
            comparing_raster_Path=PortoAlegre_plot.project.AUX_PATH.joinpath("FloodMask_nrow4248_ncol8052.tif"),
            add_scores=False,
            add_bkg=False,
            add_legend=False,
            ax=(1,3,1),
            fig=fig,
            extents=[-51.2, -51.1, -29.8, -29.7] # North Porto Alegre
            )

        # Porto Alegre - Zoom 2
        PortoAlegre_plot.plot_map_mask(
            variable=variable, 
            data_area="global", #global or flood or control
            data_type="swot", #swot
            time_selection="2024-05-06",
            title="Zoom [b]",
            comparing_raster_Path=PortoAlegre_plot.project.AUX_PATH.joinpath("FloodMask_nrow4248_ncol8052.tif"),
            add_scores=False,
            add_bkg=False,
            add_legend=False,
            ax=(1,3,2),
            fig=fig,
            extents=[-51.25, -51.1, -30, -29.85] # South Porto Alegre
            )
        
        ####################
        # Greece - Zoom 1
        EMSR692_plot.swot_collection.create_flood_mask(
            variable=variable,
            data_area="global",
            data_type="swot",
            thresholds=Greece_thresholds,
            time_selection="2023-09-15",
            add_uncertainty=True,
            urban_diff=Greece_urban_diff,
            threshold_gamma=0.5,
            threshold_SNR=0.5
            )
            
        fig, ax = EMSR692_plot.plot_map_mask(
            variable=variable,
            data_area="global",
            data_type="swot",
            time_selection="2023-09-15",
            title="Zoom [c]",
            comparing_raster_Path=EMSR692_plot.project.AUX_PATH.joinpath("FM_34SEJ_20230915_CUT_nrow5720_ncol5917.tif"),
            add_scores=False,
            add_bkg=False,
            add_legend=False,
            ax=(1,3,3),
            fig=fig,
            extents=[21.94, 22.15, 39.47, 39.59] # Zoom on Metamorfosis village and neighbourhood
            )

        cmap, color_labels = EMSR692_plot.get_floodmask_colormap(True)
        l1 = mpatches.Patch(color=cmap(1), label=color_labels[1])
        l2 = mpatches.Patch(color=cmap(2), label=color_labels[2])
        l3 = mpatches.Patch(color=cmap(3), label=color_labels[3])
        l11 = mpatches.Patch(color=cmap(11), label=color_labels[11])
        l12 = mpatches.Patch(color=cmap(12), label=color_labels[12])
        l13 = mpatches.Patch(color=cmap(13), label=color_labels[13])
        l21 = mpatches.Patch(color=cmap(21), label=color_labels[21])
        l22 = mpatches.Patch(color=cmap(22), label=color_labels[22])
        l23 = mpatches.Patch(color=cmap(23), label=color_labels[23])
        ax[-1].legend(handles=[l1, l2, l3, l11, l12, l13, l21, l22, l23],loc="lower left", fontsize=20, ncols=3, bbox_to_anchor=(-0.1,-0.25), handlelength=1, handleheight=1)

        # Save figure
        fig.savefig(
            f"/data/scratch/globc/bonassies/workspace/swot_for_flood/examples/Paper_SWOT/Figs/mask_maps_{variable}_compile_zoom.pdf",
            dpi=300,
        )

        fig.savefig(
            f"/data/scratch/globc/bonassies/workspace/swot_for_flood/examples/Paper_SWOT/Figs/mask_maps_{variable}_compile_zoom.png",
            dpi=300,
        )
        plt.close("all")
        print("Elapsed time: ", round(time() - start, 2), "s for mask maps zoom", flush=True)
    ############################################################################################################################
    #### COMPARE MASKS MAP WITH ZOOM
    ############################################################################################################################
    if COMPARE_MASKS:
        ###################
        # Chinon
        Chinon_plot.swot_collection.create_flood_mask(
            variable=variable,
            data_area="global",
            data_type="swot",
            thresholds=Chinon_thresholds,
            time_selection="2024-03-31",
            add_uncertainty=True,
            threshold_gamma=0.5,
            threshold_SNR=0.5
            )

        ####################
        # Porto Alegre
        PortoAlegre_plot.swot_collection.create_flood_mask(
            variable=variable,
            data_area="global",
            data_type="swot",
            thresholds=PA_thresholds,
            time_selection="2024-05-06",
            urban_diff=PA_urban_diff,
            threshold_gamma=0.5,
            threshold_SNR=0.5,
            add_uncertainty=True,
            )

        ####################
        # Ohio
        Ohio_plot.swot_collection.create_flood_mask(
            variable=variable,
            data_area="global",
            data_type="swot",
            thresholds=Ohio_thresholds,
            time_selection="2025-02-20",
            add_uncertainty=True,
            threshold_gamma=0.5,
            threshold_SNR=0.5
            )

        
        ####################
        # Greece
        EMSR692_plot.swot_collection.create_flood_mask(
            variable=variable,
            data_area="global",
            data_type="swot",
            thresholds=Greece_thresholds,
            time_selection="2023-09-15",
            add_uncertainty=True,
            urban_diff=Greece_urban_diff,
            threshold_gamma=0.5,
            threshold_SNR=0.5
            )
        
        print("Plotting water masks comparison with FloodML", flush=True)
        start = time()
        fig, ax = plt.subplots(2, 2, figsize=(25,20))
        fig.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05, hspace=0.1, wspace=0.1)

        ax[0,0].remove()
        ax[0,1].remove()
        ax[1,0].remove()
        ax[1,1].remove()
        
        ####################
        # Chinon
        Chinon_plot.plot_map_compare_masks(
            variable=variable,
            data_area="global",
            data_type="swot",
            time_selection="2024-03-31",
            title="[a]",
            comparing_raster_Path=Chinon_plot.project.AUX_PATH.joinpath("FM_30TYT_20240331T174856_S1_132_POST_nrow1496_ncol2635.tif"),
            add_bkg=False,
            add_legend=False,
            ax=(2,2,1),
            fig=fig
            )

        ####################
        # Porto Alegre
        PortoAlegre_plot.plot_map_compare_masks(
            variable=variable,
            data_area="global", #global or flood or control
            data_type="swot", #swot
            time_selection="2024-05-06",
            title="[b]",
            comparing_raster_Path=PortoAlegre_plot.project.AUX_PATH.joinpath("FLoodML_20240506T133149_cut_32722_nrow4248_ncol8052.tif"),
            add_bkg=False,
            add_legend=False,
            ax=(2,2,2),
            fig=fig
            )

        ####################
        # Ohio
        Ohio_plot.plot_map_compare_masks(
            variable=variable,
            data_area="global",
            data_type="swot",
            time_selection="2025-02-20",
            comparing_raster_Path=Ohio_plot.project.AUX_PATH.joinpath("FM_20250222T000000_S1_POST_fusion_cut_32616_nrow3646_ncol6003.tif"),
            title="[c]",
            add_bkg=False,
            add_legend=False,
            ax=(2,2,3),
            fig=fig
            )

        ####################
        # Greece
        fig, ax = EMSR692_plot.plot_map_compare_masks(
            variable=variable,
            data_area="global",
            data_type="swot",
            time_selection="2023-09-15",
            title="[d]",
            comparing_raster_Path=EMSR692_plot.project.AUX_PATH.joinpath("FM_34SEJ_20230915_CUT_nrow5720_ncol5917.tif"),
            add_bkg=False,
            add_legend=True,
            ax=(2,2,4),
            fig=fig
            )

        ax[0].add_patch(
            mpatches.Rectangle(
                xy=(0.28, 47.1),  # lower left corner
                width=0.03,  # width of rectangle
                height=0.05,  # height of rectangle
                linewidth=2,
                linestyle='--',
                edgecolor="red",
                fill=False,
                transform=cartopy.crs.PlateCarree()._as_mpl_transform(ax[0]),
            )
        )
        ax[0].text(
            s="A",
            x=0.284, 
            y=47.1,
            transform=cartopy.crs.PlateCarree()._as_mpl_transform(ax[0]),
            fontsize=25,
            color="red",
            ha='center',
            va='center',
            **{'path_effects': [patheffects.withStroke(linewidth=3, foreground='w')]}
        )
            
        # plot in porto alegre [-51.2, -51.1, -29.8, -29.7] and [-51.25, -51.1, -30, -29.85] rectangle
        ax[1].text(
            s="Zoom [a]",
            x=-51.19, 
            y=-29.8,
            fontsize=25,
            color="red",
            transform=cartopy.crs.PlateCarree()._as_mpl_transform(ax[1]),
            **{'path_effects': [patheffects.withStroke(linewidth=3, foreground='w')]}
        )
        ax[1].add_patch(
            mpatches.Rectangle(
                xy=(-51.2, -29.8),  # lower left corner
                width=0.1,  # width of rectangle
                height=0.1,  # height of rectangle
                linewidth=2,
                color="red",
                linestyle='--',
                edgecolor="red",
                fill=False,
                transform=cartopy.crs.PlateCarree()._as_mpl_transform(ax[1]),
            )
        )
        ax[1].text(
            s="Zoom [b]",
            x=-51.24, 
            y=-30,
            fontsize=25,
            color="red",
            transform=cartopy.crs.PlateCarree()._as_mpl_transform(ax[1]),
            **{'path_effects': [patheffects.withStroke(linewidth=3, foreground='w')]}
        )
        
        ax[1].add_patch(
            mpatches.Rectangle(
                xy=(-51.25, -30),  # lower left corner
                width=0.15,  # width of rectangle
                height=0.15,  # height of rectangle
                linewidth=2,
                color="red",
                linestyle='--',
                edgecolor="red",
                fill=False,
                transform=cartopy.crs.PlateCarree()._as_mpl_transform(ax[1]),
            )
        )

        # Plot wet-snow rectangle in Ohio
        ax[2].text(
                s="B",
                x=-87.015, 
                y=37.97,
                transform=cartopy.crs.PlateCarree()._as_mpl_transform(ax[2]),
                fontsize=25,
                color="purple",
                ha='center',
                va='center',
                **{'path_effects': [patheffects.withStroke(linewidth=3, foreground='w')]}
            )
        ax[2].add_patch(
            mpatches.Rectangle(
                xy=(-87.01, 37.97),  # lower left corner
                width=0.055,  # width of rectangle
                height=0.08,  # height of rectangle
                linewidth=2,
                linestyle='--',
                edgecolor="purple",
                fill=False,
                transform=cartopy.crs.PlateCarree()._as_mpl_transform(ax[2]),
            )
        )

        ax[2].text(
                s="B'",
                x=-86.915, 
                y=37.82,
                transform=cartopy.crs.PlateCarree()._as_mpl_transform(ax[2]),
                fontsize=25,
                color="purple",
                ha='center',
                va='center',
                **{'path_effects': [patheffects.withStroke(linewidth=3, foreground='w')]}
            )
        ax[2].add_patch(
            mpatches.Rectangle(
                xy=(-86.92, 37.82),  # lower left corner
                width=0.1,  # width of rectangle
                height=0.06,  # height of rectangle
                linewidth=2,
                linestyle='--',
                edgecolor="purple",
                fill=False,
                transform=cartopy.crs.PlateCarree()._as_mpl_transform(ax[2]),
            )
        )
        # plot in greece [21.94, 22.15, 39.47, 39.59] rectangle
        ax[-1].text(
            s="Zoom [c]",
            x=21.95, 
            y=39.47,
            color="red",
            fontsize=25,
            transform=cartopy.crs.PlateCarree()._as_mpl_transform(ax[-1]),
            **{'path_effects': [patheffects.withStroke(linewidth=3, foreground='w')]}
        )
        ax[-1].add_patch(
            mpatches.Rectangle(
                xy=(21.94, 39.47),  # lower left corner
                width=0.21,  # width of rectangle
                height=0.12,  # height of rectangle
                linewidth=2,
                color="red",
                linestyle='--',
                edgecolor="red",
                fill=False,
                transform=cartopy.crs.PlateCarree()._as_mpl_transform(ax[-1]),
            )
        )
        # Add arrow for Nadir direction
        # Chinon : East > West
        # Porto Alegre : West > East
        # Ohio : East > West
        # Greece : West > East
        add_arrow_range(ax[0],  "Chinon")
        add_arrow_range(ax[1],  "PortoAlegre")
        add_arrow_range(ax[2],  "Ohio")
        add_arrow_range(ax[3], "Greece")
        
        # Save figure
        fig.savefig(
            f"/data/scratch/globc/bonassies/workspace/swot_for_flood/examples/Paper_SWOT/Figs/compared_mask_FloodML_maps_{variable}_compile.pdf",
            dpi=300,
        )
        fig.savefig(
            f"/data/scratch/globc/bonassies/workspace/swot_for_flood/examples/Paper_SWOT/Figs/compared_mask_FloodML_maps_{variable}_compile.png",
            dpi=300,
        )
        
        plt.close("all")
        print("Elapsed time: ", round(time() - start, 2), "s for compared mask maps", flush=True)
        
        
        print("Plotting zoom", flush=True)
        fig, ax = plt.subplots(1, 3, figsize=(30,10))
        fig.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05, hspace=0.1, wspace=0.1)

        ax[0].remove()
        ax[1].remove()
        ax[2].remove()

        ####################
        # Porto Alegre - Zoom 1
        PortoAlegre_plot.plot_map_compare_masks(
            variable=variable, 
            data_area="global", #global or flood or control
            data_type="swot", #swot
            time_selection="2024-05-06",
            title="Zoom [a]",
            comparing_raster_Path=PortoAlegre_plot.project.AUX_PATH.joinpath("FLoodML_20240506T133149_cut_32722_nrow4248_ncol8052.tif"),
            add_bkg=False,
            add_legend=False,
            ax=(1,3,1),
            fig=fig,
            extents=[-51.2, -51.1, -29.8, -29.7] # North Porto Alegre
            )

        # Porto Alegre - Zoom 2
        PortoAlegre_plot.plot_map_compare_masks(
            variable=variable, 
            data_area="global", #global or flood or control
            data_type="swot", #swot
            time_selection="2024-05-06",
            title="Zoom [b]",
            comparing_raster_Path=PortoAlegre_plot.project.AUX_PATH.joinpath("FLoodML_20240506T133149_cut_32722_nrow4248_ncol8052.tif"),
            add_bkg=False,
            add_legend=False,
            ax=(1,3,2),
            fig=fig,
            extents=[-51.25, -51.1, -30, -29.85] # South Porto Alegre
            )

        ####################
        # Greece - Zoom 1
        fig, ax = EMSR692_plot.plot_map_compare_masks(
            variable=variable,
            data_area="global",
            data_type="swot",
            time_selection="2023-09-15",
            title="Zoom [c]",
            comparing_raster_Path=EMSR692_plot.project.AUX_PATH.joinpath("FM_34SEJ_20230915_CUT_nrow5720_ncol5917.tif"),
            add_bkg=False,
            add_legend=True,
            ax=(1,3,3),
            fig=fig,
            extents=[21.94, 22.15, 39.47, 39.59] # Zoom on Metamorfosis village and neighbourhood
            )
        
        # Save figure
        fig.savefig(
            f"/data/scratch/globc/bonassies/workspace/swot_for_flood/examples/Paper_SWOT/Figs/compared_mask_FloodML_maps_{variable}_compile_zoom.pdf",
            dpi=300,
        )

        fig.savefig(
            f"/data/scratch/globc/bonassies/workspace/swot_for_flood/examples/Paper_SWOT/Figs/compared_mask_FloodML_maps_{variable}_compile_zoom.png",
            dpi=300,
        )
        plt.close("all")
        
        
        print("Plotting water masks comparison with Handmade floodmask", flush=True)
        start = time()
        fig, ax = plt.subplots(2, 2, figsize=(25,20))
        fig.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05, hspace=0.1, wspace=0.1)

        ax[0,0].remove()
        ax[0,1].remove()
        ax[1,0].remove()
        ax[1,1].remove()
        
        ####################
        # Chinon
        Chinon_plot.plot_map_compare_masks(
            variable=variable,
            data_area="global",
            data_type="swot",
            time_selection="2024-03-31",
            title="[a]",
            comparing_raster_Path=Chinon_plot.project.AUX_PATH.joinpath("FloodMask_nrow1496_ncol2635.tif"),
            add_bkg=False,
            add_legend=False,
            ax=(2,2,1),
            fig=fig
            )

        ####################
        # Porto Alegre
        PortoAlegre_plot.plot_map_compare_masks(
            variable=variable,
            data_area="global", #global or flood or control
            data_type="swot", #swot
            time_selection="2024-05-06",
            title="[b]",
            comparing_raster_Path=PortoAlegre_plot.project.AUX_PATH.joinpath("FloodMask_nrow4248_ncol8052.tif"),
            add_bkg=False,
            add_legend=False,
            ax=(2,2,2),
            fig=fig
            )

        ####################
        # Ohio
        Ohio_plot.plot_map_compare_masks(
            variable=variable,
            data_area="global",
            data_type="swot",
            time_selection="2025-02-20",
            comparing_raster_Path=Ohio_plot.project.AUX_PATH.joinpath("FloodMask_v2_nrow3646_ncol6003.tif"),
            title="[c]",
            add_bkg=False,
            add_legend=False,
            ax=(2,2,3),
            fig=fig
            )

        ####################
        # Greece
        fig, ax = EMSR692_plot.plot_map_compare_masks(
            variable=variable,
            data_area="global",
            data_type="swot",
            time_selection="2023-09-15",
            title="[d]",
            comparing_raster_Path=EMSR692_plot.project.AUX_PATH.joinpath("FloodMask_nrow5720_ncol5917.tif"),
            compared_legend="Handmade Flood extent",
            add_bkg=False,
            add_legend=True,
            ax=(2,2,4),
            fig=fig
            )

        ax[0].add_patch(
            mpatches.Rectangle(
                xy=(0.28, 47.1),  # lower left corner
                width=0.03,  # width of rectangle
                height=0.05,  # height of rectangle
                linewidth=2,
                linestyle='--',
                edgecolor="red",
                fill=False,
                transform=cartopy.crs.PlateCarree()._as_mpl_transform(ax[0]),
            )
        )
        ax[0].text(
            s="A",
            x=0.284, 
            y=47.1,
            transform=cartopy.crs.PlateCarree()._as_mpl_transform(ax[0]),
            fontsize=25,
            color="red",
            ha='center',
            va='center',
            **{'path_effects': [patheffects.withStroke(linewidth=3, foreground='w')]}
        )
            
        # plot in porto alegre [-51.2, -51.1, -29.8, -29.7] and [-51.25, -51.1, -30, -29.85] rectangle
        ax[1].text(
            s="Zoom [a]",
            x=-51.19, 
            y=-29.8,
            fontsize=25,
            color="red",
            transform=cartopy.crs.PlateCarree()._as_mpl_transform(ax[1]),
            **{'path_effects': [patheffects.withStroke(linewidth=3, foreground='w')]}
        )
        ax[1].add_patch(
            mpatches.Rectangle(
                xy=(-51.2, -29.8),  # lower left corner
                width=0.1,  # width of rectangle
                height=0.1,  # height of rectangle
                linewidth=2,
                color="red",
                linestyle='--',
                edgecolor="red",
                fill=False,
                transform=cartopy.crs.PlateCarree()._as_mpl_transform(ax[1]),
            )
        )
        ax[1].text(
            s="Zoom [b]",
            x=-51.24, 
            y=-30,
            fontsize=25,
            color="red",
            transform=cartopy.crs.PlateCarree()._as_mpl_transform(ax[1]),
            **{'path_effects': [patheffects.withStroke(linewidth=3, foreground='w')]}
        )
        
        ax[1].add_patch(
            mpatches.Rectangle(
                xy=(-51.25, -30),  # lower left corner
                width=0.15,  # width of rectangle
                height=0.15,  # height of rectangle
                linewidth=2,
                color="red",
                linestyle='--',
                edgecolor="red",
                fill=False,
                transform=cartopy.crs.PlateCarree()._as_mpl_transform(ax[1]),
            )
        )

        # Plot wet-snow rectangle in Ohio
        ax[2].text(
                s="B",
                x=-87.015, 
                y=37.97,
                transform=cartopy.crs.PlateCarree()._as_mpl_transform(ax[2]),
                fontsize=25,
                color="purple",
                ha='center',
                va='center',
                **{'path_effects': [patheffects.withStroke(linewidth=3, foreground='w')]}
            )
        ax[2].add_patch(
            mpatches.Rectangle(
                xy=(-87.01, 37.97),  # lower left corner
                width=0.055,  # width of rectangle
                height=0.08,  # height of rectangle
                linewidth=2,
                linestyle='--',
                edgecolor="purple",
                fill=False,
                transform=cartopy.crs.PlateCarree()._as_mpl_transform(ax[2]),
            )
        )

        ax[2].text(
                s="B'",
                x=-86.915, 
                y=37.82,
                transform=cartopy.crs.PlateCarree()._as_mpl_transform(ax[2]),
                fontsize=25,
                color="purple",
                ha='center',
                va='center',
                **{'path_effects': [patheffects.withStroke(linewidth=3, foreground='w')]}
            )
        ax[2].add_patch(
            mpatches.Rectangle(
                xy=(-86.92, 37.82),  # lower left corner
                width=0.1,  # width of rectangle
                height=0.06,  # height of rectangle
                linewidth=2,
                linestyle='--',
                edgecolor="purple",
                fill=False,
                transform=cartopy.crs.PlateCarree()._as_mpl_transform(ax[2]),
            )
        )
    
        # plot in greece [21.94, 22.15, 39.47, 39.59] rectangle
        ax[-1].text(
            s="Zoom [c]",
            x=21.95, 
            y=39.47,
            color="red",
            fontsize=25,
            transform=cartopy.crs.PlateCarree()._as_mpl_transform(ax[-1]),
            **{'path_effects': [patheffects.withStroke(linewidth=3, foreground='w')]}
        )
        ax[-1].add_patch(
            mpatches.Rectangle(
                xy=(21.94, 39.47),  # lower left corner
                width=0.21,  # width of rectangle
                height=0.12,  # height of rectangle
                linewidth=2,
                color="red",
                linestyle='--',
                edgecolor="red",
                fill=False,
                transform=cartopy.crs.PlateCarree()._as_mpl_transform(ax[-1]),
            )
        )
        # Add arrow for Nadir direction
        # Chinon : East > West
        # Porto Alegre : West > East
        # Ohio : East > West
        # Greece : West > East
        add_arrow_range(ax[0],  "Chinon")
        add_arrow_range(ax[1],  "PortoAlegre")
        add_arrow_range(ax[2],  "Ohio")
        add_arrow_range(ax[3], "Greece")
        
        # Save figure
        fig.savefig(
            f"/data/scratch/globc/bonassies/workspace/swot_for_flood/examples/Paper_SWOT/Figs/compared_mask_handmade_maps_{variable}_compile.pdf",
            dpi=300,
        )
        fig.savefig(
            f"/data/scratch/globc/bonassies/workspace/swot_for_flood/examples/Paper_SWOT/Figs/compared_mask_handmade_maps_{variable}_compile.png",
            dpi=300,
        )
        
        plt.close("all")
        print("Elapsed time: ", round(time() - start, 2), "s for compared mask maps", flush=True)
        
        
        print("Plotting zoom", flush=True)
        fig, ax = plt.subplots(1, 3, figsize=(30,10))
        fig.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05, hspace=0.1, wspace=0.1)

        ax[0].remove()
        ax[1].remove()
        ax[2].remove()

        ####################
        # Porto Alegre - Zoom 1
        PortoAlegre_plot.plot_map_compare_masks(
            variable=variable, 
            data_area="global", #global or flood or control
            data_type="swot", #swot
            time_selection="2024-05-06",
            title="Zoom [a]",
            comparing_raster_Path=PortoAlegre_plot.project.AUX_PATH.joinpath("FloodMask_nrow4248_ncol8052.tif"),
            add_bkg=False,
            add_legend=False,
            ax=(1,3,1),
            fig=fig,
            extents=[-51.2, -51.1, -29.8, -29.7] # North Porto Alegre
            )

        # Porto Alegre - Zoom 2
        PortoAlegre_plot.plot_map_compare_masks(
            variable=variable, 
            data_area="global", #global or flood or control
            data_type="swot", #swot
            time_selection="2024-05-06",
            title="Zoom [b]",
            comparing_raster_Path=PortoAlegre_plot.project.AUX_PATH.joinpath("FloodMask_nrow4248_ncol8052.tif"),
            add_bkg=False,
            add_legend=False,
            ax=(1,3,2),
            fig=fig,
            extents=[-51.25, -51.1, -30, -29.85] # South Porto Alegre
            )

        ####################
        # Greece - Zoom 1
        fig, ax = EMSR692_plot.plot_map_compare_masks(
            variable=variable,
            data_area="global",
            data_type="swot",
            time_selection="2023-09-15",
            title="Zoom [c]",
            comparing_raster_Path=EMSR692_plot.project.AUX_PATH.joinpath("FloodMask_nrow5720_ncol5917.tif"),
            add_bkg=False,
            add_legend=True,
            compared_legend="Handmade Flood extent",
            ax=(1,3,3),
            fig=fig,
            extents=[21.94, 22.15, 39.47, 39.59] # Zoom on Metamorfosis village and neighbourhood
            )
        
        # Save figure
        fig.savefig(
            f"/data/scratch/globc/bonassies/workspace/swot_for_flood/examples/Paper_SWOT/Figs/compared_mask_handmade_maps_{variable}_compile_zoom.pdf",
            dpi=300,
        )

        fig.savefig(
            f"/data/scratch/globc/bonassies/workspace/swot_for_flood/examples/Paper_SWOT/Figs/compared_mask_handmade_maps_{variable}_compile_zoom.png",
            dpi=300,
        )
        plt.close("all")
        print("Elapsed time: ", round(time() - start, 2), "s for compared mask maps zoom", flush=True)
    ############################################################################################################################
    #### SAVE MASKS
    ############################################################################################################################
    if SAVE_MASKS:
        print("Saving masks", flush=True)
        ###################
        # Chinon
        Chinon_plot.swot_collection.create_flood_mask(
            variable=variable,
            data_area="global",
            data_type="swot",
            thresholds=Chinon_thresholds,
            time_selection="2024-03-31",
            add_uncertainty=True,
            threshold_gamma=0.5,
            threshold_SNR=0.5
            )

        ####################
        # Porto Alegre
        PortoAlegre_plot.swot_collection.create_flood_mask(
            variable=variable,
            data_area="global",
            data_type="swot",
            thresholds=PA_thresholds,
            time_selection="2024-05-06",
            urban_diff=PA_urban_diff,
            threshold_gamma=0.5,
            threshold_SNR=0.5,
            add_uncertainty=True,
            )

        ####################
        # Ohio
        Ohio_plot.swot_collection.create_flood_mask(
            variable=variable,
            data_area="global",
            data_type="swot",
            thresholds=Ohio_thresholds,
            time_selection="2025-02-20",
            add_uncertainty=True,
            threshold_gamma=0.5,
            threshold_SNR=0.5
            )

        
        ####################
        # Greece
        EMSR692_plot.swot_collection.create_flood_mask(
            variable=variable,
            data_area="global",
            data_type="swot",
            thresholds=Greece_thresholds,
            time_selection="2023-09-15",
            add_uncertainty=True,
            urban_diff=Greece_urban_diff,
            threshold_gamma=0.5,
            threshold_SNR=0.5
            )
        
        Ohio_plot.swot_collection.save_tiff(
            variable=variable,
            is_mask=True,
            make_binary=False,
            remove_lowcoh=False,
            data_area="global",
            data_type="swot",
            path=Ohio_plot.project.TIFF_PATH.joinpath('output', f'watermask_{variable}_20250220_epsg{Ohio_plot.project.CRS}.tif'),
            time_selection="2025-02-20",
        )

        EMSR692_plot.swot_collection.save_tiff(
            variable=variable,
            is_mask=True,
            make_binary=False,
            remove_lowcoh=False,
            data_area="global",
            data_type="swot",
            path=EMSR692_plot.project.TIFF_PATH.joinpath('output', f'watermask_{variable}_20230915_epsg{EMSR692_plot.project.CRS}.tif'),
            time_selection="2023-09-15",
        )

        PortoAlegre_plot.swot_collection.save_tiff(
            variable=variable,
            is_mask=True,
            make_binary=False,
            remove_lowcoh=False,
            data_area="global",
            data_type="swot",
            path=PortoAlegre_plot.project.TIFF_PATH.joinpath('output', f'watermask_{variable}_20240506_epsg{PortoAlegre_plot.project.CRS}.tif'),
            time_selection="2024-05-06",
        )

        Chinon_plot.swot_collection.save_tiff(
            variable=variable,
            is_mask=True,
            make_binary=False,
            remove_lowcoh=False,
            data_area="global",
            data_type="swot",
            path=Chinon_plot.project.TIFF_PATH.joinpath('output', f'watermask_{variable}_20240331_epsg{Chinon_plot.project.CRS}.tif'),
            time_selection="2024-03-31",
        )
    #########################################################################################################################
    print("Done.")
    print("Total elapsed time: ", round(time() - start000, 2), "s", flush=True)
    
if __name__ == "__main__":
    # Define projects
    Ohio_config = configparser.ConfigParser()
    Ohio_path = "/data/scratch/globc/bonassies/workspace/swot_for_flood/examples/Ohio"
    Ohio_config.read(Ohio_path + '/config.cfg')
    Ohio_project = SwotProject(Ohio_config)
    Ohio_project.find_raster()

    Chinon_config = configparser.ConfigParser()
    Chinon_path = "/data/scratch/globc/bonassies/workspace/swot_for_flood/examples/Chinon"
    Chinon_config.read(Chinon_path + '/config.cfg')
    Chinon_project = SwotProject(Chinon_config)
    Chinon_project.find_raster()

    EMSR692_config = configparser.ConfigParser()
    EMSR692_path = "/data/scratch/globc/bonassies/workspace/swot_for_flood/examples/EMSR_692"
    EMSR692_config.read(EMSR692_path + '/config.cfg')
    EMSR692_project = SwotProject(EMSR692_config)
    EMSR692_project.find_raster()

    PortoAlegre_config = configparser.ConfigParser()
    PortoAlegre_path = "/data/scratch/globc/bonassies/workspace/swot_for_flood/examples/PortoAlegre"
    PortoAlegre_config.read(PortoAlegre_path + '/config.cfg')
    PortoAlegre_project = SwotProject(PortoAlegre_config)
    PortoAlegre_project.find_raster()
    
    # Open raster files
    start0 = time()
    print(">>> Opening Porto Alegre raster files")
    PortoAlegre_project.create_collection()
    print(f"Elapsed time: {round(time() - start0, 2)} s", flush=True)

    start = time()
    print(">>> Opening Ohio raster files")
    Ohio_project.create_collection()
    print(f"Elapsed time: {round(time() - start, 2)} s", flush=True)

    start = time()
    print(">>> Opening Chinon raster files")
    Chinon_project.create_collection()
    print(f"Elapsed time: {round(time() - start, 2)} s", flush=True)

    start = time()
    print(">>> Opening EMSR 692 raster files")
    EMSR692_project.create_collection()
    print(f"Elapsed time: {round(time() - start, 2)} s", flush=True)
    print(f"Total Elapsed time: {round(time() - start0, 2)} s", flush=True)
    
    # Define Plot Object
    Ohio_plot : PlotRaster = PlotRaster(
        Ohio_project,
        save_fig=False,
        show_fig=False
        )

    PortoAlegre_plot : PlotRaster = PlotRaster(
        PortoAlegre_project,
        save_fig=False,
        show_fig=False
        )

    Chinon_plot : PlotRaster = PlotRaster(
        Chinon_project,
        save_fig=False,
        show_fig=False
        )

    EMSR692_plot : PlotRaster = PlotRaster(
        EMSR692_project,
        save_fig=False,
        show_fig=False
        )
    
    S1_S2 = False
    ESA_WC = False
    CLASSIF = False
    MEAN = True
    HISTO = False
    WATER_MASK = True
    ZOOM_MASK = False
    MAPS = True
    COMPARE_MASKS = True
    SAVE_MASKS = False
    
    COMBINE = True
    
    ##########################################################################
    # Coherence interferometric
    variable = "gamma_tot"
    main(variable, S1_S2, ESA_WC, CLASSIF, MEAN, HISTO, WATER_MASK, ZOOM_MASK, MAPS, COMPARE_MASKS, SAVE_MASKS, Chinon_plot, PortoAlegre_plot, Ohio_plot, EMSR692_plot)
    CLASSIF = False # Once is enough
    
    ##########################################################################
    # Sigma 0
    variable = "sig0"
    main(variable, S1_S2, ESA_WC, CLASSIF, MEAN, HISTO, WATER_MASK, ZOOM_MASK, MAPS, COMPARE_MASKS, SAVE_MASKS, Chinon_plot, PortoAlegre_plot, Ohio_plot, EMSR692_plot)
    
    ##########################################################################
    # Coherent power
    variable = "coherent_power"
    main(variable, S1_S2, ESA_WC, CLASSIF, MEAN, HISTO, WATER_MASK, ZOOM_MASK, MAPS, COMPARE_MASKS, SAVE_MASKS, Chinon_plot, PortoAlegre_plot, Ohio_plot, EMSR692_plot)
    
    
    ##########################################################################
    # ALL VARIABLES
    if COMBINE:
        if not WATER_MASK:
            print("Creating flood masks for each variable")
            for variable in ["sig0", "coherent_power", "gamma_tot"]:
                if variable == "sig0":
                    Ohio_thresholds={"urban":-0, "forest":5.5, "open":9.5}
                    PA_thresholds={"urban":-0, "forest":5, "open":10}
                    PA_urban_diff=False
                    Greece_thresholds={"urban":8, "forest":7, "open":9}
                    Greece_urban_diff=True
                    Chinon_thresholds={"urban":-0, "forest":10, "open":10}
                    
                elif variable == "coherent_power":
                    Ohio_thresholds={"urban":-0, "forest":62.5, "open":65}
                    PA_thresholds={"urban":-0, "forest":62, "open":70}
                    PA_urban_diff=False
                    Greece_thresholds={"urban":70, "forest":65, "open":65}
                    Greece_urban_diff=False
                    Chinon_thresholds={"urban":-0, "forest":64, "open":64}
                    
                elif variable == "gamma_tot":
                    Ohio_thresholds={"urban":-0, "forest":0.7, "open":0.85}
                    PA_thresholds={"urban":-0.1, "forest":0.65, "open":0.8} # swot with urban diff
                    PA_urban_diff=True
                    Greece_thresholds={"urban":0.9, "forest":0.85, "open":0.9}
                    Greece_urban_diff=False
                    Chinon_thresholds={"urban":-0, "forest":0.725, "open":0.725}
                    
                ###################
                # Chinon
                Chinon_plot.swot_collection.create_flood_mask(
                    variable=variable,
                    data_area="global",
                    data_type="swot",
                    thresholds=Chinon_thresholds,
                    time_selection="2024-03-31",
                    add_uncertainty=True,
                    threshold_gamma=0.5,
                    threshold_SNR=0.5
                    )

                ####################
                # Porto Alegre
                PortoAlegre_plot.swot_collection.create_flood_mask(
                    variable=variable,
                    data_area="global",
                    data_type="swot",
                    thresholds=PA_thresholds,
                    time_selection="2024-05-06",
                    add_uncertainty=True,
                    threshold_gamma=0.5,
                    threshold_SNR=0.5,
                    urban_diff=PA_urban_diff,
                    )

                ####################
                # Ohio
                Ohio_plot.swot_collection.create_flood_mask(
                    variable=variable,
                    data_area="global",
                    data_type="swot",
                    thresholds=Ohio_thresholds,
                    time_selection="2025-02-20",
                    add_uncertainty=True,
                    threshold_gamma=0.5,
                    threshold_SNR=0.5,
                    )

                ####################
                # Greece
                EMSR692_plot.swot_collection.create_flood_mask(
                    variable=variable,
                    data_area="global",
                    data_type="swot",
                    thresholds=Greece_thresholds,
                    time_selection="2023-09-15",
                    add_uncertainty=True,
                    threshold_gamma=0.5,
                    threshold_SNR=0.5,
                    urban_diff=Greece_urban_diff,
                    )
        plot_combine_mask(
            Chinon_plot,
            PortoAlegre_plot,
            Ohio_plot,
            EMSR692_plot,
        )