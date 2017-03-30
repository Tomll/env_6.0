#!/bin/bash
usage(){
printf "\
Parse Android.mk tools

Usage:$0 model Android.mk
example:
    $0 LOCAL_MODULE pathdir/Android.mk
"
}
del_char(){
   local str="$1"
   local char="$2"
   [ -z "$str" ] && return
   echo ${str//"$2"/}
}

get_local_prefix_value(){
    local model="$2"
    str=$(cat $1 | awk '{if($0 ~ /#/ || $0 ~ /include/) {print "\n"} else if($0 ~ /LOCAL_/) {print "\n"$0} else {print $0}}' | sed -n "/[ \t]*$model\>/,/^[ \t]*$/p")
    #del 
    str=$(del_char "$str" 'ifeq')
    str=$(del_char "$str" 'ifneq')
    str=$(del_char "$str" 'else')
    str=$(del_char "$str" 'endif')
    str=$(del_char "$str" '\')
    str=$(del_char "$str" '+')
    str=$(del_char "$str" '=')
    str=$(del_char "$str" ':')
    str=$(del_char "$str" "$model")
    echo $str
}
     
del_prefix(){
    local str="$1"
    tmp=$(echo `for s in $str; do echo $s ; done | awk -F ':' '{print $2}' |sort -u`)
    echo ${tmp//' '/$FS}
}

get_prebuilt_static_jars(){
    local model="$2"
    str=$(cat $1 | awk '{if($0 ~ /#/ || $0 ~ /include/) {print "\n"} else if($0 ~ /LOCAL_/) {print "\n"$0} else {print $0}}' | sed -n "/[ \t]*$model/,/^[ \t]*$/p")
    str=$(del_char "$str" '\')
    str=$(echo $str |cut -d '=' -f2)
    del_prefix "$str" 
}

get_product_copy_files(){
    local model="$2"
    str=$(cat $1 | awk '$0 !~ /#/ && $0 !~ /include/ {print $0}' | sed -n "/^$model/,/^ *$/p")
    str=$(del_char "$str" '\')
    str=$(del_char "$str" '+')
    str=$(del_char "$str" '=')
    str=$(del_char "$str" "$model")
    str=$(del_char "$str" "\$(LOCAL_PATH)")
    echo $str
}

main(){

    if [ "$#" -ne 2 ] ;then
        echo "arguments error!" &>2
        usage 
        exit 1
    fi

    if [ "${1:0 -3}" == ".mk" ];then
        local model=$2
        local mkfile=$1
    elif [ "${2:0 -3}" == ".mk" ];then
        local model=$1
        local mkfile=$2
    else
        echo "arguments error!" &>2
        usage
        exit 1
    fi

    if [ "${model:0:5}" == "LOCAL" ];then
        if [ "$model" == "LOCAL_PREBUILT_STATIC_JAVA_LIBRARIES" ];then
            get_prebuilt_static_jars "$mkfile" "$model" 
        else
            get_local_prefix_value "$mkfile" "$model"
        fi
    elif [ "${model}" == "PRODUCT_COPY_FILES" ];then
        get_product_copy_files "$mkfile" "$model"
    fi
}
    
FS=" "
main "$@"
