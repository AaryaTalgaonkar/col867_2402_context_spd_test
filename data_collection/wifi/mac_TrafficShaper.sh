#!/bin/bash

IFACE="en0"  

# Function to apply traffic shaping
start_shaping() {
    if [ "$#" -ne 5 ]; then
        echo "Usage: $0 start <upload|download> <rate> <delay> <jitter> <loss>"
        exit 1
    fi

    DIRECTION=$1
    RATE=$2
    DELAY=$3
    JITTER=$4
    LOSS=$5

    # Remove previous shaping rules
    stop_shaping

    if [ "$DIRECTION" == "upload" ]; then
        echo "Applying egress shaping (upload) on interface: $IFACE..."
        
        sudo pfctl -E
        sudo pfctl -f /etc/pf.conf
        echo "dummynet out quick on en0 pipe 1" | sudo pfctl -a com.apple.internet-sharing -f -
        sudo pfalt pipe 1 config bw $RATE delay $DELAY jitter $JITTER loss $LOSS 
        
        

    elif [ "$DIRECTION" == "download" ]; then
        echo "Applying ingress shaping (download) on interface: $IFACE..."
        
        sudo pfctl -E
        sudo pfctl -f /etc/pf.conf
        echo "dummynet in quick on en0 pipe 2" | sudo pfctl -a com.apple.internet-sharing -f -
        sudo pfalt pipe 2 config bw $RATE delay $DELAY jitter $JITTER loss $LOSS 

    else
        echo "Invalid option: Use 'upload' or 'download'"
        exit 1
    fi

    echo "Traffic shaping applied on $IFACE for $DIRECTION with:
        - Bandwidth: $RATE
        - Delay: $DELAY ± $JITTER
        - Packet Loss: $LOSS"
}

# Function to remove traffic shaping
stop_shaping() {
    echo "Stopping traffic shaping on $IFACE..."
    sudo pfctl -F all  # Flush all PF rules
    sudo pfatl -q flush  # Clear all dummynet rules
    echo "Traffic shaping removed successfully."
}

# Main logic
if [ "$1" == "start" ]; then
    shift
    start_shaping "$@"
elif [ "$1" == "stop" ]; then
    stop_shaping
else
    echo "Usage: $0 start <upload|download> <rate>"
    echo "       $0 stop"
    exit 1
fi
