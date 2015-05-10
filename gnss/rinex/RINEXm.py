#!/usr/bin/env python3
# -*- coding:utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        RINEX
# Purpose:      RINEXファイルを取り扱うクラス
#               とりあえずの開発目標は、RINEXファイルの結合です。
#
# Author:      morishita
#
# Created:     02/02/2012
# Copyright:   (c) morishita 2012
# Licence:     new BSD
# History:     2013/1/3  isRINEX()の判定において、（拡張子の）OとNも認識するように変更した。
#                        その他、かなり改造したし関数やメソッドを追加している。
#                        可読性も少しは向上したと思う。
#                        付け焼刃的な処理もあるけど、そこは将来の課題ということで。
#                        RINEXオブジェクトのjoin()を汎化させるには、sort可能な1エポック毎の観測データを格納するクラスを宣言して、かつ格納しているエポックをハッシュで管理する必要がある。用途があれば作ります。
#-------------------------------------------------------------------------------
import os
import re
import sys
import datetime
import gnss.gps.time as gtime


def getTimeOfObsInHeader(str):
    """ RINEXのヘッダ部分で使われる時刻情報の文字列を解析して、時刻オブジェクトを返す

    Return:
        Epoch: 時系時刻情報
        None: 非時刻情報
    """
    epochPatternInRinexBody = re.compile(r"(?P<yearYY>\d{4}) +(?P<month>\d{1,2}) +(?P<day>\d{1,2}) +(?P<hour>\d{1,2}) +(?P<min>\d{1,2}) +(?P<sec>\d{1,2})[.](?P<microsecond>\d+) +(?P<timeSystem>\w+) +.*\n?")  # エポックに一致する正規表現
    matchTest = epochPatternInRinexBody.search(str)
    if matchTest != None:
        #print(matchTest.groups())
        year   = int(matchTest.group('yearYY'))
        month  = int(matchTest.group('month'))
        day    = int(matchTest.group('day'))
        hour   = int(matchTest.group('hour'))
        minute = int(matchTest.group('min'))
        sec    = int(matchTest.group('sec'))
        _microsecond   = matchTest.group('microsecond') # このままでは単位が必ずしもμsにはならないので、以下で単位を変換する
        microsecond    = int(int(_microsecond) * 10**(6 - len(_microsecond)))   # datetimeオブジェクトを使うと有効桁が一つ足りないのだが・・・実用上は問題ないと思う
        system = matchTest.group('timeSystem')
        return Epoch(system, datetime.datetime(year, month, day, hour, minute, sec, microsecond))
    else:
        return None



def getDateFromRinexBodyEpoch(str):
    """ RINEXのボディ部分で使われる時刻情報の文字列を解析して、時刻オブジェクトを返す
    2000年以降の観測データを対象としています。

    Return:
        datetime.datetime: 時刻情報
        None:              非エポック時
    """
    epochPatternInRinexBody = re.compile(r"(?P<yearYY>\d{1,2}) +(?P<month>\d{1,2}) +(?P<day>\d{1,2}) +(?P<hour>\d{1,2}) +(?P<min>\d{1,2}) +(?P<sec>\d{1,2})[.](?P<microsecond>\d+) +(?P<sat>.+)\n?")  # エポックに一致する正規表現
    matchTest = epochPatternInRinexBody.search(str)
    if matchTest != None:
        #print(matchTest.groups())
        year   = int(matchTest.group('yearYY')) + 2000      # 年は上位2桁が省略されているので2000を足す
        month  = int(matchTest.group('month'))
        day    = int(matchTest.group('day'))
        hour   = int(matchTest.group('hour'))
        minute = int(matchTest.group('min'))
        sec    = int(matchTest.group('sec'))
        _microsecond   = matchTest.group('microsecond')
        microsecond    = int(int(_microsecond) * 10**(6 - len(_microsecond)))   # 有効桁が一つ足りないのだが・・・実用上は問題ないと思う
        return datetime.datetime(year, month, day, hour, minute, sec, microsecond)
    else:
        return None




