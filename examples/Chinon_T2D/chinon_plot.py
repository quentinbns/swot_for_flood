import os
os.sys.path.append('/data/scratch/globc/bonassies/workspace/swot_for_flood')
import geopandas as gpd
import configparser
from pathlib import Path
from matplotlib import pyplot as plt
from cmap import Colormap

from core.swot_project import SwotProject
from core.plot_raster import PlotRaster


if __name__ == "__main__":
    main_path = "/data/scratch/globc/bonassies/workspace/swot_for_flood/examples/Chinon_T2D"

    config = configparser.ConfigParser()
    config.read(main_path + '/config.cfg')
    swot_project = SwotProject(config)
    swot_project.find_raster()
    swot_project.create_collection()
    
    plot_obj = PlotRaster(
        swot_project,
        save_fig=True,
        show_fig=False
        )
    

    for time in swot_project.list_flood_dates:
        print(f"Processing time: {time}", flush=True)
        exact_time = swot_project.swot_collection.get_variable("gamma_tot", "global", "swot", None).sel(time=time).time[0]
        str_time = exact_time.dt.strftime("%Y%m%dT%H%M%S").values
        
        for variable in ["sig0", "coherent_power", "gamma_tot"]:
            if variable == "sig0":
                vmin=-20.
                vmax=40.
                cmap="viridis"
                Chinon_thresholds={"urban":-0, "forest":10, "open":10}
                
            elif variable == "coherent_power":
                vmin=45.
                vmax=85.
                cmap="plasma"
                Chinon_thresholds={"urban":-0, "forest":64, "open":64}
                
            elif variable == "gamma_tot":
                vmin=0.
                vmax=1.
                cmap=Colormap("seaborn:mako").to_matplotlib()
                Chinon_thresholds={"urban":-0, "forest":0.715, "open":0.715}

            # print(f"Plotting {variable} map and histo...", flush=True)
            # fig, ax = plot_obj.plot_map_with_histogram(
            #     variable=variable,
            #     data_area="global",
            #     data_type="swot",
            #     world_cover_mask=['urban'],
            #     time_selection=time,
            #     add_bkg=False,
            #     cmap=cmap,
            #     use_seaborn=False,
            #     vmin=vmin,
            #     vmax=vmax,
            #     )
            
            print("Creating flood mask...", flush=True)
            plot_obj.swot_collection.create_flood_mask(
                variable=variable,
                data_area="global",
                data_type="swot",
                thresholds=Chinon_thresholds,
                time_selection=time,
                add_uncertainty=False,
                threshold_gamma=0.5,
                threshold_SNR=0.5,
                )

            # print("Plotting flood mask...", flush=True)
            # fig, ax = plot_obj.plot_map_mask(
            #     variable=variable,
            #     data_area="global",
            #     data_type="swot",
            #     time_selection=time,
            #     add_scores=False,
            #     add_bkg=False,
            #     add_legend=False,
            #     figsize=(10,7)
            #     )
            
            print("Saving flood mask...", flush=True)
            plot_obj.swot_collection.save_tiff(
                    variable=variable,
                    is_mask=True,
                    make_binary=True,
                    remove_lowcoh=True,
                    data_area="global",
                    data_type="swot",
                    path=plot_obj.project.TIFF_PATH.joinpath('output', f'watermask_{variable}_{str_time}_epsg{plot_obj.project.CRS}.tif'),
                    time_selection=time,
                )