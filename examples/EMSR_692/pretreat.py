import os
os.sys.path.append('/data/scratch/globc/bonassies/workspace/swot_for_flood')

import configparser
from pathlib import Path
from core.swot_project import SWOT_PROJECT

main_path = "/data/scratch/globc/bonassies/workspace/swot_for_flood/examples/EMSR_692"

config = configparser.ConfigParser()
config.read(main_path + '/config.cfg')

print(type(config),dict(config['CONFIG']))

#create the SWOT_PROJECT object
swot_project = SWOT_PROJECT(config)
print(swot_project)

# # Search and download the data
swot_project.Downloader.search_PIXC()
# swot_project.Downloader.download_pool()

# Find and pre-process the data
swot_project.Rasterizer.find_pixc()
swot_project.Rasterizer.pixc_to_gpkg()
swot_project.Rasterizer.gpkg_to_tiff()