#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import coordinate
import numpy as np
import datum.WGS84 as wgs84
import math

def dop(star_positions, receiver_position):
	""" 幾何情報から、測位精度指標DOPを計算する
	"""
	r = []
	for position in star_positions:
		_r = position.distance(receiver_position)
		r.append(_r)

	# デザイン行列（幾何行列）作成
	G = []
	for i in range(len(star_positions)):
		_r = r[i]
		_p = star_positions[i]
		row = [-(_p.e - receiver_position.e) / _r, \
		       -(_p.n - receiver_position.n) / _r, \
		       -(_p.u - receiver_position.u) / _r]
		G.append(row)
	G = np.matrix(G)

	# DOPの計算
	C = (G.T * G).I
	C = C.tolist()
	#print(C)
	PDOP = math.sqrt(C[0][0] + C[1][1] + C[2][2])
	HDOP = math.sqrt(C[0][0] + C[1][1])
	VDOP = math.sqrt(C[2][2])
	return {"PDOP":PDOP, "HDOP":HDOP, "VDOP":VDOP}

def hoge(star_positions, receiver_position, measured_distances, weight=None):
	""" 測位計算を行う
	"""
	# 重み行列の調整
	if weight == None:
		weight =  np.eye(len(star_positions))
		weight = np.matrix(weight)
	#print(type(weight))

	# 適当な初期座標からの距離
	r = []
	for position in star_positions:
		_r = position.distance(receiver_position)
		r.append(_r)
	#print("r")
	#print(r)

	# 観測された距離との差分を求める
	delta_r = []	
	for i in range(len(r)):
		_r0 = r[i]
		_r1 = measured_distances[i]
		delta_r.append(_r1 - _r0)
	#print("delta r")
	#print(delta_r)

	# デザイン行列（幾何行列）作成
	G = []
	for i in range(len(star_positions)):
		_r = r[i]
		_p = star_positions[i]
		row = [-(_p.e - receiver_position.e) / _r, \
		       -(_p.n - receiver_position.n) / _r, \
		       -(_p.u - receiver_position.u) / _r]
		G.append(row)
	G = np.matrix(G)

	# 座標の修正量を求める
	dr = np.array(delta_r)
	x = np.dot((G.T * weight * G).I * G.T * weight, dr)
	return x


def main():
	""" self test
	"""
	a = coordinate.enu(wgs84, -100, 0, 0)
	b = coordinate.enu(wgs84, 100, 0, 0)
	c = coordinate.enu(wgs84, 0, 100, 0)
	d = coordinate.enu(wgs84, 0, -100, 0)
	user = coordinate.enu(wgs84, 0, 0, 10.1)
	distance = [244, 144, 141, 240]
	for i in range(10):
		#print(i)
		fuga = hoge([a, b, c, d], user, distance)
		fuga = fuga.tolist()
		fuga = fuga[0]
		user.e += fuga[0]
		user.n += fuga[1]
		user.u += fuga[2]
	print(user)

	_dop = dop([a, b, c, d], user)
	print(_dop)

if __name__ == '__main__':
    main()