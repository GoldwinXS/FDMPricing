from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.graphics import Callback, Color, Rectangle
from kivy.uix.slider import Slider
from ProjectUtils import get_stl_files, MainAppScreen, PartAppScreen
from kivy.uix.dropdown import DropDown
import trimesh 


class QueryPage(MainAppScreen):
    """
    Class to describe the Main query page where the path is input by the user

    this class inherits from MainAppScreen, which is a wrapper around kivy.uix.screenmanager.Screen
    """

    def __init__(self, **kwargs):
        super(QueryPage, self).__init__(**kwargs)

        # setup vars
        self.parts = []

        self.add_background()
        # Define widgets
        self.entry = TextInput(height=27, text='/Users/goldwin/PycharmProjects/FDM_APP_v2/')
        self.label = Label(text='Enter a path to your .stl files here')
        self.go_button = Button(text='GO!', height=25)

        # set dynamic canvas options
        with self.canvas:
            Callback(self.resize_widgets)

        # Add widgets to self
        self.add_widget(self.go_button)
        self.add_widget(self.entry)
        self.add_widget(self.label)

    def resize_widgets(self, instance):
        """ General function to handle the resizing of widgets on this page """
        self.size_x, self.size_y = self.get_screen_width_and_height()

        # find center points for all widgets, adjusting for size
        self.go_button_center = self.get_center_point_for_widget(self.go_button.width, self.go_button.height)
        self.entry_center = self.get_center_point_for_widget(self.go_button.width, self.go_button.height)
        self.label_center = self.get_center_point_for_widget(self.go_button.width, self.go_button.height)

        # offset widgets
        self.go_button.pos = self.offset_widget(self.go_button_center, (-0.2, 0))
        self.entry.pos = self.offset_widget(self.entry_center, (0.19, 0))
        self.label.pos = self.offset_widget(self.label_center, (0, -0.2))

        # span entry bar
        self.entry.width = self.go_button.pos[0] - self.entry.pos[0]


