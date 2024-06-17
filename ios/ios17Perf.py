# -*- coding: utf-8 -*-
"""
sudo python3 iosPerf.pt > data.txt
"""

import argparse
import dataclasses
import json
import os
import platform
import re
import subprocess
import sys
import threading
import time
import argparse
import json
from datetime import datetime

from ios_device.cli.base import InstrumentsBase
from ios_device.cli.cli import print_json
from ios_device.remote.remote_lockdown import RemoteLockdownClient
from ios_device.util.utils import convertBytes
from dealData import dealData

cpu_data = []
memory_data = []
time_data = []
fps_data = []
jank_data = []
big_jank_data = []

class TunnelManager:
    def __init__(self):
        self.start_event = threading.Event()
        self.tunnel_host = None
        self.tunnel_port = None

    def get_tunnel(self):
        def start_tunnel():
            rp = subprocess.Popen([sys.executable, "-m", "pymobiledevice3", "remote", "start-tunnel"],
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT)
            while not rp.poll():
                try:
                    line = rp.stdout.readline().decode()
                except:
                    print("decode fail {0}".format(line))
                    continue
                line = line.strip()
                if line:
                    print(line)
                if "--rsd" in line:
                    ipv6_pattern = r'--rsd\s+(\S+)\s+'
                    port_pattern = r'\s+(\d{1,5})\b'
                    self.tunnel_host = re.search(ipv6_pattern, line).group(1)
                    self.tunnel_port = int(re.search(port_pattern, line).group(1))
                    self.start_event.set()

        threading.Thread(target=start_tunnel).start()
        self.start_event.wait(timeout=15)


