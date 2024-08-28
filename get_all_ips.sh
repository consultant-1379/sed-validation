#!/bin/bash
cluster=$1
IFS=$'\n' read -d '' -r -a all_cluster_ranges < <(awk '$NF == '${cluster}' {print $0}' /tmp/dns_ip_ranges.txt)

ipv4_ranges=()
storage_ranges=()
ipv6_ranges=()

for ip_range in "${all_cluster_ranges[@]}"
do
    ipType=$(echo $ip_range | awk '{print $6}')
    case $ipType in
        1)
            ipv4_start=$(echo $ip_range | awk '{print $2}')
            ipv4_end=$(echo $ip_range | awk '{print $3}')
            ipv4_ranges+=($ipv4_start $ipv4_end)
        ;;
        2)
            storage_start=$(echo $ip_range | awk '{print $2}')
            storage_end=$(echo $ip_range | awk '{print $3}')
            storage_ranges+=($storage_start $storage_end)
        ;;
        3)
            ipv6_start=$(echo $ip_range | awk '{print $4}')
            ipv6_end=$(echo $ip_range | awk '{print $5}')
            ipv6_ranges+=($ipv6_start $ipv6_end)
    esac
done
if [ $2 == "ipv4" ]
then
    echo ${ipv4_ranges[@]}
fi
if [ $2 == "storage" ]
then
    echo ${storage_ranges[@]}
fi
if [ $2 == "ipv6" ]
then
    echo ${ipv6_ranges[@]}
fi
