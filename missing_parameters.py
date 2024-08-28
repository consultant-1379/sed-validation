import os,sys,re,textwrap,requests,urllib,json,urllib2,freeips
import xml.etree.ElementTree as ElementTree
from argparse import RawTextHelpFormatter, ArgumentParser

class DeploymentHandler():
    """
    Class to perform the parameter comparison
    """

    def __init__(self):
        self.litp_parameter_set = set()
        self.sed_parameter_map = {}
        self.deployment_file = ''
        self.sed_file = ''

    def process_files(self):
        """
        Scan through the DD and SED files populating data structures containing
        lists of variables seen in each
        """
        self.litp_parameter_set = set()
        try:
            root = ElementTree.parse(self.deployment_file)
        except IOError as ex:
            print_in_colour(str(ex), RED)
            sys.exit(1)
        for elem in root.getiterator():
            text = elem.text
            if text:
                paramList = [re.match('%%(.*)%%', match).group(1) for match in
                             re.split('(%%[^%]+%%)', text) if
                             re.match('%%([^%]+)%%', match)]
                for param in paramList:
                    self.litp_parameter_set.add(param)
        try:
            with open(self.sed_file) as file:
                lines = file.readlines()
                for line in lines:
                    if (re.match('(\S+)=(\S+)', line) and
                            line != 'Variable_Name=Variable_Value'):
                        (parameter, sep, value) = line.partition('=')
                        self.sed_parameter_map[parameter] = value
        except IOError as ex:
            print_in_colour(str(ex), RED)
            sys.exit(1)


def print_missing_params(deployment_set, sed_map):
    """
    Print a list of missing parameters
    :param deployment_set: Set containing all params found in DD
    :type deployment_set: Set -> str
    :param sed_map: A dictionary containing param values keyed by param names
    :type sed_map: dict[str] -> str
    :return: None
    """
    ignore_list = ["ERICrhel76jbossimage", "ERICsles11ncmimage",
                   "ERICrhel6baseimage", "ERICrhel6jbossimage",
                   "ERICrhel76lsbimage", "ERICrhel7baseimage",
                   "ERICrhel79lsbimage", "ERICrhel79jbossimage",
                   "ERICsles15image", "uuid_ms_disk0", "vm_ssh_key"]

    sed_set = set(sed_map.keys())
    sorted_diff = sorted(deployment_set.difference(sed_set))
    collected_missing = []
    collected_missing_ignore = []

    for param in sorted_diff:
        if param not in ignore_list:
            if (param.endswith('_password_encrypted') and
                    param[0:param.index('_password_encrypted')] + "_password"
                    not in sed_set):
                collected_missing.append(param)
            elif not (param.endswith('_password_encrypted')):
                collected_missing.append(param)
        else:
            collected_missing_ignore.append(param)
    return collected_missing
    

def get_sed(setSED,clusterId):
  print("Started downloading SED...\n")
  if "http" in setSED:
    sed_url = setSED
  else:
    sed_url = "https://ci-portal.seli.wh.rnd.internal.ericsson.com/api/deployment/"+clusterId+"/sed/"+setSED+"/generate/"
  request=requests.get(sed_url,allow_redirects=True)
  if request.status_code == 200:
    open('sed.txt','wb').write(request.content)
    print("SED successfully downloaded.\n")
  else:
    print("\nThere is an issue with the link provided. Please check the SED link provided/used : "+sed_url)
    print("Status response code: "+str(request.status_code))
    exit(100)
  return "./sed.txt"
def get_dd_xml(dd_xml,product_set):
  print("\nStarted downloading the DD...\n")
  if "http" in dd_xml:
    dd_url=dd_xml
    request=requests.get(dd_url,allow_redirects=True)
    if request.status_code == 200:
     open('dd.xml','wb').write(request.content)
     print("DD successfully downloaded.\n")
     return "./dd.xml"
    else:
      print("There is an issue with the link provided, Please check the DD xml link provided/used : " + dd_url)
      print("Status response code: "+str(request.status_code))
      exit(200)
  else:
    get_req_dd(product_set,dd_xml)
    return "."+dd_xml
def get_req_dd(product_set,dd_xml):
    headers = {'User-Agent': 'Mozilla AppleWebKit Chrome Safari'}
    drop=product_set.split('::')[0]
    if product_set.split('::')[1].upper()=='GREEN':
      ps_url="http://ci-portal.seli.wh.rnd.internal.ericsson.com/getLastGoodProductSetVersion/?drop="+drop+"&productSet=ENM"
      ProductSetVer=get_data(ps_url)
    else:
      ProductSetVer=product_set.split('::')[1]

    template_version_cmd = "https://ci-portal.seli.wh.rnd.internal.ericsson.com/api/deployment/deploymentTemplates/productSet/ENM/version/"+ProductSetVer+"/?format=json"
    response = requests.get(template_version_cmd)
    template_version_dict=response.json()
    artifact = template_version_dict['mediaArtifact']
    artifact_version = template_version_dict['mediaArtifactVersion']
    template_url,version = get_template_url(artifact,artifact_version)
    get_dd(template_url,dd_xml,version)
    
