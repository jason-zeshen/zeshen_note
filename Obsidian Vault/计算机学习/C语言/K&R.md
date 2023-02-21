
7.3的demo：实现一个简单的printf函数
1. 定义变量ap
		va_list ap
2. 将ap初始化为指向第一个无名参数的指针
		va_start(ap,fmt);
3. 最后必须调用va_end，做清理工作
		va_end(ap);
4. 返回一个type类型的的对象，并将指针移动type类型的步长。
		va_arg(ap,type);

```c
#include<stdio.h>
#include<stdarg.h>

/*minprintf函数：带有可变参数表的简化的printf函数*/
void minprintf(char *fmt,...)
{
	va_list ap;
	char *p,*sval;
	int ival;
	double dval;
    
	va_start(ap,fmt);

	for(p=fmt;*p;p++) {
		if(*p!='%'){
			putchar(*p);
			continue;
		}

		switch(*++p) {
            case 'd':
				ival=va_arg(ap,int);
				printf("%d",ival);
				break;
			case 'f':
				dval=va_arg(ap,double);
				printf("%f",dval);
				break;
			case 's':
				for(sval=va_arg(ap,char *);*sval;sval++)
					putchar(*sval);
				break;
			default:
				putchar(*p);
				break;
		}
	}
	va_end(ap);

}


int main()

{   

	int aa=2;
	float bb=3.0;
	char *pp="abcd";

	minprintf("%d\n%f\n%s\n",aa,bb,pp);

	return 0;

}

```