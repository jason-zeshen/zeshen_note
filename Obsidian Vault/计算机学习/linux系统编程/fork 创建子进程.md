返回值：
	父进程得到子进程的pid号，子进程得到0。


example 1：创建4个子进程。
```c
#include <stdio.h>
#include <string.h>
#include <sys/types.h>
#include <unistd.h>
#include <stdlib.h>

int main (int argc, char *argv[])
{
    pid_t pid;
    int i;
    for (i = 0; i < 4; i++) {
        pid = fork();
        // if (pid == 0) // 父->子子子子
        if (pid > 0) // 父->子->子->子->子 
            break;
        // sleep(i);
        printf("pid(%d) = %d, i = %d\n", pid, getpid(), i);
    }

    if (i == 0) { // 父pid is 0 or 4+1
        sleep(3);
        printf("end ===== pid = %d\n", getpid());
    }
  
    return 0;

}
```

