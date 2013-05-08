#!/usr/bin/env python3
# -*- coding:utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        ubloxParser
# Purpose:      ublox受信機の出力ログを処理するパーサです
#
# Author:      morishita
# Memo  :       ublox4Tのログで正常な処理を確認しています。
#               また、動作確認はPython3.2で確認済みです。
# Created:      10/02/2012
# Copyright:   (c) morishita 2012
# Licence:     new BSD
# History:      2012/5/6    GGAセンテンスに対する正規表現を改良して、南半球や西半球でも通用するようにした。他のセンテンスについては未対応。
#               2012/12/24  ublox-6Tに合わせて、GGA, VTGのパターンを更新した。
#               2012/12/25  getStoppingList()をgetLowVelocityList()へ改名し、処理データを後処理しやすいように日付情報を含めるようにした。
#                           また、ほぼ同様の機能であるgetHighVelocityList()を整備するとともに、引数を自由に設定できるように変更した。
#               2013/4/7    GGA用の正規表現に入り込んでいたバグを修正した。
#                           また、RMC用のパターンを用意した。
#               2013/4/8    getTotalOfSeconds()においてエラーへの対処がなかったので追加した。
#                           reZDAgroupPatternに、全体にヒットするグループ<sentence>を追加した。
#-------------------------------------------------------------------------------

import sys                          # argv を取得するため
import re                           # 正規表現を使うのでインポート
import GPS
import math
import timeKM

# 並びは、ublox 6Tのデフォルトの設定を参考にして、NMEAの出力順にソートしている。
# パターンがセンテンスごとに2つあるのは、各要素毎にグループマッチング取る場合と、センテンス全体のみにヒットさせる用途があるため。
# 後者はNMEAセンテンスの抽出に使用する。
reRMCpattern      = re.compile(r'\$GPRMC,\d+(?:\.\d+)?,[AV],\d+\.\d+,[NS],\d+\.\d+,[EW],(?:\d+\.\d+)?,(?:\d+\.\d+)?,\d{6},,,[ADN]\*')
reRMCgroupPattern = re.compile(r'(?P<sentence>\$GPRMC,(?P<clock>\d+(?:\.\d+)?),[AV],(?P<lat>\d+\.\d+),(?P<NorS>[NS]),(?P<lon>\d+\.\d+),(?P<EorW>[EW]),(?P<GroundSpeed>\d+\.\d+)?,(?P<directin>\d+\.\d+)?,(?P<ddMMyy>\d{6}),(?P<geomagneticDeclinationAngle>\d+\.\d+)?,(?P<GD_EorW>[EW])?,(?P<fixMode>[ADN])\*)')
reVTGpattern      = re.compile(r'\$GPVTG,(?:\d+\.\d+)?,T,.*,M,\d+\.\d+,N,\d+\.\d+,K,.*\*')                                                  # VTGセンテンスを文字列から発見する正規表現
reVTGgroupPattern = re.compile(r'(?P<sentence>\$GPVTG,(?P<degree>\d+\.\d+)?,T,.*,M,\d+\.\d+,N,(?P<velocity_kmPh>\d+\.\d+),K,.*\*)')
reGGApattern      = re.compile(r'\$GPGGA,\d+\.\d+,\d+\.\d+,[NS],\d+\.\d+,[EW],\d,\d+,\d+\.\d+,\d+\.\d,M,\d+\.\d,M,(?:\d+\.\d)?,\d*\*')      # GGAセンテンスを文字列から発見する正規表現
reGGAgroupPattern = re.compile(r'(?P<sentence>\$GPGGA,(?P<clock>\d+\.\d+),(?P<lat>\d+\.\d+),(?P<NorS>[NS]),(?P<lon>\d+\.\d+),(?P<EorW>[EW]),(?P<Fix_Mode>\d),(?P<SVs_Used>\d+),(?P<HDOP>\d+\.\d+),(?P<Alt_MSL>\d+\.\d),M,(?P<Alt_Geoid>\d+\.\d),M,(\d+\.\d)?,\d*\*)')  # GGAセンテンスを文字列から発見する正規表現
reZDApattern      = re.compile(r'\$GPZDA,\d+\.\d+,\d\d,\d\d,\d\d\d\d,\d\d,\d\d\*')                                                          # ZDAセンテンスを文字列から発見する正規表現
reZDAgroupPattern = re.compile(r'(?P<sentence>\$GPZDA,(?P<clock>\d+\.\d+),(?P<day>\d\d),(?P<month>\d\d),(?P<year>\d\d\d\d),\d\d,\d\d\*)')   # ZDAの中身をさらにグループ分けするのに使用するパターン。これだけだと、findallで検索かけた結果がタプルのリストとして返るので文字列結合が簡単に書けない。）
# 全NMEAを抽出するパターン
reNMEApattern     = re.compile('{0}|{1}|{2}|{3}'.format(
            reZDApattern.pattern,
            reGGApattern.pattern,
            reVTGpattern.pattern,
            reRMCpattern.pattern
            ))                      # NMEAセンテンスにヒットする正規表現

