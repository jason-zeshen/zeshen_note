kill命令和kill函数：
- description:
	send a signal to a process
- int kill(pid_t pid, int signum);
- 参数：
	- pid：
		\> 0: 发送信号给指定进程。
		= 0: 发送信号给与调用kill函数的那个进程处于同一进程组的进程。
		< -1: 取绝对值后，发送信号给该绝对值对应的进程组的所有组员。
		= -1: 发送信号给所有有权限发送的进程。
	- signum：待发送的信号。

demo 1， kill命令：
> kill -9 <pid号>
> 使用信号宏：
> kill -SIGKILL <pid号>

demo 2, 循环创建5个子进程，父进程用kill函数终止任一子进程:
【kill.c】
```c
/* kill.c */


```