def isRINEX(fname):
    """ 指定されたファイルがRINEXファイルかどうかを判定する
    判定結果はTrue or False
    拡張子も判断材料とする
    """
    if os.path.exists(fname) == False:      # ファイルの存在が確認できない場合はFalseを返す
        return False
    if os.path.isfile(fname) != True:       # ファイルでなければFalseを返す
        return False
    #root, ext = os.path.splitext(fname)     # 拡張子を取得
    if re.search(".\d+[onmghON]", fname) != None:# 正規表現を利用して拡張子のチェック
        fr = open(fname, 'r')               # ファイルを開く
        firstLine = fr.readline()           # 1行だけ取得
        fr.close()
        if "RINEX" in firstLine:            # 1行目に“RINEX”とあればOK
            return True
        else:
            return False
    else:
        return False




class Epoch:
    """ エポックを表すクラス
    """
    def __init__(self, timeSystemName = "GPS", time = gtime.epoch_origin):
        """
        コンストラクタ
        Args:
            timeSystemName[str]              : 時刻系, exm. "GPS"
            time          [datetime.datetime]: 時刻
        """
        if isinstance(timeSystemName, str):
            self.tsystem = timeSystemName
        else:
            self.tsystem = ""
        if isinstance(time, datetime.datetime):
            self._epoch = time
        else:
            self._epoch = None
        return
    # プロパティ
    @property
    def system(self):
        """ 時刻系[str] """
        return self.tsystem
    @property
    def epoch(self):
        """ 時刻[datetime.datetime] """
        return self._epoch
    @property
    def year(self):
        """ 年[yyyy] """
        if self.epoch != None:
            return self.epoch.year
        else:
            return None
    @property
    def month(self):
        """ 月[MM] """
        if self.epoch != None:
            return self.epoch.month
        else:
            return None
    @property
    def day(self):
        """ 日[dd] """
        if self.epoch != None:
            return self.epoch.day
        else:
            return None
    @property
    def hour(self):
        """ 時[hh] """
        if self.epoch != None:
            return self.epoch.hour
        else:
            return None
    @property
    def minute(self):
        """ 分[mm] """
        if self.epoch != None:
            return self.epoch.minute
        else:
            return None
    @property
    def second(self):
        """ 秒[ss] """
        if self.epoch != None:
            return self.epoch.second
        else:
            return None
    @property
    def microsecond(self):
        """ μ秒[ssssss] """
        if self.epoch != None:
            return self.epoch.microsecond
        else:
            return None








