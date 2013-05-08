#-------------------------------------------------------------------------------
# Name:        strCodeConvert.py
# Purpose:      文字コードの相互変換を行う。
#               str（ユニコード）を渡せば指定のコードへ変換し、それ以外ではユニコードへの変換を実施する。
#               参考文献：http://d.hatena.ne.jp/kakurasan/20100329/p1
# Author:      morishita
#
# Created:     21/11/2012
# Copyright:   (c) morishita 2012
# Licence:     i have no licence. this code by 技術志向 (http://speirs.blog17.fc2.com/blog-entry-4.html).
#-------------------------------------------------------------------------------
#!/usr/bin/env python
# -*- coding: utf-8 -*-
import codecs

def conv_encoding(data, to_enc="utf_8"):
    """
    stringのエンコーディングを変換する
    @param ``data'' str object.
    @param ``to_enc'' specified convert encoding.
    @return str object.
    """
    if isinstance(data, str):
        return data.encode(to_enc)
    lookup = ('utf_8', 'euc_jp', 'euc_jis_2004', 'euc_jisx0213',
            'shift_jis', 'shift_jis_2004','shift_jisx0213',
            'iso2022jp', 'iso2022_jp_1', 'iso2022_jp_2', 'iso2022_jp_3',
            'iso2022_jp_ext','latin_1', 'ascii')
    for encoding in lookup:
        try:
            data = data.decode(encoding)
            break
        except:
            pass
    return data

def conv_encoding(data):
    """ strで渡されたデータを適切な文字コードでデコードする（Unicodeにする）
    """
    lookup = ('utf_8', 'euc_jp', 'euc_jis_2004', 'euc_jisx0213',
            'shift_jis', 'shift_jis_2004','shift_jisx0213',
            'iso2022jp', 'iso2022_jp_1', 'iso2022_jp_2', 'iso2022_jp_3',
            'iso2022_jp_ext','latin_1', 'ascii')
    for encoding in lookup:
        try:
            data = data.decode(encoding)
            break
        except:
            pass
    return data

def main():
    hoge = "赤い"
    text = 'りんご'.encode('utf-8')
    text2 = "あおりんご".encode('utf-8').decode('utf-8')
    result = conv_encoding("たべたいな")
    print(result)

if __name__ == '__main__':
    main()
