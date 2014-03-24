#!/bin/bash

source ../kcgi-bin/publish/config/config.sh

while [ 1 ]
do

	cfile=$(ls -t ../kcgi-bin/publish/serverinit/tartask/ | tail -n 1)

	if [ -z "${cfile}" ]
	then
		sleep 1
		continue
	fi

	mv ../kcgi-bin/publish/serverinit/tartask/${cfile} ../kcgi-bin/publish/serverinit/tardone/
	tar_result=$(head -n 1 ../kcgi-bin/publish/serverinit/tardone/${cfile})	

	mkdir package

	for i in `cat ../kcgi-bin/publish/serverinit/tardone/${cfile} | sed '1d' | sed '/^$/d'`
	do
		if [ -z "$i" ]
		then
			continue
		fi

		if [ ! -z "`echo $i | egrep '^op'`" ]
		then
			install ../kcgi-bin/publish/serverinit/tarrpm/$i package/op.sh
			continue
		fi

		install ../kcgi-bin/publish/serverinit/tarrpm/$i package/
	done

	chmod +x package/*.sh

	perl -i -pe 's!!!g' package/*.sh

	tar -zcvf ${tar_result} package

	rm -r -f package
		
	install ${tar_result} ${package_dst_dir}
	rm -f ${tar_result}

	curl "http://127.0.0.1:50000/kcgi-bin/publish/serverinit/oktarfile.php?temp=Success&md5=${cfile}" >/dev/null 2>&1
	sleep 1
done
