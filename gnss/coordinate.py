#!/usr/bin/env python3
# -*- coding:utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        coordinate
# Purpose:  緯度経度に関する演算に対して補助することが目的です。
#
# Author:      morishita
#
# Created:     27/02/2014
# Copyright:   (c) morishita 2014
# Licence:     MIT
# Histroy:
#           2014/2/27    GPS用に用意したモジュールを基に、汎用部分を抽出した。
#                        いつか、ecefクラスに返り値をxyzクラス（新設）とする差分を定義したい。
#           2014/3/1     見やすくするためにメソッド間に空行を追加
#           2014-09-06   enuクラスに足し算と引き算の定義を追加
#-------------------------------------------------------------------------------

import math                     # 算術モジュールを追加


class enu:
    """  enu座標系を扱うクラス
    """
    def __init__(self, datum, e=0.0, n=0.0, u=0.0):
        """ 初期化
        Argv:
            datum: <gnss.datum.x>   測地系モジュール
            e:     <float> or <str> 局地座標系における東方向座標値
            n:     <float> or <str> 局地座標系における北方向座標値
            u:     <float> or <str> 局地座標系における鉛直方向座標値
        """
        self.datum = datum
        self.e = float(e)
        self.n = float(n)
        self.u = float(u)

    def __add__(self, other):
        """ 足し算
        """
        e = self.e + other.e
        n = self.n + other.n
        u = self.u + other.u
        return enu(self.datum, e, n, u)

    def __sub__(self, other):
        """ 引き算
        """
        #print("sub")
        e = self.e - other.e
        n = self.n - other.n
        u = self.u - other.u
        #print(e, n, u)
        return enu(self.datum, e, n, u)

    def __str__(self):
        """ 文字列化
        """
        return "{0:.4f},{1:.4f},{2:.4f}".format(self.e, self.n, self.u)

    def distance(self, other):
        """ 距離を返す
        """
        #print("dist")
        #print(self)
        #print(other)
        diff = self - other
        #print("diff")
        #print(diff)
        return math.sqrt(diff.e ** 2 + diff.n ** 2 + diff.u ** 2)

    # プロパティ
    @property
    def elevation_rad(self):
        """ 仰角[rad]を返す
        """
        return math.atan2(self.u, math.sqrt(self.e ** 2 + self.n ** 2))

    @property
    def elevation_degree(self):
        """ 仰角[degree]を返す
        """
        return self.elevation_rad * 180.0 / math.pi

    @property
    def azimuth_rad(self):
        """ 方位角[rad]を返す
        地理上の北を0 [rad]とし、時計回りに正とします。
        磁北とは異なりますのでご注意ください。
        """
        theta = math.atan2(self.e, self.n)
        if theta < 0:
            theta += 2.0 * math.pi
        return theta

    @property
    def azimuth_degree(self):
        """ 方位角[degree]を返す
        地理上の北を0 [°]とし、時計回りに正とします。
        磁北とは異なりますのでご注意ください。
        """
        return self.azimuth_rad * 180.0 / math.pi



class ecef:
    """  ecef座標系を扱うクラス
    """
    def __init__(self, datum, x=0.0, y=0.0, z=0.0):
        """ 初期化
        Argv:
            datum: <gnss.datum.x>   測地系モジュール
            x:     <float> or <str> ECEF座標系におけるx軸座標値
            y:     <float> or <str> ECEF座標系におけるy軸座標値
            z:     <float> or <str> ECEF座標系におけるz軸座標値
        """
        self.datum = datum
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)

    def __str__(self):
        """ 文字列化
        """
        return "{0:.4f},{1:.4f},{2:.4f}".format(self.x, self.y, self.z)

    def to_blh(self):
        """ blh座標系へ変換する.
        """
        if self.x == 0.0 and self.y == 0.0 and self.z == 0.0:
            return None
        h = self.datum.a ** 2.0 - self.datum.b ** 2.0
        p = math.hypot(self.x, self.y)
        t = math.atan2(self.z * self.datum.a, p * self.datum.b)
        sint = math.sin(t)
        cost = math.cos(t)

        lat = math.atan2(self.z + h / self.datum.b * (sint ** 3.0), p - h / self.datum.a * (cost ** 3.0)) # 緯度[rad]を計算
        n   = self.datum.a / math.sqrt(1.0 - self.datum.E2 * (math.sin(lat) ** 2.0))                      # 卯酉線曲率半径
        lon = math.atan2(self.y, self.x)                    # 経度[rad]を計算
        height = (p / math.cos(lat)) - n                    # 楕円体高[m]を計算

        lat = lat * 180.0 / math.pi                         # 単位をdegに変換
        lon = lon * 180.0 / math.pi
        return blh(self.datum, lat, lon, height, "degree")

    def to_enu(self, origin):
        """ ENU座標系へ変換したオブジェクトを返す
        Argv:
            origin: <blh> or <ecef> 視点原点座標
        """
        ans = None
        if isinstance(origin, ecef) or isinstance(origin, blh):
            origin_blh = None
            if isinstance(origin, blh):
                origin_blh = blh(self.datum, origin.B, origin.L, origin.H, origin.unit) # copy
                origin_blh.change_unit_to_rad()
                origin = origin.to_ecef()
            else:
                origin_blh = origin.to_blh().change_unit_to_rad()
            dx = self.x - origin.x
            dy = self.y - origin.y
            dz = self.z - origin.z
            sB = math.sin(origin_blh.B)
            cB = math.cos(origin_blh.B)
            sL = math.sin(origin_blh.L)
            cL = math.cos(origin_blh.L)
            e = -dx * sL + dy * cL
            n = -dx * cL * sB + -dy * sL * sB + dz * cB
            u = dx * cL * cB + dy * sL * cB + dz * sB
            ans = enu(self.datum, e, n, u)
            #print(ans)
        return ans




