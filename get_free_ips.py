import ipaddress
import subprocess
import sys

def free_ips(ipRanges, sedIpList, ipType):
    """
    Perform a ping sweep of a range of IP addresses.
    Returns a list of unassigned IP addresses.
    """
    ipRanges = ipRanges.split()
    free_ips = []
    for i in range(len(ipRanges)):
        if i >= len(ipRanges) - 1:
            break
        ip = ipRanges[i]
        ip = ipaddress.ip_address(unicode(ip))
        while True:
            if isinstance(ip, ipaddress.IPv4Address):
                cmd = 'grep  "' + str(ip) + '" /tmp/dmt_ips.txt'
            elif isinstance(ip, ipaddress.IPv6Address):
                cmd = 'grep  "' + str(ip) + '" /tmp/dmt_ips.txt'
            result = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            ipFound, errors = result.communicate()
            if not ipFound:
                if ip not in sedIpList:
                    free_ips.append(str(ip))

            ip += 1
            if ip == ipaddress.ip_address(unicode(ipRanges[i + 1])):
                break
    print("========= Free " + ipType + "'s =========")
    for ip in free_ips:
        print(ip)
        pass
