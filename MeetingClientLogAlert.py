#!/usr/bin/env python
#_*_ coding:utf-8 _*_
'''
@auther: tanglei
@contact: tanglei_0315@163.com
@file: MeetingClientLogAlert.py
@time: 2019/3/13 16:36
'''
#!/usr/bin/env python
#_*_ coding:utf-8 _*_
'''
@auther: tanglei
@contact: tanglei_0315@163.com
@file: MeetingClientLogAlert.py
@time: 2019/2/22 11:20
'''
import os
import sys
import stat
import re
import ConfigParser
import json
import time
import shutil
import codecs
import win32api
import win32process
from playsound import playsound

file_path = os.path.join(os.path.abspath('conf'),'setting.ini')
#ajjl_warning_sound = os.path.join(os.path.abspath('mp3'),)
#meeting_warning_sound = os.path.join(os.path.abspath('mp3'),)

#去除BOM_UTF8编码的\xef\xbb\xbf的第一种方法,经测试可以使用，但是最好将配置文件和函数写在程序的最上面
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

DeleteBOM_UTF8(file_path)

from common.logger import logger

Logger_Info_file = logger("INFO")
Logger_Error_file = logger("ERROR")

#获取配置文件
conf = ConfigParser.ConfigParser()
conf.read(file_path)
#文件夹，文件名和关键字
dir_name = conf.get('FILE','dir')
file_name = conf.get('FILE','file')
key_name_createmeetingresponse = conf.get('KEY','CreateMeetingResponse')
#一些时间间隔的配置
os_compare_file_time = int(conf.get('TIME_NUMBER','OS_COMPARE_FILE_TIME'))
interval_time = int(conf.get('TIME_NUMBER','INTERVAL_TIME'))
#按键精灵的安装目录，进程名以及重启时间
anjianjingling_exe = conf.get('exe','anjianjingling')
anjianjingling = conf.get('exe','anjianjingling_exe')
restart_time = int(conf.get('exe','restart_time'))
#报警文本信息
ajjl_warning_text = conf.get('text','ajjl_warning_text')
ajjl_error_text = conf.get('text','ajjl_error_text')
meeting_warning_text = conf.get('text','meeting_warning_text')
ajjl_mp3 = os.path.join(os.path.abspath('mp3'),'ajjl.mp3')
ajjl_error_mp3 = os.path.join(os.path.abspath('mp3'),'ajjl_error.mp3')
meeting_mp3 = os.path.join(os.path.abspath('mp3'),'meeting.mp3')
network_ok_mp3 = os.path.join(os.path.abspath('mp3'),'network_ok.mp3')
network_no_mp3 = os.path.join(os.path.abspath('mp3'),'network_no.mp3')

#获取所有X1Box_x86文件中带有adminPhoneId关键字的文件名
def file_key_file(dir,file_name,key):
    file_list = []
    file_key_list = []
    #获取匹配到关键字的所有文件
    for root, dirs, files in os.walk(dir):
        for item in files:
            matchObj = re.match(file_name + '.*',item)
            if matchObj:
                file_list.append(root + '\\' + matchObj.group())
    #从文件中找到匹配有关键字的文件
    for item in file_list:
        with open(item,'r') as f:
            lines = f.readlines()
            for line in lines:
                result = re.search(key, line)
                if result:
                    file_key_list.append(item)
    if file_key_list:
        return file_key_list
    else:
        return 4

#获取包含关键字的最新时间戳和最新的文件名
def get_new_file_and_timestamp(file_list):
    time_list = []
    file_dict = {}
    if file_list.__str__().strip('(').strip(')').strip(',') != '4':
        # 匹配到关键字的最新文件创建的时间戳
        for item in file_list:
            file_createtime = int(os.path.getctime(item))
            time_list.append(file_createtime)
            file_dict_name = {file_createtime: item}
            file_dict.update(file_dict_name)
        max_filecreatetime = max(time_list)
        # 获取匹配关键字最新的文件名
        for k, v in file_dict.items():
            if k == max_filecreatetime:
                filename = v
        return (max_filecreatetime,filename)
    else:
        return '14'

#查看网络是否畅通
def ping_netCheck(ip):
    cmd = "ping " + str(ip) + " -n 5"
    exit_code = os.system(cmd)
    if exit_code:
        return False
    return True

