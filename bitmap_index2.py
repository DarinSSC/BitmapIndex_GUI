import input_test2
import numpy
import time
import numbapro
import pickle
import data_pickle
import bitmap_pickle
from numbapro import cuda
from numba import *

__author__ = 'zhai_jy'

tpb = 1024

def get_attr(attr_input, attr_num, attr_total, lists, key, offset):  # get attr in bitmap_list
    bin32 = 0xffffffff
    bin31 = 0x80000000
    bitmap_list = [([0] * attr_total) for i in range(attr_num)]
    lengt = [[]for i in range(attr_num)]
    lie = [[]for i in range(attr_num)]
    for i in range(attr_num):
        for j in range(len(attr_input[i])):
            attrt = attr_input[i][j]
            if attrt != -1:
                lengt[i].append(key[i][attrt])
                lie[i].append(offset[i][attrt])
            else:
                lengt[i].append(0)
                lie[i].append(0)

    for i in range(attr_num):
        for j in range(len(attr_input[i])):
            attrt = attr_input[i][j]
            if attrt != -1:
                local = -1
                for k in range(lengt[i][j]):
                    local += 1
                    attr_bit = lists[i][lie[i][j] + k]
                    if attr_bit > bin31:
                        #print '******************************local'
                        #print local
                        bitmap_list[i][local] |= attr_bit
                    else:
                        local = local + attr_bit - 1

            else:
                for k in range(attr_total):  # if All, set 1-Fill
                    bitmap_list[i][k] = bin32

    return bitmap_list


@cuda.jit('void(int32[:,:], int32[:], int32, int32, int32)', target = 'gpu')
def index_gpu(bitmap_list, index_list, attr_num, attr_total, attr_mul):  # list[] & list[]
    idx = cuda.grid(1)
    for i in range(attr_mul):
        idy = idx * attr_mul + i
        if idy < attr_total:
            num = 0xffffffff
            bin1 = 0x80000000
            for j in range(attr_num):
                num = num & bitmap_list[j][idy]

            num = num << 1
            for j in range(31):
                if num & bin1 == bin1:		#find address
                    addr = idy * 31 + j + 1
                    index_list[addr-1] = addr

                num = num << 1

def get_indexList(path, attr_selected):
    path1, path2, attr_num = bitmap_pickle.get_pic_path(path)
    f1 = open(path1, 'rb')  # read data_map.pkl
    try:
        attr_map = pickle.load(f1)
        attr_list = pickle.load(f1)
        attr_total = pickle.load(f1)
    finally:
        f1.close()

    f2 = open(path2, 'rb')  # read bitmap_pic.pkl
    try:
        lists = pickle.load(f2)
        key = pickle.load(f2)
        offset = pickle.load(f2)
    finally:
        f2.close()

    # attr_input is a list that stores the numbers of input attributes
    # attr_num is the total number of attributes
    # attr_total is the total number of data/31
	attr_input = [[] for i in xrange(attr_num)]
	for i in xrange(attr_num):
		for attri in attr_selected[i]:
			if attri in attr_map[i]:
				attr_input[i].append(attr_map[i][attri])
			elif attri == 'All':
				attr_input[i].append(-1)
		if len(attr_input[i])>1 and (-1 in attr_input[i]):
			attr_input[i].remove(-1)
	print attr_input

    search_start_time = time.time()
    if len(attr_input) != attr_num:  # there might be a wrong input in input_test.py
        print 'No eligible projects'
    else:
        tpb = 1024
        blocknum = 1
        attr_mul = (attr_total + (tpb * blocknum - 1))/(tpb * blocknum)
        # attr_mul is the number that each thread need to be performed
        #print '---index----\nattr_num:%d\nattr_total:%d\nattr_mul:%d\n----------' % (attr_num, attr_total, attr_mul)
        # attr_num = 1
        index_list = numpy.zeros(attr_total*31, dtype='int32')
        bitmap_list = get_attr(attr_input, attr_num, attr_total, lists, key, offset)
        stream = cuda.stream()
        d_bitmap_list = cuda.to_device(numpy.array(bitmap_list), stream)
        d_index_list = cuda.to_device(numpy.array(index_list), stream)
        index_gpu[blocknum, tpb, stream](d_bitmap_list, d_index_list, attr_num, attr_total, attr_mul)
        index_list = d_index_list.copy_to_host()
        stream.synchronize()
    search_end_time = time.time()
    return index_list, search_end_time-search_start_time

if __name__ == '__main__':
    #path1 = 'data_map.pkl'  # get data_map
    #path2 = 'bitmap_pic.pkl'   # get bitmap
    path = 'data.txt'
    path1, path2,attr_num = bitmap_pickle.get_pic_path(path)
    
    attr_input, attr_num, attr_total, lists, key, offset = input_test2.input_attr(path1, path2)
    # attr_input is a list that stores the numbers of input attributes
    # attr_num is the total number of attributes
    # attr_total is the total number of data/31
    

    if len(attr_input) != attr_num:  # there might be a wrong input in input_test.py
        print 'No eligible projects'
    else:
        tpb = 1024
        attr_mul = 1
        blocknum = (attr_total+(tpb - 1))/tpb
        #attr_mul = (attr_total + (tpb * blocknum - 1))/(tpb * blocknum)
        # attr_mul is the number that each thread need to be performed
        print '---index----\nattr_num:%d\nattr_total:%d\nattr_mul:%d\n----------' % (attr_num, attr_total, attr_mul)
        # attr_num = 1
        index_list = numpy.zeros(attr_total*31, dtype='int32')
        bitmap_list = get_attr(attr_input, attr_num, attr_total, lists, key, offset)
        stream = cuda.stream()
        d_bitmap_list = cuda.to_device(numpy.array(bitmap_list), stream)
        d_index_list = cuda.to_device(numpy.array(index_list), stream)
        index_gpu[blocknum, tpb, stream](d_bitmap_list, d_index_list, attr_num, attr_total, attr_mul)
        index_list = d_index_list.copy_to_host()
        stream.synchronize()
        print '----index_list------'
        print '[',
        for index in index_list:
            if index != 0:
                print '%d,' % index,
        print ']'

