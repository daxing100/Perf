import argparse
import datetime
import time as ti

import matplotlib.pyplot as plt
import tidevice
from tidevice._perf import DataType


# 连接设备
t = tidevice.Device()
perf = tidevice.Performance(t, [
    DataType.CPU,
    DataType.MEMORY,
    DataType.FPS
])

# 用于存储数据
cpu_data = []
memory_data = []
fps_data = []

# 用于计算Jank和Big Jank的数据
frame_times = []
jank_count = [0]
big_jank_count = [0]
jank_data = []
big_jank_data = []


def calculate_jank(current_fps):
    if current_fps == 0:
        return
    current_frame_time = 1 / current_fps * 1000
    frame_times.append(current_frame_time)

    if len(frame_times) > 3:
        frame_times.pop(0)

    if len(frame_times) == 3:
        avg_frame_time = sum(frame_times) / len(frame_times)
        movie_frame_time_2x = 1000 / 24 * 2
        movie_frame_time_3x = 1000 / 24 * 3

        if current_frame_time > avg_frame_time * 2 and current_frame_time > movie_frame_time_2x:
            jank_count[0] += 1

        if current_frame_time > avg_frame_time * 2 and current_frame_time > movie_frame_time_3x:
            big_jank_count[0] += 1


def callback(_type: tidevice.DataType, value: dict):
    timestamp = ti.time()
    formatted_time = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
    if _type == DataType.CPU:
        cpu_data.append((formatted_time, value))  # 存储格式化后的时间和值
    elif _type == DataType.MEMORY:
        memory_data.append((formatted_time, value))
    elif _type == DataType.FPS:
        fps_data.append((formatted_time, value))
        calculate_jank(value['value'])
        jank_data.append((formatted_time, jank_count[0]))
        big_jank_data.append((formatted_time, big_jank_count[0]))

def main(bundle_id, duration, interval):
    # 连接设备
    t = tidevice.Device()
    perf = tidevice.Performance(t, [
        DataType.CPU,
        DataType.MEMORY,
        DataType.FPS
    ])

    end_time = ti.time() + duration
    perf.start(bundle_id, callback=callback)
    while ti.time() < end_time:
        ti.sleep(int(interval))
    perf.stop()

    # 将数据分别提取出来用于绘图
    cpu_times, cpu_values = zip(*cpu_data)
    memory_times, memory_values = zip(*memory_data)
    fps_times, fps_values = zip(*fps_data)
    jank_times, jank_values = zip(*jank_data)
    big_jank_times, big_jank_values = zip(*big_jank_data)

    # 创建一个新的图形和网格
    fig, axs = plt.subplots(2, 1, figsize=(24, 12))

    # CPU使用率和内存使用量
    ax1 = axs[0]
    ax1.set_xlabel('Time')
    ax1.set_ylabel('CPU Usage', color='blue')
    ax1.plot(cpu_times, [v['value'] for v in cpu_values], label='CPU Usage', color='blue')
    ax1.tick_params(axis='y', labelcolor='blue')

    for i, (time, value) in enumerate(zip(cpu_times, cpu_values)):
        if i % 2 == 0:
            ax1.text(time, value['value'], f"{round((value['value'] / 6), 2)}", color='blue', fontsize=8, ha='center',
                     va='bottom')

    # 为内存使用创建第二个 y 轴
    ax2 = ax1.twinx()
    ax2.set_ylabel('Memory Usage', color='orange')
    ax2.plot(memory_times, [v['value'] for v in memory_values], label='Memory Usage', color='orange')
    ax2.tick_params(axis='y', labelcolor='orange')

    for i, (time, value) in enumerate(zip(memory_times, memory_values)):
        if i % 3 == 0:
            ax2.text(time, value['value'], f"{round(value['value'], 2)}", color='orange', fontsize=8, ha='center',
                     va='bottom')

    # 合并图例
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
    # 标题
    ax1.set_title('CPU and Memory Usage Over Time')

    # 第二个图：FPS、Jank 和 Big Jank
    ax3 = axs[1]
    ax3.set_xlabel('Time')
    ax3.set_ylabel('FPS and Jank', color='green')
    ax3.plot(fps_times, [v['value'] for v in fps_values], label='FPS', color='green')
    ax3.plot(jank_times, jank_values, label='Jank Count', color='red')
    ax3.plot(big_jank_times, big_jank_values, label='Big Jank Count', color='purple')
    ax3.tick_params(axis='y', labelcolor='green')

    # 添加数据标记
    for i, (time, value) in enumerate(zip(fps_times, fps_values)):
        if i % 2 == 0:
            ax3.text(time, value['value'], f"{value['value']}", color='green', fontsize=8, ha='center', va='bottom')

    for i, (time, value) in enumerate(zip(jank_times, jank_values)):
        if i % 3 == 0:
            ax3.text(time, value, f"{value}", color='red', fontsize=8, ha='center', va='bottom')

    for i, (time, value) in enumerate(zip(big_jank_times, big_jank_values)):
        if i % 2 == 0:
            ax3.text(time, value, f"{value}", color='purple', fontsize=8, ha='center', va='bottom')

    # 合并图例
    lines3, labels3 = ax3.get_legend_handles_labels()
    ax3.legend(lines3, labels3, loc='upper left')

    # 标题
    ax3.set_title('FPS, Jank and Big Jank Over Time')

    plt.subplots_adjust()
    plt.savefig("ios_perf.png")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='IOS Performance Analyzer')
    parser.add_argument('--bundle_id', dest='bundle_id', type=str, help='Bundle_id of test app')
    parser.add_argument('--duration', dest='duration', type=int, help='Duration of the test in seconds')
    parser.add_argument('--interval', dest='interval', type=int, help='interval of the test in seconds')

    args = parser.parse_args()
    bundle_id = args.bundle_id
    duration = args.duration
    interval = args.interval
    main(bundle_id, duration, interval)
