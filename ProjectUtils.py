import stl
import rectpack
from stl import mesh
import pandas as pd
from tkinter import Canvas


# a subclass of Canvas for dealing with resizing of windows
class ResizingCanvas(Canvas):
    def __init__(self,parent,**kwargs):
        Canvas.__init__(self,parent,**kwargs)
        self.bind("<Configure>", self.on_resize)
        self.height = self.winfo_reqheight()
        self.width = self.winfo_reqwidth()

    def on_resize(self,event):
        # determine the ratio of old width/height to new width/height
        wscale = float(event.width)/self.width
        hscale = float(event.height)/self.height
        self.width = event.width
        self.height = event.height
        # resize the canvas
        self.config(width=self.width, height=self.height)
        # rescale all the objects tagged with the "all" tag
        self.scale("all",0,0,wscale,hscale)

def hollow_estimate(stl_path, thickness, infill):
    """ Given a path, and desired thickness/infill, this will estimate the hollowed volume of the mesh """
    file_mesh = mesh.Mesh.from_file(stl_path) # load mesh
    volume, cog, inertia = file_mesh.get_mass_properties() # get info
    surface = file_mesh.areas.sum() # get surface area

    wall_volume_after_hollow = float(surface) * float(thickness)
    empty_space_after_hollow = volume - wall_volume_after_hollow
    infill_amount = empty_space_after_hollow * (int(infill) / 100)

    hollowed_volume = wall_volume_after_hollow + infill_amount

    if empty_space_after_hollow < 0 or hollowed_volume>volume:
        hollowed_volume = volume

    return hollowed_volume


def find_mins_maxs(path):
    minx = maxx = miny = maxy = minz = maxz = None
    obj = mesh.Mesh.from_file(path)

    for p in obj.points:
        # p contains (x, y, z)
        if minx is None:
            minx = p[stl.Dimension.X]
            maxx = p[stl.Dimension.X]
            miny = p[stl.Dimension.Y]
            maxy = p[stl.Dimension.Y]
            minz = p[stl.Dimension.Z]
            maxz = p[stl.Dimension.Z]
        else:
            maxx = max(p[stl.Dimension.X], maxx)
            minx = min(p[stl.Dimension.X], minx)
            maxy = max(p[stl.Dimension.Y], maxy)
            miny = min(p[stl.Dimension.Y], miny)
            maxz = max(p[stl.Dimension.Z], maxz)
            minz = min(p[stl.Dimension.Z], minz)

    boundingx = maxx - minx
    boundingy = maxy - miny
    boundingz = maxz - minz

    return boundingx, boundingy, boundingz




# LISTS WILL BE IN THE FORM [['paths'], ['quantities'], ['material'], ['infills'], ['thicknesses']]

machine_dimensions = 170.7165


