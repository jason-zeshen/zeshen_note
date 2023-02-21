

>[思考中rand()函数产生随机数需不需要srand()的发现](https://blog.csdn.net/qq_33961152/article/details/80390861)

在程序中每次调用rand()产生的数字都相同”这是不对的！！

要知道为什么不对，还是先说明一下rand()函数吧，rand()函数是会用系统提供的种子(没有用srand()提供时)或者srand()提供的种子计算出一组随机数，嗯，是一组！而不是一个！！可以把这一组数看做是存储在一个数组里，如果这个数组名字叫做A，那么第一次输出rand()产生的随机数会输出A[0]，第二次输出就是A[1]，以此类推。

所以，因为用种子产生的是一组随机数，所以，在程序中每次调用rand()就是把这个数组中的书一个个显示出来，肯定就是一系列不一样的数。这就解决了我不用srand()也可以产生一组随机数的问题。

大家口中说的“不用srand()每次产生的随机数就一样”，意思是，这一组随机数一样。所以用srand(time(0))来使每次程序执行时的种子不一样，产生的随机数组不一样。

demo
```c
#include <stdio.h>
#include <stdlib.h>
//回调函数
void callback_array(int *array,int  m,int(*getNextRandomValue)(void)){
    int i;
    for(i=0;i<m;i++){
        array[i]=getNextRandomValue();
     }
}
//获取随机值
int getNextRandomValue(void){
    //srand((unsigned)time(NULL));
    return rand();
}
int main(void)
{
    int array[10],i;
    callback_array(array,10,getNextRandomValue);
    for(i=0;i<10;i++){
        printf("%d\n",array[i]);
    }
    printf("\n");
    return 0;
}
```

每次输出都一样，输出：
1804289383
846930886
1681692777
1714636915
1957747793
424238335
719885386
1649760492
596516649
1189641421