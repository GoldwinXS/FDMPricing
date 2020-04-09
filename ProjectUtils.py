import stl as mesh
import pandas as pd
import os
import json
from kivy.uix.screenmanager import Screen
from kivy.uix.dropdown import DropDown
from kivy.uix.widget import Widget
from kivy.uix.gridlayout import GridLayout
from kivy.graphics import Callback, Color, Rectangle

class MainAppScreen(Widget):
    """ A wrapper class to eliminate some repetitive code and abstract utility functions """

    def update_rect(self, *args):
        """ Update function that makes the background dynamic """
        self.rect.pos = self.pos
        self.rect.size = self.size

    def add_background(self):
        """ Adds a background of the specified color """

        with self.canvas:
            # add background
            options = load_json('options.json')
            Color(*options['background'])  # set the colour

            # Setting the size and position of canvas
            self.rect = Rectangle(pos=self.center,
                                  size=(self.width / 2.,
                                        self.height / 2.))

            # bind this to self
            self.bind(pos=self.update_rect,
                      size=self.update_rect)

    def get_center_point_for_widget(self, w, h):
        """
        simple utility function to find the center point of where a widget should be relative to the screen

        Args:
            w: (float): the width of the widget. Used to find the center point.
            h (float): the height of the widget. Used to find the center point.
        """
        return self.center_x - w / 2, self.center_y - h / 2

    def get_screen_center(self):
        return self.center_x, self.center_y

    def get_screen_width_and_height(self):
        return self.center_x * 2, self.center_y * 2

    def offset_widget(self, c_pos, offset):
        """
        function to calculate offset coords from the center

        NB: -ve values will shift left, +ve values will shift right

        Args:
            offset (tuple): defines the ratios of how much one wants to shift the widget
            c_pos (tuple): defines where the center of the widget would be if placed in the center of the screen
        """
        screen_w, screen_h = self.center_x * 2, self.center_y * 2
        offset_x, offset_y = offset
        x, y = c_pos
        change_x, change_y = offset_x * screen_w, offset_y * screen_h
        return x - change_x, y - change_y


class PartAppScreen(GridLayout):
    """ A wrapper class to eliminate some repetitive code and abstract utility functions """

    def update_rect(self, *args):
        """ Update function that makes the background dynamic """
        self.rect.pos = self.pos
        self.rect.size = self.size

    def add_background(self):
        """ Adds a background of the specified color """

        with self.canvas:
            # add background
            options = load_json('options.json')

            Color(*options['background'])  # set the colour

            # Setting the size and position of canvas
            self.rect = Rectangle(pos=self.center, size=(self.width / 2., self.height / 2.))

            # bind this to self
            self.bind(pos=self.update_rect, size=self.update_rect)

    def simple_price_estimator(self, volume, hollow_estimate, height, infill):
        print_time = self.time_estimate(infill, volume, height)
        material_price = 10
        return material_price * hollow_estimate + print_time * 20

    """ STATIC METHODS """

    @staticmethod
    def hollow_estimate(volume, surface_area, thickness, infill):
        """
        Given a path, and desired thickness/infill, this will estimate the hollowed volume of the mesh

        Expects numbers in the range [0,100]

        Args:
            infill: (float): infill amount. expected in range [0,100]
            thickness: (float): thickness of part
            surface_area: (float): surface area of part
            volume (float): volume amount
        """
        wall_volume_after_hollow = float(surface_area) * float(thickness)
        empty_space_after_hollow = volume - wall_volume_after_hollow
        infill_amount = empty_space_after_hollow * (int(infill) / 100)

        hollowed_volume = wall_volume_after_hollow + infill_amount

        if empty_space_after_hollow < 0 or hollowed_volume > volume:
            hollowed_volume = volume

        return hollowed_volume

    @staticmethod
    def time_estimate(infill, volume, height):
        infill = int(infill)

        #   NOTE: EXPERIMENTATION MUST BE DONE TO FIND GOOD VALUES   #

        intermittent_factor = 16.39505801

        coeff_A = 0
        coeff_B = 2549.326795
        coeff_C = 123.6015845
        coeff_D = 2549.326795
        coeff_E = 16.39505801

        answer_sec = coeff_A + (coeff_B * volume) + (coeff_C * height) + (
                coeff_D * (infill / 100) * volume) + coeff_E * height * intermittent_factor

        answer_hrs = (answer_sec / 60) / 60

        return answer_hrs


def find_bbox_dims(mesh_obj):
    """ takes a mesh obj and returns its bounding box dimensions

    Args:
        mesh_obj (mesh.Mesh()): a numpy-stl mesh object
    """
    return mesh_obj.x.max() - mesh_obj.x.min(), \
           mesh_obj.y.max() - mesh_obj.y.min(), \
           mesh_obj.z.max() - mesh_obj.z.min()


def get_stl_files(path):
    """
    A simple function to load all of the .stl files in a given folder

    Args:
        path (str): path to specify where to get stl files
    """

    try:
        folder_files = os.listdir(path)
        file_names = [file for file in folder_files if file.endswith('.stl')]
        path_names = [path + file for file in folder_files if file.endswith('.stl')]

        meshes = [mesh.Mesh.from_file(m) for m in path_names]

        # TODO: make a "switch units" button so we can have differently scaled parts
        for m in meshes:
            m.points /= 100

        volume = [m.get_mass_properties()[0] for m in meshes]
        surface = [m.areas.sum() for m in meshes]
        bbox_dims = [find_bbox_dims(m) for m in meshes]

        return {'file_name': file_names,
                'volume': volume,
                'mesh': meshes,
                'surface': surface,
                'path': path_names,
                'bbox': bbox_dims}
    except:
        pass


def load_json(fp):
    with open(fp) as file:
        return json.load(file)


def save_json(fp, json_obj):
    with open(fp, 'w') as file:
        json.dump(json_obj, fp=file)