class HeaderOfRINEX:
    """ RINEXヘッダ情報
    ヘッダに含まれるコメント文の時刻とTIME OF OBSが異なり得るのだけど、現時点では放置しています。
    """
    def __init__(self, rinexFile = ""):
        """ RINEXファイルよりヘッダ情報を取得する
        """
        self._header = []
        self._start = ""
        self._end = ""
        self._timeOfFirstObs = Epoch()
        self._timeOfLastObs  = Epoch()
        self._isSet = False                             # セットされるとTrueになる
        self.set(rinexFile)                             # もし可能ならヘッダー情報をセットする
        return
    def copy(self):
        """ オブジェクトのディープコピーを返します
        Return:
            RINEXヘッダ情報[HeaderOfRINEX]
        """
        ans = HeaderOfRINEX()
        for men in self._header:
            ans._header.append(men)
        ans._start = self._start
        ans._end = self._end
        ans._timeOfFirstObs = Epoch(self._timeOfFirstObs.system, self._timeOfFirstObs.epoch)
        ans._timeOfLastObs  = Epoch(self._timeOfLastObs.system, self._timeOfLastObs.epoch)
        ans._isSet = self._isSet
        return ans
    def set(self, fname = ""):
        """ 指定されたファイルのヘッダー情報をセットする
        ヘッダ情報は上書きされます。
        """
        if isRINEX(fname):
            self._header = []
            fr = open(fname,'r')                        # ファイルを開く
            txt = fr.readlines()
            fr.close()
            for line in txt:
                self._header.append(line)
                if "TIME OF FIRST OBS" in line:
                    self._timeOfFirstObs = getTimeOfObsInHeader(line) # この書き方だと解析ミスが出たらバグになるが、出たことないので放置
                if "TIME OF LAST OBS" in line:
                    self._timeOfLastObs = getTimeOfObsInHeader(line)
                if "start" in line:
                    self._start = line
                elif "end" in line:
                    self._end = line
                if "END OF HEADER" in line:             # ヘッダー部分を抜けるとループを停止
                    self._isSet = True
                    break
        return
    def fusion(self, fname):
        """ ファイル名を指定して、含まれるヘッダー情報から終了時刻情報を抜き出して時刻を上書きする
        日本語が変かも。
        指定されたファイルが時間的に逆行している場合は矛盾が生じるので注意して下さい。
        2013/1/3時点では矛盾を抱えているが、時間がないので現行の処理に影響しない程度に処理している。
        """
        if isRINEX(fname) and self._isSet == True:       # 一度はセットしておかなければ
            fr = open(fname,'r')                        # ファイルを開く
            txt = fr.readlines()
            fr.close()
            for line in txt:
                if "TIME OF FIRST OBS" in line:
                    tfo = getTimeOfObsInHeader(line)
                    if self._timeOfFirstObs.epoch > tfo.epoch:
                        self._timeOfFirstObs.epoch = tfo.epoch
                if "TIME OF LAST OBS" in line:
                    tlo = getTimeOfObsInHeader(line)
                    if self._timeOfLastObs.epoch < tlo.epoch:
                        self._timeOfLastObs.epoch = tlo.epoch
                if "end" in line:
                    self._end = line
                if "END OF HEADER" in line:             # ヘッダー部分を抜けるとループを停止
                    break
        return
    def getHeader(self):
        """ ヘッダ情報をリストとして返す
        Return:
            list: ヘッダ情報がセットされていない場合は、空のリストを返します。
        """
        ans = []
        if self._isSet == True:
            #print("in header first: {0}".format(self._timeOfFirstObs.epoch)) # for debug
            #print("in header last: {0}".format(self._timeOfLastObs.epoch))
            for line in self._header:
                if "TIME OF FIRST OBS" in line:
                    str = "  {0:4d}    {1:2d}    {2:2d}    {3:2d}    {4:2d}   {5:2d}.{6:06d}0".format(self._timeOfFirstObs.year, self._timeOfFirstObs.month, self._timeOfFirstObs.day, self._timeOfFirstObs.hour, self._timeOfFirstObs.minute, self._timeOfFirstObs.second, self._timeOfFirstObs.microsecond)
                    str += self._timeOfFirstObs.system.rjust(8) # 右揃え
                    str += "         TIME OF FIRST OBS   \n"
                    ans.append(str)
                elif "TIME OF LAST OBS" in line:
                    str = "  {0:4d}    {1:2d}    {2:2d}    {3:2d}    {4:2d}   {5:2d}.{6:06d}0".format(self._timeOfLastObs.year, self._timeOfLastObs.month, self._timeOfLastObs.day, self._timeOfLastObs.hour, self._timeOfLastObs.minute, self._timeOfLastObs.second, self._timeOfLastObs.microsecond)
                    str += self._timeOfLastObs.system.rjust(8)
                    str += "         TIME OF LAST OBS    \n"
                    ans.append(str)
                elif "end" in line:                           # end（終了時刻）だけは置換する
                    ans.append(self._end)
                else:
                    ans.append(line)
        return ans
    # プロパティ
    @property
    def isSet(self):
        """ ヘッダ情報の格納状況[bool], True: 格納されています """
        return self._isSet
    @property
    def timeOfFirstObs(self):                                   # 読み込み用
        """ 観測開始時刻[Epoch] """
        return self._timeOfFirstObs
    @timeOfFirstObs.setter                                      # 書き込み用
    def timeOfFirstObs(self, t):
        """ 観測開始時刻[Epoch]
        観測終了時刻との関係のチェックなどは行いません（できません）のでご注意ください。
        Args:
            t: datetime.datetime型の場合、現時点の時系で時刻を更新します。
               Epoch型の場合、そのまま置換します。
               それ以外の型の場合、Noneをセットします。
        """
        #print("called timeOfFirstObs. t is {0}.".format(t)) # for debug
        if isinstance(t, datetime.datetime):
            self._timeOfFirstObs = Epoch(self._timeOfFirstObs.system, t)
        elif isinstance(t, Epoch):
            self._timeOfFirstObs = t
        else:
            self._timeOfFirstObs = None
    @property
    def timeOfLastObs(self):
        """ 観測終了時刻[Epoch] """
        return self._timeOfLastObs
    @timeOfLastObs.setter
    def timeOfLastObs(self, t):
        """ 観測開始時刻[Epoch]
        観測終了時刻との関係のチェックなどは行いません（できません）のでご注意ください。
        Args:
            t: datetime.datetime型の場合、現時点の時系で時刻を更新します。
               Epoch型の場合、そのまま置換します。
               それ以外の型の場合、Noneをセットします。
        """
        if isinstance(t, datetime.datetime):
            self._timeOfLastObs = Epoch(self._timeOfLastObs.system, t)
        elif isinstance(t, Epoch):
            self._timeOfLastObs = t
        else:
            self._timeOfLastObs = None




