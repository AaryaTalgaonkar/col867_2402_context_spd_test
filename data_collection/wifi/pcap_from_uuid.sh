# CSV file containing the data
CSV_FILE="shaping.csv"
METADATA_DIR="metadata"
TEMP_DIR="temp"
PCAP_DIR="my_pcaps"

# Ensure the metadata directory exists
mkdir -p "$METADATA_DIR"

echo "Starting metadata processing..."
echo ""

# Read the CSV line by line, skipping the header
awk -F, 'NR>1' "$CSV_FILE" | while IFS=, read -r MACHINE DATE TIMESTAMP UUID; do
    echo "Processing entry: MACHINE=$MACHINE, DATE=$DATE, TIMESTAMP=$TIMESTAMP, UUID=$UUID"
    
    # Convert date format from YYYY/MM/DD to YYYYMMDD
    FORMATTED_DATE=$(echo "$DATE" | sed 's,/,,g')
    FILE_LIST="$METADATA_DIR/${FORMATTED_DATE}.txt"
    
    # Check if the file already exists
    if [[ -f "$FILE_LIST" ]]; then
        echo "$FILE_LIST already exists. Skipping..."
        echo ""
        continue
    fi
    
    # Create the file
    touch "$FILE_LIST"
    echo "Created $FILE_LIST"
    
    # Construct GCS path
    GCS_PATH="gs://archive-measurement-lab/ndt/pcap/${FORMATTED_DATE:0:4}/${FORMATTED_DATE:4:2}/${FORMATTED_DATE:6:2}/"
    
    # List files and save output
    echo "Fetching file list from $GCS_PATH..."
    gsutil ls "$GCS_PATH" >> "$FILE_LIST" 2>/dev/null || echo "Failed to fetch list for $FORMATTED_DATE"
    echo "Fetched file list for $FORMATTED_DATE into $FILE_LIST"
    echo ""
done

echo "Metadata processing complete."
echo ""

# Ensure the temp directory and PCAP directory exist
mkdir -p "$PCAP_DIR"

echo "Starting file processing..."
echo ""

# Read the CSV line by line, skipping the header
awk -F, 'NR>1' "$CSV_FILE" | while IFS=, read -r MACHINE DATE TIMESTAMP UUID; do
    echo "Processing entry: MACHINE=$MACHINE, DATE=$DATE, TIMESTAMP=$TIMESTAMP, UUID=$UUID"
    
    # Convert date format from YYYY/MM/DD to YYYYMMDD
    FORMATTED_DATE=$(echo "$DATE" | sed 's,/,,g')
    FILE_LIST="$METADATA_DIR/${FORMATTED_DATE}.txt"
    
    # Ensure metadata file exists
    if [[ ! -f "$FILE_LIST" ]]; then
        echo "Metadata file $FILE_LIST does not exist. Skipping..."
        continue
    fi


    rm -rf "$TEMP_DIR"
    mkdir -p "$TEMP_DIR"
    

    # Find first 3 matching filenames after the given timestamp containing the machine name
    MATCHING_FILES=$(grep "$MACHINE" "$FILE_LIST" | awk -F'[T.]' -v ts="$TIMESTAMP" '$2>=ts' | sort | head -n 5)
    
    located=0  # Initialize as not found
    # Process each matching file
    for FILE in $MATCHING_FILES; do
        echo "Processing $FILE..."
        
        # Download the file to TEMP_DIR
        gsutil cp "$FILE" "$TEMP_DIR/" 2>/dev/null || { echo "Failed to download $FILE"; continue; }
        

        BASE_NAME=$(basename "$FILE" .tgz)
        EXTRACT_DIR="$TEMP_DIR/$BASE_NAME"
        mkdir -p "$EXTRACT_DIR"
        tar -xzf "$TEMP_DIR/$(basename "$FILE")" -C "$EXTRACT_DIR" 2>/dev/null || { echo "Failed to extract $FILE"; continue; }

        # Locate the day directory directly inside TEMP_DIR
        BASE_NAME=$(basename "$FILE" .tgz)
        DAY_DIR="$TEMP_DIR/$BASE_NAME/$DATE"
        
        
        for ARCHIVE in "$DAY_DIR"/*; do
            UUID=$(echo -n "$UUID" | tr -d '\r')
            if [[ "$ARCHIVE" == *"$UUID"* ]]; then
                echo "Found matching UUID in $ARCHIVE"
                echo ""
                gunzip -c "$ARCHIVE" > "$PCAP_DIR/$(basename "$ARCHIVE" .gz)" 2>/dev/null || echo "Extraction failed for $ARCHIVE"
                located=1
                break
            fi
        done
        if [[ $located -eq 1 ]]; then
            break
        fi
    done
done

rm -rf "$TEMP_DIR"
# rm -rf "$METADATA_DIR"
echo "Processing complete."
