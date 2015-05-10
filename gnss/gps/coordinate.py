#!/usr/bin/env python3
# -*- coding:utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        coordinate
# Purpose:  緯度経度に関する演算に対して補助することが目的です。
#
# Author:      morishita
#
# Created:     15/01/2012
# Copyright:   (c) morishita 2012
# Licence:     MIT
# Histroy:
#           2012/9/5    XYZとBLHのprint()対応のために、__str__を追加した。
#           2012/11/15  BLHの文字列化において、桁数をそろえるように変更した。
#           2013/1/3    基準エポックを定義した
#           2014/2/10   モジュールをgnss.gpsへ移して、モジュール名をcoordinateへ変更した。
#                       関数名もちょこっと改名
#                       epochOriginをtime.pyへ引っ越す
#           2014/2/14   XYZクラスの名前をecefへ変更
#                       BLHクラスの名前をblhへ変更
#                       blhクラスにecef座標系へ変換する関数to_ecef()を実装
#                       blhクラスにchange_unit_to_degree(), change_unit_to_rad()を実装
#                       WGA84モジュールの変更を反映
#                       enuクラスを新設
#            2014/2/27  汎用性を得るために、親クラスを作成し、これを継承する形に改めた。
#            2014/3/1   メンテナンスの観点から、測地系モジュールを代入する形に変更
#-------------------------------------------------------------------------------

import math                     # 算術モジュールを追加
import gnss.datum.WGS84 as wgs84
import gnss.coordinate as gnss_coor


datum = wgs84

class enu(gnss_coor.enu):
    """  enu座標系を扱うクラスです.
    """
    def __init__(self, e=0.0, n=0.0, u=0.0):
        """ 初期化
        Argv:
            e:     <float> or <str> 局地座標系における東方向座標値
            n:     <float> or <str> 局地座標系における北方向座標値
            u:     <float> or <str> 局地座標系における鉛直方向座標値
        """
        gnss_coor.enu.__init__(self, datum, e, n, u)
    def __str__(self):
        """ 文字列化
        """
        return gnss_coor.enu.__str__(self)



class ecef(gnss_coor.ecef):
    """  ecef座標系を扱うクラスです.
    """
    def __init__(self, x=0.0, y=0.0, z=0.0):
        """ 初期化
        Argv:
            x:     <float> or <str> ECEF座標系におけるx軸座標値
            y:     <float> or <str> ECEF座標系におけるy軸座標値
            z:     <float> or <str> ECEF座標系におけるz軸座標値
        """
        gnss_coor.ecef.__init__(self, datum, x, y, z)
    def __str__(self):
        """ 文字列化
        """
        return gnss_coor.ecef.__str__(self)



class blh(gnss_coor.blh):
    """ 緯度・経度・楕円体高を表現するクラス.
    """
    def __init__(self, B=0.0, L=0.0, H=0.0, unit="degree"):
        """ 初期化
        Argv:
            B:     <float> or <str> 緯度
            L:     <float> or <str> 経度
            H:     <float> or <str> 楕円体高
            unit:  <str>            e.g. "degree" or "rad"
        """
        gnss_coor.blh.__init__(self, datum, B, L, H, unit)
    def __str__(self):
        """ 文字列化
        """
        return gnss_coor.blh.__str__(self)






def main():
    print("---self test---")
    hoge = ecef(1.0, 1.0, 6400000).to_blh()
    print(hoge.B, hoge.L, hoge.H)
    hoge = blh(32.8545684, 130.9808465, 0.0)
    print(hoge)
    target = blh(32.8613858, 130.9526228, 0.0)
    distance = hoge.get_distance(target)
    print("distance: {0} m.".format(distance))



if __name__ == '__main__':
    main()
