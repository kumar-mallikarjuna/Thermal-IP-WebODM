from rest_framework import status
from rest_framework.response import Response

from app.plugins import PluginBase, Menu, MountPoint
from app.plugins.views import TaskView
from django.shortcuts import render
from django import forms

from PIL import Image
import io
import uuid
import os
import base64
import subprocess

import numpy as np

raw_image = None
temperature_image = None

class FileForm(forms.Form):
    file_field = forms.FileField(label='Load Image')

class ProcessTaskView(TaskView):
    def post(self, request, pk=None):
        buff = request.FILES['file_field']

        try:
            fname = "%s.jpg" % uuid.uuid4()
            with open("plugins/temperature/public/tmp/" + fname, "wb+") as f:
                for chunk in buff.chunks():
                    f.write(chunk)

            encoded = subprocess.run(["exiftool", "-b", "-j", "plugins/temperature/public/tmp/" + fname], stdout=subprocess.PIPE).stdout.decode("utf-8")
            encoded = encoded[encoded.index("RawThermalImage\": "):]
            encoded = encoded[26:encoded.index("\",")]

            processed_fname = "processed_%s" % fname

            with open("plugins/temperature/public/tmp/" + processed_fname, "wb") as f:
                f.write(base64.b64decode(encoded))
            
            global raw_image, temperature_image
            raw_image = Image.open("plugins/temperature/public/tmp/" + processed_fname)

            def DN_to_temp(x):
                y = (x-7593)/25.0

                y = y.clip(min=0)
                
                return y

            if(raw_image != None):
                temperature_image = DN_to_temp(np.int32(raw_image))
                temperature_image_plot = np.uint8(((temperature_image-temperature_image.min()) / (temperature_image.max() - temperature_image.min())) * 255)
                Image.fromarray(temperature_image_plot).save("plugins/temperature/public/tmp/temperature_" + fname)
                Image.open("plugins/temperature/public/tmp/" + processed_fname)

            return Response(fname, status=status.HTTP_200_OK)
        except Exception as e:
            print(e)

        return Response("Failed")

class RawTaskView(TaskView):
    def get(self, request, pk=None):
        x = int(float(request.GET['x']))
        y = int(float(request.GET['y']))

        DN = np.array(raw_image)[y, x]

        return Response("X: %d, Y: %d, DN: %d, Temperature: %0.2fC"
                                % (
                                    x,
                                    y,
                                    DN,
                                    temperature_image[y, x]
                                )
                , status=status.HTTP_200_OK)

class Plugin(PluginBase):

    def main_menu(self):
        return [Menu("Temperature", self.public_url(""), "")]

    def include_js_files(self):
    	return ['main.js']

    def include_css_files(self):
    	return ['main.css']

    def build_jsx_components(self):
        return ['component.jsx']

    def app_mount_points(self):
        # Show script only if '?print=1' is set
        def dynamic_cb(request):
            return render(request, self.template_path("app.html"), {
                'title': 'Test',
                'form': FileForm()
            })

        return [
            MountPoint("$", dynamic_cb),
            MountPoint("process$", ProcessTaskView.as_view()),
            MountPoint("raw$", RawTaskView.as_view()),
        ]
