```c
/* makefile */
src = $(wildcard *.c)
obj = $(patsubst %.c, %, $(src))
CC = gcc
CFLAGES=-Wall -g

all:$(obj)
$(obj):%:%.c
	$(CC) $< -o $@ $(CFLAGES)

.PHONY:clean all
clean:
	-rm -rf $(obj)
```