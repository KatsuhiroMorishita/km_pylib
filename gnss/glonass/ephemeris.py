#!/usr/bin/env python3
# -*- coding:utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        ephemeris
# Purpose:  IGSの放送歴を基にGLONASS衛星軌道の計算を行い、各種アルゴリズムの確認を行うこと
# Memo:     GLONASSやQZSの計算も行いたいので、将来的な拡張がしやすいようにクラス構造はカチッと固めていません。
# Author:      morishita
#
# Created:     01/03/2014
# Copyright:   (c) morishita 2012
# Licence:     MIT
# Histroy:
#           2014/3/1     GPS用のモジュールをほぼコピー
#                        とりあえず、正規表現とセルフテスト用の文字列のみ変更した。
#           2014/3/2     衛星軌道の計算が意外と面倒だ。
#-------------------------------------------------------------------------------

import os
import re
import math
import inspect
import datetime
import timeKM
import gnss.gps.time as gtime
import gnss.datum.WGS84 as wgs84
import gnss.gps.coordinate as gcoor
import gnss.ephemeris as gnss_eph

time_system = gtime
datum = wgs84
coor = gcoor
system_name = "GLONASS"

#定数など
value_pattern = r"[-]?\d[.]\d+[EeDd][\s+-]\d{1,2}"                          # 文字列での数値表現
eph_pattern = re.compile(                                                   # IGSのRINEXフォーマット放送暦に対応した正規表現. see RINEX 2.11.
    r"(?P<sat_name>(?: \w)?\s?\d{1,2})" +                                   # 衛星の番号
    r"\s(?P<epoch>\d{1,2} +\d{1,2} +\d{1,2} +\d{1,2} +\d{1,2} +\d{1,2}[.]\d+)" +  # この航法メッセージの基準エポック(UTC)
    r"\s?(?P<sv_clock_bias>{0})".format(value_pattern) +                    # クロック補正係数(-TauN)
    r"\s?(?P<sv_relative_frequency_bias>{0})".format(value_pattern) +       # クロック補正係数(+GammaN)
    r"\s?(?P<message_frame_time>{0})".format(value_pattern) +               # クロック補正係数？(tk)
    r"\s?(?P<position_X>{0})".format(value_pattern) +                       # (km)
    r"\s?(?P<velocity_X_dot>{0})".format(value_pattern) +                   # (km/sec) 
    r"\s?(?P<X_acceleration>{0})".format(value_pattern) +                   # (km/sec2)
    r"\s?(?P<health>{0})".format(value_pattern) +                           # (0=OK)
    r"\s?(?P<position_Y>{0})".format(value_pattern) +                       # (km)
    r"\s?(?P<velocity_Y_dot>{0})".format(value_pattern) +                   # (km/sec) 
    r"\s?(?P<Y_acceleration>{0})".format(value_pattern) +                   # (km/sec2)
    r"\s?(?P<frequency_number>{0})".format(value_pattern) +                 # (-7 ... +13)
    r"\s?(?P<position_Z>{0})".format(value_pattern) +                       # (km)
    r"\s?(?P<velocity_Z_dot>{0})".format(value_pattern) +                   # (km/sec) 
    r"\s?(?P<Z_acceleration>{0})".format(value_pattern) +                   # (km/sec2)
    r"\s?(?P<Age_of_oper>{0})".format(value_pattern)                        # (days)
    )



