#!/usr/bin/env python
#_*_ coding:utf-8 _*_
'''
@auther: tanglei
@contact: tanglei_0315@163.com
@file: MeetingClientLogAlert.py
@time: 2019/2/22 11:20
'''
import os,sys,stat
import re
import ConfigParser
import json
import time
import shutil
from common.logger import logger
from ctypes import cdll

Logger_Info_file = logger("INFO")
Logger_Error_file = logger("ERROR")

#去除BOM_UTF8编码的\xef\xbb\xbf的第一种方法
def DeleteBOM_UTF8(file_name):
    file_temp = []
    f = open(file_name,'r')
    for line in f.readlines():
        if '\xef\xbb\xbf' in line:
            data = line.replace('\xef\xbb\xbf','')
        else:
            data = line
        file_temp.append(data)
    fw = open(file_name,'w')
    fw.truncate()
    for item in file_temp:
        fw.writelines(item)
    fw.close()
    f.close()

#去除BOM_UTF8编码的\xef\xbb\xbf的第二种方法
def remove_BOM(config_path):
    content = open(config_path).read()
    content = re.sub(r"\xfe\xff","", content)
    content = re.sub(r"\xff\xfe","", content)
    content = re.sub(r"\xef\xbb\xbf","", content)
    open(config_path, 'w').write(content)

#获取配置文件
file_path = os.path.join(os.path.abspath('conf'),'setting.ini')
remove_BOM(file_path)
conf = ConfigParser.ConfigParser()
conf.read(file_path)
dir_name = conf.get('FILE','dir')
file_name = conf.get('FILE','file')
key_name_createmeeting = conf.get('KEY','CreateMeeting')
key_name_createmeetingresponse = conf.get('KEY','CreateMeetingResponse')
os_compare_file_time = int(conf.get('TIME_NUMBER','OS_COMPARE_FILE_TIME'))
interval_time = int(conf.get('TIME_NUMBER','INTERVAL_TIME'))
count_num = int(conf.get('TIME_NUMBER','COUNT_NUMBER'))
count_wait_time = int(conf.get('TIME_NUMBER','COUNT_WAIT_TIME'))
interval_key_time = int(conf.get('TIME_NUMBER','INTERVAL_KEY_TIME'))

#找到目录下指定文件名的最新日志文件
def find_new_file(dir,file):

    temp_list = []
    file_lists = os.listdir(dir)
    for f in file_lists:
        if file in f and f.endswith('.txt'):
            temp_list.append(f)
    temp_list.sort(key=lambda file:os.path.getmtime(dir+'\\'+file))
    filepath = os.path.join(dir,temp_list[-1])
    return filepath

#获得最新日志文件创建的时间戳
def create_file_time(file):
    time = int(os.path.getctime(file))
    return time

#获取当前系统的时间戳
def get_os_time():
    t = int(time.time())
    return t

#确定最新文件中关键字的字符所在位置
def seek_number(file,key):

    with open(file,'r') as f:
        col = 0
        while f:
            col += 1
            temp_str = f.readline()
            index = temp_str.find(key)
            if index != -1:
                return f.tell()
            if not temp_str:
                return 44

#提取关键字所在行的下面一行的字符串
def next_str(file,seek_num,key):

    with open(file,'r') as f:
        f.seek(seek_num,0)
        lines = f.readlines()
        for line in lines:
            patten = key
            result = re.search(patten,line)
            if result:
                return line

#截取返回的字符串信息
def cut_str(str):

    str_1 = str.replace("$@$","")
    pos = str_1.find('{')
    return str_1[pos:]

#将字符串通过json转为字典格式，并判断其中的结果
def is_result(str):

    response_dict = json.loads(str)
    result_rc = response_dict["result"]["rc"]
    if result_rc != 0:
        return 444

#查看文件夹的权限
def get_permission(dir):
    mode = oct(os.stat(dir).st_mode)[-3:]
    return mode

