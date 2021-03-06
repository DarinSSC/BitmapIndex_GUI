#!/usr/bin/python
# coding=utf-8

import data_pickle
import radix_sort
import numpy
import numbapro
import time
import math
import pickle
from numbapro import cuda
from numba import *

tpb = 1024

@cuda.jit('void(int32[:,:],int32[:,:],int32[:,:])',target = 'gpu')
def sum(a,b,c):	
	i,j = cuda.grid(2)
	c[i][j] = a[i][j] + b[i][j]
	

def set_bit(num,off_set):
	#off_set should be range from 0 to 31.
	#The right bit refers to 0 while the left to 31
	mask = 1<<off_set
	return (num|mask)
	
def bin(s):
	#transform the integer to the type of binary code
	#return value is a string
	return str(s) if s<=1 else bin(s>>1) + str(s&1)

#step2.produce chId and literal
@cuda.jit('void(int64[:], uint32[:], int64[:], int64)', target='gpu')
def produce_chId_lit_gpu(rid, literal, chunk_id, length):
	i = cuda.grid(1)
	if i <length:
		chunk_id[i] = rid[i]/31
		literal[i] = (literal[i]|1<<31) #the left bit set to 1
		off_set = 30-rid[i]%31
		literal[i] = (literal[i]|1<<off_set)


@cuda.jit('void(int32[:], int64[:], int32, int32[:])')
def produce_flag(input_data, chunk_id, length, flag):#flag initialized to 0 if a reduced segment start here, flag set to 1
	i = cuda.grid(1)
	if i<length:
		if i == 0 or (input_data[i] != input_data[i-1] or chunk_id[i] != chunk_id[i-1]):
			flag[i] = 1

@cuda.jit('void(int64[:], int64[:], int64[:], int64)')
def get_startPos(dd_flag, d_flag, d_start_pos, length):
	i = cuda.grid(1)
	if i<length and dd_flag[i]:
		d_start_pos[d_flag[i]] = i

@cuda.jit('void(uint32[:], uint32[:], int64)',target='gpu')
def or_reduction(literal, tmp_out, length):
    
    bw = cuda.blockDim.x
    bx = cuda.blockIdx.x
    tid = cuda.threadIdx.x
    shared_list = cuda.shared.array(shape = (tpb), dtype = uint32)
	
    i = bx*bw + tid
    shared_list[tid] = 0x00000000
    if i<length:
    	shared_list[tid] = literal[i]

    cuda.syncthreads()

    hop = bw/2
    while hop > 0:
        if tid < hop:
			shared_list[tid] = shared_list[tid] | shared_list[tid+hop]

        cuda.syncthreads()
        hop /= 2
    if tid == 0:
        tmp_out[bx] = shared_list[0]
  
'''
def reduce_by_key(input_data, chunk_id, literal, length):
	length = numpy.int64(len(input_data))
	bin_length = max(len(bin(length-1)),len(bin(tpb-1)))
	thread_num = numpy.int64(math.pow(2,bin_length))
	block_num = max(thread_num/tpb,1)

	flag = numpy.zeros(thread_num, dtype='int64')
	arg_useless = numpy.zeros(thread_num, dtype='int64')
	stream = cuda.stream()
	d_flag = cuda.to_device(flag, stream)
	d_chunk_id = cuda.to_device(chunk_id, stream)
	d_literal = cuda.to_device(literal, stream)
	
	produce_flag[block_num,tpb](input_data, d_chunk_id, length, d_flag)
	d_flag.to_host(stream)
	stream.synchronize()
	
	start_pos = numpy.ones(length, dtype='int64') * (-1)
	
	radix_sort.Blelloch_scan_caller(d_flag, arg_useless, 0)
	
	d_start_pos = cuda.to_device(start_pos, stream)
	dd_flag = cuda.to_device(flag, stream)

	get_startPos[(length-1)/tpb+1, tpb](dd_flag, d_flag, d_start_pos, length)
	d_start_pos.to_host(stream)
	stream.synchronize()
	
	start_pos = filter(lambda x: x>=0, start_pos)

	reduced_length = len(start_pos)

	start_pos = list(start_pos)
	start_pos.append(length)

	reduced_input_data = []
	reduced_chunk_id = []
	reduced_literal =[]

	print 'append stage in reduce_by_key:'
	start = time.time()
	for i in xrange(reduced_length):
		data_to_reduce = literal[start_pos[i]:start_pos[i+1]]

		reduce_block_num = (len(data_to_reduce)-1)/tpb + 1 
		
		tmp_out = numpy.zeros(reduce_block_num, dtype='uint32')
		d_tmp_out = cuda.to_device(tmp_out, stream)

		or_reduction[reduce_block_num, tpb](numpy.array(data_to_reduce), d_tmp_out,len(data_to_reduce))

		d_tmp_out.to_host(stream)
		stream.synchronize()
		result = 0x00000000
		for j in xrange(reduce_block_num):
			result |= tmp_out[j]
		
		reduced_input_data.append(input_data[start_pos[i]])
		reduced_chunk_id.append(chunk_id[start_pos[i]])
		reduced_literal.append(result)
	end = time.time()
	print str(end-start)
	return numpy.array(reduced_input_data), numpy.array(reduced_chunk_id), reduced_literal
'''

