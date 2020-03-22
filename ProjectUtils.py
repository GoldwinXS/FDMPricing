import stl
import rectpack
from stl import mesh
import pandas as pd
import numpy as np
from tkinter import Canvas

max_prints = 100
number_of_printers = 1
machine_dimensions = 170.7165
material_data = pd.read_csv("matData.csv")
printer_data = pd.read_csv("printerData.csv")


# a subclass of Canvas for dealing with resizing of windows
# class ResizingCanvas(Canvas):
#     def __init__(self, parent, **kwargs):
#         Canvas.__init__(self, parent, **kwargs)
#         self.bind("<Configure>", self.on_resize)
#         self.height = self.winfo_reqheight()
#         self.width = self.winfo_reqwidth()
#
#     def on_resize(self, event):
#         # determine the ratio of old width/height to new width/height
#         wscale = float(event.width) / self.width
#         hscale = float(event.height) / self.height
#         self.width = event.width
#         self.height = event.height
#         # resize the canvas
#         self.config(width=self.width, height=self.height)
#         # rescale all the objects tagged with the "all" tag
#         self.scale("all", 0, 0, wscale, hscale)


def hollow_estimate(volume, surface_area, thickness, infill):
    """

    Given a path, and desired thickness/infill, this will estimate the hollowed volume of the mesh
    expects numbers in the range [0,100]

    """
    # volume, cog, inertia = mesh_obj.get_mass_properties()  # get info
    # surface = mesh_obj.areas.sum()  # get surface area

    # volume = volume[0]
    wall_volume_after_hollow = float(surface_area) * float(thickness)
    print(volume , wall_volume_after_hollow)
    empty_space_after_hollow = volume - wall_volume_after_hollow
    infill_amount = empty_space_after_hollow * (int(infill) / 100)

    hollowed_volume = wall_volume_after_hollow + infill_amount

    if empty_space_after_hollow < 0 or hollowed_volume > volume:
        hollowed_volume = volume

    return hollowed_volume


def find_mins_maxs(mesh_obj):
    """"""

    maxx = mesh_obj.x.max()
    minx = mesh_obj.x.min()
    maxy = mesh_obj.y.max()
    miny = mesh_obj.y.min()
    maxz = mesh_obj.z.max()
    minz = mesh_obj.z.min()

    boundingx = maxx - minx
    boundingy = maxy - miny
    boundingz = maxz - minz

    return boundingx, boundingy, boundingz


def convert_stringlist_to_intlist(sting_list):
    """ converts a list of strings to a list of ints"""
    assert len(sting_list) > 0, "Nothing in list to convert!"
    return list(map(int, sting_list))


def get_used_build_areas(packer):
    """simple function to return the number of builds actually used for a packer object"""
    for i in range(len(packer)):
        try:
            l = packer[i]
        except IndexError:
            return i
    return len(packer)


def pack_parts(query_df, printer_dims):
    """ will determine how many builds are required for each part"""

    heights = []
    packer = rectpack.newPacker()
    reassign_to_zero = lambda x: 0 if x == '' else (x)

    qty_list = [int(reassign_to_zero(qty.get())) for qty in query_df['quantities_variables']]

    for dims, qty in zip(query_df['part_dims'], qty_list):
        n_range = int(qty)
        xs, ys, zs = [dims[0]] * n_range, [dims[1]] * n_range, [dims[2]] * n_range
        heights = zs
        for x, y in zip(xs, ys):
            packer.add_rect(x, y)

    for printer_dim in printer_dims:
        packer.add_bin(printer_dim[0], printer_dim[1])

    packer.pack()

    return packer, heights


def calc_build_info(query_df):
    """ will determine how many builds are required for each material and part """
    # TODO: load machine dimensions from file...
    printer_dims = [(machine_dimensions, machine_dimensions)] * max_prints
    # df = pd.DataFrame(query_dict)
    # packed_parts,heights = pack_parts(df,printer_dims)

    builds = {"materials": [],
              "volume": [],
              "hollowvolume_ci": [],
              "height": [],
              "infill": []}

    # for each unique material:
    for material in query_df['materials'].unique():
        parts_in_material = query_df[query_df['materials'] == material]

        packed_parts, height = pack_parts(parts_in_material, printer_dims)
        # n_builds = get_used_build_areas(packed_parts)/number_of_printers
        # convert_to_

        hollowed_volumes = np.array(
            [hollow_estimate(v, s, t, i) for v, s, t, i in zip(parts_in_material['part_volume'].values.tolist(),
                                                               parts_in_material['part_surface_area'].values.tolist(),
                                                               parts_in_material['thicknesses'].values.tolist(),
                                                               parts_in_material['infills'].values.tolist())])


        part_volumes = np.array([var for var in parts_in_material['part_volume'].values])[...,0]
        part_quantities = np.array([int(var.get()) for var in parts_in_material['quantities_variables'].values.tolist()])
        total_volume = sum(part_volumes * part_quantities)

        infill = parts_in_material['infills'].mean()

        builds['materials'].append(material)
        builds['volume'].append(total_volume)
        builds['hollowvolume_ci'].append(hollowed_volumes.sum())
        builds['height'].append(max(height))
        builds['infill'].append(infill)

    return builds


def calc_build_material_costs(builds_dict):
    df = pd.DataFrame(builds_dict)

    build_result_dict = {'material': [],
                         'total_price': [],
                         'total_volume': []}

    for i, build in df.iterrows():
        print(build)
        total_mat_price = mult_estimator(material=build['materials'],
                                         volume=build['volume'],
                                         hollowvolume_ci=build['hollowvolume_ci'],
                                         height=build['height'],
                                         infill=build['infill'])

        total_vol = build['volume'] - build['hollowvolume_ci'] + build['infill']
        build_result_dict['material'].append(build['materials'])
        build_result_dict['total_price'].append(total_mat_price)
        build_result_dict['total_volume'].append(total_vol)

    return build_result_dict


def price_by_material(query_df):
    # for key,item in query_dict.items():
    builds = calc_build_info(query_df)
    return calc_build_material_costs(builds)


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


def get_material_data_from_df(material_name, key):
    """ a function that simply retrieves information for a given material """
    return material_data[material_data['name'] == material_name][key].values[0]


def mult_estimator(material, volume, hollowvolume_ci, height, infill):
    print_time = time_estimate(infill, volume, height)

    material_density = get_material_data_from_df(material, 'g/cc')
    material_cost = get_material_data_from_df(material, '$/gk')
    material_prep_time = get_material_data_from_df(material, 'preptime')

    energy_cost = (printer_data.iloc[0, 3] * printer_data.iloc[0, 4]) / 1000

    amortizement_hourly = printer_data.iloc[0, 7] * 52
    amortizement_cost = (0.33 * printer_data.iloc[0, 5] + material_prep_time) / amortizement_hourly

    other_costs = printer_data.iloc[0, 0] / amortizement_hourly

    total_volume = hollowvolume_ci * 16.3871

    total_material_cost = ((total_volume * int(material_density)) / 1000) * float(material_cost)

    production_cost = (print_time * (energy_cost + amortizement_cost + other_costs)) + total_material_cost

    final_price = (production_cost * printer_data.iloc[0, 6]) + (printer_data.iloc[0, 1] * printer_data.iloc[0, 2])

    # print(other_costs)
    # print(energy_cost)
    # print(amortizement_cost)
    # print(total_material_cost)
    # print(production_cost)
    # print(final_price)
    # print(print_time)

    return final_price
