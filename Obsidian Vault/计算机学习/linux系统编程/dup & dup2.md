【重定向】
复制一个文件描述符
duplicate a file descriptor

dup(inf oldfd)
	返回一个新的文件描述符。
	int newfd = dup(int oldfd);
	
dup2(int oldfd, int new newfd); 
	成功：返回一个新文件描述符；失败：-1设置errno为相应值
	成功后新旧fd同时指向oldfd指向的文件

example：
```c
int fd;
fd = open("文件路径", O_RDWR | O_CREAT | O_TRUNC, 0644); // 0 表示8进制
execlp("date", "date", NULL);
```


