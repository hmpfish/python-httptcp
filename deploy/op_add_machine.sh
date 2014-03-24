#!/bin/bash

if [ -z "$1" ]
then
	echo "$0 ipfile-list"
	echo "ipfile-list contains: ip"
	exit
fi

iplist=$1

while read ip
do
	if [ -z "${ip}" ]
	then
		continue
	fi
	curl -o nz "http://127.0.0.1:50000/kcgi-bin/publish/users/no_cookie_add_machine.php?g_user=${ip}&g_token=%2cddx26fced3%2cfejgdfg83%2c&g_yewu=richmail139&g_person=huangmp&ac=radd&OK=Submit"
done < $iplist
