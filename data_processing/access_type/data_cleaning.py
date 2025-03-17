# cellular_classifier.py
import pandas as pd
from scapy.all import rdpcap, IP, IPv6
import logging
import ipaddress

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_ip_to_asn_mapping(csv_path: str) -> pd.DataFrame:
    """
    Load IP-to-ASN mapping from a CSV file.
    """
    try:
        ip_to_asn_df = pd.read_csv(csv_path)
        logger.info(f"Loaded {len(ip_to_asn_df)} IP-to-ASN mappings from {csv_path}")

        # Add integer representations of start and end IPs
        ip_to_asn_df['start_ip_int'] = ip_to_asn_df['start_ip'].apply(lambda x: int(ipaddress.ip_address(x)))
        ip_to_asn_df['end_ip_int'] = ip_to_asn_df['end_ip'].apply(lambda x: int(ipaddress.ip_address(x)))

        return ip_to_asn_df
    except FileNotFoundError:
        logger.error(f"CSV file not found: {csv_path}")
        raise
    except Exception as e:
        logger.error(f"Error loading IP-to-ASN mapping CSV: {str(e)}")
        raise

def get_asn(ip: str, ip_to_asn_df: pd.DataFrame) -> int:
    """Get ASN for an IP address using the loaded IP-to-ASN mapping."""
    try:
        ip_int = int(ipaddress.ip_address(ip))
        # Filter rows where the IP falls within the start and end range
        match = ip_to_asn_df[
            (ip_to_asn_df['start_ip_int'] <= ip_int) & (ip_to_asn_df['end_ip_int'] >= ip_int)
        ]
        if not match.empty:
            return match.iloc[0]['asn']  # Return the first matching ASN
        return None  # No match found
    except ValueError:
        logger.warning(f"Invalid IP address: {ip}")
        return None
    except Exception as e:
        logger.error(f"ASN lookup failed for {ip}: {str(e)}")
        return None

def load_cellular_asns(file_path: str) -> set:
    """Load cellular ASNs from text file"""
    try:
        cellular_asns = set()
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and line.isdigit():
                    cellular_asns.add(int(line))
                else:
                    logger.warning(f"Skipping invalid ASN: {line}")
        logger.info(f"Loaded {len(cellular_asns)} cellular ASNs from {file_path}")
        return cellular_asns
    except FileNotFoundError:
        logger.error(f"ASN file not found: {file_path}")
        raise

def process_pcap(pcap_path: str, ipv4_to_asn_df: pd.DataFrame, ipv6_to_asn_df: pd.DataFrame, cellular_asns: set, output_csv: str) -> pd.DataFrame:
    """Process PCAP file and generate features"""
    logger.info(f"Processing {pcap_path}")
    
    # Read PCAP file
    packets = rdpcap(pcap_path)
    
    isIPv6Packet = False
    # Extract features
    data = []
    for pkt in packets:
        if pkt.haslayer(IP):
            ip_layer = pkt[IP]
            data.append({
                'timestamp': pkt.time,
                'src_ip': ip_layer.src,
                'dst_ip': ip_layer.dst,
                'packet_size': len(ip_layer),
                'protocol': ip_layer.proto,
                'ttl': ip_layer.ttl
            })
        elif pkt.haslayer(IPv6):  # Handle IPv6 packets
            ipv6_layer = pkt[IPv6]
            isIPv6Packet = True
            data.append({
                'timestamp': pkt.time,
                'src_ip': ipv6_layer.src,
                'dst_ip': ipv6_layer.dst,
                'packet_size': len(ipv6_layer),
                'protocol': ipv6_layer.nh,  # Next Header field in IPv6
                'ttl': ipv6_layer.hlim,  # Hop Limit in IPv6
                'ip_version': 6  # Indicate it's an IPv6 packet
            })
        else:
            # Handle non-IP packets
            ip_layer = pkt[IP]
            data.append({
                'timestamp': pkt.time,
                'packet_type': type(pkt).__name__,
                'packet_size': len(pkt)
            })
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Add network features
    logger.info("Adding ASN features...")
    if isIPv6Packet:
        df['src_asn'] = df['src_ip'].apply(lambda x: get_asn(x, ipv6_to_asn_df))
        df['dst_asn'] = df['dst_ip'].apply(lambda x: get_asn(x, ipv6_to_asn_df))
    else : 
        df['src_asn'] = df['src_ip'].apply(lambda x: get_asn(x, ipv4_to_asn_df))
        df['dst_asn'] = df['dst_ip'].apply(lambda x: get_asn(x, ipv4_to_asn_df))
    
    # Cellular classification
    df['is_cellular'] = df['src_asn'].isin(cellular_asns).astype(int)
    
    # Save DataFrame to CSV
    logger.info(f"Saving processed data to {output_csv}")
    df.to_csv(output_csv, index=False)

    # Cleanup
    df = df.dropna(subset=['src_asn', 'dst_asn'])
    return df.drop(columns=['src_ip', 'dst_ip'])

# Example usage
if __name__ == "__main__":
    # Load cellular ASNs from file
    CELLULAR_ASN_FILE = '../data_collection/cellular/cellular_asns.txt'  # One ASN per line
    cellular_asns = load_cellular_asns(CELLULAR_ASN_FILE)
    
    # Path to the IP-to-ASN mapping CSV file
    IPv4_TO_ASN_CSV = 'ipv4_to_asn_mapping.csv'  
    IPv6_TO_ASN_CSV = 'ipv6_to_asn_mapping.csv'  
    
    # Load the IP-to-ASN mapping
    ipv4_to_asn_df = load_ip_to_asn_mapping(IPv4_TO_ASN_CSV)
    ipv6_to_asn_df = load_ip_to_asn_mapping(IPv6_TO_ASN_CSV)

    # Process PCAP files
    cellular_traffic = process_pcap('ndt-bmn8w_1738217747_00000000002F0AA5.pcap', ipv4_to_asn_df, ipv6_to_asn_df, cellular_asns, 'traffic.csv')
    wifi_traffic = process_pcap('ndt-9pvq9_1737862997_0000000000BA5BCB.pcap', ipv4_to_asn_df, ipv6_to_asn_df, cellular_asns, 'traffic.csv')
