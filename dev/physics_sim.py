import numpy as np
import math


class Phys_sim:

    @staticmethod
    def vector_angle(x, y):
        return math.atan(y / x)

    @staticmethod
    def time_at_yf(viy, g, yi, yf):
        root = ((viy ** 2) + (2 * g * (yi - yf))) ** 0.5
        return (viy + root) / g

    @staticmethod
    def position(pi, vi, g, t):
        return pi + (vi * t - (1 / 2) * g * (t ** 2))

    @staticmethod
    def coordo_final_2d(vi, angle, temps, g, pix, piy):
        angle_rad = math.radians(angle)
        vix = vi * math.cos(angle_rad)
        viy = vi * math.sin(angle_rad)
        return Phys_sim.position(pix, vix, 0, temps), Phys_sim.position(piy, viy, g, temps)

    @staticmethod
    def coordo_final_2d_speed_separated(vix, viy, temps,g , pix, piy):
        return Phys_sim.position(pix, vix, 0, temps), Phys_sim.position(piy, viy, g, temps)

    @staticmethod
    def final_speed_1d(vi, a, t):
        return vi + a * t

    @staticmethod
    def final_speed_2d(vi, a, t, angle):
        angle_rad = math.radians(angle)
        vix = vi * math.cos(angle_rad)
        viy = vi * math.sin(angle_rad)
        return Phys_sim.final_speed_1d(vix, 0, t), Phys_sim.final_speed_1d(viy, a, t)

    @staticmethod
    def explo_impulsion_finale(coordo, vi, explo_force):
        x, y = coordo
        vix, viy = vi
        c = (vix ** 2 + viy ** 2) ** 0.5

        ux = vix / c
        uy = viy / c

        ex = ux * explo_force
        ey = uy * explo_force

        vfx = vix + ex
        vfy = viy + ey
        return vfx, vfy

    @staticmethod
    def v_explo_new_missiles(number_missiles, explo_angle, vi):
        vix, viy = vi
        c = (vix ** 2 + viy ** 2) ** 0.5
        angle_origin_vector = Phys_sim.vector_angle(vix, viy)
        explo_angle_rad = math.radians(explo_angle)

        mvix = c * math.cos(explo_angle_rad + angle_origin_vector)
        mviy = c * math.sin(explo_angle_rad + angle_origin_vector)


        m2vix = c * math.cos(angle_origin_vector - explo_angle_rad)
        m2viy = c * math.sin(angle_origin_vector - explo_angle_rad)


        return (vix, viy), (mvix, mviy), (m2vix, m2viy)



    @staticmethod
    def get_arc_points(coordo_ini, coordo_final, speed_ini_x, speed_ini_y, g, final_time, iteration_time):
        nb_iteration = (math.floor(math.floor(final_time)/iteration_time)) + 2
        arc_coordinates = np.zeros(nb_iteration, dtype=object)
        arc_coordinates[0] = coordo_ini
        arc_coordinates[-1] = coordo_final
        for i in range(1, nb_iteration - 1):
            arc_coordinates[i] = Phys_sim.coordo_final_2d_speed_separated(speed_ini_x, speed_ini_y, i * iteration_time, g, coordo_ini[0], coordo_ini[1])

        return arc_coordinates

    @staticmethod
    def get_new_missiles_points(nb_missiles, coordo_init, tuples_coordo_final, tuples_speeds, g, final_time, iteration_time):
        missiles_points_array = []
        for i in range(nb_missiles):
            points = Phys_sim.get_arc_points(coordo_init, tuples_coordo_final[i], tuples_speeds[i][0], tuples_speeds[i][1], g, final_time[i], iteration_time)
            missiles_points_array.append(points)
        return tuple(missiles_points_array)


    @staticmethod
    def get_final_coordinates_missile(all_object_speeds, g, coordo_ini, final_pos_y):
        all_coordo = []
        time = []
        for object in all_object_speeds:
            time_at_y0 = Phys_sim.time_at_yf(object[1], g, coordo_ini[1], final_pos_y)
            time.append(time_at_y0)
            pos_x = (Phys_sim.position(coordo_ini[0], object[0], 0, time_at_y0))
            pos = (pos_x,final_pos_y )
            all_coordo.append(pos)

        return tuple(time), tuple(all_coordo)

    @staticmethod
    def get_all_points(coordo_init, coordo_cluster, initial_speed_x, initial_speed_y, g, time_to_cluster, missiles_final_time, missiles_speed_ini, missiles_final_coordo,iteration_time,nb_missiles ):

        inital_arc_coordinates = Phys_sim.get_arc_points(coordo_init, coordo_cluster, initial_speed_x, initial_speed_y, g, time_to_cluster, iteration_time)
        objects_arc_coordinates = Phys_sim.get_new_missiles_points(nb_missiles, coordo_cluster, missiles_final_coordo, missiles_speed_ini, g, missiles_final_time, iteration_time)

        return inital_arc_coordinates, objects_arc_coordinates


    @staticmethod
    def get_final_coordinates_from_start_data(initial_speed, time_to_split, coordo_init, initial_angle, g,  split_force, split_angle, nb_object_split, final_pos_y):

        coordo_at_split = Phys_sim.coordo_final_2d(initial_speed, initial_angle, time_to_split, g, coordo_init[0], coordo_init[1])
        speed_at_split = Phys_sim.final_speed_2d(initial_speed, g, time_to_split, initial_angle)
        speed_ref_after_split = Phys_sim.explo_impulsion_finale(coordo_at_split, speed_at_split, split_force)
        speed_all_objects_after_split = Phys_sim.v_explo_new_missiles(nb_object_split, split_angle, speed_ref_after_split)

        return Phys_sim.get_final_coordinates_missile(speed_all_objects_after_split, g, coordo_at_split, final_pos_y)

    @staticmethod
    def get_all_points_from_start_data(initial_speed, time_to_split, coordo_init, initial_angle, g,  split_force, split_angle, nb_object_split, final_pos_y, iteration_time):

        coordo_at_split = Phys_sim.coordo_final_2d(initial_speed, initial_angle, time_to_split, g, coordo_init[0], coordo_init[1])
        speed_at_split = Phys_sim.final_speed_2d(initial_speed, g, time_to_split, initial_angle)
        speed_ref_after_split = Phys_sim.explo_impulsion_finale(coordo_at_split, speed_at_split, split_force)
        speed_all_objects_after_split = Phys_sim.v_explo_new_missiles(nb_object_split, split_angle, speed_ref_after_split)

        final_objects_time_coordinates = Phys_sim.get_final_coordinates_missile(speed_all_objects_after_split, g, coordo_at_split, final_pos_y)

        angle_rad = math.radians(initial_angle)
        speed_ini_x = initial_speed * math.cos(angle_rad)
        speed_ini_y = initial_speed * math.sin(angle_rad)

        return Phys_sim.get_all_points(coordo_init, coordo_at_split, speed_ini_x, speed_ini_y, g, time_to_split, final_objects_time_coordinates[0],speed_all_objects_after_split, final_objects_time_coordinates[1], iteration_time, nb_object_split)





