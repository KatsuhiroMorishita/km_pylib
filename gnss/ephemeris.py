#!/usr/bin/env python3
# -*- coding:utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        ephemeris
# Purpose:  各種測位衛星のエフェメリスの取り扱いを簡単にすることを目的としています。
# Author:      morishita
#
# Created:     15/02/2014
# Copyright:   (c) morishita 2012
# Licence:     MIT
# Histroy:
#           2014/2/15   GPS用に作成したephemerisモジュールを基に作成開始
#           2014/2/26   ほぼ仕様が固まった。リリースできそう。
#                       本日の時点では、managerクラスのテストの全てとsub_managerクラスの一部の機能をテストできていません。
#                       未テスト分はQZSのモジュールを作成した後にテストします。
#           2014/3/2    オブジェクトの比較、ハッシュ値生成、文字列化でepochが利用されていなかった点を修正した。
#-------------------------------------------------------------------------------
import re
import types
import copy
import inspect
import os.path
import datetime

class ephemeris:
    """ エフェメリスを格納するクラス
    継承して使われることを想定しているため、メンバは最低限しか宣言していません。
    __xx__という関数は、本クラスを継承した子クラスでも実装して下さい。
    """
    def __init__(self, system_name, sat_name=""):
        """ コンストラクタ
        Argv:
            system_name: <str> 測位システム名, e.g. "GPS"
            sat_name:    <str> 衛星の名前, e.g. "J 1" @ QZS
        """
        self.system_name = system_name
        self.sat_name = sat_name

    def __eq__(self, other):
        """ ==比較演算子に対応する
        メンバの内容で比較します。
        """
        member_self = inspect.getmembers(self)      # 保持しているオブジェクト全てを取得
        member_other = inspect.getmembers(other)    # 本クラスを継承したオブジェクトが追加したオブジェクトも得られる
        #print(member_self)
        #print(member_other)
        if len(member_self) != len(member_other):   # オブジェクト数に差があれば異なるオブジェクトとみなす
            #print("h1")
            return False
        # 中身で検査（この方法では厳密な判定はできないが、必要十分だと思う）
        other_dict = {}
        for name, value in member_other:            # 中身のチェックをやりやすくするために辞書を作成
            other_dict[name] = value
        for name, value in member_self:             # 保持しているオブジェクトの値の差を検査する
            if name not in other_dict:              # 片方が所持していないオブジェクトを持っていなかったらアウト
                #print("h2")
                return False
            if name[:2] != "__" and (
                    isinstance(value, int) or 
                    isinstance(value, float) or 
                    isinstance(value, type(None)) or 
                    isinstance(value, datetime.datetime) or
                    isinstance(value, str)):
                #print(name)
                #print(type(value))
                if value != other_dict[name]:
                    #print("h3")
                    return False
        return True

    def __hash__(self):
        """ ハッシュ値を返す
        メンバの値が同じであれば同じ値を返します。
        """
        ans = 0
        member_self = inspect.getmembers(self)      # 保持しているオブジェクト全てを取得
        for name, value in member_self:             # 保持しているオブジェクトの値を文字列化する
            if name[:2] != "__" and (
                    isinstance(value, int) or
                    isinstance(value, float) or
                    isinstance(value, type(None)) or
                    isinstance(value, datetime.datetime) or
                    isinstance(value, str)
                    ):
                ans ^= hash(value)
        return ans

    def __str__(self):
        """ オブジェクトの文字列表現を返す
        隠れメンバは文字列化しません。
        """
        ans = "+++++object members+++++\n"
        member_self = inspect.getmembers(self)      # 保持しているオブジェクト全てを取得
        for name, value in member_self:             # 保持しているオブジェクトの値を文字列化する
            #print(name)
            #print(type(value))
            if name[:2] != "_" and name[:2] != "__" and (
                    isinstance(value, int) or 
                    isinstance(value, float) or 
                    isinstance(value, type(None)) or 
                    isinstance(value, datetime.datetime) or
                    isinstance(value, str)
                    ):
                ans += name + ": " + str(value) + "\n"
        return ans

    def calc_sat_position(self, epoch=0.0):
        """ 衛星座標を計算して返す
        これはダミー関数です。
        各測位システムで実装してください。
        """
        return

    # プロパティ
    @property
    def is_available(self):
        """ 演算可能かどうかを返す
        """
        return True




