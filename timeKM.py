#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        timeKM.py
# Purpose: 時刻関係の演算手段（特にGPS関係）を提供する。
#
# Author:      morishita
#
# Created:     12/01/2012
# Copyright:   (c) morishita 2012
# Licence:     New BSD License
# Memo: ユリウス日とは、元期BC4713年1月1.5日から数えた平均太陽日で定義される。1日の始まりは真昼である。
#       修正ユリウス日とは、ユリウス日から2,400,000.5日を差し引いたものであり、端数0.5をつけることで1日の始まりを真夜中にしたものである。
# Update history information:
#               2012/1/13   Rubyで構築した関数を全て移植した。
#                           初めての実用的なPythonコーディングなのでよく分からないところが多い。。
#                           また、うるう年をチェックする関数IsLeapYear()と年と月を指定すると月末日を返す関数Get_LastDayOfMonth()を追加整備した。
#                           ユリウス日を求める演算も、1900年3月以前が計算可能な関数を整備した。
#                           いくつかの関数ではエラー対策を追加している。
#               2012/2/18   正規表現を利用した時刻オブジェクトを返す関数を整備。また、Python3エンジンでエラーが起きたので修正。
#               2012/12/25  Get_Delimited_hhmmss_From_hhmmss()とCompareTime()を追加
#               2013/1/4    一部の文字処理でエラーが出ていたのを修正した。
#                           reDateGroupedPatternがss.ssssにもマッチするように変更し、getTime()が時刻をμ秒単位まで認識するようにした。
#-------------------------------------------------------------------------------
#!/usr/bin/env python

import re
import datetime

# 正規表現パターン
# [yyyy/MM/dd hh:mm:ss]または[yyyy-MM-dd hh:mm:ss]にヒットする。(/|-)で、/か-で区切られた日付にヒットする。また、?:を付けるとグループ化されない
reDateGroupedPattern = re.compile(r'(?P<time>(?P<date>(?P<year>\d{4})(?:/|-)(?P<month>\d{1,2})(?:/|-)(?P<day>\d{1,2}))\ (?P<clock>(?P<hour>\d{1,2}):(?P<minute>\d{1,2}):(?P<sec>\d{1,2})([.](?P<microsecond>\d+))?))')
# hoge