def manager(list_of_lists):
    rectangles = []
    # answer = []
    printer_dims = [(machine_dimensions, machine_dimensions), (machine_dimensions, machine_dimensions)]
    infill_average = 0
    infill_sum = 0

    req = list_of_lists  # list_of_lists
    for number_of_parts in range(0, len(req[0])):

        for quantity_numbers in range(0, int(req[1][number_of_parts])):
            # get xyz of parts
            dims = find_mins_maxs(req[0][number_of_parts])

            # find optimal orientation of part. For now it's just the largest dimension. Spit out height and x_y dimensions
            height = max(dims)  # RIGHT HERE is where the orientator functions would take over
            temp = list(dims)
            temp.remove(height)
            temp = list(temp)
            x, y = temp[0], temp[1]
            infill_sum += int(req[3][number_of_parts])

            rectangles.append([x, y, req[0][number_of_parts], req[4][number_of_parts],
                               req[3][number_of_parts]])  # [x, y, file_path, thickness, infill]

    infill_average = infill_sum / len(rectangles)

    # print(len(rectangles))

    def number_of_builds(list_of_rectangles):
        # print(list_of_rectangles)
        builds = []
        packer = rectpack.newPacker()
        ans = 0
        temp = []
        temp_count = 0
        max_dims, max_heights = [], []
        for b in range(0, 2):
            packer.add_bin(*printer_dims[b])
            # print(printer_dims[b])
        max_x, max_y = 0, 0

        for i in range(0, len(list_of_rectangles)):
            temp.append(list_of_rectangles[i])
            packer.add_rect(list_of_rectangles[i][0], list_of_rectangles[i][1])
            packer.pack()



            temp_count += 1
            if len(packer) > 1:
                ans += 1

                volume = 0
                hollow_volume = 0

                max_heights.append([height])

                for j in range(0, temp_count):
                    hollow_volume += hollow_estimate(temp[j][2], temp[j][3], temp[j][4])
                    volume += mesh.Mesh.from_file(temp[j][2]).get_mass_properties()[0]
                    # print(volume)

                builds.append([req[2][0], volume, hollow_volume, height, infill_average])
                # material, volume, hollow_volume, height, temp[temp_count][3], temp[temp_count][4]
                temp.clear()
                temp_count = 0

                packer = rectpack.newPacker()
                for b in range(0, 2):
                    packer.add_bin(*printer_dims[b])

        if len(packer) == 1:
            volume = 0
            hollow_volume = 0
            for j in range(0, len(temp)):
                hollow_volume += hollow_estimate(temp[j][2], temp[j][3], temp[j][4])
                volume += mesh.Mesh.from_file(temp[j][2]).get_mass_properties()[0]

            builds.append([req[2][0], volume, hollow_volume, height, infill_average])

        ans += 1

        return builds

    a = number_of_builds(rectangles)

    return a


def price_combiner(list_of_builds):
    total_mat_price = 0
    volume = 0

    for i in range(0, len(list_of_builds)):
        total_mat_price += mult_estimator(*list_of_builds[i])
        volume += list_of_builds[i][1]

    return (list_of_builds[0][0], total_mat_price, volume)


def material_prices(list_of_lists):
    final_list = []

    for i in range(0, len(list_of_lists)):
        a = manager(list_of_lists[i])
        b = price_combiner(a)
        final_list.append(b)
    return final_list


def time_estimate(infill,volume,height):
    infill = int(infill)

        #   NOTE: EXPERIMENTATION MUST BE DONE TO FIND GOOD VALUES   #

    intermittent_factor = 16.39505801

    coeff_A = 0
    coeff_B = 2549.326795
    coeff_C = 123.6015845
    coeff_D = 2549.326795
    coeff_E = 16.39505801

    answer_sec = coeff_A+(coeff_B*volume)+(coeff_C*height)+(coeff_D*(infill/100)*volume)+coeff_E*height*intermittent_factor

    answer_hrs = (answer_sec/60)/60


    return answer_hrs



material_data = pd.read_csv("matData.csv")
printer_data = pd.read_csv("printerData.csv")

class Material:
    def __init__(self, name, price, density):
        self.name = name
        self.price = price
        self.density = density


materials = []

material_name = []
prices = []
densities = []
prep_time = []

for i in range(0, material_data.shape[0]):
    # materials.append(Material(matdata.iloc[i, 0], matdata.iloc[i, 1], matdata.iloc[i, 2]))
    material_name.append(material_data.iloc[i, 0])
    prices.append(material_data.iloc[i, 1])
    densities.append(material_data.iloc[i, 2])
    prep_time.append(material_data.iloc[i, 3])


def mult_estimator(material, volume, hollowvolume_ci, height, infill):

    print_time = time_estimate(infill, volume, height)

    index = material_name.index(material)

    material_density = densities[index]
    material_cost = prices[index]

    energy_cost = (printer_data.iloc[0, 3] * printer_data.iloc[0, 4]) / 1000

    amortizement_hourly = printer_data.iloc[0, 7] * 52
    amortizement_cost = (0.33 * printer_data.iloc[0, 5] + prep_time[index]) / amortizement_hourly

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
