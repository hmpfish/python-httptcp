#!/bin/bash


source ../kcgi-bin/publish/config/config.sh

while [ 1 ]
do

	cfile=$(ls -t daemon_tok/ | tail -n 1)

	if [ -z "${cfile}" ]
	then
		sleep 1
		continue
	fi

	${mysql_bin} -umonitor -p${mysql_root_pass} -h ${mysql_host} -e "select f_exec from mashbd_plat.t_pltask where f_md5='"${cfile}"' and f_exec='4';" | sed '1d' > packexec
	if [ ! -s packexec ]
	then
		mv daemon_tok/${cfile} daemon_fail/${cfile}
		sleep 1
		continue
	fi

	pname=$(cat daemon_tok/${cfile} | head -n 1 | awk '{print $1}')

	while [ 1 ]
	do	
		${mysql_bin} -umonitor -p${mysql_root_pass} -h ${mysql_host} -e "select interip from mashbd_plat.t_monitor where packagedown='1' and packagename='"${pname}"';" | sed '1d' > packexec

		if [ -s packexec ]
		then
			sleep 1
			continue
		else
			break
		fi
	done

	if [ -e packexec ]
	then
		rm -f packexec
	fi

	rm -f daemon_tok/${cfile}

	${mysql_bin} -umonitor -p${mysql_root_pass} -h ${mysql_host} -e "update mashbd_plat.t_pltask set f_exec='3' where f_md5='"${cfile}"';"

	sleep 1
	continue
done