# 各種定数
GPSepoch_JD = 2444244.5			# ユリウス日表現によるGPSの開始エポック
listOfWeekName = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT", "N/A"]
WEEK_ERROR = 7
listOfMonthName = ["Dummy", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
dictOfMonthNameAndNum = {"Jan":1, "Feb":2, "Mar":3, "Apr":4, "May":5, "Jun":6, "Jul":7, "Aug":8, "Sep":9, "Oct":10, "Nov":11, "Dec":12}
dictOfLastDayOfMonth = {"Jan":31, "Feb":28, "Mar":31, "Apr":30, "May":31, "Jun":30, "Jul":31, "Aug":31, "Sep":30, "Oct":31, "Nov":30, "Dec":31}
TIME_A_DAY = 86400.0


def getTime(oneDataStr):
    """ 文字列から時刻を抽出して、時刻オブジェクトを返す

    Args:
        oneDataStr: 解析したい文字列
    Return:
        datetime.datetime: 正常な処理が行われると、時刻オブジェクトを返す
        None:              文字列が不正
    """
    matchTest = reDateGroupedPattern.search(oneDataStr)
    if matchTest != None:
        #print(matchTest.groups())
        year   = int(matchTest.group('year'))
        month  = int(matchTest.group('month'))
        day    = int(matchTest.group('day'))
        hour   = int(matchTest.group('hour'))
        minute = int(matchTest.group('minute'))
        sec    = int(matchTest.group('sec'))
        _microsecond   = matchTest.group('microsecond')                             # このままでは単位が必ずしもμsにはならないので、以下で単位を変換する
        if _microsecond != None:
            microsecond  = int(int(_microsecond) * 10**(6 - len(_microsecond)))     # datetimeオブジェクトを使うとGNSS分野で有効桁が少々足りないのだが・・・実用上は問題ないと思う
        else:
            microsecond  = 0
        return datetime.datetime(year, month, day, hour, minute, sec, microsecond)
    else:
        return None

def getTimeSecondIgnored(oneDataStr):
    """ 文字列から時刻を抽出して、時刻オブジェクトを返す

    時刻の内、秒を無視します。
    Args:
        oneDataStr: 解析したい文字列
    Return:
        datetime.datetime: 正常な処理が行われると、時刻オブジェクトを返す
        None:              文字列が不正
    """
    matchTest = reDateGroupedPattern.search(oneDataStr)
    if matchTest != None:
        #print(matchTest.groups())
        year   = int(matchTest.group('year'))
        month  = int(matchTest.group('month'))
        day    = int(matchTest.group('day'))
        hour   = int(matchTest.group('hour'))
        minute = int(matchTest.group('minute'))
        return datetime.datetime(year, month, day, hour, minute, 0, 0)
    else:
        return None
    return

def CompareTime(time1 = "2012/1/1 0:0:0", time2 = "2012/1/2 10:10:10"):
    """ 文字列形式の日付（時刻付）の比較を行います

    Args:
        time1: 比較対象
        time2: 比較物
    Returns:
        time1がtime2よりも過去であれば、true
    """
    t1 = getTime(time1)
    t2 = getTime(time2)
    if t1 != None and t2 != None:
        return t2 > t1
    else:
        return None

def IsLeapYear(year):
    """ うるう年かどうかを判定する.

    Args:
        year: 年
    Returns:
        うるう年であればｔｒｕｅを返します。
    """
    _year = int(year)
    if _year % 4 == 0 and _year % 100 != 0 or _year % 400 == 0:
        return True
    else:
        return False

def Get_LastDayOfMonth(year, month):
    """ 指定した年と月における最終日を返す.

    Args:
        year: 年
        month: 月
    Returns:
        指定された年・月の日付を返します。
    """
    _year = int(year)
    _month = int(month)
    nameOfmonth = listOfMonthName[_month]
    _lastDayOfMonth = dictOfLastDayOfMonth[nameOfmonth]
    if _month == 2 and IsLeapYear(_year):
        _lastDayOfMonth += 1
    return _lastDayOfMonth


def Get_GPSday_From_JulianDate(jd):
    """ ユリウス日をGPS日に変換する.

    """
    return float(jd) - GPSepoch_JD

def Get_GPSweek_From_JulianDate(jd):
    """ ユリウス日をGPS週番号に変換する.

    """
    _gpsDays = Get_GPSday_From_JulianDate(float(jd))
    _gpsWeek = int(_gpsDays / 7)
    return _gpsWeek

def Get_ModifiedJulianDate_From_JuliusDate(jd):
    """ ユリウス日を修正ユリウス日に変換する.

    """
    return float(jd) - 2400000.5

def Get_JulianDate_From_Arrayed_yyyyMMdd(date = ["2011","1","21"], ssssss = 0.0):
    """ 年・月・日が入った配列（要素3つ）から、1900.3-2100.2の間で使えるユリウス日を返す.

    引数の要素は文字列でも数値でも構いません。
    GPS理論と応用pp.44-45を参考にしました。

    引数date：日付を年月日の順で納めた配列
    引数ssssss：時間[s]（例えば、午前3時なら3*3600です）
    引数の例：['2011','1','21'] (== 2011年1月1日), 500.0
    """
    year = int(date[0])
    month = int(date[1])
    day = int(date[2])
    if month <= 2:
        y = year -1
        m = month + 12
    else:
        y = year
        m = month
    _fractional_part = ssssss / TIME_A_DAY  # 1日の端数を計算
    julianDate = float(int(365.25 * y)) + float(int(30.6001 * (m + 1))) + float(day) + _fractional_part + 1720981.5
    return julianDate                       # Julian date

def Get_JulianDate_From_Arrayed_yyyyMMdd2(date = ["2011","1","21"], ssssss = 0.0):
    """ 年・月・日が入った配列（要素3つ）から、1900.3-2100.2の間で使えるユリウス日を返す.

    引数の要素は文字列でも数値でも構いません。
    演算アルゴリズムはWikipediaを参考にしました。
    出典はJean Meeus, Astronomical Formulae for Calculators, Fourth ed., Willmann-Bell Inc., 1982　とのことですが、原書を確認したわけではありません。
    GPS理論と応用pp.44-45のアルゴリズムと比較すると、1900年3月以降では完全に一致していました。
    また、1900年1月1日～1900年2月29日の演算結果が正しいことは確認済みです。
    これ以前の演算結果に関しては自己責任でご利用ください。

    引数date：日付を年月日の順で納めた配列
    引数ssssss：時間[s]（例えば、午前3時なら3*3600です）
    引数の例：['2011','1','21'] (== 2011年1月1日), 500.0
    """
    year = int(date[0])
    month = int(date[1])
    day = int(date[2])
    if 1 <= month <= 2:
        y = year -1
        m = month + 12
    elif month < 1 or month > 12:
        raise ValueError("月の指定に誤りがあります。0以下であったり13以上になっていないか確認してください。")
    else:
        y = year
        m = month
    if (year == 1582 and month == 10 and day >= 15) or (year == 1582 and month > 10) or year > 1582: # 1582年10月15日以降と判断する
        A = int(y / 100)
        B = 2 - A + int(A / 4)
    else:
        B = 0
    _fractional_part = ssssss / TIME_A_DAY  # 1日の端数を計算
    jd = int(365.25 * y) + int(30.6001 * (m + 1)) + day + _fractional_part + 1720994.5 + B
    return jd                               # Julian date

def Get_JulianDate_From_yyyyMMdd(date):
    """ "yyyymmdd"形式の年月日(数値もしくは文字列)をユリウス日へ変換する.

    引数の例： "20100504" == 2010年5月4日
    """
    year  = int(date)  / 10000
    month = (int(date) % 10000) / 100
    day   = int(date)  % 100
    dateArray = [year, month, day]
    return Get_JulianDate_From_Arrayed_yyyyMMdd2(dateArray)

def Get_DayOfWeek_From_DelimitedDate(date = "2010.3.30"):
    """ スラッシュ（/）やドット（.）で区切られた文字列での日付を受け取り、GPSで云う曜日番号を返す.

    一度ユリウス日を求め、そそれからGPS日（開始エポック1980年1月6日）を求めて、
    それを7で割った余りを求めることで曜日を求めています。
    従ってこの計算アルゴリズムの有効期限はConvert_yyyyMMddArrayToJulius()に依存します。
    ユリウス日は平均太陽日で定義されるので、GPSの1日とは違います。
    日付変更の微妙な時間を使おうとしても誤る可能性があることを念頭に入れておいてください。
    引数のdateは、"."又は"/"で分割された年月日の順で文字列表現の数値が入っている必要がある。
    引数の例： "2010/5/30"
    """
    _date_arr = date.split("/")             # 年月日に分割
    if len(_date_arr) == 1:
        _date_arr = date.split(".")

    if len(_date_arr) == 3:
        jd = Get_JulianDate_From_Arrayed_yyyyMMdd2(_date_arr)
        return (Get_GPSweek_From_JulianDate(jd) % 7)
    else:
        raise ValueError("引数の解析エラーが発生しました。引数で渡された日付はyyyy/MM/ddまたはyyyy.MM.dd形式となっていますか？")

def Get_DayOfYear_From_DelimitedDate(date = "2010.3.30"):
    """ スラッシュ（/）やドット（.）で区切られた文字列での日付を受け取り、その年の元旦から数えて何日目なのかを返す.

    指定された日付と元旦のユリウス日を計算して、その差を出力します。
    従ってこの計算アルゴリズムの有効期限はConvert_yyyyMMddArrayToJulius()に依存します。
    ユリウス日は平均太陽日で定義されるので、GPSの1日とは違います。
    日付変更の微妙な時間を使おうとしても誤る可能性があることを念頭に入れておいてください。
    引数のdateは、"."又は"/"で分割された年月日の順で文字列表現の数値が入っている必要がある。
    引数の例： "2010/3/30"
    """
    _date_arr = date.split("/")             # 年月日に分割
    if len(_date_arr) == 1:
        _date_arr = date.split(".")

    if len(_date_arr) == 3:
        _julius_day = Get_JulianDate_From_Arrayed_yyyyMMdd2(_date_arr)
        _date_arr[1] = 1                    # 同年の1月1日のユリウス日を求める
        _date_arr[2] = 1
        _julius_day_1m1d = Get_JulianDate_From_Arrayed_yyyyMMdd2(_date_arr)
        return int(_julius_day - _julius_day_1m1d + 1)
    else:
        raise ValueError("引数の解析エラーが発生しました。引数で渡された日付はyyyy/MM/ddまたはyyyy.MM.dd形式となっていますか？")

def Get_GPSweek_From_DelimitedDate(date = "2010.3.30"):
    """ スラッシュ（/）やドット（.）で区切られた文字列での日付を受け取り、GPS週番号を返す.

    一度ユリウス日を求め、それからGPS日（開始エポック1980年1月6日）を求めて、
    それを7で割ることでGPS週番号を求めています。
    従ってこの計算アルゴリズムの有効期限はConvert_yyyyMMddArrayToJulius()に依存します。
    さらに、ユリウス日は平均太陽日で定義されるので、GPSの1日とは違います。
    日付変更の微妙な時間を使おうとしても誤る可能性があることを念頭に入れておいてください。
    引数のdateは、"."又は"/"年月日の順で文字列表現の数値が入っている必要がある。
    引数の例： "2010/3/30"
    """
    _date_arr = date.split("/")             # 年月日に分割
    if len(_date_arr) == 1:
        _date_arr = date.split(".")

    if len(_date_arr) == 3:
        jd = Get_JulianDate_From_Arrayed_yyyyMMdd2(_date_arr)
        return Get_GPSweek_From_JulianDate(jd)
    else:
        raise ValueError("引数の解析エラーが発生しました。引数で渡された日付はyyyy/MM/ddまたはyyyy.MM.dd形式となっていますか？")

def Get_DayOfWeek_From_yyyyMMdd(date = "20100530"):
    """ 日付yyyyMMdd(文字列/数値)から曜日を得る.

    曜日の計算にはツェラーの公式の変形式を用いる。
    2100や1900年は計算できません。
    引数の例： "20100530" == 2010年5月30日
    """
    sun = 0                                 # 便宜上の曜日定義。GPS時刻に合わせて、日曜日を0とする。
    sat = 6

    _date = int(date)
    _week = WEEK_ERROR                      # そのまま返ればエラー

    if _date < 20991231 and _date > 19010101:
        year = int(_date / 10000)           # 小数点以下を切り捨て
        m = int((_date % 10000) / 100)      # mm
        if m > 12 or m < 1:                 # エラー対策:月の検査
            return _week
        q = _date % 100                     # day
        if q > dictOfLastDayOfMonth[listOfMonthName[m]] or q < 1:# エラー対策：日の検査
            return _week
        if m == 1 or m == 2:
            m += 12                         # 1,2月は前の年の13,14月として扱うため12を足す
            year -= 1                       # 同上の理由により1年引く
        j = int(year / 100)                 # yyyyの上位2桁
        k = year % 100                      # yyyyの下位2桁
        _week = (year + int(year / 4) - int(year / 100) + int(year / 400) + int((13 * m + 8) / 5) + q) % 7
        if _week < sun or _week > sat:
            _week = WEEK_ERROR              # もしものエラー回避
    return _week

def Get_ssssss_From_hhmmss(time = "134059"):
    """ 時刻hhmmssから、0時からの経過時間ssssss[s]を計算する.

    """
    _time = int(time)
    time_ss = _time % 100
    time_mm = int((_time % 10000 - time_ss) / 100)
    time_hh = int(_time / 10000)
    _time = time_hh * 3600 + time_mm * 60 + time_ss
    return _time

def Get_ssssss_From_Delimited_hhmmss(time = "21:36:54"):
    """ 文字列の時刻“hh:mm:ss”から、時刻ssssss[s]を計算する

	ex. 01:02:06 -> 3726(== 3600+120+6)
    """
    _time_arr = time.split(":")                 # 時分秒に分割
    time_ss = int(float(_time_arr[2]))
    time_mm = int(_time_arr[1])
    time_hh = int(_time_arr[0])
    time_value = time_hh * 3600 + time_mm * 60 + time_ss
    return time_value

def Get_ssssss_From_Delimited_hhmmss2(time = "21:36.54"):
    """ 文字列の時刻"hh:mm.ss"から、時刻ssssss[s]を計算する.

	ex. "01:02.06" -> 3726(== 3600+120+6)
    """
    _time_arr  = time.split(":")			# 時,分秒に分割
    _time_arr2 = _time_arr[1].split(".")	# 分,秒に分割
    time_ss    = int(_time_arr2[1])
    time_mm    = int(_time_arr2[0])
    time_hh    = int(_time_arr[0])
    time_value = time_hh * 3600 + time_mm * 60 + time_ss
    return time_value

def Get_Delimited_hhmmss_From_ssssss(ssssss = "56223"):
    """ ssssss形式の時間を"hh:mm:ss"形式へ変換する.

    """
    _time = int(ssssss)
    return str(int(_time / 3600)) + ":" + str(int((_time % 3600) / 60)) + ":" + str(int(_time % 60))

def Get_Delimited_hhmmss_From_hhmmss(time = "213654"):
    """ 文字列の時刻“hhmmss”から、時刻hh:mm:ssを計算する

	ex. 10206 -> 1:2:6
    """
    _timef = float(time)
    _time = int(_timef)
    time_ss = _timef % 100
    time_mm = int((_timef % 10000 - time_ss) / 100)
    time_hh = int(_time / 10000)
    _time = str(time_hh) + ":" + str(time_mm) + ":" + str(time_ss)
    return _time

def Get_hhmmss_From_ssssss(ssssss = "56223"):
    """ 0時からの経過時間ssssss[s]を時刻hhmmssへ変換する.

	ex. 3726(==3600+120+6) -> 10206(==01:02:06)
    """
    _time = int(ssssss)
    if _time < 0:
        _time += 86400
    _time = _time % 86400
    _time  = int(_time / 3600) * 10000 + int((_time % 3600) / 60) * 100 + _time % 60
    return _time

def Get_JST_From_UTC(ssssss = "56223"):
    """ ssssss[s]形式のUTC時間をssssss[s]形式のJSTへ変換する.

    """
    _time = int(ssssss)
    return (_time + 3600 * 9) % (24 * 3600)

def Get_ddMMyy_From_yyyyMMdd(date = "20100530"):
    """ yyyymmdd形式の日付をNMEAのddMMyy形式へ変換する.

    """
    date_v = int(date)         # 文字列であれば、数値に直して格納する。
    _yyyy = date_v / 10000
    _mm   = (date_v % 10000) / 100
    _dd   = date_v % 100
    return _yyyy % 100 + _mm * 100 + _dd * 10000

def Get_ddmmyy_From_Delimited_yyyyMMdd(date = "2010/05/30"):
    """ "yyyy/mm/dd"又は"yyyy.mm.dd"形式の日付をNMEAのddmmyy形式へ変換する.

    """
    _date_arr = date.split("/")             # 年月日に分割
    if len(_date_arr) == 1:
        _date_arr = date.split(".")
    _yyyy = _date_arr[0]
    _mm   = _date_arr[1]
    _dd   = _date_arr[2]
    return (int(_yyyy) % 100) + (int(_mm) * 100) + (int(_dd) * 10000)

def Get_Delimited_yyyyMMdd_From_Delimited_MMddyyyy(date = "2/30/2012"):
    """ "MM/dd/yyyy"形式の日付を"yyyy/MM/dd"形式へ変換する.

    """
    _date_arr = date.split("/")
    if len(_date_arr) == 1:
        _date_arr = date.split(".")
    _yyyy = _date_arr[2]
    _mm   = _date_arr[0]
    _dd   = _date_arr[1]
    return _yyyy + "/" + _mm + "/" + _dd

def Get_Delimited_yyyyMMdd_From_Delimited_ddMMyyyy(date = "30/2/2012"):
    """ "dd/MM/yyyy"形式の日付を"yyyy/MM/dd"形式へ変換する.

    """
    _date_arr = date.split("/")
    if len(_date_arr) == 1:
        _date_arr = date.split(".")
    _yyyy = _date_arr[2]
    _mm   = _date_arr[1]
    _dd   = _date_arr[0]
    return _yyyy + "/" + _mm + "/" + _dd

def Get_ExcelTime_From_yyyyMMdd_and_ssssss(date = "20120113", ssssss = 0.0):
    """ yyyymmdd形式の日付とssssss表現の時刻から、Excelで使用可能な時刻へ変換する.

    引数の型は、文字列でも数値でも良い

	エクセルの時刻表現は、1900/1/1を基準とした日数と、午前0時を基準とした秒数（ssssss）の割合である小数部で表される。
    """
    _fractional_part = float(ssssss) / TIME_A_DAY  # 1日の端数を計算
    return Get_JulianDate_From_yyyyMMdd(int(date)) - Get_JulianDate_From_Arrayed_yyyyMMdd2("1900/1/1".split("/")) + _fractional_part

def main():
    print("セルフテスト& サンプルコード（コードを読んで下さい）")
    print("うるう年判定 " + "2000年: " + str(IsLeapYear(2000)) + ", 2001年: " + str(IsLeapYear(2001)) + ", 2004年: " + str(IsLeapYear(2004)) + ", 2100年: " + str(IsLeapYear(2100)))
    print("月末日 " + "2000年2月: " + str(Get_LastDayOfMonth(2000, 2)) + ", 2001年2月: " + str(Get_LastDayOfMonth(2001, 2)))
    print("GPS日の演算テスト GPS元期 " + str(GPSepoch_JD) + ": " + str(Get_GPSday_From_JulianDate(GPSepoch_JD)) + ", 2000年1月1日: " + str(Get_GPSday_From_JulianDate(Get_JulianDate_From_Arrayed_yyyyMMdd2([2000, 1, 1]))))
    print("ユリウス日からGPS週番号を求めるテスト 1999年8月22日: " + str(Get_GPSweek_From_JulianDate(Get_JulianDate_From_Arrayed_yyyyMMdd2([1999, 8, 22]))))
    print("修正ユリウス日のテスト　GPS元期 " + str(GPSepoch_JD) + ": " + str(Get_ModifiedJulianDate_From_JuliusDate(GPSepoch_JD)))
    print("ユリウス日のテスト　その1　リストを利用しています。 [2000, 1, 1](2000年1月1日): " + str(Get_JulianDate_From_Arrayed_yyyyMMdd([2000, 1, 1])))
    print("ユリウス日のテスト　その2  リストを利用しています。 [2000, 1, 1](2000年1月1日): " + str(Get_JulianDate_From_Arrayed_yyyyMMdd2([2000, 1, 1])))
    print("ユリウス日のテスト　その3↓\n演算アルゴリズムの異なる処理を2通り実行していますので比較してみてください。")
    for year in range(1899, 1903):
        print(str(year) + "/1/1, " + "Julian 1: " + str(Get_JulianDate_From_Arrayed_yyyyMMdd([year, 1, 1])) + ", Julian 2: " + str(Get_JulianDate_From_Arrayed_yyyyMMdd2([year, 1, 1])))
    print("ユリウス日のテスト　その4 　デリミタの無い日付yyyyMMddを使って計算しています。 20000101（2000年1月1日）: " + str(Get_JulianDate_From_yyyyMMdd(20000101)))
    print("曜日番号のテスト \"2000/1/1\": " + str(Get_DayOfWeek_From_DelimitedDate("2000/1/1")))
    print("年間の通算日のテスト \"2000/1/1\": " + str(Get_DayOfYear_From_DelimitedDate("2000/1/1")))
    print("日付文字列からGPS週番号を求めるテスト \"2000/1/1\": " + str(Get_GPSweek_From_DelimitedDate("2000/1/1")))
    print("日付から曜日を取得 2012年1月13日: " + listOfWeekName[Get_DayOfWeek_From_yyyyMMdd(20120113)])
    print("時分秒を指定して、通算秒を得るテスト 000130（0h1m30s）: " + str(Get_ssssss_From_hhmmss("000130")) + " s")
    print("デリミタの無い時分秒から、デリミタの有る時分秒へ変換するテスト 000130(0h1m30s)： " + Get_Delimited_hhmmss_From_hhmmss("000130"))
    print("時刻から通算秒を求めるテスト 134059（13h40m59s）: " + str(Get_ssssss_From_hhmmss(134059)))
    print("デリミタのある時刻から通算秒を求めるテスト その1 \"13:40:50\" :  " +  str(Get_ssssss_From_Delimited_hhmmss("13:40:59")))
    print("デリミタのある時刻から通算秒を求めるテスト その2 \"13:40.50\" :  " +  str(Get_ssssss_From_Delimited_hhmmss2("13:40.59")))
    print("通算秒からデリミタのある時刻文字列を求めるテスト 49259:  " + str(Get_Delimited_hhmmss_From_ssssss(49259)))
    print("通算秒からデリミタのない時刻を求めるテスト 49259:  " + str(Get_hhmmss_From_ssssss(49259)))
    print("通算秒表現の日本標準時（JST）をUTCへ変換するテスト49259: " + str(Get_JST_From_UTC(49259)) + " 見やすくするためにデリミタ付き時分秒: " + str(Get_Delimited_hhmmss_From_ssssss(Get_JST_From_UTC(49259))))
    print("デリミタの無い日付yyyyMMddをNMEAで使用されているddMMyyへ変換するテスト 20120101（2012年1月1日）: " + str(Get_ddMMyy_From_yyyyMMdd(20120101)))
    print("デリミタの有る日付\"yyyy/MM/dd\"をNMEAで使用されているddMMyyへ変換するテスト \"2012/1/1\": " + str(Get_ddmmyy_From_Delimited_yyyyMMdd("2012/1/1")))
    print(" \"MM/dd/yyyy\"形式の日付を\"yyyy/MM/dd\"形式へ変換するテスト \"5/25/2012\": " + str(Get_Delimited_yyyyMMdd_From_Delimited_MMddyyyy("5/25/2012")))
    print(" \"dd/MM/yyyy\"形式の日付を\"yyyy/MM/dd\"形式へ変換するテスト \"25/5/2012\": " + str(Get_Delimited_yyyyMMdd_From_Delimited_ddMMyyyy("25/5/2012")))
    print("デリミタの無い日付と通算秒からMicrosoft Office Excel時刻を計算するテスト 19000101（1900年1月1日）: " + str(Get_ExcelTime_From_yyyyMMdd_and_ssssss(19000101)) + ", 20000101（2000年1月1日）: " + str(Get_ExcelTime_From_yyyyMMdd_and_ssssss(20000101)))
    hoge = getTime("2012/12/29 6:48:3.5")
    hoge2 = getTime("2012/12/29 6:48:3")
    print(reDateGroupedPattern.pattern)
    pass
if __name__ == '__main__':
    main()
