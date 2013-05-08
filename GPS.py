#!/usr/bin/env python3
# -*- coding:utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        GPS
# Purpose:  緯度経度に関する演算に対して補助することが目的です。
#
# Author:      morishita
#
# Created:     15/01/2012
# Copyright:   (c) morishita 2012
# Licence:     New BSD
# Histroy:
#           2012/9/5    XYZとBLHのprint()対応のために、__str__を追加した。
#           2012/11/15  BLHの文字列化において、桁数をそろえるように変更した。
#           2013/1/3    基準エポックを定義した
#-------------------------------------------------------------------------------

import math                     # 算術モジュールを追加
import WGS84
import datetime

epochOrigin = datetime.datetime(1980, 1, 6)                 # GPSの基準エポック


class XYZ:
    """  XYZ座標系を扱うクラスです.
    """
    def __init__(self, x = 0.0, y = 0.0, z = 0.0):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
    def __str__(self):
        """ 文字列化
        """
        return str(self.x) + "," + str(self.y) + ","+ str(self.z)
    def ToBLH(self):
        """ BLH座標系へ変換する.
        """
        if self.x == 0.0 and self.y == 0.0 and self.z == 0.0:
            return None
        h = WGS84.EquatorialRadius ** 2.0 - WGS84.ShortRadius ** 2.0
        p = math.hypot(self.x, self.y)
        t = math.atan2(self.z * WGS84.EquatorialRadius, p * WGS84.ShortRadius)
        sint = math.sin(t)
        cost = math.cos(t)

        lat = math.atan2(self.z + h / WGS84.ShortRadius * (sint ** 3.0), p - h / WGS84.EquatorialRadius * (cost ** 3.0))# 緯度[rad]を計算
        n   = WGS84.EquatorialRadius / math.sqrt(1.0 - WGS84.E2 * (math.sin(lat) ** 2.0))                               # 卯酉線曲率半径
        lon = math.atan2(self.y, self.x)                    # 経度[rad]を計算
        height = (p / math.cos(lat)) - n                    # 楕円体高[m]を計算

        lat = lat * 180.0 / math.pi                         # 単位をdegに変換
        lon = lon * 180.0 / math.pi
        return BLH(lat, lon, height)

class BLH:
    """ 緯度経度と楕円体高を表現するクラス.
    """
    def __init__(self, B = 0.0, L = 0.0, H = 0.0):
        self.B = float(B)       # 緯度
        self.L = float(L)       # 経度
        self.H = float(H)       # 楕円体高
    def __str__(self):
        """ 文字列化
        """
        return ("%0.8f" % self.L) + "," + ("%0.8f" % self.B) + ","+ ("%0.4f" % self.H)
    def distance(self, position_BLH):
        """ 指定座標までの距離[m]を返す
        20 km程度の近距離において使用可能です。
        引数の単位は度とします。
        """
        centerLat = (self.B + position_BLH.B) / 2.0 # 2点間の中間点の緯度
        unitB, unitL = GetUnit_Length(centerLat)
        widthB = abs(self.B - position_BLH.B)
        widthL = abs(self.L - position_BLH.L)
        _distance = ((widthB * unitB) ** 2.0 + (widthL * unitL) ** 2.0) ** 0.5
        return _distance


def Convert_xyz2BLH(x, y, z):
    """ x,y,z表現の座標をblh形式（緯経度・高度）へ直す.

    地球を半径6400,000kmの球と仮定しているので、変換値は大まかでしかない。
    """
    _positon = XYZ(x, y, z)
    return _positon.ToBLH()

def Convert_dddmm2ddd(position):
    """ dddmm.mmmm形式の緯度・傾度をddd.ddddddフォーマットに変換する
    """
    _position = float(position)
    _ddd = int(_position) / 100
    _mm = float(_position) - _ddd * 100
    _ans = _ddd + _mm / 60.0
    return _ans

def Convert_ddd2ddmm(position):
    """ ddd.dddddd表現の緯経度を、数値のdddmm.mmmm形式に直す.
    """
    _ddd = float(position)
    _mm = (float(position) - _ddd) * 60.0
    _ans = _ddd * 100.0 + _mm
    return _ans

def GetUnit_Length(lat_deg):            # 単位はdeg
    """ 受け取った緯度における、緯経度一度当たりの単位長さを返す関数.

    例えば、緯経度差が分かっている場合に、2点間が近距離で有れば距離を計測することが出来る
    理科年表を参考にした
    """
    _lat = lat_deg * math.pi / 180.0
    _unitL = math.pi / 180.0 * WGS84.EquatorialRadius * math.cos(_lat) / math.sqrt(1 - WGS84.E2 * (math.sin(_lat) ** 2.0))
    _unitB = math.pi / 180.0 * WGS84.EquatorialRadius * (1 - WGS84.E2) / (1 - WGS84.E2 * (math.sin(_lat) ** 2.0) ** 1.5)
    return (_unitB, _unitL)



def main():
    hoge = Convert_xyz2BLH(1.0, 1.0, 6400000)
    print(hoge.B, hoge.L, hoge.H)
    hoge = BLH(32.813917, 130.639056, 0.0)
    print(hoge)
    target = BLH(32.813700, 130.729547, 0.0)
    print(hoge.distance(target))

if __name__ == '__main__':
    main()
