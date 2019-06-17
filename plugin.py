from rest_framework import status
from rest_framework.response import Response

from app.plugins import PluginBase, Menu, MountPoint
from app.plugins.views import TaskView
from django.shortcuts import render
from django import forms

class TestForm(forms.Form):
    testField = forms.CharField(label='Test')


class TestTaskView(TaskView):
    def get(self, request, pk=None):
        task = self.get_and_check_task(request, pk)
        return Response(task.id, status=status.HTTP_200_OK)


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
                'test_form': TestForm()
            })

        return [
            MountPoint("$", dynamic_cb)
        ]


