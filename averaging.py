#!/usr/bin/env python3
# -*- coding:utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        averaging
# Purpose:      時刻[yyyy/MM/dd hh:mm:ss][yyyy-MM-dd hh:mm:ss]と観測値からなる簡単なフォーマットのデータを平均します
# Abst.:        データファイルは時系列になっている必要があります。
#               平均化する期間は、エポック-term <= t <= エポック です。
#
#               mainでは、
#               データを取り出すのに時刻と観測値を対にした辞書を使っています。
#               従って、時間分解能を今より小さくすると時刻に一致しなくなりえるので将来的に問題になるかもしれません。
#               現在の時間分解能は1秒です。
#               もし、時間分解能を高めたい場合は、辞書を使った方法からforを使って全検索するようにしてください。
#               それで時間が掛かりすぎるなら、データベースの利用を想定した方が良いでしょう。
# Author:      morishita
#
# Created:     18/02/2012
# Copyright:   (c) morishita 2012
# Licence:     new BSD
# History:      2013/5/14   timeKMモジュールのフォルダへパスを通したので、実行時にパスを増やすコードを削除した。
#               2013/5/17   数値以外の入ったデータにもヒットしていたので、数字以外にヒットしないように変更した。
#                           timeKMモジュールの仕様変更に対応
#                           数値に、符号が入ってきてもOKなように変更
#                           NumBuffの中で、valが非値であるかどうか検査しきれていないのはかなり問題だ。
#-------------------------------------------------------------------------------
import datetime
import re
import sys
import timeKM

delta = 60              # 平均化する間隔[sec]
term = 60               # 平均化する期間[sec]
samplingRate = 0.5      # 観測データのサンプリング速度[SPS]又は[Hz], 欠損率の計算に使用しているだけなので、クリティカルな設定値ではない
missingThreshold = 0.8  # 欠損値の許容割合

reValuePattern       = re.compile(r'((?:-|\+)?\d+\.?\d*|NA|na|NaN)')
reDataPattern        = re.compile(r'(?P<all>{0}(?P<values>((?: |,|\t){1})+))'.format(timeKM.reDateGroupedPattern.pattern, reValuePattern.pattern))

class NumBuff:
    """ リストを渡すことで平均を計算するためのクラスです
    """
    def __init__(self):
        self.buffer = []
        self.errorMsg = ""
        self.count = []                                         # 加算数
        return

    def len(self):
        """ バッファに格納されているデータ長を返す
        """
        return len(self.buffer)

    def addForMean(self, addList):
        """ 後で平均化するために値（リスト）を受け取り、内部変数を加算する
        リストの中身は数値であること。
        非値や欠損値にも対応しています。
        途中で入力されるデータ数が増えても、それに対応してカウントを続けます。
        この関数を呼び出すと、meanを呼び出すまで内部変数が加算されます。
        """
        if type(addList) == list:
            if len(self.buffer) == 0:                           # 初回時の処理
                for member in addList:
                    if member != "" and member != "NA":
                        self.buffer.append(float(member))       # リストが空であれば、代入するだけ
                        self.count.append(1.0)                  # カウント数を初期化
                    else:
                        self.buffer.append(0.0)                 # 非値なので0.0で初期化
                        self.count.append(0.0)                  # カウント数を初期化
            else:
                for _i in range(len(self.buffer)):              # とりあえず、現時点で保有するリストのサイズ分だけ格納する
                    val = addList[_i]
                    if _i < len(addList) and val != "" and val != "NA": # 渡されたリストの要素数が少ないor非値の場合へ対処
                        self.buffer[_i] += float(val)
                        self.count[_i] += 1.0
                if len(self.buffer) < len(addList):                 # 既にあるバッファサイズを超えた場合
                    for _i in range(len(self.buffer), len(addList)):
                        val = addList[_i]
                        if val != "" and val != "NA":
                            self.buffer.append(float(val))  # リストが空であれば、代入するだけ
                            self.count.append(1.0)                  # カウント数を初期化
                        else:
                            self.buffer.append(0.0)                 # 非値なので0.0で初期化
                            self.count.append(0.0)                  # カウント数を初期化
            return
        else:
            return

    def mean(self):
        """ 平均する
        平均化したものをリストで返します。
        """
        for _i in range(len(self.buffer)):
            if self.count[_i] != 0.0:
                self.buffer[_i] /= self.count[_i]
            else:
                self.buffer[_i] = ""        # 欠損値
            self.count[_i] = 1.0
        return self.buffer

    def toString(self):
        """ 現時点で保持しているメンバーを文字列化して返す
        """
        ans = ""
        count = 0
        for member in self.buffer:
            if member != "" and member != "NA":
                ans += "{0:.5f}".format(member)
            else:
                ans += ""                   # 将来、NAにするかも
            count += 1
            if count != len(self.buffer):   # 最後の要素でなければ、カンマの区切り記号を入れる
                ans += ","
        return ans





def getHealthyDataList(txt):
    """ テキストデータの実験ログから正常なデータのみを抽出してリストとして返す
    """
    helthy = reDataPattern.finditer(txt)
    ans = []
    for men in helthy:
        ans.append(men.group('all'))
    return ans

def getClockDict(txt):
    """ テキストデータの実験ログから、時刻をキーとした辞書を作成して返す
    return:
        None: 正常な実験データが得られなかった場合
    """
    ans  = {}
    dataList = getHealthyDataList(txt)              # 実験データからリストを作る
    if len(dataList) == 0:
        return None
    #print(dataList[0])
    for one in dataList:                            # リストを走査しながら時刻をキーとした辞書を作成
        #print(one)
        time = timeKM.getTime(one)                  # 時刻を取得
        #print(time)
        ans.update(dict({time:one}))
    return ans

