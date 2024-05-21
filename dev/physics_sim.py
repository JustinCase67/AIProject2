import numpy as np
import math
from typing import Tuple


class PhysSim:
    FloatTuple = Tuple[float, float]

    @staticmethod
    def vector_angle(x: float, y: float):
        return math.atan2(y, x)

    @staticmethod
    def time_at_yf(viy: float, a: float, yi: float, yf: float):
        vf2 = viy ** 2 + 2 * a * (yf - yi)
        return (-viy - math.sqrt(vf2)) / a

    @staticmethod
    def position(pi: float, vi: float, a: float, t: float):
        return pi + (vi * t) + (0.5 * a * (t ** 2))

    @staticmethod
    def coordo_final_2d(vi: float, angle: float, temps: float, a: float, pix: float, piy: float):
        angle_rad = math.radians(angle)
        vix = vi * math.cos(angle_rad)
        viy = vi * math.sin(angle_rad)
        return PhysSim.position(pix, vix, 0, temps), PhysSim.position(piy, viy, a, temps)

    @staticmethod
    def coordo_final_2d_speed_separated(vix: float, viy: float, temps: float, a: float, pix: float, piy: float):
        return PhysSim.position(pix, vix, 0, temps), PhysSim.position(piy, viy, a, temps)

    @staticmethod
    def final_speed_1d(vi: float, a: float, t: float):
        return vi + a * t

    @staticmethod
    def final_speed_2d(vi: float, a: float, t: float, angle: float):
        angle_rad = math.radians(angle)
        vix = vi * math.cos(angle_rad)
        viy = vi * math.sin(angle_rad)
        return PhysSim.final_speed_1d(vix, 0, t), PhysSim.final_speed_1d(viy, a, t)

    @staticmethod
    def split_impulsion_finale(vi: FloatTuple, split_force: float):
        vix, viy = vi
        c = ((vix ** 2) + (viy ** 2)) ** 0.5

        ux = vix / c
        uy = viy / c

        ex = ux * split_force
        ey = uy * split_force

        vfx = vix + ex
        vfy = viy + ey

        return vfx, vfy

    @staticmethod
    def v_split_new_projectiles(split_angle: float, vi: FloatTuple, number_projectiles: int = 3):
        #number of projectiles can be used to expend the project
        vix, viy = vi
        c = ((vix ** 2) + (viy ** 2)) ** 0.5
        angle_origin_vector = PhysSim.vector_angle(vix, viy)
        split_angle_rad = math.radians(split_angle)

        mvix = c * math.cos(split_angle_rad + angle_origin_vector)
        mviy = c * math.sin(split_angle_rad + angle_origin_vector)

        m2vix = c * math.cos(angle_origin_vector - split_angle_rad)
        m2viy = c * math.sin(angle_origin_vector - split_angle_rad)

        return (vix, viy), (mvix, mviy), (m2vix, m2viy)

    @staticmethod
    def get_arc_points(coordo_ini: FloatTuple, coordo_final: FloatTuple, speed_ini_x: float, speed_ini_y: float,
                       g: float, final_time: float, iteration_time: float):
        nb_iteration = (math.floor(math.floor(final_time) / iteration_time)) + 2
        arc_coordinates = np.zeros(nb_iteration, dtype=object)
        arc_coordinates[0] = coordo_ini
        arc_coordinates[-1] = coordo_final
        for i in range(1, nb_iteration - 1):
            arc_coordinates[i] = PhysSim.coordo_final_2d_speed_separated(speed_ini_x, speed_ini_y, i * iteration_time,
                                                                         g, coordo_ini[0], coordo_ini[1])

        return arc_coordinates

    @staticmethod
    def get_new_projectiles_points(nb_projectiles: int, coordo_init: FloatTuple, tuples_coordo_final, tuples_speeds, g: float,
                                final_time, iteration_time: float):
        projectiles_points_array = []
        for i in range(nb_projectiles):
            points = PhysSim.get_arc_points(coordo_init, tuples_coordo_final[i], tuples_speeds[i][0],
                                            tuples_speeds[i][1], g, final_time[i], iteration_time)
            projectiles_points_array.append(points)
        return tuple(projectiles_points_array)

    @staticmethod
    def get_final_coordinates_projectile(all_object_speeds, g: float, coordo_ini: FloatTuple, final_pos_y: float):
        all_coordo = []
        time = []
        for object in all_object_speeds:
            time_at_y0 = PhysSim.time_at_yf(object[1], g, coordo_ini[1], final_pos_y)
            time.append(time_at_y0)
            pos_x = (PhysSim.position(coordo_ini[0], object[0], 0, time_at_y0))
            pos = (pos_x, final_pos_y)
            all_coordo.append(pos)

        return tuple(time), tuple(all_coordo)

    @staticmethod
    def get_all_points(coordo_init: FloatTuple, coordo_cluster: FloatTuple, initial_speed_x: float,
                       initial_speed_y: float, g: float, time_to_cluster: float, projectiles_final_time,
                       projectiles_speed_ini, projectiles_final_coordo, iteration_time: float, nb_projectiles: int = 3):

        inital_arc_coordinates = PhysSim.get_arc_points(coordo_init, coordo_cluster, initial_speed_x, initial_speed_y,
                                                        g, time_to_cluster, iteration_time)

        objects_arc_coordinates = PhysSim.get_new_projectiles_points(nb_projectiles, coordo_cluster, projectiles_final_coordo,
                                                                  projectiles_speed_ini, g, projectiles_final_time,
                                                                  iteration_time)

        return inital_arc_coordinates, objects_arc_coordinates

    @staticmethod
    def get_final_coordinates_from_start_data(initial_speed: float, time_to_split: float, coordo_init: FloatTuple,
                                              initial_angle: float, g, split_force: float, split_angle: float,
                                              nb_object_split: int, final_pos_y: float):

        coordo_at_split = PhysSim.coordo_final_2d(initial_speed, initial_angle, time_to_split, g, coordo_init[0],
                                                  coordo_init[1])
        speed_at_split = PhysSim.final_speed_2d(initial_speed, g, time_to_split, initial_angle)
        speed_ref_after_split = PhysSim.split_impulsion_finale(speed_at_split, split_force)
        speed_all_objects_after_split = PhysSim.v_split_new_projectiles(split_angle, speed_ref_after_split)

        return PhysSim.get_final_coordinates_projectile(speed_all_objects_after_split, g, coordo_at_split, final_pos_y)

    @staticmethod
    def get_all_points_from_start_data(initial_speed: float, time_to_split: float,
                                       coordo_init: FloatTuple, initial_angle: float, g: float, split_force: float,
                                       split_angle: float, nb_object_split: int, final_pos_y: float,
                                       iteration_time: float):

        coordo_at_split = PhysSim.coordo_final_2d(initial_speed, initial_angle, time_to_split, g, coordo_init[0],
                                                  coordo_init[1])
        speed_at_split = PhysSim.final_speed_2d(initial_speed, g, time_to_split, initial_angle)
        speed_ref_after_split = PhysSim.split_impulsion_finale(speed_at_split, split_force)
        speed_all_objects_after_split = PhysSim.v_split_new_projectiles(split_angle, speed_ref_after_split)

        final_objects_time_coordinates = PhysSim.get_final_coordinates_projectile(speed_all_objects_after_split, g,
                                                                               coordo_at_split, final_pos_y)

        angle_rad = math.radians(initial_angle)
        speed_ini_x = initial_speed * math.cos(angle_rad)
        speed_ini_y = initial_speed * math.sin(angle_rad)

        return PhysSim.get_all_points(coordo_init, coordo_at_split, speed_ini_x, speed_ini_y, g, time_to_split,
                                      final_objects_time_coordinates[0], speed_all_objects_after_split,
                                      final_objects_time_coordinates[1], iteration_time, nb_object_split)

