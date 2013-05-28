#!/usr/bin/env python3
# -*- coding:utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        pressureLgger
# Purpose:      気圧ロガーを用いた実験のログを整理するためのスクリプト
#               ライブラリ的に用いる。
#
# Author:      morishita
#
# Created:     15/02/2012
# Copyright:   (c) morishita 2012
# Licence:     new BSD
# History:     2013/5/14    時刻に関する処理を削除して、timeKMモジュールを参照するように改めた。
#              2013/5/19    正規表現パターンを修正
#                           クラスのメソッドにsetlineを追加
#-------------------------------------------------------------------------------
import datetime
import re
import timeKM

reDataPattern        = re.compile(r'\d{4}/\d{1,2}/\d{1,2} \d{1,2}:\d{1,2}:\d{1,2},-?\d+\.\d+,\d+\.\d+,-?\d+\.?\d*,\d+')# AD変換値にはマイナスは付かないのだが、ここではキャリブレーション後を見越してつけておく
reDataGroupedPattern = re.compile(r'(?P<date>(?P<year>\d{4})/(?P<month>\d{1,2})/(?P<day>\d{1,2})) (?P<clock>(?P<hour>\d{1,2}):(?P<minute>\d{1,2}):(?P<second>\d{1,2})),(?P<other>(?P<SCP1000_Temperature>-?\d+\.\d+),(?P<SCP1000_Pressure>\d+\.\d+),(?P<Thermistor_Temperature>-?\d+\.?\d*),(?P<brightness>\d+))')

class PressureLogger:
    def __init__(self):
        """ 初期化する
        """
        self.SCP1000_Temperature = 0.0
        self.SCP1000_Pressure = 0.0
        self.Thermistor_Temperature = 0.0
        self.brightness = 0.0
        self.__count = 0.0
        return
    def setline(self, line):
        """ 文字列を解析して、パラメータをセットします
        フォーマットに合致した場合、Trueを返します。
        """
        self.SCP1000_Temperature = 0.0
        self.SCP1000_Pressure = 0.0
        self.Thermistor_Temperature = 0.0
        self.brightness = 0.0
        self.__count = 0.0
        matchTest = reDataGroupedPattern.search(line)
        if matchTest != None:
            self.SCP1000_Temperature = float(matchTest.group('SCP1000_Temperature'))
            self.SCP1000_Pressure = float(matchTest.group('SCP1000_Pressure'))
            self.Thermistor_Temperature = float(matchTest.group('Thermistor_Temperature'))
            self.brightness = float(matchTest.group('brightness'))
            return True
        else:
            return False
    def addForMean(self, scp1000Temp, scp1000Pressure, at103Temp, brightness):
        """ 平均化のために、引数で渡された数値を加算する
        mean()を実行すれば平均化します。
        """
        self.SCP1000_Temperature += float(scp1000Temp)
        self.SCP1000_Pressure += float(scp1000Pressure)
        self.AT103_Temperature += float(at103Temp)
        self.brightness += float(brightness)
        self.__count += 1.0
        return
    def mean(self):
        """ 平均化する
        算術平均です。
        最大とか最少とか外れ値とかは全く考慮しません。
        """
        self.SCP1000_Temperature /= self.__count
        self.SCP1000_Pressure /= self.__count
        self.AT103_Temperature /= self.__count
        self.brightness /= self.__count
        self.__count = 0.0
    def toString(self):
        """ データを文字列化して返す
        """
        return "{0:.2f},{1:.2f},{2:.1f},{3:.1f}".format(self.SCP1000_Temperature, self.SCP1000_Pressure, self.AT103_Temperature, self.brightness)

def getHealthyRate(txt):
    """ ファイルの正常なデータ割合を簡易計測して返す
    """
    tempList = txt.split('\n')                              # 改行コードで分割（ゴミデータも含まれている）
    healthyList = getHealthyDataList(txt)                   # ゴミデータを除いたデータに分割
    return float(len(healthyList)) / float(len(tempList))   # 割合を計算して返す

def getHealthyDataList(txt):
    """ テキストデータの実験ログから正常なデータのみを抽出してリストとして返す
    """
    return reDataPattern.findall(txt)

def getHealthyDataTxt(txt):
    """ テキストデータの実験ログから正常なデータのみを抽出してテキストデータとして返す
    改行コードを間に挟んだ文字列としてテキストデータを返します。
    """
    return '\n'.join(getHealthyDataList(txt))

def getClockDict(txt):
    """ テキストデータの実験ログから、時刻をキーとした辞書を作成して返す
    """
    ans  = {}
    dataList = getHealthyDataList(txt)      # 実験データからリストを作る
    for one in dataList:                    # リストを走査しながら時刻をキーとした辞書を作成
        time = timeKM.getTime(one)          # 時刻を取得
        ans.update(dict({time:one}))
    return ans

def checkline(line):
    """ 文字列を解析して、観測データであることを確認します
    フォーマットに合致した場合、Trueを返します
    """
    matchTest = reDataPattern.search(line)
    if matchTest != None:
        return (True, matchTest.group(0))
    else:
        return False, ""


def main():
    pass

if __name__ == '__main__':
    main()