@cuda.jit('void(uint32[:], int64[:], int64, uint32[:], int32[:], int64[:], int32[:], int64[:])')
def get_reduced(literal, start_pos, reduced_length, reduced_literal, input_data, chunk_id, reduced_input_data, reduced_chunk_id):
	i = cuda.grid(1)
	if i < reduced_length:
		for lit in literal[start_pos[i]:start_pos[i+1]]:
			reduced_literal[i] |= lit
		reduced_input_data[i] = input_data[start_pos[i]]
		reduced_chunk_id[i] = chunk_id[start_pos[i]]
		

def reduce_by_key(input_data, chunk_id, literal, length):
	length = numpy.int64(len(input_data))
	bin_length = max(len(bin(length-1)),len(bin(tpb-1)))
	thread_num = numpy.int64(math.pow(2,bin_length))
	block_num = max(thread_num/tpb,1)

	flag = numpy.zeros(thread_num, dtype='int64')
	arg_useless = numpy.zeros(thread_num, dtype='int64')
	stream = cuda.stream()
	d_flag = cuda.to_device(flag, stream)
	d_chunk_id = cuda.to_device(chunk_id, stream)
	d_literal = cuda.to_device(literal, stream)
	
	produce_flag[block_num,tpb](input_data, d_chunk_id, length, d_flag)
	d_flag.to_host(stream)
	stream.synchronize()
	
	start_pos = numpy.ones(length, dtype='int64') * (-1)
	
	radix_sort.Blelloch_scan_caller(d_flag, arg_useless, 0)
	 
	d_start_pos = cuda.to_device(start_pos, stream)
	dd_flag = cuda.to_device(flag, stream)
	
	get_startPos[(length-1)/tpb+1, tpb](dd_flag, d_flag, d_start_pos, length)
	d_start_pos.to_host(stream)
	stream.synchronize()

	start_pos = filter(lambda x: x>=0, start_pos)
	reduced_length = len(start_pos)
	start_pos = list(start_pos)
	start_pos.append(length)
	#print reduced_length

	reduced_input_data = numpy.zeros(reduced_length, dtype='int32')
	reduced_chunk_id = numpy.zeros(reduced_length, dtype='int64')
	reduced_literal =numpy.zeros(reduced_length, dtype='uint32')

	#print 'append stage in reduce_by_key:'
	start = time.time()
	dd_start_pos = cuda.to_device(numpy.array(start_pos), stream)
	d_reduced_chunk_id = cuda.to_device(reduced_chunk_id, stream)
	d_reduced_literal = cuda.to_device(reduced_literal, stream)
	d_reduced_input_data = cuda.to_device(reduced_input_data, stream)

	block_num = (reduced_length-1)/tpb + 1
	get_reduced[block_num, tpb](d_literal, dd_start_pos, reduced_length, d_reduced_literal, input_data, d_chunk_id, d_reduced_input_data, d_reduced_chunk_id)#kernel function

	d_reduced_literal.to_host(stream)
	d_reduced_chunk_id.to_host(stream)
	d_reduced_input_data.to_host(stream)	
	stream.synchronize()
	
	'''
	reduced_input_data = []
	reduced_chunk_id = []
	reduced_literal =[]
	for i in xrange(reduced_length):
		data_to_reduce = literal[start_pos[i]:start_pos[i+1]]

		reduce_block_num = (len(data_to_reduce)-1)/tpb + 1 
		
		tmp_out = numpy.zeros(reduce_block_num, dtype='uint32')
		d_tmp_out = cuda.to_device(tmp_out, stream)
		start = time.time()
		or_reduction[reduce_block_num, tpb](numpy.array(data_to_reduce), d_tmp_out,len(data_to_reduce))
		end = time.time()
		print str(end-start)
		d_tmp_out.to_host(stream)
		stream.synchronize()
		result = 0x00000000
		for j in xrange(reduce_block_num):
			result |= tmp_out[j]
		
		reduced_input_data.append(input_data[start_pos[i]])
		reduced_chunk_id.append(chunk_id[start_pos[i]])
		reduced_literal.append(result)
	'''
	end = time.time()
	#print str(end-start)
	return numpy.array(reduced_input_data), numpy.array(reduced_chunk_id), reduced_literal	