class reader:
    """ エフェメリスを読み込むクラス
    """
    def __init__(self, extension_pattern="\.\d{2}[nNq]", ephemeris_pattern="dummy pattern (?P<sat_name>\d+)", ephemeris_class=ephemeris):
        """
        Argv:
            extension_pattern: <str>   拡張子正規表現パターン
            ephemeris_pattern: <str>   エフェメリスの正規表現パターン（グループ化しておくこと）
            ephemeris_class:   <class> エフェメリスクラス, isinstance(ephemeris_class, type) == true　となる
        """
        #print("test")
        self._extension_pattern = extension_pattern
        self._ephemeris_pattern = ephemeris_pattern
        self._ephemeris_class = ephemeris_class                 # ここで型のチェックをして、エラーをスローすべきだろうか？
        self._value_grouped_pattern = re.compile(r"(?P<value>[-]?\d[.]\d+)[ED](?P<power>[\s+-]\d{1,2})")

    def get_date(self, date_str):
        """ RINEXのボディ部分で使われる時刻情報の文字列を解析して、時刻オブジェクトを返す
        1980年～2079年の観測データを対象としています。
        Argv:
            <str>   被解析文字列
        Return:
            <datetime.datetime>: 時刻情報
                                非エポック時はNoneを返します。
        """
        epochPatternInRinexBody = re.compile(r"(?P<yearYY>\d{1,2}) +(?P<month>\d{1,2}) +(?P<day>\d{1,2}) +(?P<hour>\d{1,2}) +(?P<min>\d{1,2}) +(?P<sec>\d{1,2})[.](?P<microsecond>\d+)")  # エポックに一致する正規表現
        matchTest = epochPatternInRinexBody.search(date_str)
        if matchTest != None:
            #print(matchTest.groups())
            year   = int(matchTest.group('yearYY'))
            if year < 80:                                       # 下二桁しかない西暦を復元（60年以上使われることはないだろうね？）
                year += 2000
            else:
                year += 1900
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

    def _change_to_value(self, value_str):
        """ 文字列の数字を数値へ変換する
        Return:
            不正があればNoneを返す
        """
        ans = None
        #print(value_str)
        if isinstance(value_str, str):
            match_test = self._value_grouped_pattern.search(value_str)
            if match_test != None:
                value = float(match_test.group('value'))
                power = int(match_test.group('power'))
                ans = value * (10 ** power)
        return ans

    def read_ephemeris_from_txt(self, txt):
        """ テキストから読み出したエフェメリスをリストで返す
        Argv:
            fname: <str> ファイルパス（相対でも可）
        Return:
            <list<ephemeris>> エフェメリスを格納した要素数0以上のリスト
        """
        #print("test")
        eph = []
        if isinstance(txt, str) and self.is_available:          # ファイルの存在が確認できない場合はFalseを返す
            #print("test")
            txt = txt.replace("\n", " ")                        # 余計な文字を変換
            txt = re.sub("\s{2,}", " ", txt)
            match_test = self._ephemeris_pattern.finditer(txt)
            if match_test != None:
                #print("hit")
                #print(match_test)
                for mem in match_test:
                    #print(type(mem))
                    #print(mem.groups())
                    #print(mem.groupdict())
                    # 要素データを取得
                    _eph = self._ephemeris_class()                  # エフェメリスクラスのインスタンスを生成
                    sat_name = mem.group('sat_name').strip()
                    _eph.sat_name = sat_name                        # PRN番号など. QZSだと"J *"となるので、整数化できない。
                    _eph.epoch = self.get_date(mem.group('epoch'))  # エポック（時刻）
                    # その他
                    _dict = mem.groupdict()
                    #print(_dict)
                    for key in _dict:
                        if key != "sat_name" and key != "epoch":
                            #print(key)
                            #print(_dict[key])
                            if _dict[key] != None:  # ヒットしていることが条件
                                setattr(_eph, key, self._change_to_value(_dict[key]))    # オブジェクトにメンバを追加
                    #obj = inspect.getmembers(_eph)                 # オブジェクトの検査 for debug
                    #print(obj)
                    #import sys
                    #sys.exit(0)
                    eph.append(_eph)
        return eph

    def read_ephemeris(self, fname):
        """ ファイルから読み出したエフェメリスをリストで返す
        Argv:
            fname: <str> ファイルパス（相対でも可）
        Return:
            <list<ephemeris>> エフェメリスを格納した要素数0以上のリスト
        """
        eph = []
        if os.path.exists(fname) == False:                  # ファイルの存在が確認できない場合
            return eph
        if os.path.isfile(fname) != True:                   # ファイルかどうか確認
            return eph
        root, ext = os.path.splitext(fname)
        if re.search(self._extension_pattern, ext) != None: # 正規表現を利用して拡張子のチェック.
            fr = open(fname, 'r')                           # ファイルを開く
            txt = fr.read()
            fr.close()
            eph = self.read_ephemeris_from_txt(txt)
        return eph

    def read_ephemeris_from_dir(self, dir_path):
        """ フォルダ内のファイルから読み出したエフェメリスをリストで返す
        Argv:
            dir_path: <str> フォルダパス（相対でも可）
        Return:
            <list<ephemeris>> エフェメリスを格納した要素数0以上のリスト
        """
        eph = []
        if os.path.exists(dir_path) == False:   # フォルダの存在が確認できない場合
            return eph
        if os.path.isdir(dir_path) != True:     # フォルダでなければFalseを返す
            return eph
        flist = os.listdir(dir_path)
        for name in flist:
            fpath = os.path.join(dir_path, name)# ファイルの相対パスを作成
            #fpath = dir_path + "/" + name
            eph += self.read_ephemeris(fpath)   # 読み込んだエフェメリスを追加
        return eph

    # プロパティ
    @property
    def is_available(self):
        """ 利用可能かどうかを返す
        """
        #print(type(self._ephemeris_class))
        return isinstance(self._ephemeris_class, type) # とりあえずこれだけ




