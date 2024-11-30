import sys
import csv
import re
from collections import defaultdict

def convert_mpstat_to_csv(mpstat_log_path, csv_output_path, include_all_columns=True):
    try:
        with open(mpstat_log_path, "r") as mpstat_log:
            # Dictionary to store data by timestamp
            data = defaultdict(dict)
            cpu_columns = set()

            for line in mpstat_log:
                # Match lines with CPU data
                match = re.match(
                    r'^\s*(\d+:\d+:\d+)\s+([a-zA-Z0-9]+)\s+([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)',
                    line
                )
                if match:
                    # Extract data
                    time, cpu, usr, nice, sys, iowait, irq, soft, steal, guest, gnice, idle = match.groups()
                    data[time][cpu] = {
                        "%usr": float(usr),
                        "%sys": float(sys),
                        "%idle": float(idle),
                    }
                    if include_all_columns:
                        data[time][cpu].update({
                            "%nice": float(nice),
                            "%iowait": float(iowait),
                            "%irq": float(irq),
                            "%soft": float(soft),
                            "%steal": float(steal),
                            "%guest": float(guest),
                            "%gnice": float(gnice),
                        })
                    cpu_columns.add(cpu)

            # Sort CPUs and timestamps
            cpu_columns = sorted(cpu_columns)
            timestamps = sorted(data.keys())

            # Write to CSV
            with open(csv_output_path, "w", newline="") as csv_file:
                csv_writer = csv.writer(csv_file)

                # Write interlaced header
                metrics = ["%usr", "%sys", "%idle"]
                if include_all_columns:
                    metrics += ["%nice", "%iowait", "%irq", "%soft", "%steal", "%guest", "%gnice"]
                header = ["Time"] + [f"CPU {cpu} {metric}" for metric in metrics for cpu in cpu_columns]
                csv_writer.writerow(header)

                # Write rows
                for time in timestamps:
                    row = [time]
                    for metric in metrics:
                        for cpu in cpu_columns:
                            row.append(data[time].get(cpu, {}).get(metric, 0))  # Append metric value or 0 if missing
                    csv_writer.writerow(row)

        print(f"CSV file successfully created: {csv_output_path}")

    except Exception as e:
        print(f"Error: {e}")

# Entry point for the script
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python convert_mpstat_to_csv.py <mpstat_log_path> <csv_output_path> [include_all_columns=True]")
        sys.exit(1)

    mpstat_log_path = sys.argv[1]
    csv_output_path = sys.argv[2]
    include_all_columns = sys.argv[3].lower() == "true" if len(sys.argv) > 3 else True
    convert_mpstat_to_csv(mpstat_log_path, csv_output_path, include_all_columns)