def getClockList(txt):
    """ テキストデータの実験ログから、時刻をリストに格納して返す
    return:
        None: 正常な実験データが得られなかった場合
    """
    ans  = []
    dataList = getHealthyDataList(txt)              # 実験データからリストを作る
    if len(dataList) == 0:
        return None
    #print(dataList[0])
    for one in dataList:                            # リストを走査しながら時刻をキーとした辞書を作成
        #print(one)
        time = timeKM.getTime(one)                  # 時刻を取得
        #print(time)
        ans.append(time)
    return ans

def getDataList(line):
    """ 時刻に続いてデーが格納されている文字列を解析して、データのみをリストとして返す
    区切り文字はタブ・カンマ・半角スペースです。
    タブとカンマは一つあれば分割しますが、半角スペースは連続してある場合も分割します。
    return:
        None: 時刻が文字列に含まれていない場合
    """
    match = reDataPattern.search(line)                      # 日付+データにマッチするかをチェック
    if match == None:
        return None
    else:
        values = match.group('values')
        return reValuePattern.findall(values)


def createAverageList(fname, step, span, epoch = None):
    """ 平均化した値を時刻と
    データの並びが逆順だろうが、順不同だろうが動作します。
    デフォルトでは、t - span <= エポック <= t　を対象として平均します。

    Args:
        fname:  ファイル名
        step:   時間ステップ
        span:   平均する時間幅
        epoch:  基準時刻
    return:
        None:   正常な実験データが得られなかった場合
        tapple: {time: (values, count)}, max len of values, first time, last time)
            count:      平均したデータ数
            max len:    valuesの最大要素数
            first time: 最も過去の観測時刻
            last time:  最も最近の観測時刻
    """
    fr = open(fname, 'r')                                                   # ファイル内容を読み込む
    txt = fr.read()
    fr.close()
    clockDict = getClockDict(txt)                                           # 時刻を基にした辞書を作成
    if clockDict == None:
        print("There are no measurment data with time-stamp.")
        return None
    clockList = list(clockDict.keys())                                      # 観測時刻をリストで取得
    clockList.sort()                                                        # 観測時刻を時系列に並べ直す（走査を高速に行うために重要）
    firstTime = min(clockList)
    lastTime  = max(clockList)
    print("first time is : " + str(firstTime))                              # 時刻は以下の処理でかなり重要になるので、表示させる（問題がある場合は手動で停止できるように）
    print("last  time is : " + str(lastTime))
    _step = datetime.timedelta(seconds = step)                              # 何度も呼び出すことになるので予めオブジェクトにしておく
    _span = datetime.timedelta(seconds = span)
    currentTime = firstTime + _step
    if epoch != None:                                                       # 基準時刻が設定されていれば、それに従う
        diff    = (firstTime + _step) - epoch
        #print(diff.total_seconds())
        stepNum = int(diff.total_seconds() / step)
        currentTime = epoch + datetime.timedelta(seconds = stepNum * step)
    _maxLenOfValues = 0
    _minIndex = 0
    data  = {}
    while currentTime <= lastTime:
        _minTime = currentTime - _span
        _maxTime = currentTime
        _obsData = NumBuff()                                                # データを格納するクラスオブジェクトを生成
        _count = 0
        _minIndexFound = False
        for i in range(_minIndex, len(clockList)):                          # 走査を高速に行うために、rangeを使って検索範囲を絞っていく
            time = clockList[i]
            if _minTime <= time and _maxTime >= time:
                if _minIndexFound == False:                                 # 検索範囲を絞るための工夫
                    _minIndexFound = True
                    _minIndex = i
                one = clockDict[time]                                       # 観測データ（文字列）を取得
                matchList = getDataList(one)
                if matchList != None:
                    _count += 1
                    #print(matchList)
                    _obsData.addForMean(matchList)                          # データを加算
            if _maxTime < time:
                break
        data.update(dict({currentTime:(_obsData.mean(), _count)}))
        if _maxLenOfValues < _obsData.len():
            _maxLenOfValues = _obsData.len()
        currentTime += _step
    return (data, _maxLenOfValues, firstTime, lastTime)


def main():
    global delta, term, samplingRate, missingThreshold      # グローバル変数の使用を宣言
    print("Processing start...")
    argvs = sys.argv                                        # コマンドライン引数を格納したリストの取得
    argc = len(argvs)                                       # 引数の個数
    #print(argvs)                                           # デバッグプリント
    #print(argc)
    if (argc != 2):                                                         # 引数が足りない場合は、その旨を表示
        print('Usage: # python {0} filename'.format(argvs[0]))              # 0はスクリプトファイル自体を指す
        quit()                                                              # プログラムの終了
    fname = argvs[1]#"test.txt" #
    result = createAverageList(fname, delta, term)
    if result != None:
        data, maxLenOfValues, first, last = result
        saveName = fname.split('.')[0] + "_meaned.csv"
        fw = open(saveName, 'w')
        clockList = list(data.keys())
        clockList.sort()
        for time in clockList:
            values, count = data[time]
            fw.write(str(time))
            for i in range(maxLenOfValues):
                fw.write(",")
                if i < len(values):
                    fw.write("{0:.03f}".format(values[i]))
            fw.write("," + str(count))
            fw.write("\n")
        fw.close()
    print("fin.")

if __name__ == '__main__':
    main()
