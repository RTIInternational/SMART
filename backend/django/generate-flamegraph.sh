#!/bin/bash

# Create output directory if it doesn't exist
output_dir="/var/log/flamegraphs"
mkdir -p "$output_dir"

# Initialize counter for flamegraphs
flamegraph_count=0

# Loop through all memray_*.bin files in /var/log
for file in /var/log/memray_*.bin; do
    # Check if file exists (to handle the case where no files match the pattern)
    if [ -f "$file" ]; then
        filename=$(basename "$file")
        output_file="${output_dir}/${filename%.bin}_flamegraph.svg"
        
        echo "Generating flamegraph for $filename..."
        
        # Run memray flamegraph command with output file specified
        memray flamegraph "$file" -o "$output_file"
        
        echo "Flamegraph saved to $output_file"
        
        ((flamegraph_count++))
    fi
done

echo "Total flamegraphs generated: $flamegraph_count"