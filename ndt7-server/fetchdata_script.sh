#!/bin/bash

# Set start and end dates (YYYYMMDD format)
START_DATE="20250301"
END_DATE="20250308"

# Ensure the data directory exists
mkdir -p data

# Loop through each date in the range
current_date="$START_DATE"
while [[ "$current_date" -le "$END_DATE" ]]; do
    echo "Processing date: $current_date"

    # Construct the GCS path for the current date
    GCS_PATH="gs://archive-measurement-lab/ndt/pcap/${current_date:0:4}/${current_date:4:2}/${current_date:6:2}/"

    # List the first 5 files for the current date and save them
    gsutil ls "$GCS_PATH" 2>/dev/null | head -n 5 >> folders.txt

    # Move to the next day
    current_date=$(date -d "$current_date + 1 day" +"%Y%m%d")
done

# Download all collected files into the "data" directory
cat folders.txt | xargs -I {} -P 10 gsutil -m cp "{}" data/

echo "Download complete!"
