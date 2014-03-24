#!/bin/bash

if [ -z "$3" ] 
then
        exit
fi

WORK_DIR_PROJECT=$(cd  "$(dirname "$0")/"; pwd)
cd $WORK_DIR_PROJECT
msg=$1
rtx=$2
mobile=$3

msg=$(echo "$msg" | sed 's/\+/ /g')

if [ "${mobile}" != "no" ]
then
        php ./send_sms_post.php "${mobile}" "$msg"
fi

if [ "${rtx}" != "no" ]
then
        #encode_str=$(${WORK_DIR_PROJECT}/Encode "$(date '+%Y-%m-%d %H:%M:%S') ${msg}")
        encode_str=$(${WORK_DIR_PROJECT}/Encode "${msg}")
        /usr/bin/curl --max-time 5 "http://hosts.oa.com/rtx?receiver=${rtx}&msg=${encode_str}&title=Alarm" >/dev/null 2>&1
fi
echo "$1 $2 $3" >> /tmp/xxhhhhhh

exit