class blh:
    """ 緯度・経度・楕円体高を表現するクラス.
    """
    def __init__(self, datum, B=0.0, L=0.0, H=0.0, unit="degree"):
        """ 初期化
        Argv:
            datum: <gnss.datum.x>   測地系モジュール
            B:     <float> or <str> 緯度
            L:     <float> or <str> 経度
            H:     <float> or <str> 楕円体高
            unit:  <str>            e.g. "degree" or "rad"
        """
        self.datum = datum
        self.B = float(B)       # 緯度
        self.L = float(L)       # 経度
        self.H = float(H)       # 楕円体高[m]
        self.unit = unit        # 単位

    def __str__(self):
        """ 文字列化
        """
        return "{0:.10f},{1:.10f},{2:.10f}".format(self.L, self.B, self.H)

    def copy(self):
        return blh(self.datum, self.B, self.L, self.H, self.unit)

    def change_unit_to_degree(self):
        """ 単位をdegreeへ変換する
        """
        if self.unit == "rad":
            self.B *= 180.0 / math.pi
            self.L *= 180.0 / math.pi
            self.H *= 180.0 / math.pi
            self.unit = "degree"

    def change_unit_to_rad(self):
        """ 単位をradへ変換する
        """
        if self.unit == "degree":
            self.B *= math.pi / 180.0
            self.L *= math.pi / 180.0
            self.H *= math.pi / 180.0
            self.unit = "rad"

    def get_unit_length(self, lat_deg):
        """ 受け取った緯度における、緯経度一度当たりの単位長さを返す
        例えば、緯経度差が分かっている場合に、2点間が近距離で有れば距離を計測することが出来る
        理科年表を参考にした。
        Argv:
            lat_deg: <float> 緯度[degree]
        """
        _lat = lat_deg * math.pi / 180.0
        _unitL = math.pi / 180.0 * self.datum.a * math.cos(_lat) / math.sqrt(1 - self.datum.E2 * (math.sin(_lat) ** 2.0))
        _unitB = math.pi / 180.0 * self.datum.a * (1 - self.datum.E2) / (1 - self.datum.E2 * (math.sin(_lat) ** 2.0) ** 1.5)
        return (_unitB, _unitL)

    def get_distance(self, target_position_blh):
        """ 指定座標までの距離[m]を返す
        20 km程度の近距離において使用可能です。
        引数の単位は度とします。
        Argv:
            target_position_blh: <blh> 距離計算上の目標座標
        """
        _target = target_position_blh.copy()                    # 単位をdegreeにそろえるために、コピー（引数のオブジェクトを変更しないためコピーする）
        _target.change_unit_to_degree()
        centerLat = (self.B + _target.B) / 2.0                  # 2点間の中間点の緯度
        unitB, unitL = self.get_unit_length(centerLat)
        widthB = abs(self.B - _target.B)
        widthL = abs(self.L - _target.L)
        _distance = ((widthB * unitB) ** 2.0 + (widthL * unitL) ** 2.0) ** 0.5
        return _distance

    def to_ecef(self):
        """ ecef座標系に変換したオブジェクトを返す
        ref: GPSのための実用プログラミング第1版, p. 29
        """
        copy = blh(self.datum, self.B, self.L, self.H, self.unit)
        copy.change_unit_to_rad()
        n = self.datum.a / math.sqrt(1.0 - self.datum.E2 * math.sin(copy.B) ** 2.0)
        x = (n + copy.H) * math.cos(copy.B) * math.cos(copy.L)
        y = (n + copy.H) * math.cos(copy.B) * math.sin(copy.L)
        z = ((1.0 - self.datum.E2) * n + copy.H) * math.sin(copy.B)
        return ecef(self.datum, x, y, z)




def convert_dddmm2ddd(position):
    """ dddmm.mmmm形式の緯度・傾度をddd.ddddddフォーマットに変換する
    """
    _position = float(position)
    _ddd = int(_position) / 100
    _mm = float(_position) - _ddd * 100
    _ans = _ddd + _mm / 60.0
    return _ans

def convert_ddd2ddmm(position):
    """ ddd.dddddd表現の緯経度を、数値のdddmm.mmmm形式に直す.
    """
    _ddd = float(position)
    _mm = (float(position) - _ddd) * 60.0
    _ans = _ddd * 100.0 + _mm
    return _ans




def main():
    print("---self test---")
    import gnss.datum.WGS84 as sample_datum
    hoge = ecef(sample_datum, 1.0, 1.0, 6400000).to_blh()
    print(hoge.B, hoge.L, hoge.H)
    hoge = blh(sample_datum, 32.8545684, 130.9808465, 0.0)
    print(hoge)
    target = blh(sample_datum, 32.8613858, 130.9526228, 0.0)
    distance = hoge.get_distance(target)
    print("distance: {0} m.".format(distance))




if __name__ == '__main__':
    main()
