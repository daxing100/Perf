import argparse
import re
import subprocess
import time

import matplotlib.pyplot as plt


def get_pid(package_name):
    output = subprocess.getoutput(f"adb shell pidof {package_name}")
    return output.strip()


"""
CPU Usage(Normalized)：规范化CPU利用率
由于移动设备CPU频率时刻变化，用传统CPU利用率计算方法，假定在低频率时刻计算出CPU利用率=30%，和在CPU高频时刻计算出CPU利用率=30%。
同样都是30%但性能消耗是完全不样的，明显高频消耗更高。传统CPU利用率已无法真实反映性能消耗。
所以我们需要一种规范化(可量化)的统计方式。将频率因素考虑进去。
CPU Usage(Normalized)=(CPU执行时间/CPU总时间) * (当前时刻所有CPU频率之和/所有CPU频率最大值之和)。
"""


def get_cpu_times(pid):
    stat_output = subprocess.getoutput(f"adb shell cat /proc/{pid}/stat")
    stat_fields = stat_output.split()
    try:
        utime = int(stat_fields[13])
        stime = int(stat_fields[14])
        cutime = int(stat_fields[15])
        cstime = int(stat_fields[16])
        total_time = utime + stime + cutime + cstime
    except (ValueError, IndexError) as e:
        print(f"Error parsing /proc/{pid}/stat: {e}")
        total_time = 0
    return total_time


def get_total_cpu_time():
    stat_output = subprocess.getoutput("adb shell cat /proc/stat")
    cpu_line = stat_output.splitlines()[0]
    cpu_fields = cpu_line.split()[1:]
    total_time = sum(int(field) for field in cpu_fields)
    return total_time


def get_current_cpu_freq_sum():
    freq_output = subprocess.getoutput("adb shell 'cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_cur_freq'")
    freqs = [int(freq) for freq in freq_output.split()]
    return sum(freqs)


def get_max_cpu_freq_sum():
    max_freq_output = subprocess.getoutput("adb shell 'cat /sys/devices/system/cpu/cpu*/cpufreq/cpuinfo_max_freq'")
    max_freqs = [int(freq) for freq in max_freq_output.split()]
    return sum(max_freqs)


def calculate_normalized_cpu_usage(prev_times, current_times, max_freq_sum):
    delta_proc_time = current_times['proc'] - prev_times['proc']
    delta_total_time = current_times['total'] - prev_times['total']
    current_freq_sum = current_times['freq']

    if delta_total_time == 0:
        return 0.0

    cpu_usage = (delta_proc_time / delta_total_time) * (current_freq_sum / max_freq_sum)
    return cpu_usage


"""
PSS Memory，统计结果和Android Java API标准结果一
"""


def get_memory_usage(package_name):
    # Run adb shell dumpsys meminfo <package_name> | grep 'TOTAL'
    command = f"adb shell dumpsys meminfo {package_name} | grep 'TOTAL'"
    try:
        meminfo_output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
        # Example output line: "    TOTAL       3455     3404      442      123     3404      123"
        if meminfo_output:
            # Extract the PSS memory value
            match = re.search(r'TOTAL\s+(\d+)\s+\d+\s+\d+\s+\d+\s+\d+\s+\d+\s+\d+', meminfo_output.decode('utf-8'))
            if match:
                pss_memory_kb = int(match.group(1))
                pss_memory_mb = pss_memory_kb / 1024  # Convert from KB to MB
                return pss_memory_mb
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
    return 0


def get_realtime_fps():
    output = subprocess.getoutput("adb shell dumpsys SurfaceFlinger --latency")  # 获取的数值时间单位为纳秒

    frame_times_ns = []
    for line in output.splitlines():
        try:
            frame_time_ns = int(line.strip())
            frame_times_ns.append(frame_time_ns)
        except ValueError:
            continue

    if not frame_times_ns:
        return None

    avg_frame_time_ns = sum(frame_times_ns) / len(frame_times_ns)
    avg_frame_time_s = avg_frame_time_ns / 1e9  # 纳秒单位转为秒
    fps = 1 / avg_frame_time_s
    return fps, frame_times_ns


"""
Jank计算方法：
1.      同时满足以下两条件，则认为是一次卡顿Jank.
a)      当前帧耗时>前三帧平均耗时2倍。
b)      当前帧耗时>两帧电影帧耗时(1000ms/24*2=84ms)。
2.      同时满足两条件，则认为是一次严重卡顿BigJank.
a)      当前帧耗时>前三帧平均耗时2倍。
b)      当前帧耗时>三帧电影帧耗时(1000ms/24*3=125ms)。
"""


def calculate_jank_and_bigjank(frame_times_ns):
    # 定义电影帧时间（单位：纳秒）
    movie_frame_time_ns = 1000 / 24 * 1e6  # ms to ns
    two_movie_frames_ns = 2 * movie_frame_time_ns  # 84ms in ns
    three_movie_frames_ns = 3 * movie_frame_time_ns  # 125ms in ns

    jank_count = 0
    big_jank_count = 0

    for i in range(3, len(frame_times_ns)):
        current_frame_time_ns = frame_times_ns[i]
        previous_frame_times_ns = [frame_times_ns[i - 1], frame_times_ns[i - 2], frame_times_ns[i - 3]]
        average_previous_time_ns = sum(previous_frame_times_ns) / 3

        if current_frame_time_ns > 2 * average_previous_time_ns:
            if current_frame_time_ns > two_movie_frames_ns:
                jank_count += 1
            if current_frame_time_ns > three_movie_frames_ns:
                big_jank_count += 1

    return jank_count, big_jank_count


