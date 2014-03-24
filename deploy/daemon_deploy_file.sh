#!/bin/bash


source ../kcgi-bin/publish/config/config.sh

while [ 1 ]
do

	cfile=$(ls -t ../kcgi-bin/publish/serverinit/rtask/ | tail -n 1)

	if [ -z "${cfile}" ]
	then
		sleep 1
		continue
	fi

	mv ../kcgi-bin/publish/serverinit/rtask/${cfile} ../kcgi-bin/publish/serverinit/rdone/rtask/
	if [ -e ../kcgi-bin/publish/serverinit/rsh/${cfile} ]
	then
		mv ../kcgi-bin/publish/serverinit/rsh/${cfile} ../kcgi-bin/publish/serverinit/rdone/rsh/
		mkdir package
		install ../kcgi-bin/publish/serverinit/rdone/rsh/${cfile} package/op.sh
		chmod +x package/*.sh
		perl -i -pe 's!!!g' package/*.sh
		tar -zcvf ${cfile}.tar.gz package
		rm -r -f package
		install ${cfile}.tar.gz ${package_dst_dir}
		rm -f ${cfile}.tar.gz
	fi
	perl -i -pe 's!!!g' ../kcgi-bin/publish/serverinit/rdone/rtask/${cfile}
	tar_result=$(head -n 1 ../kcgi-bin/publish/serverinit/rdone/rtask/${cfile})
	while [ 1 ]
	do	
		${mysql_bin} -umonitor -p${mysql_root_pass} -h ${mysql_host} -e "select interip from mashbd_plat.t_monitor where packagedown='1';" | sed '1d' > packon

		if [ -s packon ]
		then
			sleep 1
			continue
		else
			break
		fi
	done

	if [ -e packon ]
	then
		rm -f packon
	fi

	${mysql_bin} -umonitor -p${mysql_root_pass} -h ${mysql_host} -e "update mashbd_plat.t_pltask set f_exec='4' where f_md5='"${cfile}"';"

	for i in `cat ../kcgi-bin/publish/serverinit/rdone/rtask/${cfile} | sed '1d' | sed '/^$/d'`
	do
		if [ -z "$i" ]
		then
			continue
		fi


		if [ ! -z "`echo ${tar_result} | grep '^rsh/'`" ]
		then	
			${mysql_bin} -umonitor -p${mysql_root_pass} -h ${mysql_host} -e "update mashbd_plat.t_monitor set packagedown='1',packagename='"${cfile}".tar.gz' where interip='"$i"';"
		else
			${mysql_bin} -umonitor -p${mysql_root_pass} -h ${mysql_host} -e "update mashbd_plat.t_monitor set packagedown='1',packagename='"${tar_result}"' where interip='"$i"';"
		fi
	done

	if [ ! -z "`echo ${tar_result} | grep '^rsh/'`" ]
	then
		curl "http://127.0.0.1:50000/kcgi-bin/publish/serverinit/oktarfabu.php?temp=OK&md5=${cfile}&baoname=${cfile}.tar.gz" >/dev/null 2>&1
		echo ${cfile}.tar.gz > daemon_tok/${cfile}
	else
		curl "http://127.0.0.1:50000/kcgi-bin/publish/serverinit/oktarfabu.php?temp=OK&md5=${cfile}&baoname=${tar_result}" >/dev/null 2>&1
		echo ${tar_result} > daemon_tok/${cfile}
	fi

	curl "http://127.0.0.1:50000/kcgi-bin/publish/serverinit/confroutefabudourl.php" >/dev/null 2>&1
	sleep 1
done
