import subprocess
import os

def get_layer_names(filename, verbose=False):
    if verbose:
        print("Getting layer names")
    process = subprocess.Popen(["xcfinfo", filename],
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    out, err = process.communicate()
    layerInfo = out.decode("utf-8").split("\n")[1:-1]
    layers = list(" ".join(layer.split(" ")[4:]) for layer in layerInfo)[::-1]
    if verbose:
        print("Found layers: [\"%s\"]"%"\", \"".join(layers))
    return layers

def extract_layer(filename, scene, layer, verbose=False):
    if verbose:
        print("Extracting layer: \"%s\""%layer)
    layersDir = "layers"
    dirName = "%s/%s"%(layersDir, scene)
    output = "%s/%s.png"%(dirName, layer)
    if not os.path.exists(layersDir):
        os.mkdir(layersDir)
    if not os.path.exists(dirName):
        os.mkdir(dirName)
    with open(output, "wb") as outputFile:
        process = subprocess.call(["xcf2png", filename, layer, "-b", "white"],
                                  stdout=outputFile,
                                  stderr=subprocess.PIPE)
    if verbose:
        print("Saved to %s"%output)
    return output

def extract_scene(scene, verbose=False):
    if verbose:
        print("Extracting scene %s"%scene)
    filename = "scenes/%s.xcf"%scene
    if verbose:
        print("Extracting layers from %s"%filename)
    layers = get_layer_names(filename, verbose)
    filenames = []
    for i in layers:
        filenames.append(extract_layer(filename, scene, i, verbose))
    if verbose:
        print("Done extracting layers")
    return layers, filenames
