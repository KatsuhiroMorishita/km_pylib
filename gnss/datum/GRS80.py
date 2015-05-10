#!/usr/bin/env python3
# -*- coding:utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        GRS80
# Purpose: GRS80測地系に関するパラメータと機能を提供する
#
# Author:      morishita
#
# Created:     1/3/2014
# Copyright:   (c) morishita 2012
# Licence:     MIT
# History:     2014/3/1     WGS84を基に作成
#-------------------------------------------------------------------------------
import math

# 各種パラメータ
a = 6378137.0                                    				# 赤道半径[m]
InversOblateness = 298.25722101                                 # 扁平率の逆数
E2 = 2.0 / InversOblateness - (1.0 / InversOblateness) ** 2.0   # 離心率の二乗. or = f * (2.0 - f)
e = math.sqrt(E2)												# 離心率
f = 1.0 / InversOblateness                             			# 扁平率
b = a * (1.0 - f)               								# 短半径[m]
pi = 3.1415926535898                                            # 円周率 @WGS84
c = 2.99792458 * (10 ** 8)                                      # 光速 [m/s] @WGS84
omega_e = 7.292115E-05                                          # 地球回転角速度　Earth's rotation rate (rad/s)
GM = 3.986005e14                                                # 地球重力定数[m^3/s^2] 

def main():
    print("WGS84 parameters.")
    print("長半径: {0}".format(a))
    print("短半径: {0}".format(b))
    print("扁平率: {0}".format(f))
    print("離心率: {0}".format(e))
    print("光速: {0}".format(c))
    print("円周率: {0}".format(pi))
    print("地球回転角速度: {0}".format(omega_e))
    print("地球重力定数: {0}".format(GM))


if __name__ == '__main__':
    main()