class RINEX:
    """ RINEXオブジェクト
    """
    def __init__(self, fname = ""):
        """ 初期化用のファイル名付きのコンストラクタ
        Args:
            fname: 読み込ませたいRINEXファイルのパスを渡してください。相対パスでもOKです。省略しても構いません。
        """
        self._txt = []                                          # ヘッダーを含まない、テキスト情報を格納する
        self._header = HeaderOfRINEX()
        if fname != "":
            self.set(fname)
    def copy(self):
        """ オブジェクトのディープコピーを返します
        Return:
            RINEX情報[RINEX]
        """
        ans = RINEX()
        for men in self._txt:
            ans._txt.append(men)
        ans._header = self._header.copy()
        return ans
    def set(self, fname):
        """ 指定されたRINEXファイルで初期化します
        TIME OF OBSと、実際のボディに記述されているエポックの矛盾の検査は行いません。
        """
        self._txt = []
        self._header = HeaderOfRINEX()
        if isRINEX(fname):
            __header = HeaderOfRINEX(fname)                     # ヘッダー情報を取得
            if __header.isSet:
                self._header = __header
                fr = open(fname,'r')                            # ファイルを開く
                _text = fr.readlines()
                fr.close()
                _headerRead = False
                for line in _text:
                    if _headerRead:                             # ヘッダー部分を読み飛ばしていれば以下を処理する
                        self._txt.append(line)                  # ヘッダ以外の文字列を格納する
                    if "END OF HEADER" in line:                 # ヘッダー部分を読み飛ばす仕掛け
                        _headerRead = True
        return
    def join(self, fname):
        """ 指定されたRINEXファイルを結合します
        本オブジェクトよりも、引数で渡されたRINEXファイルの方が時間的に遅い必要があります。
        時間的に連続しているかどうかは確認していません。
        """
        if isRINEX(fname):
            __header = HeaderOfRINEX(fname)                     # ヘッダー情報を取得
            if __header.isSet:
                if self._header.isSet == False:                  # 未セットならセットする
                    self._header = __header
                else:
                    self._header.fusion(fname)                   # ヘッダー情報を統合
                fr = open(fname,'r')                            # ファイルを開く
                _text = fr.readlines()
                fr.close()
                _headerRead = False
                _copyEnable = False
                lastEpoch = gtime.epoch_origin
                for line in _text:
                    if _headerRead:                             # ヘッダー部分を読み飛ばしていれば以下を処理する
                        _epoch = getDateFromRinexBodyEpoch(line)# 文字列解析してエポックを取得
                        if _epoch != None:
                            #result3 = re.findall("G *\d+", line)   # 衛星番号にヒットする
                            #print(result3)
                            if lastEpoch < _epoch:              # 保持しているエポックよりも大きいことを確認
                                lastEpoch = _epoch
                                _copyEnable = True
                            else:
                                _copyEnable = False             # 古いエポックならコピーしない
                        if _copyEnable:
                            self._txt.append(line)              # ヘッダ以外の文字列を結合させる
                    if "END OF HEADER" in line:                 # ヘッダー部分を読み飛ばす仕掛け
                        _headerRead = True
        return

    def save(self, saveName):
        """ 指定されたファイル名で保存する
        """
        fw = open(saveName,'w')                             # 書き込み用にファイルを開く
        __header = self._header.getHeader()                 # ヘッダー情報を取得
        for line in __header:
            fw.write(line)                                  # ヘッダー情報をファイルへ書き込む
        for line in self._txt:
            fw.write(line)                                  # ファイルへ書き込む
        fw.close()
        return

    def pickOut(self, t1, t2):
        """ 指定した時刻間におけるデータを抽出したRINEXオブジェクト返す
        t1 <= t <= t2の範囲とする。

        Args:
            t1: 開始時刻(datetime.datetimeオブジェクト)
            t2: 終了時刻(datetime.datetimeオブジェクト)
        Returen:
            RINEXオブジェクト, ただし、引数に不正があった場合や本オブジェクト内に指定された時間内のデータが存在しない場合はNoneを返します。
        """
        if self.isSet:
            if (isinstance(t1, datetime.datetime) and isinstance(t2, datetime.datetime)):
                if(t1 < t2):
                    first = gtime.epoch_origin
                    last = gtime.epoch_origin
                    _copyEnable = False
                    __txt = []
                    for line in self._txt:
                        _epoch = getDateFromRinexBodyEpoch(line)# 文字列解析してエポックを取得
                        if _epoch != None:
                            if t1 <= _epoch <= t2:
                                if _copyEnable == False:
                                    first = _epoch
                                    _copyEnable = True
                                last = _epoch
                            if _epoch > t2:                 # これ以上は走査する必要がない
                                break
                        if _copyEnable:
                            __txt.append(line)              # ヘッダ以外の文字列を結合させる
                    if len(__txt) > 0:
                        ans = RINEX()
                        ans._header = self._header.copy()   # ただの代入では同じインスタンスを指すことになり、以下の処理がうまく行かない
                        ans._header.timeOfFirstObs = first
                        ans._header.timeOfLastObs  = last
                        ans._txt = __txt
                        #print(first)                       # for debug
                        #print(last)
                        #print(ans._header.timeOfFirstObs)  # for debug
                        #print(ans._header.timeOfLastObs)
                        return ans
                    else:
                        return None
            else:
                return None
        else:
            return None
    # プロパティ
    @property
    def isSet(self):
        """ RINEXデータ格納状況[bool], True: 格納されています """
        if self._header.isSet and len(self._txt) > 0:
            return True
        else:
            return False


