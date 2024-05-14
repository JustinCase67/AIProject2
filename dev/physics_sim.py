import numpy as np
import math

class phys_sim:
    @staticmethod
    def time_at_yf(viy,g, yi, yf):
        root = ((viy**2) + (2 * g * (yi - yf) ))**0.5

        return (viy + root ) / g

    @staticmethod
    def position(pi, vi, g, t):
        return pi + (vi * t - (1 / 2) * g * (t ** 2))

    @staticmethod
    def coordo_explo(vi, angle, temps, g, pix, piy):
        vix = vi * math.cos(math.radians(angle))
        viy = vi * math.sin(math.radians(angle))
        return phys_sim.position(pix, vix, 0, temps), phys_sim.position(piy, viy, g, temps)

    @staticmethod
    def final_speed_1d(vi, a, t):
        return vi + a * t

    @staticmethod
    def final_speed_2d(vi, a, t, angle):
        vix = vi * math.cos(math.radians(angle))
        viy = vi * math.sin(math.radians(angle))
        return phys_sim.final_speed_1d(vix,0,t), phys_sim.final_speed_1d(viy,a,t)

    @staticmethod
    def explo_impulsion_finale(coordo, vi, explo_force):
        x, y = coordo
        vix, viy = vi
        c = (vix**2 + viy**2)**0.5
        print(c)

        ux = vix/c
        uy = viy/c

        ex = ux * explo_force
        ey = uy * explo_force

        vfx = vix + ex
        vfy = viy + ey
        return vfx, vfy

    @staticmethod
    def v_explo_new_missiles(number_missiles, explo_angle, vi):
        vix, viy = vi
        c = (vix ** 2 + viy ** 2) ** 0.5
        print(c)


        mvix = c * math.cos(math.radians(explo_angle))
        mviy = c * math.sin(math.radians(explo_angle))

        m2vix = c * math.cos(math.radians(-explo_angle))
        m2viy = c * math.sin(math.radians(-explo_angle))

        return (vix, viy), (mvix, mviy), (m2vix, m2viy)





vi = 10
g = 9.81
t = 1.427
angle = 0
exploF = 1.5
exploAngle = 10
print("time at 0", phys_sim.time_at_yf(0, g, 10, 0))
coordo = phys_sim.coordo_explo(vi, angle, t, g, 0, 10)
print(coordo)
final_speed = phys_sim.final_speed_2d(vi,g, t, angle)
print(final_speed)
explo_final = phys_sim.explo_impulsion_finale(coordo, final_speed, exploF)
print(explo_final)
new_missiles = phys_sim.v_explo_new_missiles(0,exploAngle,explo_final)
print(new_missiles)