@cuda.jit('void(int32[:], int32[:], int64)')
def produce_head(reduced_input_data, d_head, reduced_length):
	i = cuda.grid(1)
	if i<reduced_length and i>0:
		if reduced_input_data[i]==reduced_input_data[i-1]:
			d_head[i] = 0

@cuda.jit('void(int32[:], int64[:], int64[:], int64)')
def produce_fill_gpu(d_head, d_reduced_chunk_id, reduced_chunk_id, reduced_length):
	i = cuda.grid(1)
	if i<reduced_length:
		if not d_head[i]:
			d_reduced_chunk_id[i] = reduced_chunk_id[i] - reduced_chunk_id[i-1] - 1
		
def produce_fill(reduced_input_data, reduced_chunk_id, reduced_length):#step 4
	head = numpy.ones(reduced_length, dtype='int32')
	stream = cuda.stream()
	d_head = cuda.to_device(head, stream)
	d_reduced_input_data = cuda.to_device(reduced_input_data, stream)
	
	block_num = reduced_length/tpb + 1

	produce_head[block_num,tpb](d_reduced_input_data, d_head, reduced_length)#produce head
	d_head.to_host(stream)
	stream.synchronize()
	d_reduced_chunk_id = cuda.to_device(reduced_chunk_id,stream)
	produce_fill_gpu[block_num, tpb](d_head, d_reduced_chunk_id, reduced_chunk_id, reduced_length)
	d_reduced_chunk_id.to_host(stream)
	stream.synchronize()
	#convert to int32 because the range a fill_word can describe is 0~(2^31-1)
	return numpy.array(reduced_chunk_id, dtype='int32'), head

@cuda.jit('void(int32[:], int32[:], uint32[:], int32[:], int64)')
def getIdx_gpu(fill_word, reduced_literal, index, compact_flag, length):
	i = cuda.grid(1)
	if i<length:
		index[i*2] = fill_word[i]
		index[i*2+1] = reduced_literal[i]
		if not fill_word[i]:
			compact_flag[i*2] = 0

@cuda.jit('void(uint32[:], int64[:], int64[:], uint32[:], int64)')
def scatter_index(d_index, d_compact_flag, compact_flag, out_index, reduced_length):
	i = cuda.grid(1)
	if i<2*reduced_length and compact_flag[i]:
		out_index[d_compact_flag[i]] = d_index[i]		


