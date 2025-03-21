# Description: Define the colormap for the SWOT classification
#
# Import the necessary libraries
import matplotlib.colors

# SWOT CLASSIFICATION COLORS
DICT_COLOR_SWOT = {
    '#377E22': {
        "label":'Land',
        "value":1
    },
    '#296118': { 
        "label":'Land near water',
        "value":2
    },
    '#4A68DA': {
        "label":'Water near land',
        "value":3
    },
    '#2202F5': {
        "label":'Open water',
        "value":4
    },
    '#0B007B': {
        "label":'Dark water',
        "value":5
    },
    '#EA3323': {
        "label":'Low-coherence water near land',
        "value":6
    },
    '#F2A93C': {
        "label":'Open low-coherence water',
        "value":7
    },
}

def defined_SWOT_cmap():
    """Define the colormap for the SWOT classification
    """
    # create the colormap
    colors_SWOT = ["#000000" for r in range(256)]
    for key, dico in DICT_COLOR_SWOT.items():
        colors_SWOT[int(dico["value"])] = key
    cmap_SWOT = matplotlib.colors.ListedColormap(colors_SWOT, name="SWOT")

    # sequences needed for an informative colorbar
    values_SWOT = [dico["value"] for dico in DICT_COLOR_SWOT.values()]

    boundaries_SWOT = [(values_SWOT[i + 1] + values_SWOT[i]) / 2 for i in range(len(values_SWOT) - 1)]
    boundaries_SWOT = [0] + boundaries_SWOT + [255]

    ticks_SWOT = [(boundaries_SWOT[i + 1] + boundaries_SWOT[i]) / 2 for i in range(len(boundaries_SWOT) - 1)]
    tick_labels_SWOT = [dico["label"] for dico in DICT_COLOR_SWOT.values()]

    normalizer_SWOT = matplotlib.colors.Normalize(vmin=0, vmax=255)
    
    return cmap_SWOT, normalizer_SWOT, boundaries_SWOT, ticks_SWOT, tick_labels_SWOT, values_SWOT