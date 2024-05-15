import numpy as np
import math


class phys_sim:

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
        return phys_sim.position(pix, vix, 0, temps), phys_sim.position(piy, viy, g, temps)

    @staticmethod
    def coordo_final_2d_speed_separated(vix, viy, temps,g , pix, piy):
        return phys_sim.position(pix, vix, 0, temps), phys_sim.position(piy, viy, g, temps)

    @staticmethod
    def final_speed_1d(vi, a, t):
        return vi + a * t

    @staticmethod
    def final_speed_2d(vi, a, t, angle):
        angle_rad = math.radians(angle)
        vix = vi * math.cos(angle_rad)
        viy = vi * math.sin(angle_rad)
        return phys_sim.final_speed_1d(vix, 0, t), phys_sim.final_speed_1d(viy, a, t)

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
        angle_origin_vector = phys_sim.vector_angle(vix, viy)
        explo_angle_rad = math.radians(explo_angle)

        mvix = c * math.cos(explo_angle_rad + angle_origin_vector)
        mviy = c * math.sin(explo_angle_rad + angle_origin_vector)


        m2vix = c * math.cos(angle_origin_vector - explo_angle_rad)
        m2viy = c * math.sin(angle_origin_vector - explo_angle_rad)

        print("angle of speed vector : ", phys_sim.vector_angle(vix, viy))

        return (vix, viy), (mvix, mviy), (m2vix, m2viy)



    @staticmethod
    def get_arc_points(coordo_ini, coordo_final, speed_ini_x, speed_ini_y, g, final_time, iteration_time):
        nb_iteration = (math.floor(math.floor(final_time)/iteration_time)) + 2
        arc_coordinates = np.zeros(nb_iteration, dtype=object)
        arc_coordinates[0] = coordo_ini
        arc_coordinates[-1] = coordo_final
        for i in range(1, nb_iteration - 1):
            arc_coordinates[i] = phys_sim.coordo_final_2d_speed_separated(speed_ini_x, speed_ini_y, i*iteration_time,g, coordo_ini[0], coordo_ini[1])

        return arc_coordinates

    @staticmethod
    def get_new_missiles_points(nb_missiles, coordo_init, tuples_coordo_final, tuples_speeds, g, final_time, iteration_time):
        missiles_points_array = []
        for i in range(nb_missiles):
            points = phys_sim.get_arc_points(coordo_init,tuples_coordo_final[i],tuples_speeds[i][0],tuples_speeds[i][1],g, final_time[i], iteration_time)
            missiles_points_array.append(points)
        return tuple(missiles_points_array)


    @staticmethod
    def get_final_coordinates_missile(all_object_speeds, g, coordo_ini, final_pos_y):
        all_coordo = []
        time = []
        for object in all_object_speeds:
            time_at_y0 = phys_sim.time_at_yf(object[1], g, coordo_ini[1], final_pos_y)
            time.append(time_at_y0)
            pos_x = (phys_sim.position(coordo_ini[0], object[0], 0, time_at_y0))
            pos = (pos_x,final_pos_y )
            all_coordo.append(pos)

        return tuple(time), tuple(all_coordo)

    @staticmethod
    def get_all_points(coordo_init, coordo_cluster, initial_speed_x, initial_speed_y, g, time_to_cluster, missiles_final_time,
                       missiles_speed_ini, missiles_final_coordo,iteration_time,nb_missiles ):

        return phys_sim.get_arc_points(coordo_init,coordo_cluster,initial_speed_x, initial_speed_y,g,time_to_cluster,iteration_time),\
               phys_sim.get_new_missiles_points(nb_missiles, coordo_cluster, missiles_final_coordo, missiles_speed_ini,g,missiles_final_time,iteration_time)



vi = 10
g = 9.81
t = 2.3
coordo_init = (0,50)

angle = 0
exploF = 1.5
exploAngle = 10
print("time at 0", phys_sim.time_at_yf(0, g, coordo_init[1], 0))
final_speed = phys_sim.final_speed_2d(vi, g, t, angle)
print("final speed : ", final_speed)
coordo = phys_sim.coordo_final_2d(vi, angle, t, g, coordo_init[0], coordo_init[1])
print("coordo :", coordo)
explo_final = phys_sim.explo_impulsion_finale(coordo, final_speed, exploF)
print("explo final vitesse: ", explo_final)
new_missiles = phys_sim.v_explo_new_missiles(0, exploAngle, explo_final)
print("new missiles vitesse: ", new_missiles)




arc_coordinates_1 = phys_sim.get_arc_points(coordo_init,coordo,10,0, g, t, 1)
print("first arc : ", arc_coordinates_1)

final_time_coordo_x = phys_sim.get_final_coordinates_missile(new_missiles, g, coordo, 0)
print("missiles arc final", final_time_coordo_x[1])

all_missiles_points = phys_sim.get_new_missiles_points(3, coordo, final_time_coordo_x[1], new_missiles,g,final_time_coordo_x[0],1)
print(all_missiles_points)




all_points = phys_sim.get_all_points(coordo_init,coordo,10,0,g,t, final_time_coordo_x[0],new_missiles,final_time_coordo_x[1],1,3)
print(all_points)


#print(arc_coordinates)
#arc_coordinates[0] = (1,56)
#print(arc_coordinates)





