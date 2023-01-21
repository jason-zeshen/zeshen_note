概念：
- 会话(session)是一个或多个进程组的集合。

创建一个会话需要注意以下6点注意事项：
1. 调用进程不能是进程组组长，该进程变成新会话首进程(session header)
2. 该进程成为一个新进程组的组长进程。
3. 需有root权限 (ubuntu不需要)
4. 新会话丢弃原有的控制终端，该会话没有控制终端
5. 该调用进程是组长进程，则出错返回
6. (重要！)__建立新会话时，先调用fork, 父进程终止，子进程调用setsid__

demo 1，创建会话，并且打印创建前后的pid，ppid，pgid，sid。
注意，如果parent process先结束，则child process调用getppid返回1。
```c
/* session.c */
#include<stdio.h>
#include<stdlib.h>
#include <unistd.h>

void pid_printf()
{
    printf("Child_pid(%d); ", getpid());
    printf("Parent_pid(%d); ", getppid());
    printf("Group_pid(%d); ", getpgid(0));
    printf("Session_pid(%d)\n", getsid(0));
}

int main()
{
    pid_t pid;

    pid = fork();
    if (pid < 0) {
        perror("fork error!");
        exit(1);
    }else if (pid == 0) { // child process
        pid_printf();
        setsid(); // creates a session
        printf("===== creates a new session =====\n");
        pid_printf();

    }else if (pid > 0) { // parent process
        sleep(3);
    }

    return 0;
}
```

