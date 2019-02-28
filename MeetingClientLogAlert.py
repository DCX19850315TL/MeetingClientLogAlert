#!/usr/bin/env python
#_*_ coding:utf-8 _*_
'''
@auther: tanglei
@contact: tanglei_0315@163.com
@file: MeetingClientLogAlert.py
@time: 2019/2/22 11:20
'''
import os
import re
import ConfigParser
import json
import time
from common.logger import logger

Logger_Info_file = logger("INFO")
Logger_Error_file = logger("ERROR")

#获取配置文件
file_path = os.path.join(os.path.abspath('conf'),'setting.ini')
conf = ConfigParser.ConfigParser()
conf.read(file_path)
dir_name = conf.get('FILE','dir')
file_name = conf.get('FILE','file')
key_name_createmeeting = conf.get('KEY','CreateMeeting')
key_name_createmeetingresponse = conf.get('KEY','CreateMeetingResponse')

#找到目录下指定文件名的最新日志文件
def find_new_file(dir,file):

    file_lists = os.listdir(dir)
    file_lists.sort(key=lambda file:os.path.getmtime(dir+'\\'+file))
    filepath = os.path.join(dir,file_lists[-1])
    return filepath

#获得最新日志文件创建的时间戳
def create_file_time(file):
    time = os.path.getctime(file)
    return time

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

#判断日志文件是否在不停的更新创建
def is_create_file(file,num):
    temp_list = []
    temp_list.append(file)
    for item in temp_list:
        if temp_list.count(item) > num:
            print '按键精灵出现问题'
            return 4444
            break

if __name__ == '__main__':
    try:
        temp_list = []
        while_str = True
        while while_str:
            new_log_file = find_new_file(dir_name, file_name)
            temp_list.append(new_log_file)
            for item in temp_list:
                if temp_list.count(item) >= 4:
                    print '按键精灵出现问题'
                    Logger_Error_file.error('按键精灵出现问题')
                    while_str = False
                    break
                else:
                    seeknum = seek_number(new_log_file,key_name_createmeeting)
            if seeknum == 44:
                print '按键精灵出现问题'
                Logger_Error_file.error('按键精灵出现问题')
                while_str = False
                break
            else:
                response_str = next_str(new_log_file, seeknum, key_name_createmeetingresponse)
                # 将iso-8859-1的编码转换为utf-8编码
                cutstr = cut_str(response_str).decode('iso-8859-1').encode('utf8')
                result = is_result(cutstr)
                if result == 444:
                    print '大网会议创建失败'
                    Logger_Error_file.error('大网会议创建失败')
                    while_str = False
                    break
                else:
                    if while_str == False:
                        pass
                    else:
                        print '大网会议创建成功'
                        Logger_Info_file.info('大网会议创建成功')
            time.sleep(5)
    except Exception,e:
        Logger_Error_file.exception(e)