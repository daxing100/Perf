# Perf

android执行命令：

python3 android/androidPerf.py --package_name com.*.* --interval 3 --duration 30


ios执行命令：
修改dealData文件中cpu_data.append(float(cpu_match.group(1)) / x), x为测试机器的CPU核数
sudo python3 ios/ios17Perf.py --bundle_id tv.danmaku.bilianime --udid 00008101-00185468217A001E




