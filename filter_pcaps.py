import os
import shutil
import tarfile
import tempfile
from scapy.all import rdpcap, IP, IPv6, TCP
import ipwhois
import gzip

def extract_50mb(tgz_path, extract_folder):
    """Extracts a .tgz file into a given directory."""
    try:
        with tarfile.open(tgz_path, "r:gz") as tar:
            tar.extractall(path=extract_folder)
    except Exception as e:
        print(f"Error extracting {tgz_path}: {e}")

def find_innermost_folder(base_folder):
    """Finds the innermost yyyy/mm/dd folder."""
    for root, _, _ in os.walk(base_folder, topdown=True):
        parts = root.split(os.sep)
        if len(parts) >= 3 and parts[-3].isdigit() and parts[-2].isdigit() and parts[-1].isdigit():
            return root
    return None

def extract_pcap(gz_path, temp_folder):
    """Extracts a .pcap.gz file to a temporary directory."""
    try:
        extracted_file = os.path.join(temp_folder, os.path.splitext(os.path.basename(gz_path))[0])
        with gzip.open(gz_path, 'rb') as f_in, open(extracted_file, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
        return extracted_file
    except Exception as e:
        print(f"Error extracting {gz_path}: {e}")
        return None

def get_client_ip(pcap_path):
    """Extracts the client IP address from a pcap file."""
    try:
        packets = rdpcap(pcap_path, count=1)
        if packets:
            packet = packets[0]
            if IP in packet:
                src_ip, dst_ip = packet[IP].src, packet[IP].dst
            elif IPv6 in packet:
                src_ip, dst_ip = packet[IPv6].src, packet[IPv6].dst
            else:
                return None

            src_port = packet[TCP].sport if TCP in packet else None
            dst_port = packet[TCP].dport if TCP in packet else None

            if src_port and src_port != 443:
                return src_ip
            elif dst_port and dst_port != 443:
                return dst_ip
    except Exception as e:
        print(f"Error reading {pcap_path}: {e}")
    return None

def get_asn(ip):
    """Retrieves the ASN for a given IP address."""
    try:
        obj = ipwhois.IPWhois(ip)
        result = obj.lookup_rdap(asn_methods=["whois"])
        return result.get("asn")
    except Exception as e:
        print(f"Error fetching ASN for {ip}: {e}")
    return None

def load_asns(asn_file):
    """Loads a list of ASNs from a file."""
    try:
        with open(asn_file, "r") as file:
            return {line.strip() for line in file if line.strip()}
    except Exception as e:
        print(f"Error reading ASN file {asn_file}: {e}")
        return set()

def filter_pcaps_date(data_folder, filtered_folder, cellular_asns):
    """Filters pcap files based on ASN."""
    os.makedirs(filtered_folder, exist_ok=True)
    with tempfile.TemporaryDirectory() as temp_folder:
        for file in os.listdir(data_folder):
            file_path = os.path.join(data_folder, file)
            if file.endswith(".gz"):
                extracted_file = extract_pcap(file_path, temp_folder)
                if not extracted_file:
                    continue  
                ip_address = get_client_ip(extracted_file)
                if ip_address:
                    asn = get_asn(ip_address)
                    if asn in cellular_asns:
                        shutil.move(extracted_file, os.path.join(filtered_folder, os.path.basename(extracted_file)))

def filter_pcaps(data_directory, work_dir, filtered_pcaps, asn_file):
    os.makedirs(work_dir, exist_ok=True)
    os.makedirs(filtered_pcaps, exist_ok=True)
    cellular_asns = load_asns(asn_file)
    
    for tgz_file in os.listdir(data_directory):
        if tgz_file.endswith(".tgz"):
            tgz_path = os.path.join(data_directory, tgz_file)
            extract_folder = os.path.join(work_dir, os.path.splitext(tgz_file)[0])
            extract_50mb(tgz_path, extract_folder)
            innermost_folder = find_innermost_folder(extract_folder)
            print(innermost_folder)
            if innermost_folder:
                filter_pcaps_date(innermost_folder, filtered_pcaps, cellular_asns)

if __name__ == "__main__":
    DATA_DIRECTORY = "data"
    WORK_DIR = "work_dir"
    FILTERED_PCAPS = "filtered_pcaps"
    ASN_FILE = "cellular_asns.txt"
    filter_pcaps(DATA_DIRECTORY, WORK_DIR, FILTERED_PCAPS, ASN_FILE)