import re
import matplotlib.pyplot as plt

# 从文件中读取数据
with open('data.txt', 'r') as file:
    lines = file.readlines()

# 提取 CPU、Memory 和 FPS 的信息
cpu_data = []
memory_data = []
fps_data = []
time_data = []

for line in lines:
    if 'currentTime' in line:
        time_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+)', line)
        if time_match:
            current_time = time_match.group(1)
            time_data.append(current_time)

    if 'CPU' in line:
        cpu_match = re.search(r'CPU\': \'([\d.]+) %\'', line)
        if cpu_match:
            cpu_data.append(float(cpu_match.group(1)))

    if 'Memory' in line:
        memory_match = re.search(r'Memory\': \'([\d.]+) MiB\'', line)
        if memory_match:
            memory_data.append(float(memory_match.group(1)))

    if 'fps' in line:
        fps_match = re.search(r'\'fps\': (\d+)', line)
        if fps_match:
            fps_data.append(float(fps_match.group(1)))

# 绘制图表
fig, ax1 = plt.subplots(figsize=(10, 6))

ax1.plot(time_data, cpu_data, marker='o', color='tab:blue', label='CPU Usage')
ax1.plot(time_data, memory_data, marker='o', color='tab:red', label='Memory Usage')
ax1.set_xlabel('Time')
ax1.set_ylabel('Usage (%)')
ax1.tick_params(axis='y')
ax1.legend(loc='upper left')

ax2 = ax1.twinx()
ax2.plot(time_data, fps_data, marker='o', color='tab:green', label='FPS')
ax2.set_ylabel('FPS')
ax2.tick_params(axis='y')
ax2.legend(loc='upper right')

plt.title('CPU, Memory, and FPS Usage Over Time')
plt.xticks(rotation=45)
plt.grid(True)

plt.tight_layout()
plt.show()
