#!/usr/bin/python
import os,sys,paramiko,urllib2, re,subprocess, socket,ipaddress, get_free_ips
def get_sed_file(deployment, delta=60):
    try:
        req = urllib2.Request('https://ci-portal.seli.wh.rnd.internal.ericsson.com/api/deployment/' + deployment + '/sed/MASTER/generate/')
        response = urllib2.urlopen(req)
        sedFile = response.readlines()
    except:
        print("Could not retrieve SED for deployment: " + deployment)
        return None

    if sedFile_valid(sedFile, deployment):
        return sedFile
    else:
        return None
def sedFile_valid(sedFile, deployment):
    if re.findall("Deployment ID: " + deployment + " does not exist", sedFile[0]):
        print("Deployment ID: " + deployment + " does not exist")
        return False
    else:
        return True
def get_ip_from_sed(sed):
    ips = []
    for line in sed:
        try :
            try:
                ip = line.split("ipaddress=")[1].strip("\n").strip("\r").strip("\t").strip()
            except:
                try:
                    ip = line.split("ipv6address=")[1].strip("\n").strip("\r").strip("\t").strip()
                except:
                    ip = line.split("storage=")[1].strip("\n").strip("\r").strip("\t").strip()
            if len(ip) != 0:
                ips.append(ip)
        except:
            pass
    return ips[1:]
def check_dns(pattern):
    result = subprocess.check_output("grep -i ieatENM5" + pattern + " /net/159.107.177.22/Public/db.athtem.eei.ericsson.se | grep -v 2001", shell=True)
    result+=subprocess.check_output("grep -i ieatENM5" + pattern + " /net/159.107.177.22/Public/db.athtem.eei.ericsson.se | grep 2001", shell=True)
    return result
def freeIpv4(servicesIPsv4,sedIpList):
  freeSerIps = []
  flag=0
  for ipv4 in servicesIPsv4:
      if ipv4 in sedIpList:
         pass
      else:
         result = subprocess.check_output("grep -i " + ipv4 + " /net/159.107.177.22/Public/db.athtem.eei.ericsson.se | grep -v 2001", shell=True)
         freeSerIps.append(result.split("\n")[0])
  return freeSerIps
def freeStorage(storageIPs,sedIpList):
  freeStrIp = []
  flag = 0
  for storageIp in storageIPs:
      if storageIp in sedIpList:
         pass
      else:
        result = subprocess.check_output("grep -i " + storageIp + " /net/159.107.177.22/Public/db.athtem.eei.ericsson.se | grep -v 2001", shell=True)
        freeStrIp.append(result.split("\n")[0])
        flag = 1
  return freeStrIp
def freeIpv6(servicesIPsv6,sedIpList):
  freeIPv6=[]
  for ipv6 in servicesIPsv6:
   if ipv6 == ' ':
     pass
   else:
     flag = 0
     for match in sedIpList:
       if match == ' ':
         pass
       else:
         if str(ipaddress.ip_address(unicode(ipv6)).exploded) == str(ipaddress.ip_address(unicode(match)).exploded):
            flag = 1
            break
     if flag != 1:
        result = subprocess.check_output("grep -i " + str(ipv6) + " /net/159.107.177.22/Public/db.athtem.eei.ericsson.se | grep 2001", shell=True)
        freeIPv6.append(result.split("\n")[0])
  return freeIPv6
def get_DNS_ips(deployment):
  servicesIPsv4 = subprocess.check_output('bash get_all_ips.sh ' + str(deployment) + ' ipv4', shell=True)
  storageIPs = subprocess.check_output('bash get_all_ips.sh ' + str(deployment) + ' storage', shell=True)
  servicesIPsv6 = subprocess.check_output('bash get_all_ips.sh ' + str(deployment) + ' ipv6', shell=True)
  return storageIPs,servicesIPsv4,servicesIPsv6
def freeip(storageIPs,servicesIPsv4,servicesIPsv6,sedIpList):
  freeServicesIPsv4 = get_free_ips.free_ips(servicesIPsv4, sedIpList, 'IPv4')
  freeStorageIPs = get_free_ips.free_ips(storageIPs, sedIpList, 'Storage IP')
  freeServicesIPsv6 = get_free_ips.free_ips(servicesIPsv6, sedIpList, 'IPv6')
  return freeServicesIPsv4, freeStorageIPs, freeServicesIPsv6