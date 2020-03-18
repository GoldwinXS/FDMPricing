import tkinter as tk
import os
from ProjectUtils import hollow_estimate, material_prices



class App:
    first_use = True

    def __init__(self):

        """ Main Application class """

        self.names = []
        self.infills = []
        self.infill_variables = []
        self.materials = []
        self.material_variables = []
        self.thicknesses = []
        self.thickness_variables = []
        self.quantities = []
        self.quantities_variables = []
        self.file_names = []
        # self.c = []
        self.drop_down_variables = []

        self.requests = [] # A list of lists which holds the information for one line

        self.root = tk.Tk()
        self.root.wm_title("FDM QUOTING SOFTWARE V 2.2.7")
        self.root.iconbitmap("icon.ico")

        # Submit button
        self.submit_button = tk.Button(self.root, text="Submit")
        self.submit_button.bind("<Button-1>", self.create_window)
        # self.submit_button.pack(side='left',expand=True)
        self.submit_button.grid(row=0, column=0, sticky=tk.E + tk.W)

        # Path Entry
        self.path_field = tk.Entry(self.root)
        # self.path_field.pack(side='right',expand=True)
        self.path_field.grid(row=0, column=1, sticky=tk.E+tk.W+tk.N+tk.S)
        self.root.resizable(True,True)
        self.root.mainloop()

    def price_sorter(self, list, request_list):


        final_prices = []
        mats, paths, qtys, infill, thick = [var[2] for var in request_list], [var[0] for var in
                                                                              request_list], [var[1] for var
                                                                                              in
                                                                                              request_list], [
                                               var[3] for var in request_list], [var[4] for var in
                                                                                 request_list]

        for var1 in range(0, len(mats)):
            for var2 in range(len(paths[var1])):
                final_prices.append(0)

        for i in range(len(mats)):

            material, price, total_vol = list[i]
            lower_case_list = [item.lower() for item in self.file_names]

            for j in range(0, len(paths[i])):
                number_of_parts = float(qtys[i][j])
                hollow_vol = hollow_estimate(paths[i][j], thick[i][j], infill[i][j])
                total_hollow_vol = hollow_vol * number_of_parts

                name = paths[i][j]

                left = name.rfind("/")
                right = name.rfind(".")
                pathless_name = name[left + 1:right].lower()

                relative_amt = total_hollow_vol / total_vol
                unit_price = (relative_amt * price) / number_of_parts

                if unit_price < 10:
                    unit_price = 10

                place = lower_case_list.index(pathless_name + ".stl")

                final_prices[place] = round(unit_price, 2)

        return final_prices

    def combiner(self, list_of_lists):
        mats = []
        materials = {}

        final_list = []

        for i in range(len(list_of_lists)):
            mats.append(list_of_lists[i][2])
            materials = list(set(mats))

        for j in range(0, len(materials)):

            paths = []
            qts = []
            thk = []
            infs = []
            mat = [materials[j]]
            temp_list = []

            for i in range(0, len(list_of_lists)):

                if list_of_lists[i][2] == materials[j]:
                    paths.append(list_of_lists[i][0])
                    qts.append(list_of_lists[i][1])
                    infs.append(list_of_lists[i][3])
                    thk.append(list_of_lists[i][4])

                    temp_list = [paths, qts, mat, infs, thk]

            final_list.append(temp_list)
        return final_list

    def report_window(self, g):

        report_window = tk.Toplevel(self.root, bg="white")

        report_window.iconbitmap("icon.ico")
        report_window.wm_title("REPORT WINDOW")
        materials = []
        quantities = []
        labels = []
        copy_buttons = []

        self.label_text = ["Name", "Material", "Quantity", "Unit Price"]

        for j in range(0, len(self.label_text)):
            labels.append(tk.Label(report_window, text=self.label_text[j], font='Helvetica 18 bold', bg="white"))
            labels[j].grid(column=j, row=0, padx=5, pady=5)

        self.requests = []

        for i in range(0, len(self.file_names)):
            name = tk.Label(report_window, text=self.file_names[i].rstrip(".stl"), bg="white")
            name.grid(column=0, row=i + 1, sticky=tk.W)

            materials.append(self.drop_down_variables[i].get())
            material = tk.Label(report_window, text=materials[i], bg="white")
            material.grid(column=1, row=i + 1)

            quantities.append(self.quantities_variables[i].get())
            quantity = tk.Label(report_window, text=quantities[i], bg="white")
            quantity.grid(column=2, row=i + 1)

            self.requests.append([self.path_field.get() + "/" + self.file_names[i], self.quantities_variables[i].get(),
                                  self.drop_down_variables[i].get(), self.infills[i].get(), self.thicknesses[i].get()])

            copy_button = tk.Button(report_window, text="Copy to Clipboard",
                                    command=lambda x=i: clipboard(x))
            copy_button.grid(column=4, row=i + 1, padx=5, pady=5)

        combined_request = self.combiner(self.requests)
        final_info = material_prices(combined_request)
        final_unit_prices = self.price_sorter(final_info, combined_request)

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
        This funciton creates a new tkinter window which will allow the user to specify what parameters they would like for a given part
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
        file_names = self.file_names = [file for file in os.listdir(path) if file.endswith('.stl')]

        self.new_window.bind("<Configure>", self.AuxscrollFunction)

        label_text = ["Name", "Material", "Infill (%)", "Thickness (in)", "Quantity"]

        self.first_use = False

        self.scroll_bar.config(command=self.canvas.yview)
        self.canvas['yscrollcommand'] = self.scroll_bar.set

        for index in range(0, len(file_names)):

            labels = []

            for j in range(0, len(label_text)):
                labels.append(tk.Label(self.new_window, text=label_text[j], font='Helvetica 18 bold', bg="white"))
                labels[j].grid(column=j, row=0, padx=5, pady=5)

            self.drop_down_variables.append(tk.StringVar(self.root))
            self.infill_variables.append(tk.StringVar(self.root))
            self.material_variables.append(tk.StringVar(self.root))
            self.thickness_variables.append(tk.StringVar(self.root))
            self.quantities_variables.append(tk.StringVar(self.root))

            self.name = tk.Label(self.new_window, text=file_names[index].rstrip(".stl"), bg="white")
            self.name_labels.append(self.name)
            self.new_window.update()

            self.infills.append(tk.Entry(self.new_window, textvariable=self.infill_variables[index]))
            self.thicknesses.append(tk.Entry(self.new_window, textvariable=self.thickness_variables[index]))
            self.materials.append(
                tk.OptionMenu(self.new_window, self.drop_down_variables[index], "ASA", "PEEK", "PLA", "ABS",
                              "Ultem 1010",
                              "Ultem 9085", "Nylon 12",
                              "Zytel", "PC-ABS"))
            self.quantities.append(tk.Entry(self.new_window, textvariable=self.quantities_variables[index]))
            self.copy_parameter = tk.Button(self.new_window, text="Copy Parameters",
                                            command=lambda x=index: copy_parameters(x))

            self.name.grid(column=0, row=index + 1, sticky=tk.W)
            self.materials[index].grid(column=1, row=index + 1)
            self.infills[index].grid(column=2, row=index + 1)
            self.thicknesses[index].grid(column=3, row=index + 1)
            self.quantities[index].grid(column=4, row=index + 1)
            self.copy_parameter.grid(column=5, row=index + 1, padx=5, pady=2)

        self.create_report_button = tk.Button(self.root, text="GO", bg="green", fg="white",
                                              font='Helvetica 18 bold')
        self.create_report_button.bind("<Button-1>", self.report_window)
        self.create_report_button.grid(row=2, column=2, padx=5, pady=2)

        def copy_parameters(index):
            self.new_window.forget()
            selected_material = self.drop_down_variables[index].get()
            selected_infill = self.infill_variables[index].get()
            selected_thickness = self.thickness_variables[index].get()
            selected_quantity = self.quantities_variables[index].get()

            for i in range(0, len(self.file_names)):
                self.drop_down_variables[i].set(selected_material)
                self.infill_variables[i].set(selected_infill)
                self.thickness_variables[i].set(selected_thickness)
                self.quantities_variables[i].set(selected_quantity)


    def refresh(self, frame):
        """ This function will assign all of the vars for GUI elements to empty lists, effectively clearing them """
        self.canvas.grid_forget()
        self.canvas.destroy()
        self.new_window = tk.Canvas(self.frame, bg="white")
        self.names = []
        self.infills = []
        self.infill_variables = []
        self.materials = []
        self.material_variables = []
        self.thicknesses = []
        self.thickness_variables = []
        self.quantities = []
        self.quantities_variables = []
        self.file_names = []
        self.drop_down_variables = []

        self.requests = []

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
