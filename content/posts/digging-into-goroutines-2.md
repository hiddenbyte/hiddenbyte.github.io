---
title: "Digging Into Goroutines II"
date: 2020-08-20T23:50:33+01:00
draft: true
---

The previous post, [Digging Into Goroutines I](https://mehul.pt/posts/digging-into-goroutines-1/), explained "how" the _Go compiler_ and _runtime_ work together to launch a _goroutine_.

This post will try to answer the question: __How a _goroutine_ is scheduled to be executed after being launched or created?__

The runtime component that is responsible to schedule a _goroutine_ for execution is the _Go Scheduler_.

### Go Scheduler

The _Go Scheduler_ has three main concepts:

* __Goroutine__;
* __Worker thread__;
* and the __Processor__.

lorem lorem lorem lorem lorem lorem lorem lorem lorem 
lorem lorem lorem lorem lorem lorem lorem lorem lorem 

![Go scheduler concepts relation](/images/go-sched-concepts.png)

lorem lorem lorem lorem lorem lorem lorem lorem lorem 
lorem lorem lorem lorem lorem lorem lorem lorem lorem 