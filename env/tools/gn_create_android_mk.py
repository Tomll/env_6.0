#!/usr/bin/python
#-*- coding: utf-8 -*-
import re
import os
import sys
import zipfile
import commands
import subprocess

class OPtions(object):  pass
Options = OPtions()

def Run(args, **kwargs):
    """Create and return a subprocess.Popen object, printing the command
  line on the terminal if -v was specified."""
    #print "running: " ,args
    return subprocess.Popen(args, **kwargs)

def single_line(lines):
    l=[]
    special_line=''
    is_special_line=False
    for line in lines:
        line=line.strip()
        if line.startswith('#'): continue
        line=line.replace(":=","=")
        if line.endswith('\\'):
            special_line+="%s ^_^"%line.rstrip('\\').strip()
            is_special_line=True
        else:
            if is_special_line:
                special_line+="%s ^_^"%line.strip()
                l.append(special_line)
                special_line=''
                is_special_line=False
            else:
                l.append(line)
    return l

def extract_data_from_mk(mk,s_type, data):
    b_index=0
    e_index=0
    patterns={
            'apk' : 'include $(BUILD_PACKAGE)' ,
            'sjar' : 'include $(BUILD_STATIC_JAVA_LIBRARY)' ,
            'prebuilt': 'include $(BUILD_PREBUILT)', 
            'mulit_prebuilt': 'include $(BUILD_MULTI_PREBUILT)',
            } 

    end_pattern = patterns.get(s_type, '')

    if not end_pattern: 
        return data

    begin_pattern=re.escape('include $(CLEAR_VARS)')
    end_pattern=re.escape(end_pattern)

    with open(mk,'r') as f :  lines = f.readlines()
    lines = single_line(lines)
    for i in range(len(lines)):
        str=lines[i].strip()
        if not str or str.startswith('#'): continue
        #find begin
        b_match=re.match(begin_pattern,str)
        if b_match:
            b_index = i
            continue

        #find end
        e_match=re.match(end_pattern,str)
        if e_match: 
            e_index = i
        if b_index < e_index:
            #print b_index, e_index+1
            d={}

            for l in lines[b_index:e_index + 1]:
                if not l: continue
                key   = re.split('[+=]',l)[0].strip()
                value = re.split('[+=]',l)[1:]
                if l.find('+=') != -1:
                    if d.get(key,''): 
                        d[key].extend(value)
                    else:
                        d[key]=value
                else:
                    d[key]=value
            if d:
                d['type']=s_type
                data.append(d)
            b_index = e_index
    return data

def write_copy_files(mk, data ,mode='a'):
    if not data.get('PRODUCT_COPY_FILES',''): return 
    fd = open(mk, mode)

    for l in data['PRODUCT_COPY_FILES']:
        if not l.strip(): continue
        splList = l.split('^_^')
        for sl in splList:
            sl=sl.strip()
            if not sl: continue
            if sl.startswith('$(foreach'):
                fd.write('PRODUCT_COPY_FILES += %s\n'%(sl))
            else:
                if sl.find(':') == -1 : continue
                file_path=sl.split(':')[-1]
                if not os.path.exists(os.path.join(Options.apkOutDir,file_path)) : continue
                fd.write('PRODUCT_COPY_FILES += $(LOCAL_PATH)/%s:%s \n'%(file_path, file_path))

    fd.close()


