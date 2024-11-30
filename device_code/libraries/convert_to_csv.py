import sys
import csv
import re

def convert_to_csv(top_log_path, csv_output_path):
    try:
        with open(top_log_path, "r") as top_log, open(csv_output_path, "w", newline="") as csv_file:
            csv_writer = csv.writer(csv_file)
            
            # Write header
            csv_writer.writerow(["Time", "PID", "USER", "PR", "NI", "VIRT", "RES", "SHR", "S", "%CPU", "%MEM", "TIME+", "COMMAND"])
            
            # Process each line in the top log
            for line in top_log:
                # Match lines with data
                match = re.match(r'^(\d+:\d+:\d+)\s+(\d+|all)\s+([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)\s+(.*)$', line)
                if match:
                    csv_writer.writerow(match.groups())
        print(f"CSV file successfully created: {csv_output_path}")
    except Exception as e:
        print(f"Error: {e}")

# Entry point for the script
if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python convert_to_csv.py <top_log_path> <csv_output_path>")
        sys.exit(1)
    
    top_log_path = sys.argv[1]
    csv_output_path = sys.argv[2]
    convert_to_csv(top_log_path, csv_output_path)
