#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        time
# Purpose: 時刻関係の演算手段を提供する。
#
# Author:      morishita
#
# Created:     01/03/2014
# Copyright:   (c) morishita 2012
# Licence:     MIT
# Memo: 1) ユリウス日とは、元期BC4713年1月1.5日から数えた平均太陽日で定義される。1日の始まりは真昼である。
#       2) 修正ユリウス日とは、ユリウス日から2,400,000.5日を差し引いたものであり、端数0.5をつけることで1日の始まりを真夜中にしたものである。
#       3) QGSTとGPSTはほぼ同期している。うるう秒の扱いも同一。ただし、数n秒の差はある模様。
# Update history information:
#               2014/3/1   GPS用に作成したものをそのままコピー
#                          GPSTとQZSTの間にはナノ秒単位のずれがありますし、QZSは現時点では放送暦と最終暦の間で時刻系が異なります。
#                          QZSは仕様が固まるまで…もしくはGNSS測位について考えるようになったら考慮します。
#-------------------------------------------------------------------------------
import re
import decimal
import datetime
import timeKM

# 各種定数
GPSepoch_JD = 2444244.5			               # ユリウス日表現によるGPSの開始エポック
epoch_origin = datetime.datetime(1980, 1, 6)   # GPSの基準エポック(UTC)
leap_list = [                                  # うるう秒の挿入1秒後の時刻(UTC)
    datetime.datetime(1981, 7, 1, 0, 0, 0),    # ref: http://www.bugbearr.jp/?%E6%97%A5%E6%99%82/%E5%B9%B4%E8%A1%A8
    datetime.datetime(1982, 7, 1, 0, 0, 0),
    datetime.datetime(1983, 7, 1, 0, 0, 0),
    datetime.datetime(1985, 7, 1, 0, 0, 0),
    datetime.datetime(1988, 1, 1, 0, 0, 0),
    datetime.datetime(1990, 1, 1, 0, 0, 0),
    datetime.datetime(1991, 1, 1, 0, 0, 0),
    datetime.datetime(1992, 7, 1, 0, 0, 0),
    datetime.datetime(1993, 7, 1, 0, 0, 0),
    datetime.datetime(1994, 7, 1, 0, 0, 0),
    datetime.datetime(1996, 1, 1, 0, 0, 0),
    datetime.datetime(1997, 7, 1, 0, 0, 0),
    datetime.datetime(1999, 1, 1, 0, 0, 0),
    datetime.datetime(2006, 1, 1, 0, 0, 0),
    datetime.datetime(2009, 1, 1, 0, 0, 0),
    datetime.datetime(2012, 7, 1, 0, 0, 0),
]



def get_GPSday_From_JulianDate(jd):
    """ ユリウス日をGPS日に変換する.
    """
    return float(jd) - GPSepoch_JD

def get_GPSweek_From_JulianDate(jd):
    """ ユリウス日をGPS週番号に変換する.
    """
    _gpsDays = get_GPSday_From_JulianDate(float(jd))
    _gpsWeek = int(_gpsDays / 7)
    return _gpsWeek

def get_DayOfWeek_From_DelimitedDate(date = "2010.3.30"):
    """ スラッシュ（/）やドット（.）で区切られた文字列での日付を受け取り、GPSで云う曜日番号を返す.

    一度ユリウス日を求め、そそれからGPS日（開始エポック1980年1月6日）を求めて、
    それを7で割った余りを求めることで曜日を求めています。

    ユリウス日は平均太陽日で定義されるので、GPSの1日とは違います。
    日付変更の微妙な時間を使おうとしても誤る可能性があることを念頭に入れておいてください。
    引数のdateは、"."又は"/"で分割された年月日の順で文字列表現の数値が入っている必要がある。
    引数の例： "2010/5/30"
    """
    _date_arr = date.split("/")             # 年月日に分割
    if len(_date_arr) == 1:
        _date_arr = date.split(".")

    if len(_date_arr) == 3:
        jd = timeKM.get_JulianDate_From_Arrayed_yyyyMMdd2(_date_arr)
        jd_origin = timeKM.get_JulianDate_From_Arrayed_yyyyMMdd2([1980, 1, 6])
        return (jd - jd_origin) % 7
    else:
        raise ValueError("引数の解析エラーが発生しました。引数で渡された日付はyyyy/MM/ddまたはyyyy.MM.dd形式となっていますか？")


def get_GPSweek_From_DelimitedDate(date = "2010.3.30"):
    """ スラッシュ（/）やドット（.）で区切られた文字列での日付を受け取り、GPS週番号を返す.

    一度ユリウス日を求め、それからGPS日（開始エポック1980年1月6日）を求めて、
    それを7で割ることでGPS週番号を求めています。
    従ってこの計算アルゴリズムの有効期限はConvert_yyyyMMddArrayToJulius()に依存します。
    さらに、ユリウス日は平均太陽日で定義されるので、GPSの1日とは違います。
    日付変更の微妙な時間を使おうとしても誤る可能性があることを念頭に入れておいてください。
    引数のdateは、"."又は"/"年月日の順で文字列表現の数値が入っている必要がある。

    正確には、GPS週番号はGPS開始エポック（1980/1/6 0:0:0）からの経過時間[s]を1週間（3600*24*7）で割った日数をさらに7で割って求める。
    したがって、本関数で求まるGPS週番号はうるう秒分ずれることに注意。
    昼間の計算なら問題ありません。

    引数の例： "2010/3/30"
    """
    _date_arr = date.split("/")             # 年月日に分割
    if len(_date_arr) == 1:
        _date_arr = date.split(".")

    if len(_date_arr) == 3:
        jd = timeKM.get_JulianDate_From_Arrayed_yyyyMMdd2(_date_arr)
        return get_GPSweek_From_JulianDate(jd)
    else:
        raise ValueError("引数の解析エラーが発生しました。引数で渡された日付はyyyy/MM/ddまたはyyyy.MM.dd形式となっていますか？")


