作用：使进程执行某一程序。

int execlp(const char \*file, const char \*arg, ...);		借助 PATH 环境变量找寻待执行程序
	参1： 程序名
	参2： argv0
	参3： argv1
	...： argvN
	哨兵：NULL

int execl(const char \*path, const char \*arg, ...);		自己指定待执行程序路径。