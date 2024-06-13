参考： https://gitcode.com/15525730080/iOS17_perf/overview?utm_source=csdn_github_accelerator&isLogin=1


# ios17Perf

修改iosPerf文件

bundle_id = "Your App BundleId" // t3 app list

udid = "Your IPhone UDID" //t3 list

修改dealData文件中cpu_data.append(float(cpu_match.group(1)) / x), x为测试机器的CPU核数

Jank计算参考PerfDog
![img.png](img.png)
