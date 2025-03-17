IFACE="wlp0s20f3"  # Change this to your actual network interface

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
        
        tc qdisc add dev $IFACE root handle 1: htb default 10
        tc class add dev $IFACE parent 1: classid 1:1 htb rate $RATE
        tc qdisc add dev $IFACE parent 1:1 handle 10: netem delay $DELAY $JITTER loss $LOSS

    elif [ "$DIRECTION" == "download" ]; then
        echo "Applying ingress shaping (download) on interface: $IFACE..."
        
        # Check if IFB module is loaded, load it if not
	if ! lsmod | grep -q "^ifb "; then
	    echo "Loading IFB kernel module..."
	    sudo modprobe ifb
	fi
	
	# Check if ifb0 exists, create it if not
        if ! ip link show ifb0 &>/dev/null; then
	    echo "Creating ifb0 interface..."
	    sudo ip link add ifb0 type ifb
	fi
	
	# Check if ifb0 is up, bring it up if not
        if [[ $(cat /sys/class/net/ifb0/operstate 2>/dev/null) != "up" ]]; then
	    echo "Bringing up ifb0 interface..."
	    sudo ip link set ifb0 up
	fi
	
	

        tc qdisc add dev $IFACE handle ffff: ingress
        tc filter add dev $IFACE parent ffff: protocol ip u32 match u32 0 0 flowid 1:1 action mirred egress redirect dev ifb0
        tc qdisc add dev ifb0 root handle 1: netem delay $DELAY $JITTER loss $LOSS rate $RATE

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
    tc qdisc del dev $IFACE root 2>/dev/null
    tc qdisc del dev $IFACE ingress 2>/dev/null
    tc qdisc del dev ifb0 root 2>/dev/null
    echo "Traffic shaping removed successfully."
}

# Main logic
if [ "$1" == "start" ]; then
    shift
    start_shaping "$@"
elif [ "$1" == "stop" ]; then
    stop_shaping
else
    echo "Usage: $0 start <upload|download> <rate> <delay> <jitter> <loss>"
    echo "       $0 stop"
    exit 1
fi