def create_apk_android(mk,data, apkfile,  mode='a'):

    #特殊apk copy system/etc
    if data.get('LOCAL_PACKAGE_NAME', data['LOCAL_MODULE'])[0].strip() in [ 'com.gionee.simcontacts.SimContacts', 'com.gionee.saletimesender.SaleTimeSender', 'com.android.settingsplugin.SettingsPlugin', 'com.gionee.applockplugin.AppLockPlugin']:
        apkname=data['LOCAL_PACKAGE_NAME'][0].strip() + ".apk"
        if os.path.exists(os.path.join(Options.apkOutDir,apkname)):
            str = 'PRODUCT_COPY_FILES += $(LOCAL_PATH)/%s:system/etc/Amigo_SystemServices/%s \n'%(apkname, apkname)
            fd = open(mk, mode)
            fd.write(str)
            fd.close()
            return

    lines=[ "include $(CLEAR_VARS)\n",
            "LOCAL_MODULE_TAGS := optional\n",
            "LOCAL_MODULE_CLASS := APPS\n",
            "LOCAL_MODULE_SUFFIX := $(COMMON_ANDROID_PACKAGE_SUFFIX)\n",
            "include $(BUILD_PREBUILT)\n",
            ]

    str="LOCAL_CERTIFICATE := PRESIGNED\n"
    lines.insert(-1, str)
    str="LOCAL_MODULE := %s\n"%data['LOCAL_MODULE'][0].strip()
    lines.insert(-1, str)
    str="LOCAL_SRC_FILES := $(LOCAL_MODULE).apk\n"
    lines.insert(-1, str)

    #apk jni
    is32Abi=False
    is64Abi=False
    Abi32List=['armeabi-v7a', 'armeabi']
    Abi64List=['arm64-v8a']
    cmd='zipinfo -1 %s | grep -w ^lib'%apkfile
    p = Run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    outdata,errdata = p.communicate()
    for libso in outdata.split('\n'):
        if not libso: continue
        AbiType = libso.split('/')[1]
        if not is64Abi and AbiType in Abi32List: 
            is32Abi = True
            str="LOCAL_PREBUILT_JNI_LIBS += @%s\n"%libso
            lines.insert(-1, str)

        if not is32Abi and AbiType in Abi64List: 
            is64Abi=True
            str="LOCAL_PREBUILT_JNI_LIBS += @%s\n"%libso
            lines.insert(-1, str)

    cmd='zipinfo -1 %s | grep -w ^assets/.*.so$ | sort -r'%apkfile
    p = Run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    outdata,errdata = p.communicate()
    for libso in outdata.split('\n'):
        if not libso: continue
        AbiType = libso.split('/')[-2]
        if not is64Abi and AbiType in Abi32List: 
            is32Abi = True
            str="LOCAL_PREBUILT_JNI_LIBS += @%s\n"%libso
            lines.insert(-1, str)

        if not is32Abi and AbiType in Abi64List: 
            is64Abi=True
            str="LOCAL_PREBUILT_JNI_LIBS += @%s\n"%libso
            lines.insert(-1, str)

    if data.get('DONT_DEXPREOPT_PREBUILTS', ''):
        str="DONT_DEXPREOPT_PREBUILTS := %s \n"%data.get('DONT_DEXPREOPT_PREBUILTS')[0].strip()
        lines.insert(-1, str)
    else:
        if not is64Abi and not is32Abi :
            str="LOCAL_MULTILIB := both\n"
            lines.insert(-1, str)
        elif is32Abi:
            str="LOCAL_MULTILIB := 32\n"
            lines.insert(-1, str)
        elif is64Abi:
            str="LOCAL_MULTILIB := 64\n"
            lines.insert(-1, str)

    #OVERRIDES_PACKAGES
    if data.get('LOCAL_OVERRIDES_PACKAGES',''):
        str="LOCAL_OVERRIDES_PACKAGES := %s\n"%data['LOCAL_OVERRIDES_PACKAGES'][0].strip()
        lines.insert(-1, str)

    #Is PRIVILEGED apk
    if data.get('LOCAL_PRIVILEGED_MODULE',''):
        str="LOCAL_PRIVILEGED_MODULE := %s\n"%data['LOCAL_PRIVILEGED_MODULE'][0].strip()
        lines.insert(-1, str)

    #Copy files to system
    if data.get('PRODUCT_COPY_FILES',''):
        for l in data['PRODUCT_COPY_FILES']:
            if not l.strip(): continue
            splList = l.split('^_^')
            for sl in splList:
                sl=sl.strip()
                if not sl: continue
                if sl.startswith('$(foreach'):
                    lines.insert(-1, 'PRODUCT_COPY_FILES += %s\n'%(sl))
                else:
                    if sl.find(':') == -1 : continue
                    file_path=sl.split(':')[-1]
                    if not os.path.exists(os.path.join(Options.apkOutDir,file_path)) : continue
                    #print os.path.join(Options.apkOutDir,file_path)
                    lines.insert(-1, 'PRODUCT_COPY_FILES += $(LOCAL_PATH)/%s:%s \n'%(file_path, file_path))

    str="ifeq ($(GN_APK_%s_SUPPORT),yes)\n"%data['LOCAL_MODULE'][0].strip().upper()
    lines.insert(0, str)
    str="endif\n"
    lines.append(str)

    if not os.path.exists(mk): 
        lines.insert(0, "LOCAL_PATH := $(call my-dir)\n")

    fd = open(mk, mode)
    fd.writelines(lines)
    fd.close()

def get_path_file(fileName):
    for root, dirs, files in os.walk(Options.apkOutDir):
        if fileName in files:
            return os.path.join(root, fileName)
    return None

def main(argv):
    Options.codeDir=argv[1]
    Options.apkOutDir=argv[2]
    android_files=[]
    for root, dirs, files, in os.walk(Options.codeDir):
        if 'Android.mk' in files:
            android_files.append(os.path.join(root, "Android.mk"))
    data=[]
    for mk in android_files:
        data=extract_data_from_mk(mk,'apk',data)
        data=extract_data_from_mk(mk,'prebuilt',data)
        data=extract_data_from_mk(mk,'mulit_prebuilt',data)

    AndroidPathFile=os.path.join(Options.apkOutDir, 'Android.mk')
    for d in data:
        if d.get('type', '') == 'apk':
            apkName = get_path_file(d['LOCAL_PACKAGE_NAME'][0].strip() + '.apk')
            if apkName:
                d['LOCAL_MODULE'] = d['LOCAL_PACKAGE_NAME']
                create_apk_android(AndroidPathFile, d , apkName)

        if d.get('type', '') == 'prebuilt':
            apkName = get_path_file(d['LOCAL_MODULE'][0].strip() + '.apk')
            if apkName:
                create_apk_android(AndroidPathFile, d , apkName)

        if d.get('type', '') == 'mulit_prebuilt':
            write_copy_files(AndroidPathFile, d)
    
if __name__ == '__main__':
    main(sys.argv)
