#!/usr/bin/env python3
# -*- coding:utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        mathKM
# Purpose:  算術・・・特に、初歩的統計に関する処理機能を提供する。
#
# Author:     Katsuhiro Morishita, Kumamoto-Univ. @ 2012
#
# Created:     07/01/2013
# Copyright:   (c) morishita 2013
# Licence:     new BSD
# History:      2013/1/11   4分位数の計算時に、リストの数に下限を設けた。
#               2014/2/11   暗号理論の講義でRubyにて作ったfactorize()を移植した。
#-------------------------------------------------------------------------------
import math

def mean(valueList):
    """ 平均を返す
    外れ値の検討は行いません。
    Args:
        valueList:  処理したい値のリスト
    """
    if isinstance(valueList, list) == False:
        return None
    _sum = 0.0
    for men in valueList:
        _sum += float(men)
    return _sum / len(valueList)

def mean2(valueList, lower, upper):
    """ 指定された数値範囲にあるデータの平均を返す
    外れ値の検討は行いません。
    Args:
        valueList:  処理したい値のリスト
        lower:      指定範囲の最小値
        upper:      指定範囲の最大値
    """
    if isinstance(valueList, list) == False:
        return None
    if (isinstance(lower, int) or isinstance(lower, float)) == False:
        return None
    if (isinstance(upper, int) or isinstance(upper, float)) == False:
        return None
    if lower > upper:
        return None
    _sum = 0.0
    count = 0.0
    for men in valueList:
        if lower <= men <= upper:
            _sum += float(men)
            count += 1.0
    return _sum / count

def mean3(valueList):
    """ 平均を返す
    4分位数を用いた外れ値の検討を実施します。
    Args:
        valueList: 処理したい値のリスト
    Return:
        None: 4分位数を計算できない場合
        float: 平均の推定値
    """
    _quantile = quantile(valueList)
    if _quantile == None:
        return None
    return mean2(valueList, _quantile[1], _quantile[3])

def quantile(valueList):
    """ 4分位数を返す
    引数の中身が数値が格納されたリストであることが前提です。
    listのサイズが異様に小さい場合は考慮していません。
    最低の要素数は5です。
    Args:
        valueList:  処理したい値のリスト
    Returen:
        Tuple: (0%値, 25%値, 50%値, 75%値, 100%値)
    """
    if isinstance(valueList, list) == False:
        return None
    if len(valueList) <= 5:
        return None
    dummy = []
    for men in valueList:
        dummy.append(men)
    dummy.sort()
    size = len(dummy)
    p25 = size * 0.25
    p50 = size * 0.50
    p75 = size * 0.75
    # 最小
    v0 = dummy[0]
    # 25%値
    temp = dummy[int(p25) - 1]
    temp2 = dummy[int(p25)]
    v25 = (temp2 - temp) * (p25 - int(p25)) + temp
    # 50%値
    if size % 2 == 0:   # 偶数
        v50 = (dummy[int(p50) - 1] + dummy[int(p50)]) / 2.0
    else:               # 奇数
        v50 = dummy[int(p50)]
    # 75%値
    temp = dummy[int(p75) - 1]
    temp2 = dummy[int(p75)]
    v75 = (temp2 - temp) * (p75 - int(p75)) + temp
    # 最大値
    v100 = dummy[-1]
    return (v0, v25, v50, v75, v100)

def CheckGaussianDistribution(valueList):
    """ 分布の偏りを検査する
    山の偏り方を使って計算しています。
    もしかすると、何かしら一般的な指標があるかもしれない。
    分布の形は考慮できないアルゴリズムですのでご注意ください。
    例えば、CDMA信号のパワースペクトルは横長の長方形ですが、本関数はあれをガウス分布から遠いとは判定しません。
    Args:
        valueList:  処理したい値のリスト
                    4分位数の計算が可能である必要があります。
    Return:
        ガウス分布なら0となる指標値を返します。
        偏りが大きいほど、大きな数を返します。
        負値を返すことはありません（有ったらバグ）。
    """
    _quantile = quantile(valueList)
    if _quantile == None:
        return None
    v25 = _quantile[1]
    v50 = _quantile[2]
    v75 = _quantile[3]
    temp = (v75 - v50)
    temp2 = (v50 - v25)
    if temp > temp2:
        big = temp
        small = temp2
    else:
        big = temp2
        small = temp
    return abs(big / small - 1.0) # もしガウス分布なら、0

def TwiceDrms(valueList, trueValue):
    """ 2DRMSを計算します
    Args:
        valueList: 処理したい値のリスト
        trueValue: 真値
    """
    sum = 0.0
    for men in valueList:
        distance = abs(men - trueValue)
        sum = distance ** 2.0
    rms = math.sqrt(sum / len(valueList))
    return (trueValue, 2.0 * rms)