#获取当前系统的时间戳
def get_os_time():
    t = int(time.time())
    return t

#提取关键字所在行的字符串
def next_str(file,key):

    with open(file,'r') as f:
        lines = f.readlines()
        for line in lines:
            result = re.search(key,line)
            if result:
                return line

#截取返回的字符串信息
def cut_str(str):

    str_1 = str.replace("$@$","")
    pos = str_1.find('{')
    str_2 = str_1[pos:]
    str_2_dict = eval(str_2)
    return str_2_dict

#将字符串通过json转为字典格式，并判断其中的结果
def is_result(cut_dict):

    result_rc = cut_dict["result"]["rc"]
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

def start_ajjl():
    anjianjingling_exe_path = unicode(anjianjingling_exe,"utf-8")
    win32api.ShellExecute(0, 'open', anjianjingling_exe_path, '','',1)

def stop_ajjl_jhy(ajjl):
    os.system('taskkill /F /IM X1Box_x86.exe')
    os.system('taskkill /F /IM X86AutoUpdateService.exe')
    os.system('taskkill /F /IM %s' % (ajjl.decode('utf-8').encode('GBK')))

def restart_ajjl():
    stop_ajjl_jhy(anjianjingling)
    time.sleep(2)
    start_ajjl()

#调用百度的接口，将文字转换成语音
def text2audio(text,mp3_name):
    from aip import AipSpeech
    """ 你的 APPID AK SK """
    APP_ID = '15801962'
    API_KEY = 'iIieqWm7P2baOgh0e2veDzAr'
    SECRET_KEY = '6bZoPhY4yR2EPQ5o5LHk1o8Pu7kdNmLZ'
    try:
        client = AipSpeech(APP_ID, API_KEY, SECRET_KEY)

        result = client.synthesis(text, 'zh', 1, {
            'vol': 5, 'per': 3
        })
    except Exception, e:
        Logger_Error_file.exception(e)
    # 识别正确返回语音二进制 错误则返回dict 参照下面错误码
    if not isinstance(result, dict):
        with open(mp3_name, 'wb') as f:
            f.write(result)

#检查报警文字是否变更，变更后重新生成mp3文件
def check_text():
    temp_file = os.path.join(os.path.abspath('temp'),'text.txt')
    if not os.path.exists(temp_file):
        with open(temp_file,'w') as f:
            f.writelines(ajjl_warning_text+'\n')
            f.writelines(meeting_warning_text+'\n')
            f.writelines(ajjl_error_text)
    else:
        if os.path.getsize(temp_file) == 0:
            with open(temp_file, 'w') as f:
                f.writelines(ajjl_warning_text + '\n')
                f.writelines(meeting_warning_text+'\n')
                f.writelines(ajjl_error_text)
        else:
            with open(temp_file, 'r') as ff:
                lines = ff.readlines()
                ajjl_line = lines[0]
                meeting_line = lines[-2]
                ajjl_error_line = lines[-1]
                if ajjl_line == ajjl_warning_text and meeting_line == meeting_warning_text and ajjl_error_line == ajjl_error_text:
                    pass
                elif ajjl_line != ajjl_warning_text or meeting_line != meeting_warning_text or ajjl_error_line != ajjl_error_text:
                    with open(temp_file, 'w') as f:
                        f.writelines(ajjl_warning_text+'\n')
                        f.writelines(meeting_warning_text + '\n')
                        f.writelines(ajjl_error_text)
                        return 123

#查看mp3目录下面是否有按键精灵报警和会议报警的mp3文件
def check_mp3(mp3_text,mp3_name):
    if not os.path.exists(mp3_name):
        text2audio(mp3_text,mp3_name)
    else:
        response = check_text()
        if response == 123:
            text2audio(mp3_text, mp3_name)