def getIdx(fill_word,reduced_literal, reduced_length, head, cardinality):#step 5: get index by interleaving fill_word and literal(also remove all-zeros word)
	bin_length = max(len(bin(2*reduced_length-1)),len(bin(tpb-1)))#the bit number of binary form of array length
	thread_num = numpy.int64(math.pow(2,bin_length))#Blelloch_scan need the length of scanned array to be even multiple of thread_per_block
	compact_flag = numpy.ones(thread_num, dtype='int64')
	index = numpy.ones(2*reduced_length, dtype='uint32')
	d_index = cuda.to_device(index)
	d_fill_word = cuda.to_device(fill_word)
	d_reduced_literal = cuda.to_device(numpy.array(reduced_literal))
	d_compact_flag = cuda.to_device(compact_flag)

	block_num = reduced_length/tpb + 1

	getIdx_gpu[block_num, tpb](d_fill_word, d_reduced_literal, d_index, d_compact_flag, reduced_length)
	compact_flag = d_compact_flag.copy_to_host()

	useless_array = numpy.zeros(thread_num, dtype='int64')
	radix_sort.Blelloch_scan_caller(d_compact_flag, useless_array, 0)
	out_index_length = d_compact_flag.copy_to_host()[2*reduced_length-1] + 1
	out_index = numpy.zeros(out_index_length, dtype='uint32')
	offsets = []
	
	new_block_num = 2*reduced_length/tpb + 1

	scatter_index[new_block_num, tpb](d_index, d_compact_flag, compact_flag, out_index, reduced_length)
	for i in xrange(reduced_length):
		if head[i]:
			offsets.append(d_compact_flag.copy_to_host()[2*i])

	key_length = numpy.zeros(cardinality, dtype='int64')

	for i in xrange(cardinality-1):
		key_length[i] = offsets[i+1] - offsets[i]
	key_length[cardinality-1] = out_index_length - offsets[cardinality-1]

	return out_index, numpy.array(offsets), numpy.array(key_length)	
		
def get_pic_path(path):
	#print 'open source file in bitmap_pickle: '.strip()
	start = time.time()
	attr_dict,attr_values,attr_value_NO,attr_list, data_pic_path = data_pickle.openfile(path)
	end = time.time()
	#print str(end-start)

	#print 'index part(get bitmap, keylength and offset): '.strip()
	start = time.time()
	attr_num = len(attr_list)
	lists = [[]for i in xrange(attr_num)]
	key = [[]for i in xrange(attr_num)]
	offset = [[]for i in xrange(attr_num)]

	# attr_num = 1
	total_row = len(attr_values[0])
	for idx in range(attr_num):
		input_data = numpy.array(attr_values[idx])
		length = input_data.shape[0]
		rid = numpy.arange(0,length)
		#step1 sort
		#print 'time in step1--sort:'
		start = time.time()
		radix_sort.radix_sort(input_data,rid)
		end = time.time()
		#print str(end-start)		

		cardinality = len(attr_value_NO[idx].items())
		literal = numpy.zeros(length, dtype = 'uint32')
		chunk_id = numpy.zeros(length, dtype = 'int64')

		#print 'time in step2--produce chId_lit:'
		start = time.time()
		stream = cuda.stream()
		#d_rid = cuda.to_device(rid, stream)
		d_chunk_id = cuda.to_device(chunk_id, stream)
		d_literal = cuda.to_device(literal, stream)
		#step2 produce chunk_id and literal
		produce_chId_lit_gpu[length/tpb+1, tpb](rid, d_literal, d_chunk_id, length)
		
		#d_rid.to_host(stream)
		d_chunk_id.to_host(stream)
		d_literal.to_host(stream)
		stream.synchronize()
		end = time.time()
		#print str(end-start)

		#step3 reduce by key(value, chunk_id)
		#print 'time in step3--reduce by key:'
		start = time.time()
		reduced_input_data,	reduced_chunk_id, reduced_literal = reduce_by_key(input_data, chunk_id, literal, length)
		reduced_length = reduced_input_data.shape[0]#row
		end = time.time()
		#print str(end-start)
		#print '##############################reduced############################'
		#for i in xrange(reduced_length):
		#	print reduced_input_data[i], reduced_chunk_id[i], bin(reduced_literal[i])

		#step4 produce 0-Fill word
		#print 'time in step4--produce 0-fill word:'
		start = time.time()
		fill_word, head = produce_fill(reduced_input_data, reduced_chunk_id, reduced_length)
		end = time.time()
		#print str(end-start)

		#step 5 & 6: get index by interleaving 0-Fill word and literal(also remove all-zeros word)
		#print 'time in step5--get out_index & length & offset:'
		start = time.time()
		out_index, offsets, key_length = getIdx(fill_word,reduced_literal, reduced_length, head, cardinality)
		end = time.time()
		#print str(end-start)

		lists[idx] = out_index
		key[idx] = key_length
		offset[idx] = offsets
	end = time.time()
	#print str(end-start)
	'''
	print '*****************index:'
	print lists
	print '*****************length:'
	print key
	print '*****************offset:'
	print offset
	'''

	print 'put index result into file: '.strip()
	start = time.time()
	bitmap_pic_path = 'bitmap_pic.pkl'
	f1 = open(bitmap_pic_path, 'wb')
	pickle.dump(lists, f1, True)
	pickle.dump(key, f1, True)
	pickle.dump(offset, f1, True)
	f1.close()
	end = time.time()
	print str(end-start)
	return data_pic_path, bitmap_pic_path, attr_num