def TwiceDrms2(valueList):
    """ 2DRMSの推定値を計算します
    Args:
        valueList: 処理したい値のリスト
    Return:
        None: 4分位数を計算できない場合
        float: 2DRMSの推定値
    """
    _quantile = quantile(valueList)
    if _quantile == None:
        return None
    estimatedTrueValue = mean2(valueList, _quantile[1], _quantile[3])
    return (estimatedTrueValue, TwiceDrms(valueList, estimatedTrueValue))

def sd(valueList):
    """ 標準偏差を返す
    外れ値の検討は行いません。
    Return:
        None: 平均を計算不可能な場合
        float: 標準偏差
    """
    _mean = mean(valueList)
    if _mean == None:
        return None
    sum = 0.0
    for men in valueList:
        diff = (float(men) - _mean) ** 2.0
        sum += diff
    return (_mean, math.sqrt(sum / (len(valueList) - 1)))

def sd2(valueList, min, max):
    """ 指定範囲内のデータを用いて標準偏差を返す
    平均は4分位数を用いた推定値を用います。
    例えば、ある範囲内におけるデータを用いて計算することで外れ値を除外することができる。
    範囲外が外れ値かどうかは関知しない。
    予めデータの分布の仕方が分かっている場合に有用です
    Args:
        valueList: 処理したい値のリスト
        min      : 最低値
        max      : 最高値
    Return:
        None: 4分位数を計算できない場合
        tuple: (平均の推定値, 標準偏差の推定値, 計算に利用されたデータの割合)
    """
    copy = []
    for men in valueList:
        p = float(men)
        if min <= p <= max:
            copy.append(p)
    _mean = mean3(copy)
    if _mean == None:
        return None
    sum = 0.0
    for men in copy:
        diff = (men - _mean) ** 2.0
        sum += diff
    return (_mean, math.sqrt(sum / (len(copy) - 1)), len(copy) / len(valueList))

def sd3(valueList):
    """ 標準偏差の推定値を返す
    外れ値の検討を行います。
    ガウス分布に近い観測データで、外れ値が全体の5%以下であれば有用です。
    予め分布の形状は把握しておいてください。
    Args:
        valueList: 処理したい値のリスト
    Return:
        None: 4分位数を計算できない場合
        tuple: ((平均の推定値, 標準偏差の推定値, データの利用率), 分布の偏り方の指標)
    """
    _quantile = quantile(valueList)
    #print("in sd3()")
    #print(_quantile)
    if _quantile == None:
        return None
    dummy = []
    for men in valueList:
        dummy.append(men)
    dummy.sort()
    size = len(dummy)
    p1 = size * (0.5 - 0.3413)   # 1σに近い値を取得したい
    p2 = size * (0.5 + 0.3413)   # なぜ2σに値する0.4772を使わないかというと、外れ値が多い場合に対処できないため
    # %値, 2σに近い値を取得する
    temp = dummy[int(p1) - 1]
    temp2 = dummy[int(p1)]
    v1 = (temp2 - temp) * (p1 - int(p1)) + temp
    # %値
    temp = dummy[int(p2) - 1]
    temp2 = dummy[int(p2)]
    v2 = (temp2 - temp) * (p2 - int(p2)) + temp
    # 範囲を求める（2σの範囲に相当する部分を探そうとしている）
    lower = _quantile[2] - (_quantile[2] - v1) * 2.0        # 式はあえて整理しない
    higher = _quantile[2] + (v2 - _quantile[2]) * 2.0
    #print(lower)
    #print(higher)
    _sd = sd2(valueList, lower, higher)
    #print(_sd)
    return (_sd, CheckGaussianDistribution(valueList))

def test(sample):
    """ 各関数を使って統計データを返す
    テスト用の関数です。
    """
    _mean = mean(sample)
    _quantile = quantile(sample)
    _mean2 = mean2(sample, _quantile[1], _quantile[2])
    _sd = sd(sample)
    _sd3 = sd3(sample)
    _2drms2 = TwiceDrms2(sample)
    return (_mean, _mean2, _quantile, _sd, _sd3, _2drms2)

def factorize(n):
    """ 素因数分解を行う
    A * B の形まで分解します。
    公開鍵暗号を解く演習問題レベルなら問題ありません。
    """
    #print(n)
    x = int(math.sqrt(n)) + 1
    y = 0
    z = 0
    while(1):
        z = x * x - n
        y = math.sqrt(z)
        if (y - int(y)) != 0:
            x += 1
        if (x + y) * (x - y) == n:
            break
    return (x + y, x - y)

def main():
    # とある気圧の観測データ [hPa], 1 Hz sampling
    baro = [932.08,932.09,932.09,932.1,932.09,932.09,932.08,932.14,932.09,932.08,932.13,932.02,932.11,932.09,932.08,932.11,932.07,932.11,932.08,932.11,931.95,932.1,932.1,932.1,932.07,932.08]
    result = test(baro)
    print(result)
    
    # 素因数分解
    hoge = 8550349 * 3607151
    print(factorize(hoge))
    #import sympy                        # 標準パッケージを使った場合
    #hoge = 46546135
    #result = sympy.factorint(hoge)
    #print(result)


if __name__ == '__main__':
    main()
