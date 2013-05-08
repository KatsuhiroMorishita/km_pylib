#!/usr/bin/env python3
# -*- coding:utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        WGS84
# Purpose:
#
# Author:      morishita
#
# Created:     14/01/2012
# Copyright:   (c) morishita 2012
# Licence:     <your licence>
#-------------------------------------------------------------------------------

# 各種パラメータ
EquatorialRadius = 6378137.0                                    # 赤道半径[m]
InversOblateness = 298.257223                                   # 扁平率の逆数
E2 = 2.0 / InversOblateness - (1.0 / InversOblateness) ** 2.0   # 離心率の二乗. or = oblateness * (2.0 - oblateness)
Oblateness = 1.0 / InversOblateness                             # 扁平率
ShortRadius = EquatorialRadius * (1 - Oblateness)               # 短半径


def main():
    print("WGS84 parameters.")
    print(EquatorialRadius)
    print(InversOblateness)
    print(E2)
    print(Oblateness)
    print(ShortRadius)

if __name__ == '__main__':
    main()
