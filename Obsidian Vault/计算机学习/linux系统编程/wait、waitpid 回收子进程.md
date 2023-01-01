## wait
作用：
	回收子进程，防止僵尸进程和孤儿进程

特性：
	① 阻塞等待子进程退出
	② 回收子进程残留资源
	③ 获取子进程结束状态(退出原因)。example 2
	
-------------------
example 1：
```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/wait.h> 

#define CHIID_TIME (10)
#define PARENT_TIME (20)

int main ()
{
    pid_t pid, wpid;
    int i, status;
    pid = fork();
    if (pid == 0) {
        for (i = 0; i < CHIID_TIME; i++)
        {
            printf("child(ppid: %d;pid: %d) process going\n", getppid(), getpid());
            sleep(1);
        }
        printf("child die================================\n");

    } else {
        wpid = wait(&status); // 在此阻塞，直到子进程退出
        printf("wpid = %d, status: %d\n", wpid, status);
        for (i = 0; i < PARENT_TIME; i++)
        {
            printf("parent(ppid: %d;pid: %d) process going\n", getppid(), getpid());
            sleep(1);
        }
        printf("parent die================================\n");
    }

    return 0;

}
```



example 2, 获取子进程退出值和异常终止信号: 
```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/wait.h>

#define CHIID_TIME (10)
#define PARENT_TIME (20)

int main ()
{
    pid_t pid, wpid;
    int i, status;
    pid = fork();
    if (pid == 0) {
        for (i = 0; i < CHIID_TIME; i++)
        {
            printf("child(ppid: %d;pid: %d) process going\n", getppid(), getpid());
            sleep(1);
        }
        printf("child die================================\n");
        return 1213; // 子进程传出值
    } else {
        wpid = wait(&status); // status：子进程返回值
        printf("wpid = %d, status: %d\n", wpid, status);
        
        if (WIFEXITED(status)) { // true：子进程正常终止。
            printf("child process exit with %d\n", WEXITSTATUS(status));
        }

        if (WIFSIGNALED(status)) { // 获取使进程终止的信号的编号
            printf("child process signled with %d\n", WTERMSIG(status));
        }

        printf("parent die================================\n");
    }

    return 0;
}
```



## waitpid
pid_t waitpid(pid_t pid, int \*status, int options)
input：
	pid: 
		>0: 待回收的子进程pid号
		-1: 任意子进程
		0: 同组的子进程
		-pid：待回收的进程组号。加负号表示此pid为组号
	status：
		（传出）回收进程的状态，可为NULL；
	options：
		WNOHANG 指定回收方式为非阻塞。
			返回值：
				pid号：回收成功时返回子进程pid
				0：回收失败时返回0
output:
	>0: 回收成功，返回子进程pid
	0：函数调用时，参数3指定为WNOHANG,并且没有子进程结束
	-1：失败，erro


case 1，回收子进程，如果子进程没有结束则立即返回：
	wpid = waitpid(ppid, NULL, WNOHANG);  // ppid为待回收的子进程的pid号
	返回值：
		0：子进程尚未结束，回收失败
		> 0: 子进程pid号，回收成功


```c
/* waitpid.c */

/* 回收子进程3 */
#include <stdio.h>
#include <string.h>
#include <sys/types.h>
#include <unistd.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/wait.h>

int main (int argc, char *argv[])
{
    pid_t pid, ppid, wpid;
    int i;
    for (i = 0; i < 4; i++) {
        pid = fork();
        if (pid == 0) {
            // printf("son: pid(%d) = %d, i = %d\n", pid, getpid(), i);
            if (i == 2){
                printf("son %d\n", i);
                sleep(1);
                printf("son finish %d\n", i);
            }
            break;
        }
        if (i == 2) {
            ppid = pid;
        }
        printf("parent: pid(%d) = %d, i = %d\n", pid, getpid(), i);
    }
    if (i == 4) {
        sleep(3);
        // wpid = waitpid(ppid, NULL, 0); // 回收指定pid的子进程
        wpid = waitpid(ppid, NULL, WNOHANG); //
        printf("end ===== ppid = %d\n", ppid);
        printf("end ===== wpid = %d\n", wpid);
    }

    return 0;
}
```


## 总结
wait、waitpid 一次调用只能回收一个子进程，想回收多个可用while语句
```c
pid_t pid;
while((pid = wait(NULL) != -1)) {
	
}
```

```c
pid_t pid;
while((pid = waitpid(-1, NULL, 0) != -1)) {
	
}
```

```c
for (i = 0; i < n; i++) { // 回收n个子进程
	wait(NULL);
}
```