## function description
name:
	map or unmap files or devices into memory

void \*mmap(void \*addr, size_t length, int prot, int flags, int fd, off_t offset); 创建共享内存映射
	参数：
			addr: 指定映射区的首地址。通常传NULL，表示让系统自动分配
			length：共享内存映射区的大小。代表将文件中多大的部分映射到内存。（<=文件的实际大小）
			prot: 共享内存映射区的读写属性。PROT_READ、PROT_WRITE、PROT_READ | PROT_WRITE
			flags: 标注共享内存的共享属性。MAP_SHARED、MAP_PRIVATE
			fd: 用于创建共享内存映射区的那个文件的文件描述符
			offset: 偏移位置。默认0，表示映射文件全部。需要时4K的整倍数。
	返回值：
			成功：映射区的首地址
			失败：MAP_FAILED (void \*) -1, errno

释放
int munmap(void \*addr, size_t length);	
	Input：
		addr: mmap的返回值
		length：大小
	Output:
		0: err
		1: success

![]()
![](/images/存储映射.png)
mmap函数入参比较多，所以出错概率比较高。注意事项，各种报错及其原因：
	1.  bus err：总线错误
		文件大小为0，但是length不为0.
	2. Invalid argument
		文件大小为0，length也为0.
	3. ……

mmap函数保险的调用用法：
	1.  fd = open("文件名", 0_RDWR);
	2. mmap(NULL, 有效文件大小, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);

无血缘进程间通信可以用fifo、mmap，它们的区别：
mmap：数据可以重复读取。
fifo：数据只能一次读取。

匿名映射：
	只能用于血缘关系进程间通信。

example, 内存共享映射实例：
```c
/* mmap.c */
#include <stdio.h>
#include <string.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <sys/mman.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/types.h>

int main ()
{
    int fd;
    int len, ret;
    char *mp_str = NULL;
    // 创建文件
    fd = open("mmap.test", O_RDWR | O_CREAT | O_TRUNC, 0644);
    // 拓展文件大小
    ftruncate(fd, 20);
    len = lseek(fd, 0, SEEK_END);

    //内存共享映射
    mp_str = mmap(NULL, len, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    if (mp_str == MAP_FAILED) {
        perror("mmap err!!\n");
        exit(1);
    }

	// 写入文件
    strcpy(mp_str, "hello mmap!\n");
	
	// 释放映射区
    ret = munmap(mp_str, len);
    if (ret == -1) {
        perror("mumap err!!\n");
        exit(1);
    }
    return 0;
}
```


## 父子进程 mmap进程通信


## 无血缘关系mmap进程通信

