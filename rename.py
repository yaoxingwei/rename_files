import time 
import os
import sys

file_dir = sys.argv[1]
file_name = sys.argv[2]

def get_file_list(file_path):
    dir_list = os.listdir(file_path)
    if not dir_list:
        return
    else:
        # 注意，这里使用lambda表达式，将文件按照最后修改时间顺序升序排列
        # os.path.getmtime() 函数是获取文件最后修改时间
        # os.path.getctime() 函数是获取文件最后创建时间
        dir_list = sorted(dir_list,key=lambda x: os.path.getmtime(os.path.join(file_path, x)))
        # print(dir_list)
        return dir_list

def rename_file(dir_list):
    for i in dir_list:
        new_order = "%d" % list.index(i)
        new_name = new_order.zfill(3) + "-" + file_name
        os.rename(file_dir + i, file_dir + new_name)
        print("Original: (%s)：%s -> %s" % (list.index(i) + 1, i, new_name))

def format_file(file_path, file_list):
    for i, m4a in enumerate(file_list):
        #print(i, m4a)
        cmd = "ffmpeg -i " + file_path + m4a + " " + file_path + m4a + ".mp3"
        print(cmd)
        os.system(cmd)

list = get_file_list(file_dir)
rename_file(list)
list = get_file_list(file_dir)
format_file(file_dir, list)