def extractNMEAfromText(txt):
    """ NMEAを引数で渡されたテキストから抽出して返す
    テキストファイルの形式はbytesのバイナリ形式でも構いません。
    ubloxの搬送波位相を含むバイナリデータからNMEAを抽出するなどの用途に使用してください。
    """
    if isinstance(txt, bytes) == True:                      # バイナリデータかどうかを確認する
        _txt = txt.decode("ascii", errors='ignore')         # バイナリなら、ascii文字列化する
    else:
        _txt = txt
    _NMEAlist = reNMEApattern.findall(_txt)                 # 文字列からNMEAパターンに合致するデータを抽出してリスト化
    return '\n'.join(_NMEAlist)                             # リストを改行コードを持って結合させる

def getBLHfromGGA(GGA):
    """ GGAセンテンスを解析し、BLHを返す
    高度は楕円体高[m]です。
    解析に失敗するとNoneが返されます。
    """
    matchTest = reGGAgroupPattern.search(GGA)
    if matchTest != None:
        lat = float(matchTest.group('lat'))
        lon = float(matchTest.group('lon'))
        msl = float(matchTest.group('Alt_MSL'))
        geoid = float(matchTest.group('Alt_Geoid'))
        ellipsoid = msl + geoid                             # 楕円体高
        _lat = float(int(lat / 100.0)) + (lat % 100.0) / 60.0  # 単位を度に統一
        _lon = float(int(lon / 100.0)) + (lon % 100.0) / 60.0
        return GPS.BLH(_lat, _lon, ellipsoid)
    return None

def getTotalOfSeconds(GGA):
    """ GGAセンテンスより時刻を抜き出し、単位を秒とする通算秒（一日の中での時刻，最大86400.0）を返す
    """
    matchTest = reGGAgroupPattern.search(GGA)
    if matchTest != None:
        clock = float(matchTest.group('clock'))
        hour = float(int(clock / 10000.0))
        min = float(int((clock - hour * 10000.0) / 100.0))
        sec = float(clock % 100.0)
        return hour * 3600.0 + min * 60.0 + sec
    else:
        return None

def getDifferenceOfTOS(tos1, tos2):
    """ 2つのTOS（通算秒）から時間差[s]を返す
    tos1 - tos2を計算します。
    ただし、計算結果が負になった場合は日付が変更したとみなして86400.0を足します。
    """
    diff = tos1 - tos2
    if diff < 0.0:
        diff += 86400.0
    return diff

