#!/bin/bash
create_project_config(){ 
    local gn_pkg_name="$1"
    local gn_libs="$2"
    local gn_app_classes_dir="$3"
    [ -z "$gn_pkg_name" ] && return
    for lib in $gn_libs
    do
        local gn_libs_list_abs+="$GN_BUILD_ROOT_ENV_DIR/$lib,"
    done
    rm -rf $gn_pkg_name
    mkdir -p $gn_pkg_name
    cp -r sonar-ant-task-2.2.jar $gn_pkg_name

cat >$gn_pkg_name/project.properties<<EOF 
#### project config
sonar.profile.java=gionee java+android
sonar.projectKey=gionee.app:$gn_pkg_name
sonar.projectName=$gn_pkg_name
sonar.projectVersion=$GN_APK_VERSION_NAME
sonar.sources=$TRANSAGE_BUILD_CODE_DIR/src
`if echo  "$skipPackageDesignList" | grep -qw "$gn_pkg_name" ;then
    echo "sonar.skipPackageDesign=true"
fi`
sonar.binaries=$GN_BUILD_ROOT_ENV_DIR/$gn_app_classes_dir/classes
sonar.libraries=$gn_libs_list_abs
EOF

cat >$gn_pkg_name/build.xml<<EOF
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns:sonar="antlib:org.sonar.ant" basedir="$TRANSAGE_BUILD_CODE_DIR/../../">
<property file="$PWD/$gn_pkg_name/sonar.properties" />
<property file="$PWD/$gn_pkg_name/project.properties" />
 
<!-- other sonar propeties --> 
<property name="sonar.sourceEncoding" value="UTF-8" />
<property name="sonar.language" value="java" />
 
<target name="sonar">
<taskdef uri="antlib:org.sonar.ant" resource="org/sonar/ant/antlib.xml">
<classpath path="\${my.sonar.jars}" />
</taskdef>
<sonar:sonar/> 
</target> 
</project> 
EOF
 
cat >$gn_pkg_name/sonar.properties<<EOF
#### sonar config 
sonar.host.url=http://19.9.0.104:9000/sonar/
sonar.jdbc.url=jdbc:mysql://19.9.0.104:3306/sonar2?useUnicode=true&characterEncoding=utf8&rewriteBatchedStatements=true
sonar.jdbc.driverClassName=com.mysql.jdbc.Driver
sonar.jdbc.username=sonar
sonar.jdbc.password=sonardb
my.sonar.jars=$PWD/$gn_pkg_name/sonar-ant-task-2.2.jar
EOF

}

skipPackageDesignList="Amigo_SystemUI Amigo_SetupWizard"

create_project_config "$@"

