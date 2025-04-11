import rioxarray as rxr
import numpy as np
import pandas as pd
from pathlib import Path

if __name__ == '__main__':
    main_path = Path('/data/scratch/globc/bonassies/workspace/swot_for_flood/examples/Paper_SWOT/urban_areas')
    file_Chinon = "GHS_BUILT_C_MSZ_Chinon_32630.tif"
    file_Ohio = "GHS_BUILT_C_MSZ_Ohio_32616_cut.tif"
    file_greece = "GHS_BUILT_C_MSZ_Greece_32634_cut.tif"
    file_PortoAlegre = "GHS_BUILT_C_MSZ_PortoAlegre_32722_cut.tif"
    class_urban_file = "GHS_BUILT_C_MSZ_color.clr"

    rxr_Chinon = rxr.open_rasterio(main_path.joinpath(file_Chinon))
    rxr_Ohio = rxr.open_rasterio(main_path.joinpath(file_Ohio))
    rxr_greece = rxr.open_rasterio(main_path.joinpath(file_greece))
    rxr_PortoAlegre = rxr.open_rasterio(main_path.joinpath(file_PortoAlegre))
    
    with open(main_path.joinpath(class_urban_file), "r") as f:
        class_urban = f.readlines()
        class_urban = [x.strip() for x in class_urban]
        class_urban = [x.split(', ') for x in class_urban]
        color_urban = [x[0].split(' ') for x in class_urban]
        for x in class_urban:
            x[0] = x[0].split(' ')[0]
            if len(x) == 3:
                x.insert(1, x[1])
        class_urban = np.array(class_urban)
        class_urban[:,0] = [x[0] for x in color_urban]
        color_urban = np.array([[int(x[1]), int(x[2]), int(x[3])] for x in color_urban])
        
    class_urban = np.concatenate((class_urban, color_urban), axis=1)

    pd_urban = pd.DataFrame(class_urban, columns=["raster_index", "Spatial domain", "Built-up type", "Classification", "R", "G", "B"])
    pd_urban["simpler classification"] = pd_urban["Classification"]

    # raster_index in 1,2,3,4 then simpler classification = "open space"
    pd_urban.loc[pd_urban["raster_index"].isin(["1", "2", "3", "4", "5"]), "simpler classification"] = "open space"
    
    # replace "building height <=3m" by "building height <= 3m" to avoid problems with the latex table
    pd_urban.loc[pd_urban["simpler classification"] == "building height <=3m", "simpler classification"] = "building height <= 3m"
    
    # count the number of pixels for each class
    pd_urban["count_Chinon"] = 0
    pd_urban["count_Ohio"] = 0
    pd_urban["count_greece"] = 0
    pd_urban["count_PortoAlegre"] = 0

    for iindex in pd_urban["raster_index"]:
        pd_urban.loc[pd_urban["raster_index"] == iindex, "count_Chinon"] = rxr_Chinon.where(rxr_Chinon == int(iindex)).count(dim=['x','y']).values[0]
        pd_urban.loc[pd_urban["raster_index"] == iindex, "count_Ohio"] = rxr_Ohio.where(rxr_Ohio == int(iindex)).count(dim=['x','y']).values[0]
        pd_urban.loc[pd_urban["raster_index"] == iindex, "count_greece"] = rxr_greece.where(rxr_greece == int(iindex)).count(dim=['x','y']).values[0]
        pd_urban.loc[pd_urban["raster_index"] == iindex, "count_PortoAlegre"] = rxr_PortoAlegre.where(rxr_PortoAlegre == int(iindex)).count(dim=['x','y']).values[0]
        
    total_Chinon = rxr_Chinon.where(rxr_Chinon.isin(pd_urban["raster_index"].astype(int))).count(dim=['x','y']).values[0]
    total_Ohio = rxr_Ohio.where(rxr_Ohio.isin(pd_urban["raster_index"].astype(int))).count(dim=['x','y']).values[0]
    total_greece = rxr_greece.where(rxr_greece.isin(pd_urban["raster_index"].astype(int))).count(dim=['x','y']).values[0]
    total_PortoAlegre = rxr_PortoAlegre.where(rxr_PortoAlegre.isin(pd_urban["raster_index"].astype(int))).count(dim=['x','y']).values[0]

    # set percentage of each class
    pd_urban["percentage_Chinon"] =      100*(pd_urban["count_Chinon"] / total_Chinon)
    pd_urban["percentage_Ohio"] =        100*(pd_urban["count_Ohio"] / total_Ohio)
    pd_urban["percentage_greece"] =      100*(pd_urban["count_greece"] / total_greece)
    pd_urban["percentage_PortoAlegre"] = 100*(pd_urban["count_PortoAlegre"] / total_PortoAlegre)
    
    # Create the simpler table
    pd_simpler = pd_urban.groupby("simpler classification").sum()
    pd_simpler["percentage_Chinon"] =      100*(pd_simpler["count_Chinon"] / total_Chinon)
    pd_simpler["percentage_Ohio"] =        100*(pd_simpler["count_Ohio"] / total_Ohio)
    pd_simpler["percentage_greece"] =      100*(pd_simpler["count_greece"] / total_greece)
    pd_simpler["percentage_PortoAlegre"] = 100*(pd_simpler["count_PortoAlegre"] / total_PortoAlegre)
    
    
    try:
        pd_simpler.pop("R")
        pd_simpler.pop("G")
        pd_simpler.pop("B")
        pd_simpler.pop("raster_index")
        pd_simpler.pop("Spatial domain")
        pd_simpler.pop("Built-up type")
        pd_simpler.pop("Classification")
        pd_simpler.pop("count_Chinon")
        pd_simpler.pop("count_Ohio")
        pd_simpler.pop("count_greece")
        pd_simpler.pop("count_PortoAlegre")
    except:
        pass

    # rename columns
    pd_simpler = pd_simpler.rename(columns={"percentage_Chinon": "Chinon", "percentage_Ohio": "Ohio", "percentage_greece": "Greece", "percentage_PortoAlegre": "Porto Alegre"})
    # rename "simpler classification":"Urban Classification"
    pd_simpler = pd_simpler.rename_axis("Urban Classification")

    pd_simpler.to_latex(main_path.joinpath("urban_classification.tex"), float_format="%.2f", bold_rows=True)
    print('Done.')