def getLowVelocityList(txt, threshold, timeWidthTh = 120.0):
    """ NMEAログを解析して、指定された閾値よりも低速な時間帯のリストを返す
    静止している時間帯を抽出することができます。
    VTGセンテンスとGGAセンテンスおよびZDAを使用するので、これらの含まれないログについては（全く考慮していないので予期しない）エラーが発生します。

    Args:
        txt:          NMEAを含むテキストデータ
        threshold:    閾値[m/h]
        timeWidthTh:  状態の最低継続時間の閾値[s]
    Returns:
        閾値よりも低速と判定された時間帯の情報のリスト
    """
    _searchStartIndex = 0
    _start = 0
    _end = 0
    _startGGA = ""
    _startClock = ""
    status = False
    ans = []
    while True:
        match = reVTGgroupPattern.search(txt, _searchStartIndex)        # VTGセンテンスを走査する
        if match == None:                                               # マッチするものがなくなれば、ループを抜ける
            break
        else:
            _searchStartIndex = match.end()                             # 次の走査開始インデックスをセット
            velocity = float(match.group('velocity_kmPh'))              # 解析結果から、速度を取得する
            if velocity < threshold:                                    # 条件をクリアするかどうかをチェック
                if status == False:
                    _start = match.start()
                    match = reGGAgroupPattern.search(txt, _searchStartIndex)
                    _startGGA =  match.group('sentence')
                    match = reZDAgroupPattern.search(txt, _searchStartIndex)
                    clock = timeKM.Get_Delimited_hhmmss_From_hhmmss(match.group('clock'))
                    _startClock = match.group('year') + "/" + match.group('month') + "/" +match.group('day') + " " + clock
                status = True
            else:
                if status == True:
                    _end = match.end()
                    _endGGA =  reGGAgroupPattern.search(txt, _searchStartIndex).group('sentence')
                    timeWidth = getDifferenceOfTOS(getTotalOfSeconds(_endGGA), getTotalOfSeconds(_startGGA))    # 静止期間[s]を計算
                    if timeWidth >= timeWidthTh:                                                                # 十分に長い期間であれば以下を処理
                        print((_startGGA, timeWidth, _start, _end))
                        lat = GPS.Convert_dddmm2ddd(reGGAgroupPattern.search(_startGGA).group('lat'))           # 緯度・経度を取得する
                        lon = GPS.Convert_dddmm2ddd(reGGAgroupPattern.search(_startGGA).group('lon'))
                        ans.append((_startClock, lat, lon, timeWidth, _start, _end))                            # 抜き出された情報をタプルにして、リストに追加
                status = False
    return ans

def getHighVelocityList(txt, velocityThreshold, timeWidthTh = 120.0):
    """ NMEAログを解析して、指定された閾値よりも高速な時間帯のリストを返す
    移動している時間帯を抽出することができます。
    VTGセンテンスとGGAセンテンスおよびZDAを使用するので、これらの含まれないログについては（全く考慮していないので予期しない）エラーが発生します。

    Args:
        txt:                NMEAを含むテキストデータ
        velocityThreshold:  閾値[m/h]
        timeWidthTh:        状態の最低継続時間の閾値[s]
    Returns:
        閾値よりも高速と判定された時間帯の情報のリスト
        タプルがリストに入っています。
    """
    _searchStartIndex = 0
    _start = 0
    _end = 0
    _startGGA = ""
    _startClock = ""
    status = False
    ans = []
    while True:
        match = reVTGgroupPattern.search(txt, _searchStartIndex)        # VTGセンテンスを走査する
        if match == None:                                               # マッチするものがなくなれば、ループを抜ける
            break
        else:
            _searchStartIndex = match.end()                             # 次の走査開始インデックスをセット
            velocity = float(match.group('velocity_kmPh'))              # 解析結果から、速度を取得する
            if velocity > velocityThreshold:                            # 条件をクリアするかどうかをチェック
                if status == False:
                    _start = match.start()
                    match = reGGAgroupPattern.search(txt, _searchStartIndex)
                    _startGGA =  match.group('sentence')
                    match = reZDAgroupPattern.search(txt, _searchStartIndex)
                    clock = timeKM.Get_Delimited_hhmmss_From_hhmmss(match.group('clock'))
                    _startClock = match.group('year') + "/" + match.group('month') + "/" +match.group('day') + " " + clock
                status = True
            else:
                if status == True:
                    _end = match.end()
                    _endGGA =  reGGAgroupPattern.search(txt, _searchStartIndex).group('sentence')
                    timeWidth = getDifferenceOfTOS(getTotalOfSeconds(_endGGA), getTotalOfSeconds(_startGGA))    # 静止期間[s]を計算
                    if timeWidth >= timeWidthTh:                                                                # 十分に長い期間であれば以下を処理
                        print((_startGGA, timeWidth, _start, _end))
                        lat = GPS.Convert_dddmm2ddd(reGGAgroupPattern.search(_startGGA).group('lat'))           # 緯度・経度を取得する
                        lon = GPS.Convert_dddmm2ddd(reGGAgroupPattern.search(_startGGA).group('lon'))
                        ans.append((_startClock, lat, lon, timeWidth, _start, _end))                            # 抜き出された情報をタプルにして、リストに追加
                status = False
    return ans

def main():
    print("test.")

if __name__ == '__main__':
    main()
