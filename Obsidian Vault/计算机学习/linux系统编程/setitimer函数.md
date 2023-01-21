## 函数介绍
int setitimer(int which, const struct itimerval *new_value, struct itimerval *old_value);
- 入参：
	- which：
		- ITIMER_REAL： 采用自然计时。 ——> SIGALRM
		- TIMER_VIRTUAL: 采用用户空间计时  ---> SIGVTALRM
		- ITIMER_PROF: 采用内核+用户空间计时 ---> SIGPROF
	- new_value，定时秒数
- 传出参数：
	- old_value，上次剩余时间。
- 返回值：
	- 0: 成功
	- -1： error


## 练习
1. 使用setitimer函数实现alarm函数，重复计算机1秒数数程序。				【setitimer_alarm.c】
2. 结合man page编写程序，测试it_interval、it_value这两个参数的作用。	【setitimer_cycle.c】
提示：	it_interval：用来设定两次定时任务之间间隔的时间。
	 			it_value：定时的时长				
两个参数都设置为0，即清0操作。

