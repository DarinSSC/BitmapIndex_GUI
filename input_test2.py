import pickle
import string
__author__ = 'zhai_jy'


def input_attr(path1, path2):
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

    attr_num = len(attr_list)
    for i in range(attr_num):
        print '----------------'
        for adict in attr_map[i].items():
            print adict

    attr_input = [[] for i in range(attr_num)]
    for i in range(attr_num):
        print 'Please input the attributes you want in <%s>,or input <All>' % attr_list[i]
        attrlist = raw_input()
        attrlist = string.split(attrlist, ',')
        for attri in attrlist:
            if attri == 'All':
                attr_input[i].append(-1)
            elif attri in attr_map[i]:
                attr_input[i].append(attr_map[i][attri])
            else:
                print 'No eligible projects'
                break

    return attr_input, attr_num, attr_total, lists, key, offset


if __name__ == '__main__':
    path1 = 'data_map.pkl'
    path2 = 'bitmap_pic.pkl'
    attr_input, attr_num, attr_total, lists, key, offset = input_attr(path1, path2)





