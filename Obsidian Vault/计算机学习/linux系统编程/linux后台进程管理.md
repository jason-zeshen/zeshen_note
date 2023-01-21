> [Linux后台进程管理以及ctrl+z（挂起）、ctrl+c（中断）、ctrl+\（退出）和ctrl+d（EOF）的区别](https://www.cnblogs.com/jiangzhaowei/p/8971265.html)

一、后台进程管理命令

fg、bg、jobs、&、ctrl + z、ctrl + c、ctrl + \、ctrl + d
1、 &
加在一个命令的最后，可以把这个命令放到后台执行 ,如gftp &,
2、ctrl + z
可以将一个正在前台执行的命令放到后台，并且处于暂停状态，不可执行
3、jobs
查看当前有多少在后台运行的命令
jobs -l选项可显示所有任务的PID，jobs的状态可以是running, stopped, Terminated,但是如果任务被终止了（kill），shell 从当前的shell环境已知的列表中删除任务的进程标识；也就是说，jobs命令显示的是当前shell环境中所起的后台正在运行或者被挂起的任务信息；
4、fg
将后台中的命令调至前台继续运行
如果后台中有多个命令，可以用 fg %jobnumber将选中的命令调出，%jobnumber是通过jobs命令查到的后台正在执行的命令的序号(不是pid)
5、bg
将一个在后台暂停的命令，变成继续执行 （在后台执行）
如果后台中有多个命令，可以用bg %jobnumber将选中的命令调出，%jobnumber是通过jobs命令查到的后台正在执行的命令的序号(不是pid)
将任务转移到后台运行：
先ctrl + z；再bg，这样进程就被移到后台运行，终端还能继续接受命令。
概念：当前任务
如果后台的任务号有2个，[1],[2]；如果当第一个后台任务顺利执行完毕，第二个后台任务还在执行中时，当前任务便会自动变成后台任务号码“[2]” 的后台任务。所以可以得出一点，即当前任务是会变动的。当用户输入“fg”、“bg”和“stop”等命令时，如果不加任何引号，则所变动的均是当前任务

二、进程的终止
后台进程的终止：
方法一：
通过jobs命令查看job号（假设为num），然后执行kill %num
方法二：
通过ps命令查看job的进程号（PID，假设为pid），然后执行kill pid
前台进程的终止：
ctrl+c

三、进程的挂起（暂停的意思吧）
后台进程的挂起：
在solaris中通过stop命令执行，通过jobs命令查看job号(假设为num)，然后执行stop %num；
在redhat中，不存在stop命令，可通过执行命令kill -stop PID，将进程挂起；
当要重新执行当前被挂起的任务时，通过bg %num 即可将挂起的job的状态由stopped改为running，仍在后台执行；当需要改为在前台执行时，执行命令fg %num即可；
前台进程的挂起：
ctrl+Z;

 

四、kill的其他作用
kill除了可以终止进程，还能给进程发送其它信号，使用kill -l 可以察看kill支持的信号。
SIGTERM是不带参数时kill发送的信号，意思是要进程终止运行，但执行与否还得看进程是否支持。如果进程还没有终止，可以使用kill -SIGKILL pid，这是由内核来终止进程，进程不能监听这个信号。

 

五、ctrl+z（挂起）、ctrl+c（中断）、ctrl+\（退出）和ctrl+d（EOF）的区别

 

1、四种操作的表现

ctrl+c强行中断当前程序的执行。
ctrl+z将任务中断,但是此任务并没有结束,他仍然在进程中，只是放到后台并维持挂起的状态。如需其在后台继续运行，需用“bg 进程号”使其继续运行；再用"fg 进程号"可将后台进程前台化。

ctrl+\\ 表示退出。

ctrl+d表示结束当前输入（即用户不再给当前程序发出指令），那么Linux通常将结束当前程序。

2、ctrl+c,ctrl+d,ctrl+z在linux中意义。

linux下：
ctrl-c 发送 SIGINT 信号给前台进程组中的所有进程。常用于终止正在运行的程序。
ctrl-z 发送 SIGTSTP 信号给前台进程组中的所有进程，常用于挂起一个进程。
ctrl-d 不是发送信号，而是表示一个特殊的二进制值，表示 EOF。
ctrl-\ 发送 SIGQUIT 信号给前台进程组中的所有进程，终止前台进程并生成 core 文件。

Key Function
Ctrl-c Kill foreground process
Ctrl-z Suspend foreground process
Ctrl-d Terminate input, or exit shell
Ctrl-s Suspend output
Ctrl-q Resume output
Ctrl-o Discard output
Ctrl-l Clear screen
