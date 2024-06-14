import re
import json
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

# 从文件中读取数据
def dealData(file):
    cpu_data = []
    memory_data = []
    fps_data = []
    jank_data = []
    big_jank_data = []
    time_data = []
    with open(file, 'r') as file:
        for line in file:
            data = json.loads(line.strip())
            # 提取时间点
            current_time = data.get("currentTime", None)
            if current_time:
                current_time = datetime.strptime(current_time, '%Y-%m-%d %H:%M:%S.%f')
                time_data.append(current_time)

            # 提取CPU信息
            cpu = data.get("CPU", None)
            if cpu:
                cpu_match = re.search(r'([\d.]+) %', cpu)
                if cpu_match:
                    # 假设6代表测试设备的CPU核数
                    cpu_data.append(float(cpu_match.group(1)) / 6)

            # 提取内存信息
            memory = data.get("Memory", None)
            if memory:
                memory_match = re.search(r'([\d.]+) MiB', memory)
                if memory_match:
                    memory_data.append(float(memory_match.group(1)))

            # 提取FPS信息
            fps = data.get("fps", None)
            if fps is not None:
                fps_data.append(fps)

            # 提取jankCount信息
            jank_count = data.get("jankCount", None)
            if jank_count is not None:
                jank_data.append(jank_count)

            # 提取bigJankCount信息
            big_jank_count = data.get("bigJankCount", None)
            if big_jank_count is not None:
                big_jank_data.append(big_jank_count)

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

    last_annotated_time = time_data[0] - timedelta(seconds=2)  # 初始化为数据开始前5秒

    for i in range(len(time_data)):
        if time_data[i] >= last_annotated_time + timedelta(seconds=2):
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

    for i in range(len(time_data)):
        if time_data[i] >= last_annotated_time + timedelta(seconds=2):
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
    plt.savefig('ios_17+_perf.png')

if __name__ == '__main__':
    dealData(file='../data.txt')
