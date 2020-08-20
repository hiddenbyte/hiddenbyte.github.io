---
title: "Digging into Goroutines I"
date: 2020-07-05T23:34:56+01:00
draft: false
---

Go enables writing programs with concurrent threads of execution. And it does so by introducing the concept of _goroutine_.

> A goroutine has a simple model: it is a function executing concurrently with other goroutines in the same address space.
>
> in [Effective Go](https://golang.org/doc/effective_go.html#goroutines "Effective Go")

Before digging into goroutines, having an understanding on "how" the  _Go compiler_ and _runtime_ work together in order to launch a _goroutine_ will pave the path to its internals.

Note: the examples and tools used on this document are based on Go 1.12.9 (darwin/amd64 build).
  
## Launching a goroutine

Launching a _goroutine_ is just as simple as calling a function and can be achieved by writing a "go" statement.

> A "go" statement starts the execution of a function call as an independent concurrent thread of control, or goroutine, within the same address space.
>
> in [The Go Programming Language Specification](https://golang.org/ref/spec#Go_statements "The Go Programming Language Specification")


The source code below - main.go - has a "go" statement declared (at line 9), that launches a goroutine, executing the `heavyWeightChamp` function in a different thread of execution.

```go {linenos=table,hl_lines=[9]}
package main

import (
    "log"
    "time"
)

func main() {
    go heavyWeightChamp("some message")
    time.Sleep(2 * time.Second)
}

func heavyWeightChamp(message string) {
    log.Printf("heavyWeightChamp: Received message '%v'", message)
}
```

The Go compiler turns the "go" statement into a call to the `runtime.newproc`[^1] function. This can be verified by inspecting the application binary using `objdump`[^2] tool as depicted in the script below.

```bash {linenos=table}
go build main.go
go tool objdump main | grep  main.go:9
# Output:
#  main.go:9    0x109659d   c7042410000000      MOVL $0x10, 0(SP)
#  main.go:9    0x10965a4   488d055da10300      LEAQ go.func.*+127(SB), AX
#  main.go:9    0x10965ab   4889442408          MOVQ AX, 0x8(SP)
#  main.go:9    0x10965b0   488d05be410300      LEAQ go.string.*+4341(SB), AX
#  main.go:9    0x10965b7   4889442410          MOVQ AX, 0x10(SP)
#  main.go:9    0x10965bc   48c74424180c000000  MOVQ $0xc, 0x18(SP)
#  main.go:9    0x10965c5   e836a9f9ff          CALL runtime.newproc(SB)
```


The `runtime.newproc` receives as function arguments:

* the size (in bytes) of the arguments of the function launched as a goroutine;
* a reference to the function launched as a goroutine, in this case, a reference to `heavyWeightChamp` function;
* and all the arguments of the function launched as a goroutine.

At this point, we already know "how" the _Go compiler_ and _runtime_ work together to launch a _goroutine_: through the _runtime.newproc_ function.

## runtime.newproc


The `runtime.newproc` function is part of the `runtime` package. Also the function name is "unexported",
which means that it can only be referenced or used inside the `runtime` package and it __only can be called indirectly__ through a "go" statement.


`runtime.newproc` is __responsible for creating a goroutine__, which runs the provided function, and  __placing it in a "waiting to run goroutines" queue.__

## Conclusion

* _goroutines_ are created by calling the `runtime.newproc` function;
* The `runtime.newproc` function can only be called indirectly through a "go" statement, the compiler replaces the statement by a `runtime.newproc` call;
* The `runtime.newproc` creates a _goroutine_ and places in a "waiting to run" queue.


[^1]: [https://golang.org/pkg/runtime/?m=all#newproc](https://golang.org/pkg/runtime/?m=all#newproc)
[^2]: [https://golang.org/cmd/objdump/](https://golang.org/cmd/objdump/)