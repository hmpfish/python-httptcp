#!/bin/bash
    if [ -z "$2" ]
    then
        echo "error"
    fi

    if [ "1" == "1" ]
    then
        hostname=$(hostname)
        OSCOUNT_outinet="eth0"
        OSCOUNT_ininet="eth1"
        os_ip=$2
        os_mem_total=$(cat /proc/meminfo | grep -i memtotal | head -n 1 | awk '{print $2}')
        os_mem_free=$(cat /proc/meminfo | grep -i memfree | head -n 1 | awk '{print $2}')
        os_mem=$(printf "%.0f%%\n" `echo -e "scale=2\n${os_mem_free}/${os_mem_total}*100"|bc`)
        os_swap_total=$(cat /proc/meminfo | grep -i swaptotal | head -n 1 | awk '{print $2}')
        os_swap_free=$(cat /proc/meminfo | grep -i swapfree | head -n 1 | awk '{print $2}')
        os_swap=$(printf "%.0f%%\n" `echo -e "scale=2\n${os_swap_free}/${os_swap_total}*100"|bc`)
        os_disk=$(df -l | awk '{print 100*$5,$6,$5}' | sed '1d' | sort -n | tail -n 1 | awk '{printf("(%s)%s\n"),$2,$3}')
        os_load=$(uptime | awk '{print $10}' | sed 's/,//g')
        os_inode=$(df -i | awk '{print 100*$5,$6,$5}' | sed '1d' | sort -n | tail -n 1 | awk '{printf("(%s)%s\n"),$2,$3}')
        os_process=$(ps -ef | egrep -v "\[[a-zA-Z0-9]*\]" | wc -l)
        #os_cpu=$(top -bn 1 | grep Cpu -i | head -n 1 | awk '{print $5}' | awk -F'%' '{print $1}' | awk '{print 100-$1}' | awk '{printf("%s%%\n"),$1}')
        os_cpu=$(top -bn 1 | grep Cpu -i | head -n 1 | awk '{print $5}' | sed 's/id,//g')
        os_outinet_in=0
        os_outinet_out=0
        os_ininet_in=0
        os_ininet_out=0

        outinet_valid=$(/sbin/ifconfig ${OSCOUNT_outinet} | grep "inet addr:" | head -n 1)
        if [ -z "${outinet_valid}" ]
        then
            os_outinet_in=0
            os_outinet_out=0
        else
            out_all=$(/sbin/ifconfig ${OSCOUNT_outinet} | grep "bytes:" | awk '{print $2,$6}' | sed 's/bytes://g')
            out_all_in=$(echo "${out_all}" | awk '{print $1}')
            out_all_out=$(echo "${out_all}" | awk '{print $2}')
            out_all_in_f=0
            out_all_out_f=0
            if [ -s inet_${OSCOUNT_outinet}.tmp ]
            then
                out_all_in_f=$(cat inet_${OSCOUNT_outinet}.tmp | head -n 1 | awk '{print $1}')
                out_all_out_f=$(cat inet_${OSCOUNT_outinet}.tmp | head -n 1 | awk '{print $2}')
            fi
            ((os_outinet_in=${out_all_in}-${out_all_in_f}))
            ((os_outinet_out=${out_all_out}-${out_all_out_f}))
            ((os_outinet_in=${os_outinet_in}/1024))
            ((os_outinet_in=${os_outinet_in}/1024))
            ((os_outinet_out=${os_outinet_out}/1024))
            ((os_outinet_out=${os_outinet_out}/1024))
            div_s=240
            os_outinet_in=$(printf "%.2f\n" `echo -e "scale=2\n${os_outinet_in}/${div_s}" | bc`)
            os_outinet_out=$(printf "%.2f\n" `echo -e "scale=2\n${os_outinet_out}/${div_s}" | bc`)
            echo "${out_all_in} ${out_all_out}" > inet_${OSCOUNT_outinet}.tmp
        fi
        ininet_valid=$(/sbin/ifconfig ${OSCOUNT_ininet} | grep "inet addr:" | head -n 1)
        if [ -z "${ininet_valid}" ]
        then
            os_ininet_in=0
            os_ininet_out=0
        else
            out_all=$(/sbin/ifconfig ${OSCOUNT_ininet} | grep "bytes:" | awk '{print $2,$6}' | sed 's/bytes://g')
            out_all_in=$(echo "${out_all}" | awk '{print $1}')
            out_all_out=$(echo "${out_all}" | awk '{print $2}')
            out_all_in_f=0
            out_all_out_f=0
            if [ -s inet_${OSCOUNT_ininet}.tmp ]
            then
                out_all_in_f=$(cat inet_${OSCOUNT_ininet}.tmp | head -n 1 | awk '{print $1}')
                out_all_out_f=$(cat inet_${OSCOUNT_ininet}.tmp | head -n 1 | awk '{print $2}')
            fi
            ((os_ininet_in=${out_all_in}-${out_all_in_f}))
            ((os_ininet_out=${out_all_out}-${out_all_out_f}))
            ((os_ininet_in=${os_ininet_in}/1024))
            ((os_ininet_in=${os_ininet_in}/1024))
            ((os_ininet_out=${os_ininet_out}/1024))
            ((os_ininet_out=${os_ininet_out}/1024))
            div_s=240
            os_ininet_in=$(printf "%.2f\n" `echo -e "scale=2\n${os_ininet_in}/${div_s}" | bc`)
            os_ininet_out=$(printf "%.2f\n" `echo -e "scale=2\n${os_ininet_out}/${div_s}" | bc`)
            echo "${out_all_in} ${out_all_out}" > inet_${OSCOUNT_ininet}.tmp
        fi
        all_cons=$(netstat -aon | egrep '(tcp|udp)' | wc -l)
        printf "%-10s%-15s%-20s%-5s%-5s%-20s%-6s%-20s%-6s%-8s%-8s%-20s%-20s\n" "$1" "${os_ip}" "$(hostname)" "${os_mem}" "${os_swap}" "${os_disk}" "${os_load}" "${os_inode}" "${os_process}" "${os_cpu}" "${all_cons}" "${os_ininet_in}/${os_ininet_out}" "${os_outinet_in}/${os_outinet_out}"
    fi
    exit 
