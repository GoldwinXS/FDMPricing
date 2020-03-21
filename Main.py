import tkinter as tk
import os
from ProjectUtils import hollow_estimate, material_prices, find_mins_maxs
import pandas as pd


class App:
    first_use = True

    def __init__(self):

        """ Main Application class """
        self.set_app_dict()
        self.set_query_dict()

        self.root = tk.Tk()
        self.root.wm_title("FDM QUOTING SOFTWARE V 2.2.7")
        self.root.iconbitmap("icon.ico")

        # Submit button
        self.submit_button = tk.Button(self.root, text="Submit")
        self.submit_button.bind("<Button-1>", self.create_window)
        self.submit_button.grid(row=0, column=0, sticky=tk.E + tk.W)

        # Path Entry
        self.path_field = tk.Entry(self.root)
        self.path_field.grid(row=0, column=1, sticky=tk.E + tk.W + tk.N + tk.S)
        self.root.resizable(True, True)
        self.root.mainloop()

    def set_query_dict(self):
        """ simple function to reset the query dict which contains all of the needed info for part pricing"""
        self.query_dict = {"mesh": [],
                           "path": [],
                           "quantities_variables": [],
                           "drop_down_variables": [],
                           "infills": [],
                           "thicknesses": [],
                           "material": []}

    def set_app_dict(self):
        """ will reset the app data dict, which has all of the GUI variables """
        self.app_data = {
            "names": [],
            "infills": [],
            "infill_variables": [],
            "materials": [],
            "material_variables": [],
            "thicknesses": [],
            "thickness_variables": [],
            "quantities": [],
            "quantities_variables": [],
            "file_names": [],
            "mesh": [],
            "drop_down_variables": [],
        }

    def price_sorter(self, build_dict, query_dict):
        """ this function converts the build requirements per material to price per part"""
        query_df = pd.DataFrame(query_dict)
        build_df = pd.DataFrame(build_dict)
        n_parts = query_df.shape[0]

        query_df['part_unit_price'] = [0] * n_parts
        # query_df['part_dims'] = query_df['mesh'].apply(lambda x: find_mins_maxs(x)) # get the mesh rects for all parts

        for material in query_df['material'].unique():
            parts_in_mat_df = query_df[query_df['material'] == material] # extract only parts in that material for the query df
            build_mat_df = build_df[build_df['material'] == material] # extract relevant build info from the builds df

            # get the volume of the part given the relevant factors "thickness" and "infill" between 0 and 100
            parts_in_mat_df['part_total_vol'] = [hollow_estimate(m, t, i)
                                                for m, t, i in
                                                zip(parts_in_mat_df['mesh'], parts_in_mat_df['thicknesses'],
                                                    parts_in_mat_df['infills'])]

            # calculate the total volume of all builds
            total_vol = sum(parts_in_mat_df['part_unit_vol'] * list(map(int, parts_in_mat_df['quantities_variables'])))

            # given the volume of each part, calculate the contribution of that part towards the final price
            parts_in_mat_df['part_contrib_to_total_vol'] = [(part_vol * qty) / total_vol for part_vol, qty in
                                                            zip(parts_in_mat_df['part_total_vol'], list(
                                                                map(int, parts_in_mat_df['quantities_variables'])))]
            query_df.loc[query_df['material'] == material, 'part_total_price'] = parts_in_mat_df[
                                                                                    'part_contrib_to_total_vol'] * \
                                                                                build_mat_df['total_price'].values


        return {x: str(round(price, 2)) for x, price in zip(range(n_parts), query_df['part_unit_price'])}

    def convert_to_list(self, query_dict):
        df = pd.DataFrame(query_dict)
        return df.values.tolist()

    def report_window(self, g):
        from stl import mesh

        report_window = tk.Toplevel(self.root, bg="white")

        report_window.iconbitmap("icon.ico")
        report_window.wm_title("REPORT WINDOW")

        materials = []
        quantities = []
        labels = []
        copy_buttons = []

        self.label_text = ["Name", "Material", "Quantity", "Unit Price","Total Price"]


        for j in range(0, len(self.label_text)):
            labels.append(tk.Label(report_window, text=self.label_text[j], font='Helvetica 18 bold', bg="white"))
            labels[j].grid(column=j, row=0, padx=5, pady=5)

        self.set_query_dict()
        for i, file in enumerate(self.file_names):
            name = tk.Label(report_window, text=file.rstrip(".stl"), bg="white")
            name.grid(column=0, row=i + 1, sticky=tk.W)

            materials.append(self.app_data['drop_down_variables'][i].get())
            material = tk.Label(report_window, text=materials[i], bg="white")
            material.grid(column=1, row=i + 1)

            quantities.append(self.app_data['quantities_variables'][i].get())
            quantity = tk.Label(report_window, text=quantities[i], bg="white")
            quantity.grid(column=2, row=i + 1)

            mesh_obj = mesh.Mesh.from_file(self.path_field.get() + "/" + file)
            mesh_obj.points = mesh_obj.points / 100  # convert to inches?
            self.query_dict['mesh'].append(mesh_obj)
            self.query_dict['quantities_variables'].append(self.app_data['quantities_variables'][i].get())
            self.query_dict['drop_down_variables'].append(self.app_data['drop_down_variables'][i].get())
            self.query_dict['infills'].append(self.app_data['infills'][i].get())
            self.query_dict['thicknesses'].append(self.app_data['thicknesses'][i].get())
            self.query_dict['material'].append(self.app_data['drop_down_variables'][i].get())
            self.query_dict['path'].append(self.path_field.get() + "/" + file)
            copy_button = tk.Button(report_window, text="Copy to Clipboard",
                                    command=lambda x=i: clipboard(x))
            copy_button.grid(column=4, row=i + 1, padx=5, pady=5)

        # combined_request = self.convert_to_list(self.query_dict)
        final_info = material_prices(self.query_dict)
        final_unit_prices = self.price_sorter(final_info, self.query_dict)

        for i in range(0, len(self.file_names)):
            price = tk.Label(report_window, text=final_unit_prices[i], bg="white")
            price.grid(column=3, row=i + 1)
            copy_buttons.append(tk.StringVar(self.root))
            copy_buttons[i] = str(final_unit_prices[i])

        def clipboard(index):
            """ Simple function to copy text to the clipboard for easy reuse """
            clip = tk.Tk()
            clip.clipboard_clear()
            clip.clipboard_append(copy_buttons[index])
            clip.destroy()

    def create_window(self, g):

        """
        This function creates a new tkinter window which will allow the user to specify what parameters they would like for a given part
        The argument "g" is to work around a bug in tkinter
        """

        self.name_labels = []

        if not self.first_use:
            self.refresh(self.frame)

        else:
            self.frame = tk.Frame(self.root, bg="white")

        self.frame.grid(row=1, column=1)

        self.canvas = tk.Canvas(self.frame, bg="white")
        self.canvas.grid(rowspan=2, columnspan=2)

        self.new_window = tk.Frame(self.canvas, bg="white")
        self.scroll_bar = tk.Scrollbar(self.root, orient="vertical", command=self.canvas.yview)
        self.scroll_bar.grid(column=2, row=1, sticky="ns")
        self.canvas.create_window((0, 0), window=self.new_window, anchor='nw')
        self.canvas.grid()

        path = self.path_field.get()
        self.file_names = [file for file in os.listdir(path) if file.endswith('.stl')]

        self.new_window.bind("<Configure>", self.AuxscrollFunction)

        label_text = ["Name", "Material", "Infill (%)", "Thickness (in)", "Quantity"]

        self.first_use = False

        self.scroll_bar.config(command=self.canvas.yview)
        self.canvas['yscrollcommand'] = self.scroll_bar.set

        for index in range(len(self.file_names)):

            labels = []

            for j in range(0, len(label_text)):
                labels.append(tk.Label(self.new_window, text=label_text[j], font='Helvetica 18 bold', bg="white"))
                labels[j].grid(column=j, row=0, padx=5, pady=5)

            self.app_data['drop_down_variables'].append(tk.StringVar(self.root))
            self.app_data['infill_variables'].append(tk.StringVar(self.root))
            self.app_data['material_variables'].append(tk.StringVar(self.root))
            self.app_data['thickness_variables'].append(tk.StringVar(self.root))
            self.app_data['quantities_variables'].append(tk.StringVar(self.root))

            self.name = tk.Label(self.new_window, text=self.file_names[index].rstrip(".stl"), bg="white")
            self.name_labels.append(self.name)
            self.new_window.update()

            self.app_data['infills'].append(
                tk.Entry(self.new_window, textvariable=self.app_data['infill_variables'][index]))
            self.app_data['thicknesses'].append(
                tk.Entry(self.new_window, textvariable=self.app_data['thickness_variables'][index]))
            materials = ("ASA", "PEEK", "PLA", "ABS", "Ultem 1010", "Ultem 9085", "Nylon 12", "Zytel", "PC-ABS")
            self.app_data['materials'].append(
                tk.OptionMenu(self.new_window, self.app_data['drop_down_variables'][index], *materials))
            self.app_data['quantities'].append(
                tk.Entry(self.new_window, textvariable=self.app_data['quantities_variables'][index]))
            self.copy_parameter = tk.Button(self.new_window, text="Copy Parameters",
                                            command=lambda x=index: self.copy_parameters(x))

            self.name.grid(column=0, row=index + 1, sticky=tk.W)
            self.app_data['materials'][index].grid(column=1, row=index + 1)
            self.app_data['infills'][index].grid(column=2, row=index + 1)
            self.app_data['thicknesses'][index].grid(column=3, row=index + 1)
            self.app_data['quantities'][index].grid(column=4, row=index + 1)
            self.copy_parameter.grid(column=5, row=index + 1, padx=5, pady=2)

        self.create_report_button = tk.Button(self.root, text="GO", bg="green", fg="white", font='Helvetica 18 bold')
        self.create_report_button.bind("<Button-1>", self.report_window)
        self.create_report_button.grid(row=2, column=2, padx=5, pady=2)

    def copy_parameters(self, index):
        self.new_window.forget()
        selected_material = self.app_data['drop_down_variables'][index].get()
        selected_infill = self.app_data['infill_variables'][index].get()
        selected_thickness = self.app_data['thickness_variables'][index].get()
        selected_quantity = self.app_data['quantities_variables'][index].get()

        for i in range(0, len(self.file_names)):
            self.app_data['drop_down_variables'][i].set(selected_material)
            self.app_data['infill_variables'][i].set(selected_infill)
            self.app_data['thickness_variables'][i].set(selected_thickness)
            self.app_data['quantities_variables'][i].set(selected_quantity)

    def refresh(self, frame):
        """ This function will assign all of the vars for GUI elements to empty lists, effectively clearing them """
        self.canvas.grid_forget()
        self.canvas.destroy()
        self.new_window = tk.Canvas(self.frame, bg="white")
        self.set_app_dict()
        self.set_query_dict()

    def AuxscrollFunction(self, g):
        """ If the window is larger than a hard coded size, scrolling will be enabled """

        # NB: You need to set a max size for frameTwo. Otherwise, it will grow as needed, and scrollbar do not act
        width = 0

        for i in range(0, len(self.name_labels)):
            temp = self.name_labels[i].winfo_width()
            if temp > width:
                width = temp

        width += 100 * 7

        height = self.name_labels[0].winfo_height() * len(self.file_names) + 100

        if height > 850:
            height = 850

        if width > 1350:
            width = 1400

        self.canvas.configure(scrollregion=self.canvas.bbox("all"), width=width,
                              height=height)


App()
