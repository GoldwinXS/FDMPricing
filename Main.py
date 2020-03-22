import tkinter as tk
import os
from ProjectUtils import hollow_estimate, price_by_material, find_mins_maxs
import pandas as pd
from stl import mesh
from copy import deepcopy


class App:
    first_use = True

    def __init__(self):

        """ Main Application class """
        self.set_app_dict()

        self.root = tk.Tk()
        self.root.wm_title("FDM QUOTING SOFTWARE V 2.2.7")
        self.root.iconbitmap("icon.ico")

        # Submit button
        self.submit_button = tk.Button(self.root, text="Submit")
        self.submit_button.bind("<Button-1>", self.create_selection_window)
        self.submit_button.grid(row=0, column=0, sticky=tk.E + tk.W)

        # Path Entry
        self.path_field = tk.Entry(self.root)
        self.path_field.grid(row=0, column=1, sticky=tk.E + tk.W + tk.N + tk.S)

        self.root.resizable(True, True)
        # self.root.geometry('1000x500')
        self.root.mainloop()

    def set_app_dict(self):
        """ will reset the app data dict, which has all of the GUI variables """
        self.app_data = {
            "names": [],
            "infills": [],
            "infill_variables": [],
            "materials": [],
            "thicknesses": [],
            "thickness_variables": [],
            "quantities": [],
            "quantities_variables": [],
            "mesh": [],
            "part_dims": [],
            "part_volume": [],
            "part_surface_area": [],
            "material_variables": [],
            "drop_down_variables": []
        }

    def price_sorter(self, build_dict, query_df):
        """ this function converts the build requirements per material to price per part"""
        build_df = pd.DataFrame(build_dict)
        n_parts = query_df.shape[0]

        query_df['part_unit_price'] = [0] * n_parts
        # query_df['part_dims'] = query_df['mesh'].apply(lambda x: find_mins_maxs(x)) # get the mesh rects for all parts

        for material in query_df['materials'].unique():
            parts_in_mat_df = query_df[
                query_df['materials'] == material]  # extract only parts in that material for the query df
            build_mat_df = build_df[build_df['material'] == material]  # extract relevant build info from the builds df

            # get the volume of the part given the relevant factors "thickness" and "infill" between 0 and 100
            parts_in_mat_df['part_total_vol'] = [hollow_estimate(v, s, t, i)
                                                 for v, s, t, i in
                                                 zip(parts_in_mat_df['part_volume'],
                                                     parts_in_mat_df['part_surface_area'],
                                                     parts_in_mat_df['thicknesses'],
                                                     parts_in_mat_df['infills'])]

            # calculate the total volume of all builds
            total_vol = sum(parts_in_mat_df['part_total_vol'] * list(map(int, parts_in_mat_df['quantities_variables'])))

            # given the volume of each part, calculate the contribution of that part towards the final price
            parts_in_mat_df['part_contrib_to_total_vol'] = [(part_vol * qty) / total_vol for part_vol, qty in
                                                            zip(parts_in_mat_df['part_total_vol'], list(
                                                                map(int, parts_in_mat_df['quantities_variables'])))]
            query_df.loc[query_df['material'] == material, 'part_total_price'] = parts_in_mat_df[
                                                                                     'part_contrib_to_total_vol'] * \
                                                                                 build_mat_df['total_price'].values

        return {x: str(round(price, 2)) for x, price in zip(range(n_parts), query_df['part_unit_price'])}

    def report_window(self, g):
        from stl import mesh

        report_window = tk.Toplevel(self.root, bg="white")

        report_window.iconbitmap("icon.ico")
        report_window.wm_title("REPORT WINDOW")

        self.label_text = ["Name", "Material", "Quantity", "Unit Price", "Total Price"]

        get_varflt = lambda df_col: [float(var.get()) for var in df_col]
        get_var = lambda df_col: [var.get() for var in df_col]

        # self.app_df['infills'] = get_var(self.app_df['infill_variables'])
        # self.app_df['infills'] = get_var(self.app_df['infill_variables'])

        self.app_data['infills']=get_varflt(self.app_data['infill_variables'])
        self.app_data['materials']=get_var(self.app_data['drop_down_variables'])
        self.app_data['thicknesses']=get_varflt(self.app_data['thickness_variables'])
        self.app_data['quantities']=get_varflt(self.app_data['quantities_variables'])

        self.app_df = pd.DataFrame(self.app_data)
        query_df = self.app_df[
            ['names', 'quantities_variables', 'drop_down_variables', 'infills', 'thicknesses', 'materials',
             'part_volume', 'part_dims', 'part_volume', 'part_surface_area']]
        price_info = price_by_material(query_df)
        final_total_prices = self.price_sorter(price_info, query_df)
        final_unit_prices = {num: str(float(unit_price) / list(map(int, query_df['quantities_variables']))[num])
                             for num, unit_price in final_total_prices.items()}
        self.app_data["copy_buttons"] = [tk.StringVar(self.root) for p in final_total_prices.items()]

        # for each file, make a report window with the relevant information
        for i in range(len(self.file_names)):
            total_price = tk.Label(report_window, text=final_total_prices[i], bg="white")
            total_price.grid(column=len(final_total_prices) + 1, row=i + 1)

            unit_price = tk.Label(report_window, text=final_unit_prices[i], bg="white")
            unit_price.grid(column=len(final_total_prices) + 1, row=i + 1)

            # copy_buttons.append(tk.StringVar(self.root))

        # def clipboard(index):
        #     """ Simple function to copy text to the clipboard for easy reuse """
        #     clip = tk.Tk()
        #     clip.clipboard_clear()
        #     clip.clipboard_append(copy_buttons[index])
        #     clip.destroy()

    def create_selection_window(self, g):

        """
        This function creates a new tkinter window which will allow the user to specify what parameters they would like for a given part
        The argument "g" is to work around a bug in tkinter
        """

        # self.name_labels = []

        # if not self.first_use:
        #     self.refresh(self.frame)
        #
        # else:
        self.frame = tk.Frame(self.root, bg="white")
        self.frame.grid(row=1, column=1)

        self.canvas = tk.Canvas(self.frame, bg="white", width=600)
        self.canvas.grid(rowspan=2, columnspan=2)

        self.new_window = tk.Frame(self.canvas, bg="white")
        self.scroll_bar = tk.Scrollbar(self.root, orient="vertical", command=self.canvas.yview)
        self.scroll_bar.grid(column=6, row=1, sticky="ns")
        self.canvas.create_window((0, 0), window=self.new_window, anchor='nw')
        self.canvas.grid()

        path = self.path_field.get()
        self.file_names = [file for file in os.listdir(path) if file.endswith('.stl')]

        # self.new_window.bind("<Configure>", self.AuxscrollFunction)

        label_text = ["Name", "Material", "Infill (%)", "Thickness (in)", "Quantity"]

        # self.first_use = False

        # self.scroll_bar.config(command=self.canvas.yview)
        # self.canvas['yscrollcommand'] = self.scroll_bar.set

        # get part info for everything that we can
        self.app_data['mesh'] = [mesh.Mesh.from_file(self.path_field.get() + "/" + file) for file in self.file_names]
        self.app_data['names'] = [file.rstrip('.stl') for file in self.file_names]
        self.app_data['part_dims'] = [find_mins_maxs(m) for m in self.app_data['mesh']]
        self.app_data['part_volume'] = [m.get_mass_properties()[0] for m in self.app_data['mesh']]
        self.app_data['part_surface_area'] = [m.areas.sum() for m in self.app_data['mesh']]

        # set up sting vars
        string_vars = lambda: [tk.StringVar(self.root) for _ in range(len(self.file_names))]
        self.app_data['name_labels'] = string_vars()
        self.app_data['infill_variables'] = string_vars()
        self.app_data['material_variables'] = string_vars()
        self.app_data['thickness_variables'] = string_vars()
        self.app_data['quantities_variables'] = string_vars()
        self.app_data['drop_down_variables'] = string_vars()

        materials = ("ASA", "PEEK", "PLA", "ABS", "Ultem 1010", "Ultem 9085", "Nylon 12", "Zytel", "PC-ABS")

        assign_pos = lambda col, tk_var_list, row_shift=1: [var.grid(column=col, row=i + row_shift) for i, var in
                                                            enumerate(tk_var_list)]
        entry_vars = lambda str_vars: [tk.Entry(self.new_window, text=var, width=5) for var in str_vars]
        get_entry = lambda str_vars: [var.get() for var in str_vars]
        copy_button_vars = lambda button_text, cpy_amt: [
            tk.Button(self.new_window, text=button_text, command=lambda: self.copy_parameters(x)) for x in
            range(cpy_amt)]
        optionmenu_vars = lambda drop_down_vars: [tk.OptionMenu(self.new_window, var, *materials) for var in
                                                  drop_down_vars]

        # bind_to_mouse = lambda button_vars: [var.bind("<Button-1>", self.copy_parameters) for var in button_vars]
        label_vars = lambda names: [tk.Label(self.new_window, text=name) for name in names]

        # create tk objects for all buttons/fields/entries
        assign_pos(0, label_vars(self.app_data['names']))
        assign_pos(1, optionmenu_vars(self.app_data['drop_down_variables']))
        assign_pos(2, entry_vars(self.app_data['infill_variables']))
        assign_pos(3, entry_vars(self.app_data['thickness_variables']))
        assign_pos(4, entry_vars(self.app_data['quantities_variables']))
        assign_pos(5, copy_button_vars('copy', len(self.app_data['quantities_variables'])))


        # retrieve values from stringvars
        self.app_data['infills'] = get_entry(self.app_data['infill_variables'])
        self.app_data['materials'] = get_entry(self.app_data['material_variables'])
        self.app_data['thicknesses'] = get_entry(self.app_data['thickness_variables'])
        self.app_data['quantities'] = get_entry(self.app_data['quantities_variables'])

        for i in range(len(self.file_names)):
            labels = []
            for j in range(0, len(label_text)):
                labels.append(tk.Label(self.new_window, text=label_text[j], font='Helvetica 18 bold', bg="white"))
                labels[j].grid(column=j, row=0, padx=5, pady=5)

            self.name = tk.Label(self.new_window, text=self.file_names[i].rstrip(".stl"), bg="white")
            # self.name_labels.append(self.name)
            self.new_window.update()

        self.create_report_button = tk.Button(self.root, text="GO", bg="green", fg="white", font='Helvetica 18 bold')
        self.create_report_button.bind("<Button-1>", self.report_window)
        self.create_report_button.grid(row=2, column=2, padx=5, pady=2)
        self.app_df = pd.DataFrame(self.app_data)

    def copy_parameters(self, index):
        self.new_window.forget()
        selected_material = self.app_data['drop_down_variables'][index].get()
        selected_infill = self.app_data['infill_variables'][index].get()
        selected_thickness = self.app_data['thickness_variables'][index].get()
        selected_quantity = self.app_data['quantities_variables'][index].get()

        set_var = lambda x, var_list: [var.set(x) for var in var_list]
        set_var(selected_material, self.app_data['drop_down_variables'])
        set_var(selected_infill, self.app_data['infill_variables'])
        set_var(selected_thickness, self.app_data['thickness_variables'])
        set_var(selected_quantity, self.app_data['quantities_variables'])

    def refresh(self, frame):
        """ This function will assign all of the vars for GUI elements to empty lists, effectively clearing them """
        self.canvas.grid_forget()
        self.canvas.destroy()
        self.new_window = tk.Canvas(self.frame, bg="white")
        self.set_app_dict()
        # self.set_query_dict()

    def AuxscrollFunction(self, g):
        """ If the window is larger than a hard coded size, scrolling will be enabled """

        # NB: You need to set a max size for frameTwo. Otherwise, it will grow as needed, and scrollbar do not act
        width = 0

        # for i in range(0, len(self.name_labels)):
        #     temp = self.name_labels[i].winfo_width()
        #     if temp > width:
        #         width = temp

        width += 100 * 7

        height = self.canvas.winfo_height() #self.name_labels[0].winfo_height() * len(self.file_names) + 100

        if height > 850:
            height = 850

        if width > 1350:
            width = 1400

        self.canvas.configure(scrollregion=self.canvas.bbox("all"), width=width,
                              height=height)


App()
