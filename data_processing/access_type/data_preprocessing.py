import os
import csv
from scapy.all import rdpcap, TCP
import numpy as np
import random
def compute_iat_metrics(iats_to_443, iats_from_443):
    iats_to_443 = [float(iat) for iat in iats_to_443]
    iats_from_443 = [float(iat) for iat in iats_from_443]

    iat_mean_to_443 = np.mean(iats_to_443) if iats_to_443 else 0
    iat_variance_to_443 = np.var(iats_to_443) if iats_to_443 else 0
    iat_mean_from_443 = np.mean(iats_from_443) if iats_from_443 else 0
    iat_variance_from_443 = np.var(iats_from_443) if iats_from_443 else 0

    return iat_mean_to_443, iat_variance_to_443, iat_mean_from_443, iat_variance_from_443

def compute_latency_metrics(latencies_to_443, latencies_from_443):
    latencies_to_443 = [float(lat) for lat in latencies_to_443]
    latencies_from_443 = [float(lat) for lat in latencies_from_443]

    latency_mean_to_443 = np.mean(latencies_to_443) if latencies_to_443 else 0
    latency_variance_to_443 = np.var(latencies_to_443) if latencies_to_443 else 0
    latency_mean_from_443 = np.mean(latencies_from_443) if latencies_from_443 else 0
    latency_variance_from_443 = np.var(latencies_from_443) if latencies_from_443 else 0

    return latency_mean_to_443, latency_variance_to_443, latency_mean_from_443, latency_variance_from_443

def compute_throughput(sizes_to_443, sizes_from_443, duration):
    sizes_to_443 = [float(size) for size in sizes_to_443]
    sizes_from_443 = [float(size) for size in sizes_from_443]
    duration = float(duration)

    throughput_to_443 = sum(sizes_to_443) / duration if duration > 0 else 0
    throughput_from_443 = sum(sizes_from_443) / duration if duration > 0 else 0

    return throughput_to_443, throughput_from_443

def compute_burst_ratio(iats_to_443, iats_from_443):
    def burst_ratio(iats):
        if not iats:
            return 0
        iats_float = [float(iat) for iat in iats]
        burst_threshold = np.percentile(iats_float, 10)
        return sum(1 for iat in iats_float if iat < burst_threshold) / len(iats_float)

    return burst_ratio(iats_to_443), burst_ratio(iats_from_443)


def extract_pcap_features(pcap_file):    
    packets = rdpcap(pcap_file)
    if not packets:
        return None
    
    timestamps, iats_to_443, iats_from_443 = [], [], []
    latencies_to_443, latencies_from_443 = [], []
    sizes_to_443, sizes_from_443 = [], []
    packet_count_to_443, packet_count_from_443 = 0, 0
    
    first_timestamp = packets[0].time
    
    for i, packet in enumerate(packets):
        if TCP in packet:
            src_port = packet[TCP].sport
            dst_port = packet[TCP].dport
            timestamp = packet.time
            size = len(packet)
        
            timestamps.append(timestamp)
        
            if dst_port == 443 or dst_port == 80:
                packet_count_to_443 += 1
                sizes_to_443.append(size)
                if i > 0:
                    latencies_to_443.append(timestamp - timestamps[i - 1])
                    iats_to_443.append(timestamp - timestamps[i - 1])
            elif src_port == 443 or dst_port == 80:
                packet_count_from_443 += 1
                sizes_from_443.append(size)
                if i > 0:
                    latencies_from_443.append(timestamp - timestamps[i - 1])
                    iats_from_443.append(timestamp - timestamps[i - 1])
    
    if len(timestamps) < 2:
        return None  # Skip files with insufficient data
    
    total_time = timestamps[-1] - first_timestamp or 1
    
    burst_ratio_to_443, burst_ratio_from_443 = compute_burst_ratio(iats_to_443, iats_from_443)
    throughput_to_443, throughput_from_443 = compute_throughput(sizes_to_443, sizes_from_443, total_time)
    latency_mean_to_443, latency_variance_to_443, latency_mean_from_443, latency_variance_from_443 = compute_latency_metrics(latencies_to_443, latencies_from_443)
    iat_mean_to_443, iat_variance_to_443, iat_mean_from_443, iat_variance_from_443 = compute_iat_metrics(iats_to_443, iats_from_443)
    
    return [burst_ratio_to_443, burst_ratio_from_443, 
            throughput_to_443, throughput_from_443, 
            latency_mean_to_443, latency_mean_from_443, 
            latency_variance_to_443, latency_variance_from_443, 
            iat_mean_to_443, iat_mean_from_443, 
            iat_variance_to_443, iat_variance_from_443, 
            packet_count_to_443, packet_count_from_443]

def get_shuffled_list(data_path):
    pcap_files = []
    for label, folder in [(1, "cellular"), (0, "wifi")]:
        dir_path = os.path.join(data_path, folder)
        if os.path.exists(dir_path):
            for f in os.listdir(dir_path):
                if f.endswith(".pcap"):
                    pcap_files.append((os.path.join(dir_path, f), label))
    
    random.shuffle(pcap_files)  # Shuffle in place
    return pcap_files  # Return the shuffled list

def featurize_data(pcap_files,output_file):
    header = ["burst_ratio_to_443", "burst_ratio_from_443", 
              "throughput_to_443", "throughput_from_443", 
              "latency_mean_to_443", "latency_mean_from_443", 
              "latency_variance_to_443", "latency_variance_from_443", 
              "IAT_mean_to_443", "IAT_mean_from_443", 
              "IAT_variance_to_443", "IAT_variance_from_443", 
              "packet_count_to_443", "packet_count_from_443", "label"]
    with open(output_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(header)
        for pcap_file, label in pcap_files:
            features = extract_pcap_features(pcap_file)
            if features:
                writer.writerow(features + [label])
    
    print(f"Feature extraction complete. Results saved in {output_file}")

if __name__ == "__main__":
    DATA_PATH = "data"
    OUTPUT_CSV = "features.csv"
    pcap_files = get_shuffled_list(DATA_PATH)
    featurize_data(pcap_files,OUTPUT_CSV)  
