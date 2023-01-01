映射
void \*mmap(void \*addr, size_t length, int prot, int flags, int fd, off_t offset); 创建共享内存映射
	参数：
			addr: 指定映射区的首地址。通常传NULL，表示让系统自动分配
			length：共享内存映射区的大小。（<=文件的实际大小）
			prot: 共享内存映射区的读写属性。PROT_READ、PROT_WRITE、PROT_READ | PROT_WRITE
			flags: 标注共享内存的共享属性。MAP_SHARED、MAP_PRIVATE
			fd: 用于创建共享内存映射区的那个文件的文件描述符
			offset: 偏移位置。默认0，表示映射文件全部。需要时4K的整倍数。
	返回值：
			成功：映射区的首地址
			失败：MAP_FAILED (void \*) -1, errno

释放
int munmap(void \*addr, size_t length);	
	addr: mmap的返回值
	length：大小

注意事项：





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
