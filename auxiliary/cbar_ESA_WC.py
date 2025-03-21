import matplotlib.colors

# ESA WORLDCOVER COLORS
# <item color="#00a000" alpha="255" value="10" label="Tree cover"/>
# <item color="#966400" alpha="255" value="20" label="Shrubland"/>
# <item color="#ffb400" alpha="255" value="30" label="Grassland"/>
# <item color="#ffff64" alpha="255" value="40" label="Cropland"/>
# <item color="#c31400" alpha="255" value="50" label="Built-up"/>
# <item color="#fff5d7" alpha="255" value="60" label="Bare / sparse vegetation"/>
# <item color="#ffffff" alpha="255" value="70" label="Snow and ice"/>
# <item color="#0046c8" alpha="255" value="80" label="Permanent water bodies"/>
# <item color="#00dc82" alpha="255" value="90" label="Herbaceous wetland"/>
# <item color="#009678" alpha="255" value="95" label="Mangroves"/>
# <item color="#ffebaf" alpha="255" value="100" label="Moss and lichen"/>
DICT_COLOR_ESA = {
    '#00a000': {
        "label":'Tree cover',
        "value":10
    },
    '#966400': { 
        "label":'Shrubland',
        "value":20
    },
    '#ffb400': {
        "label":'Grassland',
        "value":30
    },
    '#ffff64': {
        "label":'Cropland',
        "value":40
    },
    '#c31400': {
        "label":'Built-up',
        "value":50
    },
    '#fff5d7': {
        "label":'Bare / sparse vegetation',
        "value":60
    },
    '#ffffff': {
        "label":'Snow and ice',
        "value":70
    },
    '#0046c8': {
        "label":'Permanent water bodies',
        "value":80
    },
    '#00dc82': {
        "label":'Herbaceous wetland',
        "value":90
    },
    '#009678': {
        "label":'Mangroves',
        "value":95
    },
    '#ffebaf': {
        "label":'Moss and lichen',
        "value":100
    }
}


def defined_ESAWC_cmap():
    """Define the colormap for the ESA WC classification
    """
    colors_ESAWC = ["#000000" for r in range(256)]
    for key, dico in DICT_COLOR_ESA.items():
        colors_ESAWC[int(dico["value"])] = key
    cmap_ESAWC = matplotlib.colors.ListedColormap(colors_ESAWC, name='ESA_World_Cover')

    # sequences needed for an informative colorbar
    values_ESAWC = [dico["value"] for dico in DICT_COLOR_ESA.values()]
    
    boundaries_ESAWC = [(values_ESAWC[i + 1] + values_ESAWC[i]) / 2 for i in range(len(values_ESAWC) - 1)]
    boundaries_ESAWC = [0] + boundaries_ESAWC + [255]
    
    ticks_ESAWC = [(boundaries_ESAWC[i + 1] + boundaries_ESAWC[i]) / 2 for i in range(len(boundaries_ESAWC) - 1)]
    tick_labels_ESAWC = [dico["label"] for dico in DICT_COLOR_ESA.values()]

    normalizer_ESAWC = matplotlib.colors.Normalize(vmin=0, vmax=255)
    
    return cmap_ESAWC, normalizer_ESAWC, boundaries_ESAWC, ticks_ESAWC, tick_labels_ESAWC, values_ESAWC