class ephemeris(gnss_eph.ephemeris):
    """  エフェメリスを扱うクラスです.
    """
    def __init__(self):
        """ 初期化
        """
        gnss_eph.ephemeris.__init__(self, system_name)  # 親クラスの初期化
        member_name = eph_pattern.groupindex.keys()     # 正規表現パターンのグループ名の一覧を取得
        for mem in member_name:
            setattr(self, mem, 0)                       # オブジェクトにメンバを追加

    def __eq__(self, other):
        """ ==比較演算子に対応する
        """
        if isinstance(other, ephemeris) == False:       # 型のチェック
            return False
        return gnss_eph.ephemeris.__eq__(self, other)

    def __hash__(self):
        """ ハッシュ値を返す
        メンバの値が同じであれば同じ値を返します。
        """
        return gnss_eph.ephemeris.__hash__(self)

    def __str__(self):
        """ オブジェクトの文字列表現を返す
        """
        return gnss_eph.ephemeris.__str__(self)
        
    def calc_sat_position(self, epoch):
        """ 指定エポックにおける衛星の座標を返す
        計算方法はICD-200Dを参照されたし。
        Argv:
            epoch (GPS time)  <datetime.datetime> or <int> or <float>
                              UTCだと、厳密な変換（をコードの整合性と利便性を保ちつつ実装するの）が面倒.
                              ただし、うるう秒+UTCと単純な変換であっても衛星位置座標の誤差は0.04 mm以下。
                              気にしなければ気にならない。
        Return:
            <gnss.gps.coordinate.ecef>: satellite position
            None:  計算できない場合
        """
        # 演算が可能かどうか確認
        if self.is_available == False:
            return None
        # 引数をGPS時刻になおす
        if isinstance(epoch, datetime.datetime):
            gpst = (epoch - time_system.epoch_origin).total_seconds()
        elif isinstance(epoch, float) or isinstance(epoch, int):
            gpst = epoch
        else:
            return None
        #　計算開始
        tdiff = gpst - (self.gps_week * timeKM.TIME_A_WEEK + self.TOE)  # GPS時刻同士の引き算で時間差を計算
        #print(tdiff)
        n0 = math.sqrt(datum.GM) / (self.SQRT_A ** 3)                   # 衛星の平均的な角速度
        M = self.M0 + (n0 + self.delta_N) * tdiff                       # 平均近点角
        M %= 2.0 * datum.pi                                             # point1. 何周していても仕方ないので、2πの剰余を求める（離心近点角の解法の収束性も改善する）
        # 離心近点角を求める
        # 以下に3つの解法を載せているが、いずれもループを抜けた時点では実用上問題になる差はない。
        # 解が振動しない範囲なら、method2,3は3ループ以下で収束する。method1は収束に数ループを要することがある。
        # 本コードでは最も収束性の良かったものを採用している。
        # なお、テストには一つのエフェメリスしか使っていないので、もしかすると不安定領域が残っているかもしれない。
        """
        E = M                                                           # method1
        for i in range(0, 20):                                          # おそらく一般的な解法. point1.なしだと、tdiffが90時間を超えると解が振動し始めて収束判定をクリアできない座標が出てくる。
            E_next = M + self.e * math.sin(E)                           # なお、point1があっても、tdiffが7461時間あたりで収束判定をクリアできなかったことがある。
            if round(E_next, 13) == round(E, 13):                       # 収束判定.　たまに解が振動するので、適当な桁数でカットする.
                E = E_next
                break
            E = E_next
        print(E)
        E = M                                                           # method2
        for i in range(0, 20):                                          # 天体の位置計算,増補版第5刷,p.147,2001.9. にある方法を利用して近似値計算
            dE = (M - E + self.e * math.sin(E)) / (1 - self.e * math.cos(E))
            E += dE
            if round(dE, 13) == 0.0:                                    # 収束判定. point1.なしだと、tdiffが900時間を超えると収束できない座標が出てくる
                break
        print(E)
        """
        E = M                                                           # method3
        for i in range(0, 20):                                          # ニュートン・ラフソン法. point1.なしでも、tdiffが12000時間まで素直に収束することを確認した。
            a = self.e * math.cos(E) - 1                                # 傾き（微分値）
            y = M - E + self.e * math.sin(E)                            # yの評価式。yが0になるように降下させる。
            E_next = -(y / a) + E                                       # 更新
            if round(E_next, 13) == round(E, 13):                       # 収束判定
                E = E_next
                break
            E = E_next
        #print(E)
        theta = math.atan2(math.sqrt(1.0 - self.e ** 2) * math.sin(E), math.cos(E) - self.e) # 真近点角
        u = theta + self.omega                                                  # 昇交点からの角度
        r = self.SQRT_A ** 2 * (1.0 - self.e * math.cos(E))                     # 地心距離
        i = self.i0 + self.i_dot * tdiff                                        # 軌道傾斜角
        d_u = self.Cus * math.sin(2.0 * u) + self.Cuc * math.cos(2.0 * u)       # 補正項
        d_r = self.Crs * math.sin(2.0 * u) + self.Crc * math.cos(2.0 * u)       # 補正項
        d_i = self.Cis * math.sin(2.0 * u) + self.Cic * math.cos(2.0 * u)       # 補正項
        u += d_u
        r += d_r
        i += d_i
        OMEGA = self.OMEGA0 + (self.OMEGA_dot - datum.omega_e) * tdiff - self.TOE * datum.omega_e# 昇交点赤経
        x = r * (math.cos(u) * math.cos(OMEGA) - math.sin(u) * math.sin(OMEGA) * math.cos(i))
        y = r * (math.cos(u) * math.sin(OMEGA) + math.sin(u) * math.cos(OMEGA) * math.cos(i))
        z = r * (math.sin(u) * math.sin(i))
        #print(x, y, z)
        return coor.ecef(x, y, z)