class sub_manager:
    """ 単一の測位システムに関するエフェメリスを管理するクラス
    """
    def __init__(self, system_name):
        """ コンストラクタ
        Argv:
            system_name: <str> 測位システム名, e.g. "GPS"
        """
        self._system_name = system_name
        self._ephs = {}           # e.g.: ["PRN001": [ephemeris・・・], ・・・}
        self._hash = []

    def __len__(self):
        """ 本オブジェクトの保持しているエフェメリスの衛星数を返す
        """
        return len(self._ephs)

    def add_ephemeris(self, eph):
        """ エフェメリスを追加する
        エフェメリスだけではGNSSのシステムを区別するのは面倒なので、異なる測位システムの放送歴を入れないでください。
        （もし区別するなら、軌道半径を使うか。）
        Argv:
            eph: <ephemeris> エフェメリス
        """
        if not isinstance(eph, list):
            eph = [eph]
        for mem in eph:
            #print(mem)
            if isinstance(mem, ephemeris):
                _hash = hash(mem)
                if _hash not in self._hash:                     # 未登録であることを確認
                    self._hash.append(_hash)
                    if mem.sat_name not in self._ephs:          # 今までに登録したことがない衛星であれば、初期化
                        self._ephs[mem.sat_name] = []
                    self._ephs[mem.sat_name].append(mem)        # sat_nameごとに追加

    def copy(self, filter_func=None):
        """ オブジェクトのコピーを返す
        filter_funcを省略するとオブジェクトのディープコピーを返します。
        Argv:
            filter_func: <Function>　エフェメリスを選定する関数
        Return:
            <sub_manager>
        """
        new_sub_mgr = sub_manager(self._system_name)
        if type(filter_func) is types.FunctionType:              # 関数であることを確認
            ephs = filter_func(self._system_name, self._ephs)
            new_sub_mgr.add_ephemeris(ephs)                      # ここは渡される選定関数の作りを信頼するしかない
        else:
            new_sub_mgr._ephs = copy.deepcopy(self._ephs)
            new_sub_mgr._hash = copy.deepcopy(self._hash)
        return new_sub_mgr

    def get_anything(self, func):
        """ funcを実行した結果を返す
        Argv:
             func: <function> 任意関数, 引数として、本クラスが保持しているエフェメリスを渡します
        Return:
            func次第
        """
        ans = None
        if type(func) is types.FunctionType:              # 関数であることを確認
            ans = func(self._system_name, self._ephs)
        return ans

    # プロパティ
    @property
    def system_name(self):
        """ 本オブジェクトの名前を返す
        """
        return self._system_name




