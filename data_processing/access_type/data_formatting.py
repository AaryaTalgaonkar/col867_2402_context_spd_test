# cellular_classifier.py
import pandas as pd
from scapy.all import rdpcap, IP, IPv6, TCP
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_pcap(pcap_path: str, output_csv: str) -> pd.DataFrame:
    """Process PCAP file and generate features"""
    logger.info(f"Processing {pcap_path}")
    
    # Read PCAP file
    packets = rdpcap(pcap_path)
    
    # Extract features
    data = []
    for pkt in packets:
        entry = {
            'timestamp': pkt.time,
            'src_ip': None,
            'dst_ip': None,
            'packet_size': None,
            'protocol': None,
            'ttl': None,
            'src_port': None,
            'des_port': None,
            'seq_no': None
        }
        #IP layer
        if pkt.haslayer(IP):
            ip_layer = pkt[IP]
            entry.update({
                'timestamp': pkt.time,
                'src_ip': ip_layer.src,
                'dst_ip': ip_layer.dst,
                'packet_size': len(ip_layer),
                'protocol': ip_layer.proto,
                'ttl': ip_layer.ttl
            })
        elif pkt.haslayer(IPv6):  # Handle IPv6 packets
            ipv6_layer = pkt[IPv6]
            entry.update({
                'timestamp': pkt.time,
                'src_ip': ipv6_layer.src,
                'dst_ip': ipv6_layer.dst,
                'packet_size': len(ipv6_layer),
                'protocol': ipv6_layer.nh,  
                'ttl': ipv6_layer.hlim,  
            })
        #TCP Layer
        if pkt.haslayer(TCP):
            tcp_layer = pkt[TCP]
            entry.update({     
                'src_port': tcp_layer.sport,
                'des_port': (tcp_layer.dport),
                'seq_no': int(tcp_layer.seq),
            })
        data.append(entry)

    
    # Create DataFrame
    df = pd.DataFrame(data)
    numeric_cols = ['packet_size', 'protocol', 'ttl', 'src_port', 'des_port', 'seq_no']
    df[numeric_cols] = df[numeric_cols].fillna(0).astype(int)

    # Save DataFrame to CSV
    logger.info(f"Saving processed data to {output_csv}")
    df.to_csv(output_csv, index=False)
    return None

# Example usage
if __name__ == "__main__":

    formatted_Data_fileName = 'PacketData.csv'
    
    # Process PCAP files
    # Note : PCAP Path will be modified as per the data directory. 
    cellular_traffic = process_pcap('ndt-bmn8w_1738217747_00000000002F0AA5.pcap', formatted_Data_fileName)
    wifi_traffic = process_pcap('ndt-9pvq9_1737862997_0000000000BA5BCB.pcap', formatted_Data_fileName)

# ------------------------------------------------------------------------------------------------------------------------------------
# Below code can be used to directly map the IP address to ASN, given the IP to ASN mapping database is available. 
# import ipaddress
# def load_ip_to_asn_mapping(csv_path: str) -> pd.DataFrame:
#     """
#     Load IP-to-ASN mapping from a CSV file.
#     """
#     try:
#         ip_to_asn_df = pd.read_csv(csv_path)
#         logger.info(f"Loaded {len(ip_to_asn_df)} IP-to-ASN mappings from {csv_path}")

#         # Add integer representations of start and end IPs
#         ip_to_asn_df['start_ip_int'] = ip_to_asn_df['start_ip'].apply(lambda x: int(ipaddress.ip_address(x)))
#         ip_to_asn_df['end_ip_int'] = ip_to_asn_df['end_ip'].apply(lambda x: int(ipaddress.ip_address(x)))

#         return ip_to_asn_df
#     except FileNotFoundError:
#         logger.error(f"CSV file not found: {csv_path}")
#         raise
#     except Exception as e:
#         logger.error(f"Error loading IP-to-ASN mapping CSV: {str(e)}")
#         raise

# def get_asn(ip: str, ip_to_asn_df: pd.DataFrame) -> int:
#     """Get ASN for an IP address using the loaded IP-to-ASN mapping."""
#     try:
#         ip_int = int(ipaddress.ip_address(ip))
#         # Filter rows where the IP falls within the start and end range
#         match = ip_to_asn_df[
#             (ip_to_asn_df['start_ip_int'] <= ip_int) & (ip_to_asn_df['end_ip_int'] >= ip_int)
#         ]
#         if not match.empty:
#             return match.iloc[0]['asn']  # Return the first matching ASN
#         return None  # No match found
#     except ValueError:
#         logger.warning(f"Invalid IP address: {ip}")
#         return None
#     except Exception as e:
#         logger.error(f"ASN lookup failed for {ip}: {str(e)}")
#         return None

# Code that would be added to process_pcap file
# Add network features
# logger.info("Adding ASN features...")
# if isIPv6Packet:
#     df['src_asn'] = df['src_ip'].apply(lambda x: get_asn(x, ipv6_to_asn_df))
#     df['dst_asn'] = df['dst_ip'].apply(lambda x: get_asn(x, ipv6_to_asn_df))
# else : 
#     df['src_asn'] = df['src_ip'].apply(lambda x: get_asn(x, ipv4_to_asn_df))
#     df['dst_asn'] = df['dst_ip'].apply(lambda x: get_asn(x, ipv4_to_asn_df))