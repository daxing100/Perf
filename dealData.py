import re
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

# 从文件中读取数据
with open('data.txt', 'r') as file:
    lines = file.readlines()

# 提取 CPU、Memory 和 FPS 的信息
cpu_data = []
memory_data = []
fps_data = []
jank_data = []
big_jank_data = []
time_data = []

for line in lines:
    if 'currentTime' in line:
        time_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+)', line)
        if time_match:
            current_time = datetime.strptime(time_match.group(1), '%Y-%m-%d %H:%M:%S.%f')
            time_data.append(current_time)

    if 'CPU' in line:
        cpu_match = re.search(r'CPU\': \'([\d.]+) %\'', line)
        if cpu_match:
            # 6代表取测试设备CPU核数
            cpu_data.append(float(cpu_match.group(1)) / 6)

    if 'Memory' in line:
        memory_match = re.search(r'Memory\': \'([\d.]+) MiB\'', line)
        if memory_match:
            memory_data.append(float(memory_match.group(1)) * 1.0486)

    if 'fps' in line:
        fps_match = re.search(r'\'fps\': (\d+)', line)
        if fps_match:
            fps_data.append(float(fps_match.group(1)))

    if 'jankCount' in line:
        jank_match = re.search(r'\'jankCount\': (\d+)', line)
        if jank_match:
            jank_data.append(jank_match.group(1))

    if 'bigJankCount' in line:
        big_jank_match = re.search(r'\'bigJankCount\': (\d+)', line)
        if big_jank_match:
            big_jank_data.append(big_jank_match.group(1))

# 确保所有数据的长度相同
min_length = min(len(time_data), len(cpu_data), len(memory_data), len(fps_data), len(jank_data), len(big_jank_data))
time_data = time_data[:min_length]
cpu_data = cpu_data[:min_length]
memory_data = memory_data[:min_length]
fps_data = fps_data[:min_length]
jank_data = jank_data[:min_length]
big_jank_data = big_jank_data[:min_length]

# 绘制图表
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10))

# 绘制 CPU 和内存使用率
ax1.plot(time_data, cpu_data, marker='o', color='tab:blue', label='CPU Usage')
ax1.plot(time_data, memory_data, marker='o', color='tab:red', label='Memory Usage')

ax1.set_xlabel('Time')
ax1.set_ylabel('Usage')
ax1.tick_params(axis='y')
ax1.legend(loc='best')

last_annotated_time = time_data[0] - timedelta(seconds=5)  # 初始化为数据开始前5秒

for i in range(len(time_data)):
    if time_data[i] >= last_annotated_time + timedelta(seconds=5):
        ax1.annotate(f'{cpu_data[i]:.2f}', (time_data[i], cpu_data[i]), textcoords="offset points", xytext=(0, 10),
                     ha='center', color='tab:blue', fontsize=6)
        ax1.annotate(f'{memory_data[i]:.2f}', (time_data[i], memory_data[i]), textcoords="offset points", xytext=(0, 10),
                     ha='center', color='tab:red', fontsize=5)
        last_annotated_time = time_data[i]

# 绘制 FPS、Jank 和 bigJank
ax2.plot(time_data, fps_data, marker='o', color='tab:green', label='FPS')
ax2.plot(time_data, jank_data, marker='o', color='tab:orange', label='Jank')
ax2.plot(time_data, big_jank_data, marker='o', color='tab:purple', label='BigJank')

ax2.set_xlabel('Time')
ax2.set_ylabel('Count')
ax2.tick_params(axis='y')
ax2.legend(loc='best')

last_annotated_time = time_data[0] - timedelta(seconds=5)  # 初始化为数据开始前5秒

for i in range(len(time_data)):
    if time_data[i] >= last_annotated_time + timedelta(seconds=5):
        ax2.annotate(f'{fps_data[i]:.0f}', (time_data[i], fps_data[i]), textcoords="offset points", xytext=(0, -20),
                     ha='center', color='tab:green')
        ax2.annotate(f'{jank_data[i]}', (time_data[i], jank_data[i]), textcoords="offset points", xytext=(0, 10),
                     ha='center', color='tab:orange')
        ax2.annotate(f'{big_jank_data[i]}', (time_data[i], big_jank_data[i]), textcoords="offset points",
                     xytext=(0, -10),
                     ha='center', color='tab:purple')
        last_annotated_time = time_data[i]

plt.suptitle('IOS 17+ Perf')
plt.xticks(rotation=90)
plt.grid(True)

plt.tight_layout(rect=(0, 0, 1, 0.96))
plt.savefig('usage_over_time.png')
