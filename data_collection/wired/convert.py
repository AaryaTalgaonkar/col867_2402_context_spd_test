import pandas as pd
from datetime import datetime

# Read the CSV file
df = pd.read_csv('wired.csv', sep='\t|,', engine='python')

# Prepare the output
output_lines = []
for _, row in df.iterrows():
    machine_site = f"{row['Machine']}-{row['Site']}"
    time_obj = datetime.strptime(row['TestTime'], '%Y-%m-%d %H:%M:%S.%f UTC')
    date = time_obj.strftime('%Y/%m/%d')
    time = time_obj.strftime('%H%M%S')
    line = f"{machine_site},{date},{time},{row['id']}"
    output_lines.append(line)

# Print or save the result
for line in output_lines:
    print(line)

# Optional: save to file
with open("output.csv", "w") as f:
    f.write("Machine,Date,Timestamp,UUID\n")
    for line in output_lines:
        f.write(line + "\n")
