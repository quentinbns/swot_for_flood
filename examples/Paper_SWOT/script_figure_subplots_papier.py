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

from time import time

if __name__ == "__main__":
    print("Start", flush=True)
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
    
    
    ########################################################################################################################
    #### S1 and S2 plots
    ########################################################################################################################
    print("Plotting S1 and S2 images", flush=True)
    fig, ax = plt.subplots(2, 2, figsize=(12, 8), dpi=300,
                            subplot_kw={'projection': (cartopy.crs.PlateCarree())})
    ax[0, 0].remove()
    ax[0, 1].remove()
    ax[1, 0].remove()
    ax[1, 1].remove()

    path_aux_Ohio = Ohio_project.AUX_PATH.joinpath("FM_20250222T000000_S1_POST_fusion_cut_32616_nrow3646_ncol6003.tif")
    path_aux_Chinon = Chinon_project.AUX_PATH.joinpath("FM_30TYT_20240331T174856_S1_132_POST_nrow1493_ncol2633.tif")
    path_aux_PortAlegre = Path("/data/scratch/globc/bonassies/workspace/swot_for_flood/examples/Paper_SWOT/S2A/S2A_merged_32722_20240506T131349.tif")
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
    
    ########################################################################################################################
    #### ESA World Cover plots
    ########################################################################################################################
    print("Plotting ESA World Cover images", flush=True)
    fig, ax = plt.subplots(2, 2, figsize=(24, 16), dpi=300,
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

    fig.savefig(
        "/data/scratch/globc/bonassies/workspace/swot_for_flood/examples/Paper_SWOT/Figs/ESA_WC_compile.pdf",
        dpi=300,
    )
    fig.savefig(
        "/data/scratch/globc/bonassies/workspace/swot_for_flood/examples/Paper_SWOT/Figs/ESA_WC_compile.png",
        dpi=300,
    )
    plt.close("all")
    
    ########################################################################################################################
    #### SWOT CLASSIFICATION
    ########################################################################################################################
    print("Plotting SWOT classification images", flush=True)
    fig, ax = plt.subplots(2, 2, figsize=(24, 16), dpi=300,
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
    
    ########################################################################################################################
    #### MEAN PLOT
    ########################################################################################################################
    print("Plotting mean images", flush=True)
    fig, ax = plt.subplots(2, 2, figsize=(15,10))

    title_aux_Chinon =     "[a]" #   "FloodML mask from Sentinel-1 image (2024-03-31 17:48)"
    title_aux_PortAlegre = "[b]" #   "Sentinel-2A RGB image (2024-05-06 13:13)"
    title_aux_Ohio =       "[c]" #   "FloodML mask from Sentinel-1 image (2025-02-22 23:48)"
    title_aux_EMSR692 =    "[d]" #   "FloodML mask from Sentine-2A image (2023-09-15 09:20)"

    Chinon_plot.plot_mean_hist_computation(
        variable="gamma_tot",
        title=title_aux_Chinon,
        fig=fig,
        ax=ax[0,0],
    )
    PortoAlegre_plot.plot_mean_hist_computation(
        variable="gamma_tot",
        title=title_aux_PortAlegre,
        fig=fig,
        ax=ax[0,1],
    )
    Ohio_plot.plot_mean_hist_computation(
        variable="gamma_tot",
        title=title_aux_Ohio,
        fig=fig,
        ax=ax[1,0],
    )
    _, ax = EMSR692_plot.plot_mean_hist_computation(
        variable="gamma_tot",
        title=title_aux_EMSR692,
        fig=fig,
        ax=ax[1,1],
    )
    fig.tight_layout()
    fig.savefig(
        "/data/scratch/globc/bonassies/workspace/swot_for_flood/examples/Paper_SWOT/Figs/mean_computation_gamma_tot_compile.pdf",
        dpi=300,
    )
    fig.savefig(
        "/data/scratch/globc/bonassies/workspace/swot_for_flood/examples/Paper_SWOT/Figs/mean_computation_gamma_tot_compile.png",
        dpi=300,
    )
    plt.close("all")
    
    #########################################################################################################################
    #### HISTOGRAMS
    #########################################################################################################################
    print("Plotting histograms", flush=True)
    fig, ax = plt.subplots(4, 3, figsize=(15,10))

    ax[0,0].set_ylabel("Chinon, France", fontsize=12, fontweight='bold')
    ax[1,0].set_ylabel("Porto Alegre\nRio Grande do Sul\nEMSN 192", fontsize=12, fontweight='bold')
    ax[2,0].set_ylabel("Owensboro, USA\nOhio River", fontsize=12, fontweight='bold')
    ax[3,0].set_ylabel("Farkadona, Greece\nEMSR 692", fontsize=12, fontweight='bold')

    y_text = 0.95

    ####################
    # Chinon
    Chinon_plot.plot_histogram(
        variable="gamma_tot",
        data_area="flood",
        data_type="swot",
        world_cover_selection="open",
        time_selection='2024-03-31',
        use_seaborn=False,
        add_ylabel=False,
        add_xlabel=False,
        title="[a]",
        fig=fig,
        ax=ax[0,0],
        y_text=y_text
    )
    Chinon_plot.plot_histogram(
        variable="gamma_tot",
        data_area="flood",
        data_type="swot",
        world_cover_selection="forest",
        time_selection='2024-03-31',
        use_seaborn=False,
        title="[b]",
        add_ylabel=False,
        add_xlabel=False,
        fig=fig,
        ax=ax[0,1],
        y_text=y_text
    )
    ax[0,2].remove() # no urban in Chinon

    ####################
    # Porto Alegre
    PortoAlegre_plot.plot_histogram(
        variable="gamma_tot",
        data_area="flood",
        data_type="swot",
        world_cover_selection="open",
        time_selection='2024-05-06',
        use_seaborn=False,
        add_ylabel=False,
        add_xlabel=False,
        title="[c]",
        fig=fig,
        ax=ax[1,0],
        y_text=y_text
    )
    PortoAlegre_plot.plot_histogram(
        variable="gamma_tot",
        data_area="flood",
        data_type="swot",
        world_cover_selection="forest",
        time_selection='2024-05-06',
        use_seaborn=False,
        title="[d]",
        add_ylabel=False,
        add_xlabel=False,
        fig=fig,
        ax=ax[1,1],
        y_text=y_text
    )
    PortoAlegre_plot.plot_histogram(
        variable="gamma_tot",
        data_area="flood",
        data_type="swot",
        world_cover_selection="urban",
        time_selection='2024-05-06',
        use_seaborn=False,
        title="[e]",
        add_ylabel=False,
        add_xlabel=False,
        fig=fig,
        ax=ax[1,2],
        y_text=y_text,
        ha="right",
        va="top",
        ha_mean="left",
    )
    ####################
    # Ohio
    Ohio_plot.plot_histogram(
        variable="gamma_tot",
        data_area="flood",
        data_type="swot",
        world_cover_selection="open",
        time_selection='2025-02-20',
        use_seaborn=False,
        add_ylabel=False,
        add_xlabel=False,
        title="[f]",
        fig=fig,
        ax=ax[2,0],
        y_text=y_text
    )
    Ohio_plot.plot_histogram(
        variable="gamma_tot",
        data_area="flood",
        data_type="swot",
        world_cover_selection="forest",
        time_selection='2025-02-20',
        title="[g]",
        use_seaborn=False,
        add_ylabel=False,
        add_xlabel=False,
        fig=fig,
        ax=ax[2,1],
        y_text=y_text
    )
    ax[2,2].remove() # no urban in Ohio
    ####################
    # Greece
    EMSR692_plot.plot_histogram(
        variable="gamma_tot",
        data_area="flood",
        data_type="swot",
        world_cover_selection="open",
        time_selection='2023-09-15',
        use_seaborn=False,
        add_ylabel=False,
        add_xlabel=True,
        title="[h]",
        fig=fig,
        ax=ax[3,0],
        y_text=y_text
    )
    EMSR692_plot.plot_histogram(
        variable="gamma_tot",
        data_area="flood",
        data_type="swot",
        world_cover_selection="forest",
        time_selection='2023-09-15',
        title="[i]",
        use_seaborn=False,
        add_ylabel=False,
        add_xlabel=True,
        fig=fig,
        ax=ax[3,1],
        y_text=y_text
    )
    EMSR692_plot.plot_histogram(
        variable="gamma_tot",
        data_area="flood",
        data_type="swot",
        world_cover_selection="urban",
        time_selection='2023-09-15',
        title="[j]",
        use_seaborn=False,
        add_ylabel=False,
        add_xlabel=True,
        fig=fig,
        ax=ax[3,2],
        y_text=y_text
    )

    # Save figure
    fig.tight_layout()
    fig.savefig(
        "/data/scratch/globc/bonassies/workspace/swot_for_flood/examples/Paper_SWOT/Figs/histo_gamma_tot_compile.pdf",
        dpi=300,
    )
    fig.savefig(
        "/data/scratch/globc/bonassies/workspace/swot_for_flood/examples/Paper_SWOT/Figs/histo_gamma_tot_compile.png",
        dpi=300,
    )
    plt.close("all")
    
    #########################################################################################################################
    #### WATER MASK
    #########################################################################################################################
    print("Plotting water mask", flush=True)
    fig, ax = plt.subplots(2, 2, figsize=(25,20))
    fig.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05, hspace=0.1, wspace=0.1)

    ax[0,0].remove()
    ax[0,1].remove()
    ax[1,0].remove()
    ax[1,1].remove()


    ####################
    # Chinon
    Chinon_plot.plot_map_mask(
        variable="gamma_tot",
        data_area="global",
        data_type="swot",
        time_selection="2024-03-31",
        title="[a]",
        comparing_raster_Path=Chinon_plot.project.AUX_PATH.joinpath("FM_30TYT_20240331T174856_S1_132_POST_nrow1493_ncol2633.tif"),
        thresholds={"urban":-0, "forest":0.75, "open":0.75},
        add_classif_score=True,
        add_uncertainty=True,
        threshold_SNR=0.5,
        add_bkg=False,
        add_legend=False,
        disk_size=3,
        ax=(2,2,1),
        fig=fig
        )

    ####################
    # Porto Alegre
    PortoAlegre_plot.plot_map_mask(
        variable="gamma_tot", 
        data_area="global", #global or flood or control
        # data_type="diff", #diff or swot or mean (not working well for mean)
        data_type="swot", #swot
        time_selection="2024-05-06",
        title="[b]",
        # thresholds={"urban":-0.1, "forest":0.1, "open":0.1}, #diff
        # thresholds={"urban":-0., "forest":0.7, "open":0.8}, #swot
        thresholds={"urban":-0.1, "forest":0.65, "open":0.8}, # swot with urban diff
        urban_diff=True,
        add_classif_score=True,
        add_uncertainty=True,
        threshold_SNR=0.5,
        # threshold_gamma=-0.15, #diff
        threshold_gamma=0.5, #swot
        add_bkg=False,
        add_legend=False,
        disk_size=3,
        ax=(2,2,2),
        fig=fig
        )

    ####################
    # Ohio
    Ohio_plot.plot_map_mask(
        variable="gamma_tot",
        data_area="global",
        data_type="swot",
        time_selection="2025-02-20",
        comparing_raster_Path=Ohio_plot.project.AUX_PATH.joinpath("FM_20250222T000000_S1_POST_fusion_cut_32616_nrow3646_ncol6003.tif"),
        thresholds={"urban":-0, "forest":0.7, "open":0.85},
        title="[c]",
        add_classif_score=True,
        add_uncertainty=True,
        threshold_SNR=0.5,
        threshold_gamma=0.2,
        add_bkg=False,
        add_legend=False,
        disk_size=3,
        ax=(2,2,3),
        fig=fig
        )

    ####################
    # Greece
    fig, ax = EMSR692_plot.plot_map_mask(
        variable="gamma_tot",
        data_area="global",
        data_type="swot",
        time_selection="2023-09-15",
        title="[d]",
        comparing_raster_Path=EMSR692_plot.project.AUX_PATH.joinpath("FM_34SEJ_20230915_CUT_nrow5720_ncol5917.tif"),
        thresholds={"urban":0.9, "forest":0.85, "open":0.85},
        add_classif_score=True,
        add_uncertainty=True,
        threshold_SNR=0.5,
        add_bkg=False,
        add_legend=False,
        disk_size=3,
        ax=(2,2,4),
        fig=fig
        )


    cmap, color_labels = EMSR692_plot.get_floodmask_colormap(True)
    l1 = mpatches.Patch(color='red', label=color_labels[1])
    l2 = mpatches.Patch(color='forestgreen', label=color_labels[2])
    l3 = mpatches.Patch(color='cornflowerblue', label=color_labels[3])
    l11 = mpatches.Patch(color='rosybrown', label=color_labels[11])
    l12 = mpatches.Patch(color='yellowgreen', label=color_labels[12])
    l13 = mpatches.Patch(color='darkcyan', label=color_labels[13])
    l21 = mpatches.Patch(color='darkred', label=color_labels[21])
    l22 = mpatches.Patch(color='darkgreen', label=color_labels[22])
    l23 = mpatches.Patch(color='darkblue', label=color_labels[23])
    ax[-2].legend(handles=[l1, l2, l3, l11, l12, l13, l21, l22, l23],loc="lower left", fontsize=18, ncols=3, bbox_to_anchor=(0.,-0.15), handlelength=1, handleheight=1)

    # Save figure
    fig.savefig(
        "/data/scratch/globc/bonassies/workspace/swot_for_flood/examples/Paper_SWOT/Figs/mask_maps_compile.pdf",
        dpi=300,
    )
    fig.savefig(
        "/data/scratch/globc/bonassies/workspace/swot_for_flood/examples/Paper_SWOT/Figs/mask_maps_compile.png",
        dpi=300,
    )
    
    plt.close("all")
    
    #########################################################################################################################
    #### MAPS COHERENCE INTERFEROMETRIC
    #########################################################################################################################
    print("Plotting maps coherence interferometric", flush=True)
    fig, ax = plt.subplots(2 , 2, figsize=(25,20))

    ax[0,0].remove()
    ax[0,1].remove()
    ax[1,0].remove()
    ax[1,1].remove()

    ####################
    # Chinon
    Chinon_plot.plot_map(
        variable="gamma_tot",
        data_area="global",
        data_type="swot",
        world_cover_selection=None,
        time_selection="2024-03-31",
        cmap=Colormap("seaborn:mako").to_matplotlib(),
        vmin=0,
        vmax=1,
        add_bkg=False,
        title="[a]",
        ax=(2,2,1),
        fig=fig
        )

    ####################
    # Porto Alegre
    PortoAlegre_plot.plot_map(
        variable="gamma_tot",
        data_area="global",
        data_type="swot",
        world_cover_selection=None,
        time_selection="2024-05-06",
        cmap=Colormap("seaborn:mako").to_matplotlib(),
        vmin=0,
        vmax=1,
        add_bkg=False,
        title="[b]",
        ax=(2,2,2),
        fig=fig
    )

    ####################
    # Ohio
    Ohio_plot.plot_map(
        variable="gamma_tot",
        data_area="global",
        data_type="swot",
        world_cover_selection=None,
        time_selection="2025-02-20",
        cmap=Colormap("seaborn:mako").to_matplotlib(),
        vmin=0,
        vmax=1,
        add_bkg=False,
        title="[c]",
        ax=(2,2,3),
        fig=fig
    )

    ####################
    # Greece
    fig, ax = EMSR692_plot.plot_map(
        variable="gamma_tot",
        data_area="global",
        data_type="swot",
        world_cover_selection=None,
        time_selection="2023-09-15",
        cmap=Colormap("seaborn:mako").to_matplotlib(),
        vmin=0,
        vmax=1,
        add_bkg=False,
        title="[d]",
        ax=(2,2,4),
        fig=fig
    )


    # Save figure
    fig.savefig(
        "/data/scratch/globc/bonassies/workspace/swot_for_flood/examples/Paper_SWOT/Figs/maps_gamma_tot_compile.pdf",
        dpi=300,
    )
    fig.savefig(
        "/data/scratch/globc/bonassies/workspace/swot_for_flood/examples/Paper_SWOT/Figs/maps_gamma_tot_compile.png",
        dpi=300,
    )
    plt.close("all")
    
    #########################################################################################################################
    print("Done.")