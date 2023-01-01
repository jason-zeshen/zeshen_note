## 练习1 ：
使用管道实现父子进程间通信，完成：ls | wc –l。假定父进程实现ls，子进程实现wc。
ls命令正常会将结果集写出到stdout，但现在会写入管道的写端；wc –l 正常应该从stdin读取数据，但此时会从管道的读端读。

example 1：
```c
/* pipe_test1.c */
#include <stdio.h>
#include <string.h>
#include <sys/types.h>
#include <unistd.h>
#include <sys/wait.h>

#define _BUF (1024)

int main ()
{
    pid_t pd;
    int ret;
    int pp[2];
  
    ret = pipe(pp);
    if (ret < 0)
        perror("pipe error!!!\n");

    pd = fork();
    if (pd > 0) {                 // parent
        printf("parent process going........\n");
        close(pp[0]); // r->0; w->1

        ret = dup2(pp[1], STDOUT_FILENO);
        if (ret == -1)
            perror("parent dup2 error!!!\n");

        ret = execlp("ls", "ls", NULL);
        if (ret == -1)
            printf("ls ret: %d\n", ret);
    } else if (pd == 0) {         // child process
        printf("chile process going........\n");
        close(pp[1]);
        ret = dup2(pp[0], STDIN_FILENO);
        if (ret == -1)
            perror("child dup2 error!!!\n");
        ret = execlp("wc", "wc", "-l", NULL);
        if (ret == -1)
            perror("wc error!!!\n");
    }

    return 0;

}
```


## 练习2：
使用管道实现兄弟进程间通信。 兄：ls  弟： wc -l  父：等待回收子进程。
要求，使用“循环创建N个子进程”模型创建兄弟进程，使用循环因子i标示。注意管道读写行为。

注意事项！！！！！
管道不支持多个读端和多个写端，别忘记关闭父进程的读写！！
![](/images/兄弟进程间通信.png)

code 1：
```c
#include <stdio.h>
#include <string.h>
#include <sys/types.h>
#include <unistd.h>
#include <sys/wait.h>
#include <errno.h>

#define _BUF (1024)
  
int main ()
{
    pid_t pid;
    int ret, i;
    int pp[2];
  
    ret = pipe(pp);
    if (ret < 0)
        perror("pipe error!!!\n");
  
    for (i = 0; i < 2; i++) {
        pid = fork();
        if (pid > 0) {
            continue;
        } else if (pid == 0) {
            printf("i: %d\n", i);
            if (i == 0){
                printf("i: %d, pid: %d\n", i, getpid());
                close(pp[1]);
                ret = dup2(pp[0], STDIN_FILENO);
                if (ret == -1)
                    perror("child dup2 error!!!\n");
                ret = execlp("wc", "wc", "-l", NULL);
                if (ret == -1)
                    perror("wc error!!!\n");
            }
            if (i == 1) {
                printf("i: %d, pid: %d\n", i, getpid());
                close(pp[0]);
                ret = dup2(pp[1], STDOUT_FILENO);
                if (ret == -1)
                    perror("parent dup2 error!!!\n");
                ret = execlp("ls", "ls", NULL);
                if (ret == -1)
                    printf("ls ret: %d\n", ret);
            }
        }
    }

    if (i == 2) {
        close(pp[0]);
        close(pp[1]);
        while ((ret = wait(NULL)) != -1) {
            printf("回收子进程pid: %d\n", ret);
        }
    }
    return 0;
}
```

code 2:
```c
/* pipe_test2.c */
#include <stdio.h>
#include <string.h>
#include <sys/types.h>
#include <unistd.h>
#include <sys/wait.h>
#include <errno.h>
#define _BUF (1024)

int main ()
{
    pid_t pid;
    int ret, i;
    int pp[2];

    ret = pipe(pp);
    if (ret < 0)
        perror("pipe error!!!\n");

    for (i = 0; i < 2; i++) { // 表达式2为父进程出口
        pid = fork();
        if (pid > 0) {
            continue;
        } else if (pid == 0) { // 子进程出口
            break;
        }
    }

    if (i == 2) {
        close(pp[0]);
        close(pp[1]);
        while ((ret = wait(NULL)) != -1) {
            printf("回收子进程pid: %d\n", ret);
        }
    }

    if (i == 0) {
        printf("i: %d, pid: %d\n", i, getpid());
        close(pp[1]);

        ret = dup2(pp[0], STDIN_FILENO);
        if (ret == -1)
            perror("child dup2 error!!!\n");

        ret = execlp("wc", "wc", "-l", NULL);
        if (ret == -1)
            perror("wc error!!!\n");

    }

    if (i == 1) {
        printf("i: %d, pid: %d\n", i, getpid());
        close(pp[0]);
        ret = dup2(pp[1], STDOUT_FILENO);
        if (ret == -1)
            perror("parent dup2 error!!!\n");
        ret = execlp("ls", "ls", NULL);
        if (ret == -1)
            printf("ls ret: %d\n", ret);
    }

    return 0;
}
```


## 练习3：
测试：是否允许，一个pipe有一个写端，多个读端呢？
是否允许有一个读端多个写端呢？
```c
/* pipe3.c */
```
