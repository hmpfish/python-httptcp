#!/bin/bash


source ../kcgi-bin/publish/config/config.sh

while [ 1 ]
do

	${mysql_bin} -umonitor -p${mysql_root_pass} -h ${mysql_host} -e "select interip,timetok from mashbd_plat.t_timer;" | sed '1d' > timert
	if [ ! -s timert ]
	then
		sleep 5
		continue
	fi

	while read TP TMK
	do
		if [ -z "${TP}" ] || [ -z "${TMK}" ]
		then
			continue
		fi

		if [ "${TMK}" == "-1" ]
		then
			continue
		fi

		time_now=$(date '+%s' -d '10 seconds ago')

		if [ "${time_now}" -ge "${TMK}" ]
		then
			${mysql_bin} -umonitor -p${mysql_root_pass} -h ${mysql_host} -e "delete from mashbd_plat.t_timer where interip='"${TP}"';"
			${mysql_bin} -umonitor -p${mysql_root_pass} -h ${mysql_host} -e "update mashbd_plat.t_monitor set oncheck='1' where interip='"${TP}"';"
		fi
	done < timert

	if [ -e timert ]
	then
		rm -f timert
	fi

	sleep 5
	continue
done