def convert_utc2leap_time(date):
    """ 指定日時におけるうるう秒を返す
    Argv:
        date: (UTC) <datetime.datetime> 日時
    Return:
        <int> うるう秒
    """
    leap = 0
    for t in leap_list:
        if t <= date:
            leap += 1
        else:
            break
    return leap

def convert_utc2gpst(date, A0="0.0", A1="0.0", Tot=None):
    """ GPS時刻を返す

    Argv:
        date: (UTC) <datetime.datetime> GPS時刻へ変換される日時
        A0:         <str>               補正パラメータ.  e.g. 0.186264514923e-08
        A1:         <str>               補正パラメータ.  e.g. 0.159872115546e-13
        Tot:  (UTC) <datetime.datetime> 補正パラメータの元期（基準日時）
              補正パラメータを無視しても誤差は15 ns以下のはずです。
    Return:
        <float> or <decimal.Decimal> GPS時刻[s]
                    <decimal.Decimal>, if type(Tot) != None
    """
    dt = date - epoch_origin
    #print(dt)
    dt = dt.total_seconds()              # 秒に直す
    gpst = dt + convert_utc2leap_time(date)      # うるう秒を足す
    if Tot != None:                      # 1秒未満分の補正. ref: RINEX 3.02 A17.
        #print("hoge")
        tot = (Tot - epoch_origin).total_seconds()
        #print(gpst)
        tot = decimal.Decimal(tot)                                                      # floatのままだと、有効数字が17桁しかないのでDecimalへ変換
        tot = tot.quantize(decimal.Decimal('.000001'), rounding=decimal.ROUND_DOWN)     # 18桁以降はゴミなので、捨てる。この捨て方はあと数十年は対応可能。
        gpst = decimal.Decimal(gpst)
        gpst = gpst.quantize(decimal.Decimal('.000001'), rounding=decimal.ROUND_DOWN)
        A0 = decimal.Decimal(A0)                                                        # 有効数字の桁数を確保するために、decimal型を利用
        A1 = decimal.Decimal(A1)
        #print((A0 + gpst - A1 * tot))
        gpst = (A0 + gpst - A1 * tot) / (decimal.Decimal("1.0") - A1)
        #print(gpst)
    return gpst

def convert_utc2gpsw(date, A0="0.0", A1="0.0", Tot=None):
    """ GPS週番号を返す
    うるう秒を考慮した値を返します。

    Argv:
        date: (UTC) <datetime.datetime> GPS週番号へ変換される日時
        A0:         <str>               補正パラメータ.  e.g. "0.186264514923e-08"
        A1:         <str>               補正パラメータ.  e.g. "0.159872115546e-13"
        Tot:  (UTC) <datetime.datetime> 補正パラメータの元期（基準日時）
              補正パラメータを無視しても誤差は15 ns以下のはずです。
    Return:
        <int> GPS週番号
    """
    return int(convert_utc2gpst(date, A0, A1, Tot) / timeKM.TIME_A_WEEK)





def main():
    print("---self test---")
    print("GPS日の演算テスト GPS元期 " + str(GPSepoch_JD) + ": " + str(get_GPSday_From_JulianDate(GPSepoch_JD)) + ", 2000年1月1日: " + str(get_GPSday_From_JulianDate(timeKM.get_JulianDate_From_Arrayed_yyyyMMdd2([2000, 1, 1]))))
    print("ユリウス日からGPS週番号を求めるテスト 1999年8月22日: " + str(get_GPSweek_From_JulianDate(timeKM.get_JulianDate_From_Arrayed_yyyyMMdd2([1999, 8, 22]))))
    print("修正ユリウス日のテスト　GPS元期 " + str(GPSepoch_JD) + ": " + str(timeKM.get_ModifiedJulianDate_From_JuliusDate(GPSepoch_JD)))
    print("日付文字列からGPS週番号を求めるテスト \"2000/1/1\": " + str(get_GPSweek_From_DelimitedDate("2000/1/1")))
    print("曜日番号のテスト \"2000/1/1\": " + str(get_DayOfWeek_From_DelimitedDate("2000/1/1")))
    now = datetime.datetime.utcnow()
    print("now (UTC): {0}".format(now))
    print("現時点でのうるう秒: {0} s".format(convert_utc2leap_time(now)))
    print("現時点でのGPS時刻: {0}".format(convert_utc2gpst(now)))
    print("現時点でのGPS週番号： {0}".format(convert_utc2gpsw(now)))

    # UTCとGPSTの間の差を計算するサンプル
    gpst = convert_utc2gpst(now)
    #print(gpst)
    gpst = decimal.Decimal(gpst)
    gpst = gpst.quantize(decimal.Decimal('.000001'), rounding=decimal.ROUND_DOWN)       # floatを基にしているのである桁以降はゴミ。それを捨てている。
    #print(gpst)
    diff = gpst - convert_utc2gpst(now, "0.186264514923e-08", "0.159872115546e-13", now)# UTCとGPS時刻との1秒以下の差分をも考慮した場合の差分を計算
    print("a example, GPST-UTC difference: {0:.20f}".format(diff))

if __name__ == '__main__':
    main()
