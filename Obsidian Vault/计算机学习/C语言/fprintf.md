描述
	C 库函数 int fprintf(FILE \*stream, const char \*format, ...) 发送格式化输出到流 stream 中。
声明
	int fprintf(FILE \*stream, const char \*format, ...)

demo 1
```c
#include <stdio.h>
#include <stdlib.h>

int main()
{
	char *str = "hello!!\n";

   fprintf(stdout, "show str: %s", str);
   
   return(0);
}
```

demo 2
```c
#include <stdio.h>
#include <stdlib.h>

int main()
{
   FILE * fp;

   fp = fopen ("file.txt", "w+");
   fprintf(fp, "%s %s %s %d", "We", "are", "in", 2014);
   
   fclose(fp);
   
   return(0);
}
```

和printf()的区别：