def plot_data(cpu_data, memory_data, fps_data, jank_data, big_jank_data):
    timestamps, cpu_values = zip(*cpu_data)
    _, mem_values = zip(*memory_data)
    _, fps_values = zip(*fps_data)
    _, jank_values = zip(*jank_data)
    _, big_jank_values = zip(*big_jank_data)

    # 创建一个宽度为12英寸，高度为6英寸的图形
    plt.figure(figsize=(24, 6))

    # 左图：CPU和内存数据
    plt.subplot(1, 2, 1)
    plt.plot(timestamps, [val * 100 for val in cpu_values], label='CPU Usage (%)', color='g', marker='s')
    plt.plot(timestamps, mem_values, label='Memory Usage (MB)', color='r', marker='^')

    for i, txt in enumerate(cpu_values):
        if i % 2 == 0:  # 每隔一个点展示一次数值
            plt.annotate(f'{txt:.2%}', (timestamps[i], cpu_values[i] * 100), textcoords="offset points", xytext=(0, 10),
                         ha='center')
    for i, txt in enumerate(mem_values):
        if i % 2 == 0:  # 每隔一个点展示一次数值
            plt.annotate(f'{txt:.2f}', (timestamps[i], mem_values[i]), textcoords="offset points", xytext=(0, 10),
                         ha='center')

    plt.xlabel('Time')
    plt.ylabel('Value')
    plt.title('CPU and Memory Usage Over Time')
    plt.xticks(rotation=45)
    plt.legend()

    # 右图：FPS、Jank和BigJank数据
    plt.subplot(1, 2, 2)
    plt.plot(timestamps, fps_values, label='FPS', color='b', marker='o')
    plt.plot(timestamps, jank_values, label='Jank Count', color='m', marker='x')
    plt.plot(timestamps, big_jank_values, label='BigJank Count', color='y', marker='d')

    for i, txt in enumerate(fps_values):
        if i % 2 == 0:  # 每隔一个点展示一次数值
            plt.annotate(f'{txt:.2f}', (timestamps[i], fps_values[i]), textcoords="offset points", xytext=(0, -10),
                         ha='center')
    for i, txt in enumerate(jank_values):
        if i % 2 == 0:  # 每隔一个点展示一次数值
            plt.annotate(f'{txt}', (timestamps[i], jank_values[i]), textcoords="offset points", xytext=(0, 10),
                         ha='center')
    for i, txt in enumerate(big_jank_values):
        if i % 2 == 0:  # 每隔一个点展示一次数值
            plt.annotate(f'{txt}', (timestamps[i], big_jank_values[i]), textcoords="offset points", xytext=(0, -15),
                         ha='center')

    plt.xlabel('Time')
    plt.ylabel('Value')
    plt.title('FPS, Jank and BigJank Over Time')
    plt.xticks(rotation=45)
    plt.legend()

    # 保存和展示图像
    plt.tight_layout()
    plt.savefig("android_perf.png")


def main(duration, interval, package_name):
    print("开始监控...")
    end_time = time.time() + duration

    pid = get_pid(package_name)
    if not pid:
        print("无法找到进程ID")
        return

    max_freq_sum = get_max_cpu_freq_sum()

    cpu_data = []
    memory_data = []
    fps_data = []
    jank_data = []
    big_jank_data = []

    prev_times = {
        'proc': get_cpu_times(pid),
        'total': get_total_cpu_time(),
        'freq': get_current_cpu_freq_sum()
    }

    while time.time() < end_time:
        time.sleep(int(interval))

        current_times = {
            'proc': get_cpu_times(pid),
            'total': get_total_cpu_time(),
            'freq': get_current_cpu_freq_sum()
        }

        cpu_usage = calculate_normalized_cpu_usage(prev_times, current_times, max_freq_sum)
        memory_usage = get_memory_usage(package_name)
        timestamp = time.strftime('%H:%M:%S')
        cpu_data.append((timestamp, cpu_usage))
        memory_data.append((timestamp, memory_usage))
        fps, frame_times_ns = get_realtime_fps()
        fps_data.append((timestamp, int(fps)))
        if frame_times_ns is not None:
            jank_count, big_jank_count = calculate_jank_and_bigjank(frame_times_ns)
            jank_data.append((timestamp, jank_count))
            big_jank_data.append((timestamp, big_jank_count))
        else:
            jank_count, big_jank_count = 0, 0

        print(
            f"{timestamp} - CPU Usage: {cpu_usage:.2%}, Memory Usage: {memory_usage:.2f} MB, FPS: {int(fps)}, "
            f"Jank: {jank_count}, BigJank: {big_jank_count}")

        prev_times = current_times

    plot_data(cpu_data, memory_data, fps_data, jank_data, big_jank_data)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Performance Analyzer')
    parser.add_argument('--package_name', dest='package_name', type=str, help='package of the application')
    parser.add_argument('--interval', dest='interval', type=str, help='interval of data')
    parser.add_argument('--duration', dest='duration', type=int, help='Duration of the test in seconds')

    args = parser.parse_args()
    package_name = args.package_name
    interval = args.interval
    duration = args.duration

    main(duration, interval, package_name)
