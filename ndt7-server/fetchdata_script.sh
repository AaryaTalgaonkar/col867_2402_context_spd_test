#!/bin/bash

# Set start and end dates (YYYYMMDD format)
START_DATE="20250301"
END_DATE="20250308"
NUM_FILES=5  # Number of files to select per day
FILE_LIST="file_paths.txt"  # Output file storing selected file paths
DATA_DIR="data"  # Directory where files will be downloaded

# Ensure the data directory exists
mkdir -p "$DATA_DIR"
> "$FILE_LIST"  # Ensure it's empty before appending

# Loop through each date in the range
current_date="$START_DATE"

while [[ "$current_date" -le "$END_DATE" ]]; do
    echo "Selecting $NUM_FILES files for date: $current_date"

    # Construct the GCS path for the current date
    GCS_PATH="gs://archive-measurement-lab/ndt/pcap/${current_date:0:4}/${current_date:4:2}/${current_date:6:2}/"

    # List all files, shuffle them randomly, then select the configured number of files
    gsutil ls "$GCS_PATH" 2>/dev/null | shuf | head -n "$NUM_FILES" >> "$FILE_LIST"

    # Move to the next day
    current_date=$(date -d "$current_date + 1 day" +"%Y%m%d")
done

# Download all collected files into the specified data directory
cat "$FILE_LIST" | xargs -I {} -P 10 gsutil -m cp "{}" "$DATA_DIR/"

echo "Download complete!"

# Delete the file list after downloads are complete
rm -f "$FILE_LIST"
