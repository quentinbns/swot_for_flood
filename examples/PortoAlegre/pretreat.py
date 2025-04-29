import os
os.sys.path.append('/data/scratch/globc/bonassies/workspace/swot_for_flood')

import configparser
from pathlib import Path
from cmap import Colormap
from core.plot_raster import PlotRaster
from core.swot_project import SwotProject

main_path = "/data/scratch/globc/bonassies/workspace/swot_for_flood/examples/PortoAlegre"

config = configparser.ConfigParser()
config.read(main_path + '/config.cfg')

print(type(config),dict(config['CONFIG']))

# # create the SWOT_PROJECT object
swot_project = SwotProject(config)
print(swot_project, flush=True)

# # Search and download the data
swot_project.Downloader.search_PIXC(only_studied=False)
swot_project.Downloader.download_pool()

# # Find and pre-process the data
swot_project.Rasterizer.find_pixc()
swot_project.Rasterizer.make_space = True
swot_project.Rasterizer.pixc_to_gpkg()
swot_project.Rasterizer.gpkg_to_tiff()

# Find and open the data
print('Find and open the data', flush=True)
swot_project.find_raster()
swot_project.create_collection()

print('Create Plot object', flush=True)
# Create the plot object
plot_obj = PlotRaster(
    swot_project,
    save_fig=True,
    show_fig=False
    )

# plot 25 maps in less than 4 minutes for raster files of 1.65Go
print('Plot all raster for interferometric coherence', flush=True)
plot_obj.plot_all_rasters(
    'gamma_tot',
    cmap=Colormap('seaborn:mako').to_matplotlib(),
    vmin=0,
    vmax=1,
)