def main():
    """ デフォルトの実行メソッドですセルフテストに使用します
    引数にRINEXファイル名を引き渡すと処理するはずです。
    """
    print("Program start...")
    # RINEXファイルの結合テスト
    print("This program combine some RINEX files.\n")
    argvs = sys.argv                                        # 引数を取得する
    argc = len(argvs)
    if argc > 1:
        _rinex = RINEX()
        for i in range(1, argc):
            fname = argvs[i]
            if isRINEX(fname):                              # RINEXファイルかどうかチェックする
                print("now target: " + fname)
                _rinex.join(fname)                          # 追加する（実行が時系列に行われることが前提）
            else:
                print("This file is not RINEX file.")
        _rinex.save("combined.txt")
    else:
        print("argv is zero. Input RINEX file names.")
    print("\nThe combined text was created.")
    # ヘッダの時刻情報処理のテスト
    tfo = "  2012    12    29    10     0   16.9970000     GPS         TIME OF FIRST OBS   "
    tlo = "  2012    12    29    12    46   37.9970000     GPS         TIME OF LAST OBS    "
    hoge = getTimeOfObsInHeader(tfo)
    hoge2 = getTimeOfObsInHeader(tlo)
    # ボディ内の時刻情報処理のテスト
    hoge3 = getDateFromRinexBodyEpoch(" 12 12 29 10  0 16.9970000  0 11G26G 5S28G 9G12S37G18G15G21G22G24")
    hoge4 = Epoch()
    hoge5 = hoge4.system
    print("Program fin.")


if __name__ == '__main__':
    main()