#修改日志文件夹目录，以方便进行日志文件的删除操作
def set_permission(dir):
    os.chmod(dir,stat.S_IRWXO|stat.S_IRWXG|stat.S_IRWXU)

#清空目录下面的所有文件
def remove_dir_file(dir):
    for root,dirs,files in os.walk(dir,topdown=False):
        for name in files:
            filename = os.path.join(root,name)
            os.remove(filename)
        for name in dirs:
            os.rmdir(os.path.join(root,name))

#统计最新的文件行数
def count_file(file):
    with open(file,'r') as f:
        count = len(f.readlines())
        f.close()
        return count

if __name__ == '__main__':
    try:
        try:
            remove_dir_file(dir_name)
        except Exception,e:
            Logger_Error_file.exception(e)
        temp_list = []
        while_str = True
        while while_str:
            if os.listdir(dir_name):
                new_log_file = find_new_file(dir_name, file_name)
                print '新的文件绝对路径:%s' % (new_log_file)
                Logger_Info_file.info('新的文件绝对路径:%s' % (new_log_file))
                try:
                    if get_os_time() - create_file_time(new_log_file) > os_compare_file_time:
                        print '没有新的日志文件创建，所以按键精灵出现问题,重复的文件名为%s' % (new_log_file)
                        Logger_Error_file.error('没有新的日志文件创建，所以按键精灵出现问题,重复的文件名为%s' % (new_log_file))
                        while_str = False
                        break
                    else:
                        for item in range(0,count_wait_time):
                            count = count_file(new_log_file)
                            if count >= count_num:
                                seeknum = seek_number(new_log_file, key_name_createmeeting)
                                print '日志行数为%s行后，进行关键字查询' % (count)
                                Logger_Info_file.info('日志行数为%s行后，进行关键字查询' % (count))
                                time_i = item
                                break
                            else:
                                time.sleep(interval_key_time)
                                if item == count_wait_time - 1 and count <= count_num:
                                    print '%s秒内的日志行数无法满足关键字查询的条件，请查看一下按键精灵和网络是否正常' % (count_wait_time)
                                    Logger_Error_file.error('%s秒内的日志行数无法满足关键字查询的条件，请查看一下按键精灵和网络是否正常' % (count_wait_time))
                                    while_str = False
                                    break
                except Exception,e:
                    Logger_Error_file.exception(e)
                try:
                    if seeknum == 44:
                        print '没有关键字的出现，说明没有发起创建会议的动作，所以按键精灵出现问题,对应的客户端日志为%s' % (new_log_file)
                        Logger_Error_file.error('没有关键字的出现，说明没有发起创建会议的动作，所以按键精灵出现问题,对应的客户端日志为%s' % (new_log_file))
                        while_str = False
                        break
                    else:
                        response_str = next_str(new_log_file, seeknum, key_name_createmeetingresponse)
                        # 将iso-8859-1的编码转换为utf-8编码
                        cutstr = cut_str(response_str).decode('iso-8859-1').encode('utf8')
                        result = is_result(cutstr)
                        if result == 444:
                            print '根据返回值不等于0，所以大网会议创建失败,对应的客户端日志为%s' % (new_log_file)
                            Logger_Error_file.error('根据返回值不等于0，所以大网会议创建失败,对应的客户端日志为%s' % (new_log_file))
                            while_str = False
                            break
                        else:
                            if while_str == False:
                                pass
                            else:
                                print '大网会议创建成功'
                                Logger_Info_file.info('大网会议创建成功')
                    time.sleep(interval_time - time_i)
                except Exception,e:
                    Logger_Error_file.exception(e)
            else:
                print '日志目录下面没有日志文件,请查看按键精灵是否正常运行脚本'
                Logger_Error_file.error('日志目录下面没有日志文件,请查看按键精灵是否正常运行脚本')
                time.sleep(5)
    except Exception,e:
        Logger_Error_file.exception(e)