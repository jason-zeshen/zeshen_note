## 管道
管道是一种最基本的IPC机制。

![](/images/管道原理图.png)


实现原理：内核借助环形队列机制，借助内核缓冲区(4k)实现。
大小：4k
特质：
	1. 伪文件；
	2. 管道中的数据只能一次读取；
	3. 数据在管道中只能单向流动。
局限性：
	1. 自己写，不能自己读；
	2. 数据不可以反复读（因为借助了环形队列机制）；
	3. 半双工通信；
	4. 血缘关系进程间可用。


### 查看缓冲区大小
命令： ulimit –a
查看pipe size的值

### 管道的读写行为
读管道：
	1. 管道有数据，read返回实际读到的字节数
	2. 管道无数据：1）无写端，read返回0（类似读到文件尾）
								2）有写端，read阻塞等待
写管道：
		1. 无读端，异常终止。（SIGPIPE导致的）
		2. 有读端：1）管道已满，阻塞等待
							2）管道未满，返回写入的字节个数

### 管道的优劣

优点：简单，相比信号，套接字实现进程间通信，简单很多。
缺点：1. 只能单向通信，双向通信需建立两个管道。
	      2. 只能用于父子、兄弟进程(有共同祖先)间通信。该问题后来使用fifo有名管道解决




## pipe
pip函数：
	int pipe(int fd[2])
	参数： fd\[0\]: 读端
				fd\[1\]: 写端
	返回值：
				0： 成功
				-1：失败

![](/images/管道通信.png)


example1，父进程写字符串，子进程读取字符串并打印到终端:
```c
/* pipe.c */
#include <stdio.h>
#include <string.h>
#include <sys/types.h>
#include <unistd.h>
#include <sys/wait.h>

#define _BUF (1024)
  
int main ()
{
    pid_t pd;
    int ret, rd_size;
    char buf[_BUF];
    int pp[2];
    
    ret = pipe(pp);
    if (ret < 0)
        perror("pipe error!!!\n");

    pd = fork();
    if (pd > 0) {                 // parent
        char *str = "THIS IS PIPE!!!\n";
        close(pp[0]); // 0: r; 1: w
        write(pp[1], str,strlen(str));
        close(pp[1]);
        wait(NULL);
    } else if (pd == 0) { // child process
        close(pp[1]);
        rd_size = read(pp[0], buf, sizeof(buf));
        write(STDOUT_FILENO, buf, rd_size);
        close(pp[0]);
    }

    return 0;
}