if __name__ == '__main__':
	path = 'data.txt'	#file path
	attr_dict,attr_values,attr_value_NO,attr_list, data_pic_path = data_pickle.openfile(path)
	attr_num = len(attr_list)
	lists = [[]for i in xrange(attr_num)]
	key = [[]for i in xrange(attr_num)]
	offset = [[]for i in xrange(attr_num)]
	
	# attr_num = 1
	total_row = len(attr_values[0])
	for idx in range(attr_num):
		input_data = numpy.array(attr_values[idx])
		length = input_data.shape[0]
		rid = numpy.arange(0,length, dtype='int64')

		#step1 sort
		radix_sort.radix_sort(input_data,rid)
		print rid
		print rid.dtype
		cardinality = len(attr_value_NO[idx].items())
		literal = numpy.zeros(length, dtype = 'uint32')
		chunk_id = numpy.zeros(length, dtype = 'int64')
		
		stream = cuda.stream()
		#d_rid = cuda.to_device(rid, stream)
		d_chunk_id = cuda.to_device(chunk_id, stream)
		d_literal = cuda.to_device(literal, stream)
		#step2 produce chunk_id and literal
		produce_chId_lit_gpu[length/tpb+1, tpb](rid, d_literal, d_chunk_id, length)
		#d_rid.to_host(stream)
		d_chunk_id.to_host(stream)
		d_literal.to_host(stream)
		stream.synchronize()
		print '!!!!!!!!!!!!!!!!!!!!!!!!!!chunk_id:!!!!!!!!!!!!!!!!!!!'
		print chunk_id
		#step3 reduce by key(value, chunk_id)
		reduced_input_data,	reduced_chunk_id, reduced_literal = reduce_by_key(input_data, chunk_id, literal, length)
		reduced_length = reduced_input_data.shape[0]#row
	#	print '##############################reduced############################'
#		for i in xrange(reduced_length):
#			print reduced_input_data[i], reduced_chunk_id[i], bin(reduced_literal[i])

		#step4 produce 0-Fill word
		fill_word, head = produce_fill(reduced_input_data, reduced_chunk_id, reduced_length)

		#step 5 & 6: get index by interleaving 0-Fill word and literal(also remove all-zeros word)
		out_index, offsets, key_length = getIdx(fill_word,reduced_literal, reduced_length, head, cardinality)
		
		lists[idx] = out_index
		key[idx] = key_length
		offset[idx] = offsets
	
	#print '*****************index:'
	#print lists
	#print '*****************length:'
	#print key
	#print '*****************offset:'
	#print offset

	f1 = open('bitmap_pic.pkl', 'wb')
	pickle.dump(lists, f1, True)
	pickle.dump(key, f1, True)
	pickle.dump(offset, f1, True)
	f1.close()


	