class PerformanceAnalyzer:
    def __init__(self, udid, host, port):
        self.udid = udid
        self.host = host
        self.port = port

    def ios17_proc_perf(self, bundle_id):
        """
        获取应用程序性能数据
        Args:
            bundle_id (str): 应用程序的Bundle ID
        """
        # 定义要提取的进程属性字段
        proc_filter = ['Pid', 'Name', 'CPU', 'Memory', 'DiskReads', 'DiskWrites', 'Threads']
        # 创建一个数据类以存储系统进程属性
        process_attributes = dataclasses.make_dataclass('SystemProcessAttributes', proc_filter)

        def on_callback_proc_message(res):
            """
            处理来自sysmontap的进程消息回调
            Args:
                res (object): 包含进程信息的回调结果对象
            """
            if isinstance(res.selector, list):
                for index, row in enumerate(res.selector):
                    if 'Processes' in row:
                        for _pid, process in row['Processes'].items():
                            attrs = process_attributes(*process)
                            # 如果指定了应用程序名称，但当前进程不匹配，则跳过
                            if name and attrs.Name != name:
                                continue
                            if not attrs.CPU:
                                attrs.CPU = 0
                            # 转换CPU、内存、磁盘读写数据的单位
                            attrs.CPU = f'{round(attrs.CPU, 2)} %'
                            attrs.Memory = convertBytes(attrs.Memory)
                            attrs.DiskReads = convertBytes(attrs.DiskReads)
                            attrs.DiskWrites = convertBytes(attrs.DiskWrites)
                            print_json(attrs.__dict__, format)
                            # 将数据写入文件
                            data = {
                                "CPU": str(attrs.CPU),
                                "Memory": str(attrs.Memory),
                            }
                            with open('data.txt', 'a') as f:
                                f.write(json.dumps(data) + '\n')

        # 使用RemoteLockdownClient连接到远程设备服务
        with RemoteLockdownClient((self.host, self.port)) as rsd:
            # 使用InstrumentsBase设置连接属性
            with InstrumentsBase(udid=self.udid, network=False, lockdown=rsd) as rpc:
                # 指定要获取的进程属性
                rpc.process_attributes = ['pid', 'name', 'cpuUsage', 'physFootprint',
                                          'diskBytesRead', 'diskBytesWritten', 'threadCount']
                # 如果指定了应用程序的Bundle ID，则获取应用程序的可执行名称
                if bundle_id:
                    app = rpc.application_listing(bundle_id)
                    if not app:
                        print(f"not find {bundle_id}")
                        return
                    name = app.get('ExecutableName')
                rpc.sysmontap(on_callback_proc_message, 1000)

    def ios17_fps_perf(self):
        """
        获取设备FPS并计算Jank和BigJank的数据
        """
        jank_count = [0]
        big_jank_count = [0]
        frame_times = []
        fps_data = []
        jank_data = []
        big_jank_data = []

        def on_callback_fps_message(res):
            nonlocal jank_count, big_jank_count, frame_times, fps_data, jank_data, big_jank_data
            data = res.selector
            # 获取当前帧率
            current_fps = data['CoreAnimationFramesPerSecond']
            now = datetime.now()
            if current_fps == 0:
                # 如果帧率为0，则帧时间为无穷大
                frame_time = float('inf')
            else:
                # 计算每帧的时间（毫秒）
                frame_time = 1 / current_fps * 1000
            frame_times.append(frame_time)
            if len(frame_times) > 3:
                # 如果列表超过3个元素，则移除第一个，保持最新的3个帧时间
                frame_times.pop(0)
            if len(frame_times) == 3:
                avg_frame_time = sum(frame_times) / len(frame_times)
                movie_frame_time = 1000 / 24 * 2  # 24 FPS视频的两帧时间
                # 判断是否出现普通卡顿
                if frame_time > avg_frame_time * 2 and frame_time > movie_frame_time:
                    jank_count[0] += 1
                # 判断是否出现严重卡顿
                if frame_time > avg_frame_time * 2 and frame_time > 1000 / 24 * 3:  # 24 FPS视频的三帧时间
                    big_jank_count[0] += 1

            fps_data.append(current_fps)
            jank_data.append(jank_count[0])
            big_jank_data.append(big_jank_count[0])
            data = {
                "currentTime": str(now),
                "fps": current_fps,
                "jankCount": jank_count[0],
                "bigJankCount": big_jank_count[0]
            }
            # 数据写入文件
            with open('data.txt', 'a') as f:
                f.write(json.dumps(data) + '\n')

        with RemoteLockdownClient((self.host, self.port)) as rsd:
            with InstrumentsBase(udid=self.udid, network=False, lockdown=rsd) as rpc:
                rpc.graphics(on_callback_fps_message, 1000)

def convert_memory_usage(memory_str):
    if ' MiB' in memory_str:
        return float(memory_str.replace(' MiB', '').replace(',', ''))
    elif ' KiB' in memory_str:
        return float(memory_str.replace(' KiB', '').replace(',', '')) / 1024
    else:
        raise ValueError(f"Unexpected memory format: {memory_str}")

if __name__ == '__main__':

    if "Windows" in platform.platform():
        import ctypes

        assert ctypes.windll.shell32.IsUserAnAdmin() == 1, "必须使用管理员权限启动"
    else:
        assert os.geteuid() == 0, "必须使用sudo权限启动"
    if os.path.exists('data.txt') and os.path.getsize('data.txt') > 0:
        os.remove('data.txt')

    parser = argparse.ArgumentParser(description='Performance Analyzer')
    parser.add_argument('--bundle_id', dest='bundle_id', type=str, help='Bundle ID of the application')
    parser.add_argument('--udid', dest='udid', type=str, help='UDID of the device')
    args = parser.parse_args()
    bundle_id = args.bundle_id
    udid = args.udid

    tunnel_manager = TunnelManager()
    tunnel_manager.get_tunnel()
    performance_analyzer = PerformanceAnalyzer(udid, tunnel_manager.tunnel_host, tunnel_manager.tunnel_port)
    threading.Thread(target=performance_analyzer.ios17_proc_perf, args=(bundle_id,)).start()
    time.sleep(0.1)
    threading.Thread(target=performance_analyzer.ios17_fps_perf, args=()).start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Interrupted. Plotting graphs...")
        dealData('data.txt')



