#!/usr/bin/env python
#_*_ coding:utf-8 _*_
'''
@auther: tanglei
@contact: tanglei_0315@163.com
@file: logger.py
@time: 2019/2/27 17:34
'''
import os
import logging
import logging.config
import logging.handlers
import ConfigParser

#定义setting配置文件路径
setting_file = os.path.join(os.path.abspath('conf'),'setting.ini')
conf = ConfigParser.ConfigParser()
conf.read(setting_file)
#定义正常日志的文件路径
InfoFile = conf.get("logger","INFO_FILE")
#定义错误日志的文件路径
ErrorFile = conf.get("logger","ERROR_FILE")
#单个日志文件的大小
FileSize = int(conf.get("logger","FILE_SIZE"))
#轮训保留的日志文件个数
RotationNumber = int(conf.get("logger","ROTATION_NUMBER"))
def logger(level):

    if not os.path.isfile(InfoFile):
        open(InfoFile, "w+").close()
    if not os.path.isfile(ErrorFile):
        open(ErrorFile, "w+").close()

    #定义字典内容
    log_setting_dict = {"version":1,
                        "incremental":False,
                        "disable_existing_loggers":True,
                        "formatters":{"precise":
                                          {"format":"%(asctime)s %(filename)s(%(lineno)d - %(processName)s - %(threadName)s - %(funcName)s): %(levelname)s %(message)s",
                                           "datefmt":"%Y-%m-%d %H:%M:%S"}},
                        "handlers":{"handlers_RotatingFile_INFO":
                                        {"level": "INFO",
                                         "formatter": "precise",
                                         "class": "logging.handlers.RotatingFileHandler",
                                         "filename": InfoFile,
                                         "mode": "a",
                                         "maxBytes": FileSize*1024*1024,
                                         "backupCount": RotationNumber
                                         },
                                    "handlers_RotatingFile_ERROR":
                                        {"level": "ERROR",
                                         "formatter": "precise",
                                         "class": "logging.handlers.RotatingFileHandler",
                                         "filename": ErrorFile,
                                         "mode": "a",
                                         "maxBytes": FileSize * 1024 * 1024,
                                         "backupCount": RotationNumber
                                         }},
                        "loggers":{"logger_INFO":
                                       {"level":"INFO",
                                        "handlers":["handlers_RotatingFile_INFO"],},
                                   "logger_ERROR":
                                       {"level":"ERROR",
                                        "handlers": ["handlers_RotatingFile_ERROR"],}}}
    logging.config.dictConfig(log_setting_dict)

    if level == "INFO":
        logger = logging.getLogger("logger_INFO")
    elif level == "ERROR":
        logger = logging.getLogger("logger_ERROR")
    return logger