#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: lishijie
# @Date:   2015-08-17 15:37:54
# @Last Modified by:   lishijie
# @Last Modified time: 2015-08-19 10:27:25

import pycurl
import StringIO
import platform
import inspect
import time
import urllib, urllib2, os, sys, json, httplib, traceback
from optparse import OptionParser

ip = None
user_name = None
password = None
iosinfos = {}
tactics_id = ''
platform_name = platform.system()
if platform_name.lower() == 'windows':
    platform_encoding = 'gbk'
else:
    platform_encoding = 'utf-8'

c = pycurl.Curl()
def output_log(log_str):
    print log_str

def send_post(ip, api, params):
    try:
        # 创建一个同libcurl中的CURL处理器相对应的Curl对象
        c = pycurl.Curl()
        string_io = StringIO.StringIO()
        c.setopt(pycurl.WRITEFUNCTION, string_io.write)
        c.setopt(pycurl.FOLLOWLOCATION, 1)
        c.setopt(pycurl.MAXREDIRS, 5)
        c.setopt(pycurl.CONNECTTIMEOUT, 60)
        c.setopt(pycurl.TIMEOUT, 300)
        c.setopt(c.POST, 1)
        # 设置要访问的网址
        c.setopt(c.URL, 'http://%s:8000/%s' % (ip, api))
        # 设置post请求，上传文件的字段名，上传的文件
        c.setopt(c.HTTPPOST, params)
        # 执行上述访问网址的操作
        c.perform()
        # Curl对象无操作时，也会自动执行close操作
        c.close()
        # 读取IO返回值
        return string_io.getvalue()
    except Exception, e:
        traceback.print_exc()

def upload_file(upload_file_path):
    global iosinfos
    if not os.path.exists(upload_file_path):
        output_log('Upload file not exists : ' + upload_file_path)
        return False
    upload_file_path = os.path.abspath(upload_file_path)
    upload_dir = os.path.split(upload_file_path)[0]

    print "upload_dir---------------",upload_dir
    filename=os.path.basename(upload_file_path)
    filename=filename.decode(platform_encoding)
    print filename
    params = [
        ('apk', (pycurl.FORM_FILE, os.path.join(upload_dir, filename.encode(platform_encoding)), pycurl.FORM_FILENAME,filename.encode('utf-8'))),
        ('username', (pycurl.FORM_CONTENTS, user_name)),
        ('password', (pycurl.FORM_CONTENTS, password)),
        ('tactics_id',((pycurl.FORM_CONTENTS, tactics_id))),
    ]
    upload_file_api = 'batch_apk_reinforce'
    output_log('Start to upload file.')
    print "params--------------------",params
    response = send_post(ip, upload_file_api, params)
    result = json.loads(response)
    state = result['state']
    msg = result['msg']
    print "result=================",result
    iosinfo = result['apkinfo']
    
    zip_id = iosinfo['apk_id']
    if state == 6:
        iosinfos[zip_id] = {'apk_name': filename, 'apk_state': 0, 'down_num': 0, 'ios_msg': ''}
        output_log('File upload success!')
        return True
    else:
        output_log('File upload failed!')
        return False

def find_state(iosinfos):
    #global iosinfos

    #iosinfos_str = json.dumps(iosinfos)
    apkinfos = iosinfos
    apkinfos = json.dumps(apkinfos)
    print "apkinfos-----------",type(apkinfos)
    params = [
        ('username', (pycurl.FORM_CONTENTS, user_name)),
        ('password', (pycurl.FORM_CONTENTS, password)),
        ('apkinfos', apkinfos)
    ]
    find_state_api = 'batch_find_apkinfos'
    output_log('Start to protect file.')
    output_log('Protecting......')
    output_log('Waiting for protect result.')

    total_num=len(iosinfos.keys())
    down_list=[]

    while True:
        response = send_post(ip, find_state_api, params)
        result = json.loads(response)
        iosinfos = result['apkinfos']
        state = result['state']
        print "state----------",state
        for k, v in iosinfos.items():
            filename = v['apk_name'][0:-4]
            filename = filename.encode('gbk')
            if v['apk_state'] == 10:
                if not k in down_list:
                    down_res=download_file(download_dir_path,k,filename)
                    output_log('File protect success!')
                    if not down_res:
                        return False
                    down_list.append(k)
            elif v['apk_state']==9:
                return False
            else:
                output_log('search go on ') 
        if len(down_list)==total_num:
            return True
        time.sleep(5)
    return False

def download_file(download_dir_path,iosinfo_id,filename):
    download_dir_path = os.path.abspath(download_dir_path)
    if not os.path.exists(download_dir_path):
        output_log('Download folder not exists : ' + download_dir_path)
        return False
    apkinfo_id = iosinfo_id
    params = [
        ('username', (pycurl.FORM_CONTENTS, user_name)),
        ('password', (pycurl.FORM_CONTENTS, password)),
        ('apkinfo_id', (pycurl.FORM_CONTENTS, str(apkinfo_id)))
    ]
    download_file_api = 'batch_apk_download'
    output_log('Start to download file.')
    response = send_post(ip, download_file_api, params)
    download_file = open(os.path.join(download_dir_path, filename + '_sec.apk'), 'wb')
    download_file.write(response)
    download_file.close()
    output_log('File download success!')
    return True

def parse_command():
    usage = r'usage: %prog [options] arg1 arg2'
    parser = OptionParser(usage=None)
    parser.add_option('-i', '--ip', action='store', dest='ip', help='protect server ip address')
    parser.add_option('-u', '--username', action='store', dest='user_name', help='user name')
    parser.add_option('-p', '--password', action='store', dest='password', help='password')
    parser.add_option('-f', '--upload', action='store', dest='upload_file_path', help='upload file path')
    parser.add_option('-t', '--tactics_id', action='store', dest='tactics_id', help='shiled version id')
    parser.add_option('-d', '--download', action='store', dest='download_dir_path', help='download directory path')
    return parser.parse_args()

if __name__ == '__main__':
    # ip user_name password is global variables
    options, args = parse_command()
    ip = options.ip
    user_name = options.user_name
    password = options.password
    upload_file_path = options.upload_file_path
    download_dir_path = options.download_dir_path
    tactics_id = options.tactics_id
    is_file_upload_success = False
    is_find_state_success = False
    is_file_download_success = False

    if ip and user_name and password and upload_file_path and download_dir_path:
        upfile = os.listdir(upload_file_path)

        upload_rets=[]
        findstate_rets = []

        for apk_up in upfile:
            upload_dir = os.path.join(upload_file_path,apk_up)
            upload_rets.append(upload_file(upload_dir))
            print "upload_rets==========",upload_rets

        is_file_download_success=find_state(iosinfos)

                #findstate_rets.append(is_find_state_success)
        # if is_file_upload_success:
        #     is_find_state_success = find_state()
        
        #    else:
        #        sys.exit(-1)

        #for is_find_state_success,iosinfos in upload_rets:

        #    if is_find_state_success:
        #        is_file_download_success = download_file(download_dir_path,iosinfos)
        #    else:
        #        sys.exit(-2)

        if is_file_download_success:
            sys.exit(0)
        else:
            sys.exit(-3)
    else:
        print 'Please input -h or --help to read commond help.'
        if not ip:
            output_log('Please input ip address.')
        if not user_name:
            output_log('Please input user name.')
        if not password:
            output_log('Please inpt password.')
        if not upload_file_path:
            output_log('Please input upload file path.')
        if not download_dir_path:
            output_log('Please input download directory path.')
        