if __name__ == '__main__':
    try:
        start_time = int(time.time())
        try:
            remove_dir_file(dir_name)
        except Exception,e:
            Logger_Error_file.exception(e)
        while_str = True
        check_mp3(ajjl_warning_text, ajjl_mp3)
        check_mp3(meeting_warning_text, meeting_mp3)
        check_mp3(ajjl_error_text,ajjl_error_mp3)
        count_number = 0
        while while_str:
            stop_time = int(time.time())
            #判断网络是否畅通
            ping_result = ping_netCheck('www.baidu.com')
            if ping_result == True:
                #判断日志文件是否包含关键字
                if get_new_file_and_timestamp(file_key_file(dir_name,file_name,key_name_createmeetingresponse)) != '14':
                    #包含关键字的最新文件名
                    new_log_file = get_new_file_and_timestamp(file_key_file(dir_name,file_name,key_name_createmeetingresponse))[1]
                    print '新的文件绝对路径:%s'.decode('utf-8').encode('GBK') % (new_log_file)
                    Logger_Info_file.info('新的文件绝对路径:%s' % (new_log_file))
                    try:
                        #判断日志多长时间没有产生日志文件
                        if get_os_time() - get_new_file_and_timestamp(file_key_file(dir_name,file_name,key_name_createmeetingresponse))[0] > os_compare_file_time:
                            print '没有新的日志文件创建，所以按键精灵出现问题,重复的文件名为%s'.decode('utf-8').encode('GBK') % (new_log_file)
                            Logger_Error_file.error('没有新的日志文件创建，所以按键精灵出现问题,重复的文件名为%s' % (new_log_file))
                            count_number += 1
                            print count_number
                            if count_number == 4:
                                stop_ajjl_jhy(anjianjingling)
                                print '按键精灵连续重启三次，指针失效无法正常进行会议终端的操作'.decode('utf-8').encode('GBK')
                                Logger_Error_file.error('按键精灵连续重启三次，指针失效无法正常进行会议终端的操作')
                                while True:
                                    playsound(ajjl_error_mp3)
                                    time.sleep(1200)
                            else:
                                playsound(ajjl_mp3)
                                restart_ajjl()
                                time.sleep(20)
                                print '按键精灵和极会议客户端进行了重启操作,重新启动的时间:%s'.decode('utf-8').encode('GBK') % (
                                    time.strftime("%Y-%m-%d %H:%M:%S"))
                                Logger_Info_file.info(
                                    '按键精灵和极会议客户端进行了重启操作,重新启动的时间:%s' % (time.strftime("%Y-%m-%d %H:%M:%S")))
                        else:
                            key_line = next_str(new_log_file, key_name_createmeetingresponse)
                            cut_str_dict = cut_str(key_line)
                            key_result = is_result(cut_str_dict)
                            if key_result == 444:
                                print '根据返回值不等于0，所以大网会议创建失败,对应的客户端日志为%s'.decode('utf-8').encode('GBK') % (new_log_file)
                                Logger_Error_file.error('根据返回值不等于0，所以大网会议创建失败,对应的客户端日志为%s' % (new_log_file))
                                for i in range(3):
                                    playsound(meeting_mp3)
                                    time.sleep(5)
                                #while_str = False
                                #break
                            else:
                                if while_str == False:
                                    pass
                                else:
                                    print '大网会议创建成功'.decode('utf-8').encode('GBK')
                                    Logger_Info_file.info('大网会议创建成功')
                                    time.sleep(interval_time)
                    except Exception,e:
                        Logger_Error_file.exception(e)
                    try:
                        if stop_time - start_time > restart_time:
                            remove_dir_file(dir_name)
                            start_time = int(time.time())
                            print '一个小时后自动清理LOG文件夹下面的所有文件,清理的时间:%s'.decode('utf-8').encode('GBK') % (time.strftime("%Y-%m-%d %H:%M:%S"))
                            Logger_Info_file.info('一个小时后自动清理LOG文件夹下面的所有文件,清理的时间:%s' % (time.strftime("%Y-%m-%d %H:%M:%S")))
                    except Exception,e:
                        Logger_Error_file.exception(e)
                else:
                    print '日志目录下面没有日志文件,请查看按键精灵是否正常运行脚本'.decode('utf-8').encode('GBK')
                    Logger_Error_file.error('日志目录下面没有日志文件,请查看按键精灵是否正常运行脚本')
                    time.sleep(5)
            else:
                print '客户端网络不通，请检查网络'.decode('utf-8').encode('GBK')
                Logger_Error_file.error('客户端网络不通，请检查网络'.decode('utf-8').encode('GBK'))
                playsound(network_no_mp3)
                time.sleep(5)
                ping_result = ping_netCheck('www.baidu.com')
                if ping_result == True:
                    playsound(network_ok_mp3)
                    continue
    except Exception,e:
        Logger_Error_file.exception(e)