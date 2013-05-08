#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      morishita
#
# Created:     05/09/2012
# Copyright:   (c) morishita 2012
# Licence:     <your licence>
#-------------------------------------------------------------------------------
#!/usr/bin/env python

import re
import GPS
import datetime

reSdfPatternd        = re.compile(r',\d{2}\.\d{2}\.\d{4},\d{2}:\d{2}\.\d{2},\d+\.\d+,\d+\.\d+,\d+,\d+\.?\d*,-?\d+,')
reSdfGroupedPattern = re.compile(r',(?P<day>\d{2})\.(?P<month>\d{2})\.(?P<year>\d{4}),(?P<hour>\d{2}):(?P<minute>\d{2})\.(?P<second>\d{2}),(?P<lat>\d+\.\d+),(?P<lon>\d+\.\d+),(?P<height>\d+),(?P<hoge1>\d+\.?\d*),(?P<hoge2>-?\d+),')


def getTime(line):
    """ 1回分のログ（文字列）から時刻を抽出して、時刻オブジェクトを返す
    文字列が不正なら、Noneを返します。
    """
    matchTest = reSdfGroupedPattern.search(line)
    if matchTest != None:
        #print(matchTest.groups())
        year   = int(matchTest.group('year'))
        month  = int(matchTest.group('month'))
        day    = int(matchTest.group('day'))
        hour   = int(matchTest.group('hour'))
        minute = int(matchTest.group('minute'))
        sec    = int(matchTest.group('second'))
        return datetime.datetime(year, month, day, hour, minute, sec, 0)
    else:
        return None
    return

def getPos(line):
    """ 文字列を解析して、位置情報を返す
    """
    matchTest = reSdfGroupedPattern.search(line)
    if matchTest != None:
        #print(matchTest.groups())
        b   = float(matchTest.group('lat'))
        l  = float(matchTest.group('lon'))
        h    = float(matchTest.group('height'))
        return GPS.BLH(b, l, h)
    else:
        return None
    return

def main():
    pass

if __name__ == '__main__':
    main()
