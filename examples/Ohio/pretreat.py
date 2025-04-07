import os
os.sys.path.append('/data/scratch/globc/bonassies/workspace/swot_for_flood')

import configparser
from pathlib import Path
from core.swot_project import SwotProject

main_path = "/data/scratch/globc/bonassies/workspace/swot_for_flood/examples/Ohio"

config = configparser.ConfigParser()
config.read(main_path + '/config.cfg')

print(type(config),dict(config['CONFIG']))

#create the SWOT_PROJECT object
swot_project = SwotProject(config)
print(swot_project, flush=True)

# # Search and download the data
# swot_project.Downloader.search_PIXC()
# swot_project.Downloader.download_pool()

# Find and pre-process the data
swot_project.Rasterizer.find_pixc()
swot_project.Rasterizer.pixc_to_gpkg()
swot_project.Rasterizer.gpkg_to_tiff()