#!/usr/bin/env python3
# -*- coding:utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        GPS
# Purpose:  IGSの放送歴を基に衛星軌道の計算を行い、各種アルゴリズムの確認を行うこと
# Memo:     GLONASSやQZSの計算も行いたいので、将来的な拡張がしやすいようにクラス構造はカチッと固めていません。
# Author:      morishita
#
# Created:     10/02/2014
# Copyright:   (c) morishita 2012
# Licence:     MIT
# Histroy:
#           2014/2/13    RINEXファイルからの読み込みまでの処理は整備完了した。
#                        後は衛星座標の計算だ。
#           2014/2/26    リリースできるほどになった。
#           2014/3/1     WGS84モジュールで定義した変数名変更へ対応
#                        時刻モジュールと楕円体モジュールと座標系モジュールを置換しやすいように改造
#                        readerクラスの初期化部分において、放送歴の拡張子部分をqzs用の"q"を取り除いた。
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
system_name = "GPS"

#定数など
value_pattern = r"[-]?\d[.]\d+[EeDd][\s+-]\d{1,2}"          # 文字列での数値表現
eph_pattern = re.compile(                                   # IGSのRINEXフォーマット放送暦に対応した正規表現
    r"(?P<sat_name>(?: \w)?\s?\d{1,2})" +                       # 衛星のPRN番号. グループ名をあえてprnとしないことでプログラムが簡素化されているので注意.
    r"\s(?P<epoch>\d{1,2} +\d{1,2} +\d{1,2} +\d{1,2} +\d{1,2} +\d{1,2}[.]\d+)" +  # この航法メッセージの基準エポック(GPS time)
    r"\s?(?P<sv_clock_bias>{0})".format(value_pattern) +        # クロック補正係数　クロックバイアス[s]
    r"\s?(?P<sv_clock_drift>{0})".format(value_pattern) +       # クロック補正係数　クロックドリフト速度[s/s]
    r"\s?(?P<sv_clock_drift_rate>{0})".format(value_pattern) +  # クロック補正係数　クロックドリフト変化率[s/s^2]
    r"\s?(?P<IODE>{0})".format(value_pattern) +                 # 軌道情報番号　Isuue of data, ephemeris
    r"\s?(?P<Crs>{0})".format(value_pattern) +                  # 軌道補正係数[m]
    r"\s?(?P<delta_N>{0})".format(value_pattern) +              # [rad/s]
    r"\s?(?P<M0>{0})".format(value_pattern) +                   # 平均近点角[rad]
    r"\s?(?P<Cuc>{0})".format(value_pattern) +                  # 軌道補正係数[rad]
    r"\s?(?P<e>{0})".format(value_pattern) +                    # 離心率
    r"\s?(?P<Cus>{0})".format(value_pattern) +                  # 軌道補正係数rad
    r"\s?(?P<SQRT_A>{0})".format(value_pattern) +               # 軌道半径[m^1/2]
    r"\s?(?P<TOE>{0})".format(value_pattern) +                  # エポック時刻（軌道）Time Of Ephemeris (sec of GPS week)
    r"\s?(?P<Cic>{0})".format(value_pattern) +                  # 軌道補正係数[rad]
    r"\s?(?P<OMEGA0>{0})".format(value_pattern) +               # 昇交点赤経Ω0[rad]
    r"\s?(?P<Cis>{0})".format(value_pattern) +                  # 軌道補正係数[rad]
    r"\s?(?P<i0>{0})".format(value_pattern) +                   # 軌道傾斜角[rad]
    r"\s?(?P<Crc>{0})".format(value_pattern) +                  # 軌道補正係数[m]
    r"\s?(?P<omega>{0})".format(value_pattern) +                # 近地点引数ω[rad]
    r"\s?(?P<OMEGA_dot>{0})".format(value_pattern) +            # Ωの変化率[rad/s]
    r"\s?(?P<i_dot>{0})".format(value_pattern) +                # i0の変化率[rad/s]
    r"\s?(?P<CODE_ON_L2ch>{0})".format(value_pattern) +
    r"\s?(?P<gps_week>{0})".format(value_pattern) +             # to go with TOE (Continuous number, not mod(1024)! )
    r"\s?(?P<L2_P_data_flag>{0})".format(value_pattern) +
    r"\s?(?P<sv_accuracy>{0})".format(value_pattern) +          # 測距精度？[m]
    r"\s?(?P<sv_health>{0})".format(value_pattern) +            # 衛星健康情報　0:OK 1～:不良
    r"\s?(?P<TGD>{0})".format(value_pattern) +                  # 群遅延[s] */
    r"\s?(?P<IODC>{0})".format(value_pattern) +                 # クロック情報番号　Issue of Data, Clock
    r"\s?(?P<TOM>{0})".format(value_pattern) +                  # transmission time of message (sec of GPS week, derived e.g. from Z-count in Hand \ Over Word (HOW)
    r"\s?(?P<fit_interval>{0})".format(value_pattern) +         # エフェメリスの有効期限[h]. Zero if not known. (see ICD-GPS-200, 20.3.4.4), 0: 4 hour, 1: 6 hour
    r"(?:" +                                                    # 省略可能とする
    r"\s?(?P<spare1>{0})".format(value_pattern) +
    r"\s?(?P<spare2>{0})".format(value_pattern) +
    r")?"
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
        self.prn = ""

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
    """ GPSのエフェメリスを読み込むクラス
    """
    def __init__(self):
        """
        """
        gnss_eph.reader.__init__(self, "\.\d{2}[nN]", eph_pattern, ephemeris)
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
                mem.prn = mem.sat_name              # 親クラスではPRN番号として処理しないのでメンバの設定を行う
                if mem.fit_interval == 0.0:         # fit intervalの調整. ref: RINEX 3.02 A18
                    mem.fit_interval == 4.0
                elif mem.fit_interval == 1.0:
                    mem.fit_interval = 6.0
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
        " 1 10  9 10  0  0  0.0-0.160860363394D-03-0.386535248253D-11 0.000000000000D+00\n" + \
        "    0.690000000000D+02 0.305937500000D+02 0.490449000598D-08-0.641460797771D+00\n" + \
        "    0.176765024662D-05 0.449971400667D-02 0.395439565182D-05 0.515361504936D+04\n" + \
        "    0.432000000000D+06 0.558793544769D-08 0.167197328015D+01 0.409781932831D-07\n" + \
        "    0.965529665683D+00 0.305468750000D+03 0.956638718151D+00-0.849392523465D-08\n" + \
        "    0.383587406527D-09 0.100000000000D+01 0.160000000000D+04 0.000000000000D+00\n" + \
        "    0.200000000000D+01 0.630000000000D+02-0.190921127796D-07 0.690000000000D+02\n" + \
        "    0.424800000000D+06 0.000000000000D+00 0.000000000000D+00 0.000000000000D+00\n" + \
        " 2 10  9 10  0  0  0.0-0.160860363394D-03-0.386535248253D-11 0.000000000000D+00\n" + \
        "    0.690000000000D+02 0.305937500000D+02 0.490449000598D-08-0.641460797771D+00\n" + \
        "    0.176765024662D-05 0.449971400667D-02 0.395439565182D-05 0.515361504936D+04\n" + \
        "    0.432000000000D+06 0.558793544769D-08 0.167197328015D+01 0.409781932831D-07\n" + \
        "    0.965529665683D+00 0.305468750000D+03 0.956638718151D+00-0.849392523465D-08\n" + \
        "    0.383587406527D-09 0.100000000000D+01 0.160000000000D+04 0.000000000000D+00\n" + \
        "    0.200000000000D+01 0.630000000000D+02-0.190921127796D-07 0.690000000000D+02\n" + \
        "    0.424800000000D+06 0.000000000000D+00 0.000000000000D+00 0.000000000000D+00\n" + \
        " 3 10  9 10  0  0  0.0-0.160860363394D-03-0.386535248253D-11 0.000000000000D+00\n" + \
        "    0.690000000000D+02 0.305937500000D+02 0.490449000598D-08-0.641460797771D+00\n" + \
        "    0.176765024662D-05 0.449971400667D-02 0.395439565182D-05 0.515361504936D+04\n" + \
        "    0.432000000000D+06 0.558793544769D-08 0.167197328015D+01 0.409781932831D-07\n" + \
        "    0.965529665683D+00 0.305468750000D+03 0.956638718151D+00-0.849392523465D-08\n" + \
        "    0.383587406527D-09 0.100000000000D+01 0.160000000000D+04 0.000000000000D+00\n" + \
        "    0.200000000000D+01 0.630000000000D+02-0.190921127796D-07 0.690000000000D+02\n" + \
        "    0.424800000000D+06 0.000000000000D+00\n" # 欠けたデータ
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
    ephs.sort(key=operator.attrgetter("prn"), reverse=True) # PRN番号順にソート
    print("ephemeris sort. --post--")
    print(ephs[0])
    print(ephs[1])

    # エフェメリスの整理
    storage = gnss_eph.organize(ephs)   #　衛星ごとに整理
    prn_nums = storage.keys()           # 衛星名（ここではPRN番号）を取得
    print("PRN numbers:")
    print(prn_nums)

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
