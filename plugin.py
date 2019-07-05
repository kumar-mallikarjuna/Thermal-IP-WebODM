from rest_framework import status
from rest_framework.response import Response

from app.plugins import PluginBase, Menu, MountPoint
from app.plugins.views import TaskView
from django.shortcuts import render
from django import forms

from PIL import Image, ImageEnhance
from PIL import ImageOps
import io
import uuid
import os
import glob
import base64
import subprocess

import numpy as np
import cv2

import matplotlib.pyplot as plt

fnames = []
raw_images = []
temperature_images = []
temperature_image = None
hot_temperature_image = None

temp_range = False
temp_min = temp_max = 0

class FileForm(forms.Form):
    file_field = forms.FileField(widget = forms.ClearableFileInput(attrs = {'multiple' : True}))

class TempForm(forms.Form):
    min_field = forms.DecimalField()
    max_field = forms.DecimalField()

class TempTaskView(TaskView):
    def post(self, request, pk=None):
        global temp_range, temp_min, temp_max
        
        temp_max_input = request.POST['max_field']
        temp_min_input = request.POST['min_field']

        if(temp_max_input != "" and temp_max_input != ""):
            temp_range = True
            temp_max = float(temp_max_input)
            temp_min = float(temp_min_input)
        else:
            temp_range = False

        return Response("", status=status.HTTP_200_OK)

class ProcessTaskView(TaskView):
    def post(self, request, pk=None):
        files = glob.glob("plugins/temperature/public/tmp/*")
        for f in files:
            os.remove(f)

        global fnames, raw_images, temperature_images, temperature_image
        global temp_min, temp_max, temp_range
        fnames = []
        raw_images = []
        temperature_images = []
        temperature_image = None
        buff_list = request.FILES.getlist('file_field')

        if(not temp_range):
            temp_min = temp_max = 0

        def DN_to_temp(x):
            y = (x-7593)/25.0
            y = y.clip(min=0)
            return y

        try:
            for buff in buff_list:
                fname = "%s.jpg" % uuid.uuid4()
                fnames.append(fname)
                with open("plugins/temperature/public/tmp/" + fname, "wb+") as f:
                    for chunk in buff.chunks():
                        f.write(chunk)

                encoded = subprocess.run(["exiftool", "-b", "-j", "plugins/temperature/public/tmp/" + fname], stdout=subprocess.PIPE).stdout.decode("utf-8")
                encoded = encoded[encoded.index("RawThermalImage\": "):]
                encoded = encoded[26:encoded.index("\",")]

                processed_fname = "processed_%s" % fname
                with open("plugins/temperature/public/tmp/" + processed_fname, "wb") as f:
                    f.write(base64.b64decode(encoded))
            
                raw_images.append("plugins/temperature/public/tmp/" + processed_fname)
                
                temperature_image = DN_to_temp(np.int32(Image.open("plugins/temperature/public/tmp/" + processed_fname)))
                temperature_images.append(temperature_image)


                if(not temp_range):
                    temp_min = temp_min if temp_min < temperature_image.min() else temperature_image.min()
                    temp_max = temp_max if temp_max > temperature_image.max() else temperature_image.max()

            for i in range(len(buff_list)):
#                print(temp_min, temp_max)
                fname = fnames[i]
                temperature_image = temperature_images[i]
                temperature_image_plot = np.int32(((temperature_image-temp_min) / float(temp_max - temp_min)) * 255.0)
                temperature_image_plot[temperature_image_plot < 0] = 0
                temperature_image_plot[temperature_image_plot > 255] = 255
                temperature_image_plot = np.uint8(temperature_image_plot)
                Image.fromarray(temperature_image_plot).save("plugins/temperature/public/tmp/temperature_" + fname)
                hot_temperature_image = cv2.applyColorMap(temperature_image_plot, cv2.COLORMAP_HOT)
                cv2.imwrite("plugins/temperature/public/tmp/hot_temperature_" + fname, hot_temperature_image)

            if(len(raw_images) > 0):
                if(len(raw_images) == 1):
                    temperature_image = temperature_images[0]
                    temperature_image_plot = np.int32(((temperature_image-temp_min) / float(temp_max - temp_min)) * 255.0)
                    temperature_image_plot[temperature_image_plot < 0] = 0
                    temperature_image_plot[temperature_image_plot > 255] = 255
                    temperature_image_plot = np.uint8(temperature_image_plot)

                    fig = plt.figure()
                    plt.xticks(np.arange(temp_min, temp_max, 5))
                    ax = plt.gca()
                    ax.set_title("Histogram (%d bins)" % int(np.floor(temp_max)-np.floor(temp_min)))
                    plt.xlabel("Temperature (Celsius)")
                    plt.ylabel("Number of pixels")
                    ax.set_facecolor('#3498db')
                    Y, X = np.histogram(temperature_image.ravel(), bins=int(np.floor(temp_max)-np.floor(temp_min)))
                    cm = plt.cm.get_cmap('hot')
                    C = [cm(((x-np.floor(temp_min))/(np.floor(temp_max)-np.floor(temp_min)))) for x in X]
                    plt.bar(X[:-1],Y,color=C,width=X[1]-X[0])
                    plt.savefig("plugins/temperature/public/tmp/hist_temperature_" + fnames[0])

