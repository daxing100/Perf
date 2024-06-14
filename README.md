# Perf

android执行命令：

python3 android/androidPerf.py --package_name com.*.* --interval 3 --duration 30
到达duration时间后测试结束

测试报告：
![android_perf.png](android_perf.png)


ios执行命令：

执行前先修改dealData文件中cpu_data.append(float(cpu_match.group(1)) / x), x为测试机器的CPU核数

sudo python3 ios/ios17Perf.py --bundle_id tv.danmaku.bilianime --udid 00008101-00185468217A001E
ctrl+c结束测试，结束后等待报告生成

测试报告：
![ios_17+_perf.png](ios_17%2B_perf.png)


