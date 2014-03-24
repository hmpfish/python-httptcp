#!/bin/bash

if [ -z "$1" ]
then
	echo "$0 ipfile-list"
	echo "ipfile-list contains: ip business1 business2"
	exit
fi

iplist=$1

while read ip bus1 bus2
do
	if [ -z "${bus2}" ]
	then
		continue
	fi
	curl -o nz2 "http://127.0.0.1:50000/kcgi-bin/publish/users/no_cookie_add_machine_yewu.php?g_user=${ip}&g_token=%2cddx26fced3%2cfejgdfg83%2c&g_yewu=richmail139&g_person=huangmp&ac=radd&bus1=${bus1}&bus2=${bus2}&OK=Submit"
done < $iplist
