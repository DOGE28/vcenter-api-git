from config import vcenter_settings
from pyVim.connect import SmartConnect, Disconnect
import ssl
import csv
import threading
import smtplib
#from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import time
import os

class vCenter():
    """
    Description: This class is used to connect to a vCenter server and retrieve information about the hosts, VMs, datastores, and networks.

    Methods:
    get_clusters() -> list: Returns a list of the clusters in the vCenter server.
    get_hosts() -> list: Returns a list of the hosts in the vCenter server.
    get_host_status() -> dict: Returns a dictionary of the hosts in the vCenter server along with certain properties.
    
    """

    def __init__(self, location): #Initiates the connection to the vCenter server
        locations = {
            'sgu_prod': 'tdc-vcsa01.tonaquint.local', 
            'sgu_inf': 'sgu-inf-vcsa01.tonaquint.local', 
            'boi_prod': 'boi-vcsa.tonaquint.local', 
            'boi_inf': 'boi-inf-vcsa01.tonaquint.local',
            'fishbowl': 'sgu-fb-vcsa01.tonaquint.com',
            'okc_inf': 'okc-inf-vcsa01.tonaquint.local'
            }
        if location not in locations:
            raise ValueError("Invalid location, possible values are: sgu_prod, sgu_inf, boi_prod, boi_inf, fishbowl, okc_inf")
        self.location = locations[location]
        self.og_location = location
        self.user = vcenter_settings.username
        self.password = vcenter_settings.password
        self.ip = self.location
        try:
            print("Attempting Connection to: ", self.location)
            context = ssl._create_unverified_context()
            self.si = SmartConnect(host=self.ip, user=self.user, pwd=self.password, sslContext=context)
            self.content = self.si.RetrieveContent()
            print("Connection Established")
        except Exception as e:
            print(f"Error connecting to {self.location}: {e}")
    
    def disconnect(self):
        Disconnect(self.si)

    def get_clusters(self) -> list:
        clusters = self.content.rootFolder.childEntity[0].hostFolder.childEntity
        return clusters
    
    def get_hosts(self) -> list:
        hosts = []
        clusters = self.get_clusters()
        for cluster in clusters:
            for host in cluster.host:
                hosts.append(host)
        return hosts
    
    def get_host_status(self) -> dict:
        hosts = self.get_hosts()
        all_hosts = {}
        all_core_count = 0
        for host in hosts:
            cpu_model = host.summary.hardware.cpuModel
            cpu_cores = host.summary.hardware.numCpuCores
            cpu_usage = str(round(host.summary.quickStats.overallCpuUsage/1000, 2)) + " GHz"
            memory = str(round(((host.summary.hardware.memorySize/1024)/1024)/1024,0))+ " GB"
            cluster_name = host.parent.name
            if host.runtime.inMaintenanceMode:
                standby = "Yes"
            else:
                standby = "No"
                all_core_count += cpu_cores
            all_hosts[host.name] = {
                'Cluster': cluster_name,
                'CPU Model': cpu_model,
                'CPU Cores': cpu_cores,
                'CPU Usage': cpu_usage, 
                'Memory': memory,
                'MaintMode': standby
            }
        return all_hosts, all_core_count
    
    def get_vms(self) -> list:
        vms = []
        clusters = self.get_clusters()
        for cluster in clusters:
            for host in cluster.host:
                for vm in host.vm:
                    vms.append(vm)
        return vms
    
    def get_datastores(self) -> list:
        datastores = []
        clusters = self.get_clusters()
        for cluster in clusters:
            for host in cluster.host:
                for datastore in host.datastore:
                    datastores.append(datastore)
        return datastores
    
    def get_networks(self) -> list:
        networks = []
        clusters = self.get_clusters()
        for cluster in clusters:
            for host in cluster.host:
                for network in host.network:
                    networks.append(network)
        return networks
    
    def get_vms_on_host(self, host) -> list:
        vms = []
        for vm in host.vm:
            vms.append(vm)
        return vms


    def write_to_csv(self):
        print("Creating CSV for ", self.og_location)
        host_data, total_cores = self.get_host_status()
        with open(f'{self.og_location}.csv', mode='w', newline='') as file:
            fieldnames = ["Host Name", "Cluster", "CPU Model", "CPU Cores", "CPU Usage", "Memory", "MaintMode"]
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()

            for host_name, host_data in host_data.items():
                writer.writerow({"Host Name": host_name, **host_data})
            writer.writerow({"Host Name": "Total Cores NOT in MM", "Cluster": total_cores, "CPU Model": "", "CPU Cores": "", "CPU Usage": "", "Memory": "", "MaintMode": ""})
            time.sleep(2)
        self.disconnect()

def send_email_with_attachment(csv_list):
    print("Creating Email")
    msg = MIMEMultipart()
    sender = 'vmware-report@tonaquint.com'
    receiver ='tsullivan@tonaquint.com'
    subject = "Weekly vCenter Core Count Report"
    body = "Attached is the weekly vCenter core count report. Opening this CSV with Excel will calculate the non-MM core counts."
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = receiver
    msg.attach(MIMEText(body, 'plain'))
    print("Attaching CSVs")
    for csv in csv_list:
        with open(csv, 'rb') as file:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(file.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename={csv}')
            #print(part)
            msg.attach(part)

    #print(msg)
    with smtplib.SMTP('10.101.70.50', 25) as smtp:
        smtp.sendmail(sender, receiver, msg.as_string())
        print("Email sent")

def sgu_prod():
    sgu_prod = vCenter('sgu_prod')
    sgu_prod.write_to_csv()

def sgu_inf():
    sgu_inf = vCenter('sgu_inf')
    sgu_inf.write_to_csv()

def boi_prod():
    boi_prod = vCenter('boi_prod')
    boi_prod.write_to_csv()

def boi_inf():
    boi_inf = vCenter('boi_inf')
    boi_inf.write_to_csv()

def fishbowl():
    fishbowl = vCenter('fishbowl')
    fishbowl.write_to_csv()

def okc_inf():
    okc_inf = vCenter('okc_inf')
    okc_inf.write_to_csv()


# Setup multiple threads to run the vCenter functions concurrently

threading.Thread(target=sgu_prod).start()
threading.Thread(target=sgu_inf).start()
threading.Thread(target=boi_prod).start()
threading.Thread(target=boi_inf).start()
threading.Thread(target=fishbowl).start()
threading.Thread(target=okc_inf).start()

# Check all files exist before proceeding...



csv_list = ['sgu_prod.csv', 
        'boi_prod.csv',
        'fishbowl.csv',]

while not all([True if csv in os.listdir() else False for csv in csv_list]):
    time.sleep(1)

send_email_with_attachment(csv_list)