#                    rav = np.uint8(temperature_image.ravel())

#                    for t in range(int(temp_min), int(temp_max)+1, 5):
#                        print("Temperature: %dC, Count: %d" % (t, (rav == t).sum()))

                    return Response("temperature_" + fnames[0] + "," + str(temp_min) + "," + str(temp_max), status=status.HTTP_200_OK)
                else:
                    images = []
                    for image in fnames:
                        images.append(cv2.imread("plugins/temperature/public/tmp/temperature_"+image))
                    stitcher = cv2.Stitcher_create()
                    (_, stitched) = stitcher.stitch(images)
                    if _ == 0:
                        fname = "%s.jpg" % uuid.uuid4()

                        cv2.imwrite("plugins/temperature/public/tmp/temperature_" + fname, stitched)
                        hot_temperature_image = cv2.applyColorMap(stitched, cv2.COLORMAP_HOT)
                        cv2.imwrite("plugins/temperature/public/tmp/hot_temperature_" + fname, hot_temperature_image)
                        temperature_image = np.array(Image.open("plugins/temperature/public/tmp/temperature_" + fname).convert('L'))
                        temperature_image_hist = (temperature_image)/255.0*float(temp_max-temp_min) + temp_min
                        
                        fig = plt.figure()
                        plt.xticks(np.arange(temp_min, temp_max, 5))
                        ax = plt.gca()
                        ax.set_title("Histogram (%d bins)" % int(np.floor(temp_max)-np.floor(temp_min)))
                        plt.xlabel("Temperature (Celsius)")
                        plt.ylabel("Number of pixels")
                        ax.set_facecolor('#3498db')
                        Y, X = np.histogram(temperature_image_hist.ravel(), bins=int(np.floor(temp_max)-np.floor(temp_min)))
                        cm = plt.cm.get_cmap('hot')
                        C = [cm(((x-np.floor(temp_min))/(np.floor(temp_max)-np.floor(temp_min)))) for x in X]
                        plt.bar(X[:-1],Y,color=C,width=X[1]-X[0])
                        plt.savefig("plugins/temperature/public/tmp/hist_temperature_" + fname)

                        return Response("temperature_" + fname + "," + str(temp_min) + "," + str(temp_max), status=status.HTTP_200_OK)
                    else:
                        print("Failed to stitch.")


        except Exception as e:
            print(e)

        return Response("Failed to create mosaic.")

class RawTaskView(TaskView):
    def get(self, request, pk=None):
        x = int(float(request.GET['x']))
        y = int(float(request.GET['y']))
        if len(raw_images) == 1:
            DN = np.array(Image.open(raw_images[0]))[y, x]

            return Response("X: %d, Y: %d, DN: %d, Temperature: %0.2fC"
                                    % (
                                        x,
                                        y,
                                        DN,
                                        temperature_image[y, x]
                                    )
                    , status=status.HTTP_200_OK)
        else:
            return Response("X: %d, Y: %d, Temperature: %0.2fC"
                                    % (
                                        x,
                                        y,
                                        (temperature_image[y, x]/255.0)*(temp_max-temp_min) + temp_min
                                    )
                    , status=status.HTTP_200_OK)

class Plugin(PluginBase):

    def main_menu(self):
        return [Menu("Temperature", self.public_url(""), "fa fa-camera fa-fw")]

    def include_js_files(self):
    	return ['main.js']

    def include_css_files(self):
    	return ['main.css']

    def build_jsx_components(self):
        return ['component.jsx']

    def app_mount_points(self):
        def dynamic_cb(request):
            return render(request, self.template_path("app.html"), {
                'title': 'Temperature',
                'form': FileForm(),
                'temp_form': TempForm()
            })

        return [
            MountPoint("$", dynamic_cb),
            MountPoint("process$", ProcessTaskView.as_view()),
            MountPoint("raw$", RawTaskView.as_view()),
            MountPoint("temp$", TempTaskView.as_view()),
        ]