class reader(gnss_eph.reader):
    """ GLONASSのエフェメリスを読み込むクラス
    """
    def __init__(self):
        """
        """
        gnss_eph.reader.__init__(self, "\.\d{2}[g]", eph_pattern, ephemeris)
    def read_ephemeris_from_txt(self, txt):
        """ テキストから読み出したエフェメリスをリストで返す
        Argv:
            fname: <str> ファイルパス（相対でも可）
        Return:
            <list<ephemeris>> エフェメリスを格納した要素数0以上のリスト
        """
        #print("test")
        eph = gnss_eph.reader.read_ephemeris_from_txt(self, txt)
        if len(eph) > 0:
            for mem in eph:
                pass
                # 特別なメンバを追加・変更する場合はここに書く
        return eph






def main():
    print("---self test---")
    # ephemerisクラスの等値判断テスト
    a = ephemeris()
    b = ephemeris()
    print("----オブジェクトa----\n" + str(a))
    if a == b:
        print("オブジェクトaとbは等値.")
    # ハッシュ値
    print("ハッシュ値:" + str(hash(a)))

    # エフェメリスを読み込むテスト
    test_str = \
        "18 14  1 25 23 45  0.0-9.693205356598D-05-0.000000000000D+00 8.637000000000D+04\n" + \
        "   -1.908828955078D+04-1.651377677917D+00-0.000000000000D+00 0.000000000000D+00\n" + \
        "    1.116154101562D+04 5.975294113159D-01 9.313225746155D-10-3.000000000000D+00\n" + \
        "    1.282693212891D+04-2.974982261658D+00-2.793967723846D-09 0.000000000000D+00\n" + \
        " 3 14  1 25 23 45  0.0 7.750466465950D-06 9.094947017729D-13 8.637000000000D+04\n" + \
        "   -1.226712060547D+04 8.047599792480D-01 9.313225746155D-10 0.000000000000D+00\n" + \
        "    6.466432128906D+03-2.815400123596D+00-0.000000000000D+00 5.000000000000D+00\n" + \
        "    2.144328710938D+04 1.309871673584D+00-2.793967723846D-09 0.000000000000D+00\n" + \
        " 4 14  1 25 23 45  0.0 5.902722477913D-05 9.094947017729D-13 8.637000000000D+04\n" + \
        "   -1.009611132812D+04 4.565620422363D-01-9.313225746155D-10 0.000000000000D+00\n" + \
        "    2.162384033203D+04-1.155596733093D+00 1.862645149231D-09 6.000000000000D+00\n" + \
        "    9.018057128906D+03 3.284611701965D+00-2.793967723846D-09 0.000000000000D+00\n"
    r = reader()
    ephs = r.read_ephemeris_from_txt(test_str)
    print("\n")
    for mem in ephs:
        print(type(mem))
        print(mem)

    # 1秒ごとに500秒間の衛星座標を計算する
    eph = ephs[0]
    toe = int(eph.TOE) + int(eph.gps_week) * timeKM.TIME_A_WEEK
    pos1 = coor.ecef()
    usr_pos = coor.blh(32.0, 130.0)
    for dt in range(500):   # range(0, 3600, 900) とすれば、0から900ずつ増える
        t = toe + dt
        pos2 = eph.calc_sat_position(t)
        d = math.sqrt((pos2.x - pos1.x) ** 2 + (pos2.y - pos1.y) ** 2 + (pos2.z - pos1.z)**2) # 座標間の直線距離 m。 地球の自転の影響で見かけの速度が変わる。
        pos1 = pos2
        #print(pos)
        sat_pos_enu = pos1.to_enu(usr_pos)
        azimuth = sat_pos_enu.azimuth_degree
        print("dt: {0:.1f} h, v: {1:.2f}, azimuth: {2:.1f}".format(dt / 3600, d, azimuth))

    # エフェメリスの読み込みテスト
    ephs = r.read_ephemeris("brdc2530.10n")
    print("number of read files: {0}".format(len(ephs)))
    #for eph in ephs:
        #print(eph)

    # エフェメリスのソート（並べ直し）
    print("\n")
    print("ephemeris sort. --pre--")
    print(ephs[0])
    print(ephs[1])
    import operator
    ephs.sort(key=operator.attrgetter("sat_name"), reverse=True) # Psat_name順にソート
    print("ephemeris sort. --post--")
    print(ephs[0])
    print(ephs[1])

    # エフェメリスの整理
    storage = gnss_eph.organize(ephs)   #　衛星ごとに整理
    sat_names = storage.keys()          # 衛星名を取得
    print("sat names:")
    print(sat_names)

    # 動的エフェメリス選択のテスト
    # 最新の放送歴を取得するサンプル
    def create_filter(epoch):
        """ '渡されたエフェメリスの中から、初めてepochを超えたTOMを持つ各衛星のエフェメリスを返す'関数を生成して返す
        Argv:
            epoch: <float or int> GPS時刻
        """
        def filter(system_name, ephs_dict):
            """ 渡されたエフェメリスの中から、初めてepochを超えたTOMを持つ各衛星のエフェメリスを返す
            Argv:
                system_name: <str> 測位システム名, e.g. "GPS", 本関数では利用しない
                ephs_dict: <dict>  エフェメリスを衛星ごとに格納した辞書, e.g.: {"1": [ephemeris・・・], ・・・}
            Return:
                <list<ephemeris>> 該当したエフェメリスのリスト
            """
            ephs = []
            for sat_name in ephs_dict:
                eph_list = ephs_dict[sat_name]
                eph_list.sort(key=operator.attrgetter("TOM"))   # TOM番号順にソート
                for eph in eph_list:
                    tom = eph.TOM + eph.gps_week * timeKM.TIME_A_WEEK # TOMをGPS時刻へ変換
                    if tom > epoch:                             # 小さい順に並んでいることが前提
                        ephs.append(eph)
                        break
            return ephs
        return filter
    epoch = 1600 * timeKM.TIME_A_WEEK + 431748 + 3600 * 7
    print("\n")
    print("ephemeris choice test:")
    print("epoch: " + str(epoch))
    func = create_filter(epoch)                                 # 関数を生成
    ephs = func(system_name, storage)                           # 生成した関数を渡して、エフェメリスを取得
    #print(ephs)
    print("len: " + str(len(ephs)))                             # 取得できたエフェメリスの数を返す
    #for eph in ephs:
    #    print("TOM: " + str(eph.TOM + eph.gps_week * timeKM.TIME_A_WEEK))


    # 衛星座標計算のテスト
    def create_filter(epoch):
        """ '渡されたエフェメリスを用いて、有効なエフェメリスを用いて各衛星座標を返す'関数を生成して返す
        応用を考慮して関数を書いているので、GPSだけの計算に比べて少し行数が多くなっています。
        Argv:
            epoch: <float or int> GPS時刻
        """
        def filter(system_name, ephs_dict):
            """ 渡されたエフェメリスを用いて、有効なエフェメリスを用いて各衛星座標を返す
            Argv:
                system_name: <str> 測位システム名, e.g. "GPS", 本関数では利用しない
                ephs_dict: <dict>  エフェメリスを衛星ごとに格納した辞書, e.g.: {"1": [ephemeris・・・], ・・・}
            Return:
                <list<tuple<int, xyz>>> 衛星番号と座標をタプルにしたリスト
            """
            poss = []
            for sat_name in ephs_dict:
                eph_list = ephs_dict[sat_name]
                for eph in eph_list:
                    if system_name == "GPS":
                        if eph.sv_health != 0:
                            continue
                        tom = eph.TOM + eph.gps_week * timeKM.TIME_A_WEEK # TOMをGPS時刻へ変換
                        if not (tom < epoch < tom + 3500 * eph.fit_interval):
                            continue
                    if system_name == "QZS":
                        #if eph.sv_health != 0: # sv_health is always 1 at 2014-02
                        #    continue
                        tom = eph.TOM + eph.gps_week * timeKM.TIME_A_WEEK # TOMをGPS時刻へ変換
                        if not (tom < epoch < tom + 3500 * eph.fit_interval):
                            continue
                    pos = eph.calc_sat_position(epoch)
                    #print(pos)
                    poss.append((sat_name, pos))
                    break
            return poss
        return filter
    epoch = 1600 * timeKM.TIME_A_WEEK + 431748 + 3600 * 5
    print("\n")
    print("satellite position calculation test:")
    #print("epoch: " + str(epoch))
    func = create_filter(epoch)                         #　関数を生成
    poss = func(system_name, storage)                   # 生成した関数を使って衛星座標を計算
    for pos in poss:                                    # 計算んできた衛星座標を表示
        name, position = pos
        print("{0}: {1}".format(name, position))


    # 可視衛星の確認
    print("\n")
    print("available:")
    origin = coor.blh(32.0, 130.0, 0.0, unit="degree") # 可視状態を計算する原点
    for pos in poss:
        name, position_ecef = pos                       # posはタプルになっているので、要素毎に分ける
        enu = position_ecef.to_enu(origin)              # 座標をENU座標系へ変換
        hoge = ""
        elevation = enu.elevation_degree                # 仰角を取得
        if elevation < 0:                               # 状況を表示
            hoge = "not available"
        else:
            hoge = "available"
        print("{0}: {1:.1f}, {2}".format(name, elevation, hoge))



if __name__ == '__main__':
    main()