class PartInfoPage(PartAppScreen):
    """
    Class to describe the Main query page where the path is input by the user

    this class inherits from MainAppScreen, which is a wrapper around kivy.uix.screenmanager.Screen
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.parts = {}

        self.add_background()  # add background

        self.back_button = Button(text='go back', size=self.center, pos=(400, 400))

        # Any changes to this list must be reflected in self.update_grid
        self.column_labels = ['Part Name',
                              'Material',
                              'Print vol',
                              'Part Thickness',
                              'Infill Amt',
                              'Print Time',
                              'Final Cost']

        # TODO load materials from options
        self.materials = {
            'ASA': {
                'price': 30,
                'density': 1.5},
            'PLA': {
                'price': 30,
                'density': 1
            },
            'ULTEM': {
                'price': 530,
                'density': 1
            }
        }

        # self.reset_all()

        with self.canvas:
            print('updating totals')
            # if len(self.parts) > 0:
            Callback(self.update_totals)

    def update_grid(self):
        """ Updates the grid and populate with parts """
        # if not isinstance(self.parts, type(None)):
        self.part_grid.rows += len(self.parts)
        for i in range(len(self.parts['path'])):
            # Create entry fields
            self.thickness_entry.append(TextInput(text='0', padding=3, halign='center'))
            self.infill_entry.append(TextInput(text='0', padding=3, halign='center'))

            # Prepare vars
            bbox_dim = self.parts['bbox'][i]
            # bbox_dim = '(' + ' x '.join([str(round(dim, 2)) for dim in bbox_dim]) + ') cm'

            # Determine the parts hollowed volume
            hollow_volume = self.hollow_estimate(self.parts['volume'][i],
                                                 self.parts['surface'][i],
                                                 float(self.thickness_entry[i].text),
                                                 float(self.infill_entry[i].text))

            # Calculate an estimated build time
            # TODO: add a better way of orienting the parts instead of just picking the first dimension
            print_time = self.time_estimate(float(self.infill_entry[i].text),
                                            float(self.thickness_entry[i].text),
                                            self.parts['bbox'][i][0])

            # Determine the final price
            final_price = self.simple_price_estimator(self.parts['volume'][i], hollow_volume,
                                                      self.parts['bbox'][i][0], float(self.infill_entry[i].text))

            # Create widgets
            file_name = Label(text=self.parts['file_name'][i])
            # bbox_dims = Label(text=bbox_dim, font_size=15)
            materials = self.create_material_dropdown()
            hollow_vol = Label(text=str(round(hollow_volume, 2)))
            print_times = Label(text=str(round(print_time * 60)) + ' min')
            final_price = Label(text='$' + str(round(final_price, 2)))

            # save now so we can modify later
            self.final_prices.append(final_price)
            self.hollow_volumes.append(hollow_vol)
            self.print_times.append(print_times)

            # Add widgets
            self.part_grid.add_widget(file_name)
            self.part_grid.add_widget(materials)
            # self.part_grid.add_widget(bbox_dims)
            self.part_grid.add_widget(hollow_vol)
            self.part_grid.add_widget(self.thickness_entry[i])
            self.part_grid.add_widget(self.infill_entry[i])
            self.part_grid.add_widget(print_times)
            self.part_grid.add_widget(final_price)

    # def update_dropdown(self,mainbutton,text):

    def create_material_dropdown(self):
        dropdown = DropDown()
        main_button = Button(text='Select Material', height=30, halign='center', )

        for mat in self.materials.keys():
            btn = Button(text=mat, height=20, size_hint_y=None, halign='center', )
            # display the value of the text if selected
            btn.bind(on_select=lambda x: dropdown.select(x.text))
            # btn.bind(on_release=lambda main_button.text=)
            dropdown.add_widget(btn)

        main_button.halign = 'center'
        main_button.bind(on_release=dropdown.open)
        dropdown.bind(on_select=lambda instance, x: setattr(main_button, 'text', x))

        return main_button

    def update_totals(self, instance):
        for i in range(len(self.final_prices)):
            # Calculate an estimated build time
            # TODO: add a better way of orienting the parts instead of just picking the first dimension

            if len(self.thickness_entry[i].text) < 1:
                self.final_prices[i].text = '0'
            if len(self.thickness_entry[i].text) < 1:
                self.final_prices[i].text = '0'

            print_time = self.time_estimate(float(self.infill_entry[i].text),
                                            float(self.thickness_entry[i].text),
                                            self.parts['bbox'][i][0])

            hollow_volume = self.hollow_estimate(self.parts['volume'][i],
                                                 self.parts['surface'][i],
                                                 float(self.thickness_entry[i].text),
                                                 float(self.infill_entry[i].text))

            new_price = self.simple_price_estimator(self.parts['volume'][i],
                                                    hollow_volume,
                                                    self.parts['bbox'][i][0],
                                                    float(self.infill_entry[i].text))

            self.hollow_volumes[i].text = str(round(hollow_volume, 2)) + 'cc'
            self.final_prices[i].text = str(round(new_price, 2)) + '$'
            self.print_times[i].text = str(round(print_time * 60)) + ' min'

    def reset_all(self):
        """ reset all of the widgets on the page and redraw essentials """

        # Var setup
        self.cols = 1
        self.rows = 3  # Main structure is a grid with 3 rows

        # self.part_grid = GridLayout(pos=(0, 0), size=(500, 500))
        self.row_default_height = 50
        self.row_force_default = True

        self.clear_widgets()

        self.part_grid = GridLayout(rows=1, cols=len(self.column_labels), row_default_height=35)  # reset part grid
        self.part_grid.cols = len(self.column_labels)  # set correct num of columns
        [self.part_grid.add_widget(Label(text=label)) for label in self.column_labels]  # add column labels

        # setup vars
        self.thickness_entry = []
        self.infill_entry = []
        self.hollow_volumes = []
        self.final_prices = []
        self.print_times = []

        self.update_grid()

        self.add_widget(self.back_button)
        self.add_widget(self.part_grid)


class FDMApp(App):
    """
    Builds all of the app screens into a single application
    """

    def build(self):
        """ Main setup for the application happens here """
        self.screen_manager = ScreenManager()

        # Load pages
        self.query_page = QueryPage()
        self.part_info_page = PartInfoPage()

        # connect pages
        self.query_page.go_button.bind(on_press=self.go_to_part_page)
        self.part_info_page.back_button.bind(on_press=self.go_back_to_start)

        # Add pages to screen manager
        self.add_screen(self.query_page, 'start')
        self.add_screen(self.part_info_page, 'part-info')

        return self.screen_manager

    def go_to_part_page(self, instance):
        """ Go to the part page with all of the part information """
        self.part_info_page.parts = get_stl_files(self.query_page.entry.text)
        self.part_info_page.reset_all()
        self.screen_manager.current = 'part-info'

    def go_back_to_start(self, instance):
        """ Go to the beginning user input area"""
        self.part_info_page.reset_all()
        self.screen_manager.current = 'start'
        self.part_info_page.back_button.bind(on_press=self.go_back_to_start)

    def add_screen(self, page, name):
        """

        Args:
            name: (str): name for the window for later reference
            page (kivy.uix.ScreenManager.Screen): a kivy screen object
        """
        screen = Screen(name=name)
        screen.add_widget(page)
        self.screen_manager.add_widget(screen)


if __name__ == "__main__":
    FDMApp().run()