class manager:
    """ GNSS全ての測位衛星に関するエフェメリスを管理するマネージャークラス
    2014/2/16時点では汎用性を重視しています。
    今後、利用頻度と汎用性が高いメソッドがあれば実装したいと思います。
    """
    def __init__(self, sub_mgr_list = []):
        self._sub = {}
        if isinstance(sub_mgr_list, sub_manager):   # 型のチェック
            for mem in sub_mgr_list:
                self._sub[mem.system_name] = mem

    def __str__(self):
        """ 文字列化
        格納している測位システムの名称と格納している衛星数を返す
        """
        ans = ""
        for system_name in self._sub:
            if ans != "":
                ans += ", "
            ans += "{0}:{1}".format(system_name, len(self._sub[mem.system_name]))
        return

    def get_sub_mgr(self, efemeris_filter=None):
        """ funcで仕分けられたエフェメリスを格納したsub_managerを返す
        Argv:
            efemeris_filter: <function> エフェメリスを仕分ける関数
        Return:
            <list<sub_manager>> sub_managerオブジェクト
        """
        _sub_mgr = []
        for system_name in self._sub:
            _sub_mgr.append(self._sub[system_name].copy(efemeris_filter))
        return _sub_mgr

    def add_sub_manager(self, sub_mgr):
        """ sub_managerを追加する
        """
        if isinstance(sub_mgr, sub_manager):        # 型のチェック
            self._sub[sub_mgr.system_name] = sub_mgr
        return
        
    def get_satellite_info(self, filter_func):
        """ 各測位システム毎にfilter_func()を適用した結果を返す
        引数で渡す関数によって返す情報が変わります。
        Argv:
            filter_func: <function> 関数
        Return:
            {"Positionig System Name": object},  e.g. {"GPS":{"PRN1":(x,y,z), "PRN2":(x,y,z), ・・・}}
        """
        ans = {}
        for system_name in self._sub:
            hoge = self._sub[system_name].get_anything()
            if hoge != None:
                ans[system_name] = hoge
        return ans




def organize(ephemeris_list):
    """ 衛星名毎にエフェメリスを整理する
    柔軟性確保のために型の検査はあまり行っていません。
    Argv:
        ephemeris_list: <list<ephemeris>> エフェメリスを整理する
    """
    _storage = {}
    if isinstance(ephemeris_list, list):
        check_list = []                             # 同じエフェメリスを除外するためのリスト
        #print("d2")
        for mem in ephemeris_list:
            #print("d3")
            if mem.is_available:
                #print("d4")
                sat_name = mem.sat_name
                if sat_name not in _storage:        # 衛星名（PRN番号）ごとに整理するので、リストを生成
                    _storage[sat_name] = []
                _hash = hash(mem)
                if _hash not in check_list:         # ただし、過去に同じものを格納済みであれば意味がないのでそのチェック
                    check_list.append(_hash)
                    _storage[sat_name].append(mem)
    return _storage



def main():
    print("---self test---")
    # 詳細はgnss.gps.ephemerisモジュールのself testの記述内容をご覧ください。


if __name__ == '__main__':
    main()