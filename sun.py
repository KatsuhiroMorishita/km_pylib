#! /usr/bin/env python
# -*- coding: utf-8 -*-
# name: sun
# author: Katsuhiro Morishita
# purpose: 日付から太陽の日の出と日没の時刻を求める
# created: 2014-08-11
# history: 2014-10-29 コメントを追加
# license: MIT
import datetime
import math
import calendar

def get_equation_of_time(epoch_utc):
    """ 均時差[h]を返す
    均時差とは、平均太陽時と実際の太陽時とのずれの近似値である。
    公転速度の変動（楕円軌道故に）と地軸の傾きの影響の補正項である。
    Argvs:
        epoch_utc:  datetime.datetime, 計算したい瞬間の時刻
    """
    first_day_of_year = datetime.datetime(epoch_utc.year, 1, 1)
    omega = 2.0 * math.pi * ((epoch_utc - first_day_of_year).total_seconds() / 24.0 / 3600.0) / 366
    theta = -0.0002789049 + 0.1227715 * math.cos(omega + 1.498311) \
        - 0.1654575 * math.cos(2.0 * omega - 1.261546) - 0.0053538 * math.cos(3.0 * omega - 1.1571)                    # http://www11.plala.or.jp/seagate/calc/calc2.html
    return theta



def get_seclination_of_sun(epoch_utc):
    """ 太陽赤緯[rad]を返す
    赤緯とは、赤道面からの仰俯角です。
    Argvs:
        epoch_utc:  datetime.datetime, 計算したい瞬間の時刻
    """
    first_day_of_year = datetime.datetime(epoch_utc.year, 1, 1)
    J = (epoch_utc - first_day_of_year).total_seconds() / 24.0 / 3600.0   # 1/1の0時からの経過日数
    #print(J)
    j = 365
    if calendar.isleap(epoch_utc.year):
        j += 1
    omega = 2.0 * math.pi / j
    # 方法その1
    #delta = 0.33281 \
    #    - 22.984 * math.cos(omega * J) - 0.34990 * math.cos(2.0 * omega * J) - 0.13980 * math.cos(3.0 * omega * J) \
    #    + 3.7872 * math.sin(omega * J) + 0.0325 * math.sin(2.0 * omega * J) + 0.07187 * math.sin(3.0 * omega * J)      # http://www11.plala.or.jp/seagate/calc/calc2.html
    #delta = delta * math.pi / 180.0
    # 方法その2
    delta = 0.006918 \
        - 0.399912 * math.cos(omega * J) - 0.006758 * math.cos(2.0 * omega * J) - 0.002697 * math.cos(3.0 * omega * J) \
        + 0.070257 * math.sin(omega * J) + 0.000907 * math.sin(2.0 * omega * J) + 0.001480 * math.sin(3.0 * omega * J) # http://www.es.ris.ac.jp/~nakagawa/met_cal/solar.html
    return delta



def get_sunrize_sunset_time(lat_deg, lon_deg, lon_origin_deg, date_utc):
    """ 日の出・日の入り時刻をタプルで返す
    精度は、5分以内です。
    Argvs:
        lon_origin_deg: float, 標準時経度。日本では135である。
    """
    lat = lat_deg * math.pi / 180.0
    lon = lon_deg * math.pi / 180.0

    # 太陽赤緯
    delta = get_seclination_of_sun(date_utc)
    # 中央標準時からのずれ[h]
    p = (lon_deg - lon_origin_deg) / 15.0
    # 均時差
    theta = get_equation_of_time(date_utc)
    # 日出・日没時刻[h]
    hoge = -math.tan(delta) * math.tan(lat) # -1 < tan(lat) < 1
    ac = math.acos(hoge)
    ang = (31.8 / 2.0 / 60.0 + 34.3333333 / 60.0) * 24.0 / 360.0      # 太陽の直径による視角度32'と大気差（屈折）の影響[h]
    rise = 12.0 - (ac / math.pi * 12.0 + p + theta) - ang
    down = 12.0 - (-ac / math.pi * 12.0 + p + theta) + ang

    origin = datetime.datetime(date_utc.year, date_utc.month, date_utc.day, 0, 0, 0)
    riseTime = origin + datetime.timedelta(hours=rise)
    downTime = origin + datetime.timedelta(hours=down)
    return (riseTime, downTime)



def get_sunrize_sunset_time2(lat_deg, lon_deg, lon_origin_deg, date_utc):
    """ 日の出・日の入り時刻をタプルで返す
    精度は、5分以内です。

    均時差と赤緯の計算に利用する時刻を日の出と日の入りでそれぞれ計算することで計算精度が上がるか確認した実験関数です。
    """
    rise, down = get_sunrize_sunset_time(lat_deg, lon_deg, lon_origin_deg, date_utc)
    # 日の出と日没時のより正確な均時差を求める
    thetaAtRise = get_equation_of_time(rise)
    thetaAtDown = get_equation_of_time(down)
    # 日の出と日没時のより正確な太陽赤緯を求める
    deltaAtRise = get_seclination_of_sun(rise)
    deltaAtDown = get_seclination_of_sun(down)

    lat = lat_deg * math.pi / 180.0
    # 中央標準時からのずれ[h]
    p = (lon_deg - 135) / 15.0
    # 太陽の直径32'による視角度と大気差（屈折）の影響[h]
    ang = (31.8 / 2.0 / 60.0 + 34.3333333 / 60.0) * 24.0 / 360.0

    # 日の出の時刻[h]
    hogehoge = -math.tan(deltaAtRise) * math.tan(lat)# -1 < tan(lat) < 1
    ac = math.acos(hogehoge)
    riseTime = 12.0 - (ac / math.pi * 12.0 + p + thetaAtRise) - ang
    # 日没時刻[h]
    hogehoge = -math.tan(deltaAtDown) * math.tan(lat)# -1 < tan(lat) < 1
    ac = math.acos(hogehoge)
    downTime = 12.0 - (-ac / math.pi * 12.0 + p + thetaAtDown) + ang

    origin = datetime.datetime(date_utc.year, date_utc.month, date_utc.day, 0, 0, 0)
    riseTime = origin + datetime.timedelta(hours=riseTime)
    downTime = origin + datetime.timedelta(hours=downTime)
    return (riseTime, downTime)