def get_template_url(artifact,version):
    headers = {'User-Agent': 'Mozilla AppleWebKit Chrome Safari'}
    template_url_cmd = "https://ci-portal.seli.wh.rnd.internal.ericsson.com/api/getMediaArtifactVersionData/mediaArtifact/"+str(artifact)+"/version/"+str(version)
    response = requests.get(template_url_cmd,{'Content-Type': 'application/json'})
    template_url_dict = response.json()
    template_url_list = template_url_dict['content']
    for content in template_url_list:
        if content['number'] == 'CXP9031758':
           template_url = content['url']
           version = content['version']
    return template_url,version
def get_dd(template_url,dd_xml,version):
    url_response = os.system("wget "+template_url+" >log.txt")
    extract_dd_response = os.system("rpm2cpio ERICenmdeploymenttemplates_CXP9031758-"+version+".rpm|cpio -ivdm ."+dd_xml)
    print("DD RPM extracted successfully.\n")
def get_data(url):
    try:
        data = requests.get(url).text
        return data
    except urllib2.URLError as e:
        print("There is an issue with the url provided. Please provide a valid path.\n")
        print(e)
        exit(1)
    except urllib2.HTTPError as e:
        print("There is an issue with the https connection, from the DMT page please check!\n")
        print(e)
def missing_para(clusterId,setSED,product_set,dd_xml):

  handler = DeploymentHandler()
  deployment_file = get_dd_xml(dd_xml,product_set)
  sed_file = get_sed(setSED,clusterId)
  handler.deployment_file = deployment_file
  handler.sed_file = sed_file
  handler.process_files()
  deployment_set = handler.litp_parameter_set
  sed_map = handler.sed_parameter_map
  missing = print_missing_params(deployment_set, sed_map)
  return missing
def file_read(fname):
        with open (fname, "r") as myfile:
                data=myfile.readlines()
                return data
def print_data(data_list,data_type):
    if len(data_list) == 0:
       print("\n\n\n---------------------------------------------------------------------------")
       if data_type == "Missing Parameters":
         print("\033[1;32mThere are no "+data_type+"\033[0m")
       else:
         print("\033[1;31mThere are no "+data_type+"\033[0m")
    else:
       print("\n\n\n---------------------------------------------------------------------------")
       if data_type == "Missing Parameters":
         print("\033[1;31m"+data_type+"\033[0m")
       else:
         print("\033[1;35m"+data_type+"\033[0m")
       for data in data_list:
         print(data)
       if data_type == "Missing Parameters":
         print("\n---------------------------------------------------------------------------\n\n\n")
         exit(400)
    print("\n---------------------------------------------------------------------------\n\n\n")

clusterId=sys.argv[1]
print("\n---------------------------------------------------------------------------")
print("\n\nDeployment ID :"+str(clusterId))

setSED=sys.argv[2]
print("\nSED Version : "+str(setSED))

product_set=sys.argv[3]
print("\nProduct Set Version : "+str(product_set))

dd_xml=sys.argv[4]
print("\nDD xml : "+dd_xml)
print("\n---------------------------------------------------------------------------")

command = sys.argv[5]
if command == "Missing_Parameters_Only":
  missing = missing_para(clusterId,setSED,product_set,dd_xml)
  print_data(missing,"Missing Parameters")

elif command == "Missing_Parameters_and_Free_IPs":
  missing = missing_para(clusterId,setSED,product_set,dd_xml)
  storageIPs,servicesIPsv4,servicesIPsv6=freeips.get_DNS_ips(clusterId)
  if "http" in setSED:
    sedIpList=freeips.get_ip_from_sed(file_read("sed.txt"))
  else:
    sedIpList=freeips.get_ip_from_sed(freeips.get_sed_file(clusterId))
  storage,service,ipv6=freeips.freeip(storageIPs,servicesIPsv4,servicesIPsv6,sedIpList)
  print_data(missing,"Missing Parameters")

elif command == "Free_IPs_Only":
  print('Downloading SED')
  get_sed(setSED, clusterId)
  storageIPs,servicesIPsv4,servicesIPsv6=freeips.get_DNS_ips(clusterId)
  if "http" in setSED:
    sedIpList=freeips.get_ip_from_sed(file_read("sed.txt"))
  else:
    sedIpList=freeips.get_ip_from_sed(freeips.get_sed_file(clusterId))
  storage,service,ipv6=freeips.freeip(storageIPs,servicesIPsv4,servicesIPsv6,sedIpList)

else:
  print("Please select a proper option")
  exit(300)
try:
  if len(missing) != 0:
    exit(400)
except:
  pass
