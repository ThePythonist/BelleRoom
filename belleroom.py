import bellexcf
import cv2
import shutil
import os
import subprocess
import opensimplex
import numpy as np

class Layer:
    def __init__(self, name, im):
        self.name = name
        self.im = im

    def __repr__(self):
        return "Layer: \"%s\""%self.name

    def canny(self):
        return cv2.Canny(self.im, 100, 200)

    def get_lines(self, verbose=False):
        if verbose:
            print("Doing Canny edge detection")
        canny = self.canny()
        if verbose:
            print("Doing dilation")
        kernel = np.ones((5,5), dtype=np.uint8)
        dilation = cv2.dilate(canny, kernel, iterations=1)
        if verbose:
            print("Finding contours")
        contours, hierarchy = cv2.findContours(dilation,
                                               cv2.RETR_TREE,
                                               cv2.CHAIN_APPROX_NONE)

        if verbose:
            print("Found %i contours"%len(contours))
            print("Reshaping contours")
        reshaped = []
        for i in contours:
            x, y, z = i.shape
            reshaped.append(i.reshape(x, z))
        return reshaped


    def get_line_color(self, lines, i, verbose=False):
        if verbose:
            print("Getting line color")
        mask = np.zeros(self.im.shape[:2], dtype=np.uint8)
        if verbose:
            print("Creating mask")
        cv2.drawContours(mask, lines, i, 255, thickness=cv2.FILLED)
        for cont in range(i+1, len(lines)):
            cv2.drawContours(mask, lines, cont, 0, thickness=cv2.FILLED)
        if verbose:
            print("Eroding mask")
        kernel = np.ones((5, 5), dtype=np.uint8)
        mask = cv2.erode(mask, kernel, iterations=2)
        if verbose:
            print("Finding mean color of masked image")
        return cv2.mean(self.im, mask=mask)


class Scene:
    def __init__(self, name, layers):
        self.name = name
        self.layers = layers

    def __repr__(self):
        stub = "Scene: \"%s\""%self.name
        if len(self.layers) == 0:
            return stub
        return "%s - [\"%s\"]"%(stub,
                                "\", \"".join(i.name for i in self.layers))

    def __getitem__(self, key):
        return self.get_layer(key)

    def get_layer(self, layerName):
        for i in self.layers:
            if i.name == layerName:
                return i
        print("Layer \"%s\" does not exist in scene \"%s\""%(layerName, self.name))
        return None

class Contour:
    def __init__(self, points, color, index):
        self.points = points
        self.color = color
        self.index = index
        self.xField = opensimplex.OpenSimplex()
        self.yField = opensimplex.OpenSimplex()
        self.time = 0

    def get_points(self, wiggle):
        roughness = 0.01
        amplitude = 15
        points = self.points[:self.index]
        if not wiggle:
            return points
        newPoints = np.zeros(points.shape, dtype=points.dtype)
        for i, point in enumerate(points):
            x, y = point
            xNoise = amplitude*self.xField.noise3d(x*roughness,
                                                   y*roughness,
                                                   self.time)
            yNoise = amplitude*self.yField.noise3d(x*roughness,
                                                   y*roughness,
                                                   self.time)
            newPoints[i] = (x + xNoise,
                            y + yNoise)
        return newPoints

class BelleRoom:
    def __init__(self, name, size, background=(255, 255, 255), fps=24, path="frames", wiggleRate=0.5, frameNoLength=10):
        self.name = name
        self.width = size[0]
        self.height = size[1]
        r, g, b = background
        self.background = (b, g, r)
        self.fps = 24
        self.path = path
        self.wiggle = True
        self.wiggleRate = wiggleRate
        self.frameNoLength = frameNoLength
        self.frame = np.zeros((self.height, self.width, 3),
                              dtype=np.uint8)
        self.frame[:] = self.background
        if os.path.exists(self.path):
            shutil.rmtree(self.path)
        os.mkdir(self.path)

        self.drawnContours = []

        self.displayWhileDrawing = True

    def display(self):
        cv2.imshow(self.name, self.frame)
        return cv2.waitKey(1) == ord("q")

    def save(self):
        self.render()
        count = len(os.listdir(self.path))
        for i in self.drawnContours:
            i.time += self.wiggleRate/self.fps
        cv2.imwrite((f"%s/%0{self.frameNoLength}i.png")%(self.path,count), self.frame)

    def clear(self):
        self.drawnContours = []
        self.render()
    
    def output(self, filename, cleanup=True, verbose=False):
        if verbose:
            print("Rendering frames to video. Cleanup: %s"%str(cleanup))
        if os.path.isfile(filename):
            if verbose:
                print("%s exists so is being deleted"%filename)
            os.remove(filename)
        process = subprocess.Popen(["ffmpeg",
                                    "-framerate",
                                    str(self.fps),
                                    "-pix_fmt",
                                    "yuv420p",
                                    "-i",
                                    self.path+f"/%0{self.frameNoLength}d.png",
                                    filename],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        out, err = process.communicate()
        if verbose:
            print(out.decode("utf-8"))
            print(err.decode("utf-8"))

        if cleanup:
            if verbose:
                print("Cleaning up")
            shutil.rmtree(self.path)

    def delay(self, time, verbose=False):
        if verbose:
            print("Delaying for %.4f seconds at %i fps"%(time, self.fps))
        frameCount = int(float(time) * float(self.fps))
        if verbose:
            print("%i frames to be rendered"%frameCount)
        
        for i in range(frameCount):
            if self.displayWhileDrawing:
                self.display()
            self.save()

    def render(self):
        self.frame[:] = self.background
        for contour in self.drawnContours:
            if contour.index == len(contour.points):
                cv2.drawContours(self.frame, [contour.get_points(self.wiggle)], 0, contour.color, thickness=cv2.FILLED)
                cv2.drawContours(self.frame, [contour.get_points(self.wiggle)], 0, (0, 0, 0), thickness=1)
            else:
                cv2.polylines(self.frame, [contour.get_points(self.wiggle)], False, (0, 0, 0), thickness=1)
    
    def draw_layer(self, layer, time, verbose=False):
        if verbose:
            print("Drawing %s in %.4f seconds at %i fps"%(layer, time, self.fps))
        lines = layer.get_lines(verbose)
        pixelCount = sum(len(i) for i in lines)
        frameCount = float(time) * float(self.fps)
        period = pixelCount/frameCount
        if verbose:
            print("Pixel count: %s"%pixelCount)
            print("%i frames to be rendered")
            print("Frame to be rendered every %i pixels"%period)

        counter = 0
        for i, line in enumerate(lines):
            col = layer.get_line_color(lines, i, verbose)
            contour = Contour(line, col, 0)
            self.drawnContours.append(contour)
            while contour.index < len(contour.points):
                contour.index += 1
                if counter >= period:
                    counter -= period
                    self.save()
                    if self.displayWhileDrawing:
                        self.display()
                counter += 1
        self.save()

def load_scene(scene, verbose=False):
    names, files = bellexcf.extract_scene(scene, verbose)
    layers = []
    for i, file in enumerate(files):
        im = cv2.imread(file)
        layers.append(Layer(names[i], im))

    return Scene(scene, layers)