def main():
    vi = 10
    g = 9.81
    time_to_split = 2.3
    coordo_init = (0,50)
    final_pos_y = 0
    initial_angle = 0
    split_force = 1.5
    split_angle = 10
    nb_splitting_objects = 3
    iteration_time_s = 1

    final_time_coordo_func = Phys_sim.get_final_coordinates_from_start_data(vi,time_to_split,coordo_init,initial_angle,g,split_force,split_angle,nb_splitting_objects,final_pos_y)
    print("final_time_coordo_func: ", final_time_coordo_func)

    all_points_func = Phys_sim.get_all_points_from_start_data(vi,time_to_split,coordo_init, initial_angle, g, split_force, split_angle, nb_splitting_objects,final_pos_y,iteration_time_s )
    print("all_points", all_points_func)
    for i in range(5000):
        final_time_coordo_func = Phys_sim.get_final_coordinates_from_start_data(vi, time_to_split, coordo_init,
                                                                                initial_angle, g, split_force, split_angle,
                                                                                nb_splitting_objects, final_pos_y)

        all_points_func = Phys_sim.get_all_points_from_start_data(vi, time_to_split, coordo_init, initial_angle, g,
                                                                  split_force, split_angle, nb_splitting_objects,
                                                                  final_pos_y, iteration_time_s)

    print("done")



if __name__ == '__main__':
    main()




