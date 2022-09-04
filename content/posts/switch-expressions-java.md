---
title: "Java: Favor 'switch' expressions over 'if' statements"
date: 2022-09-04T00:12:00+01:00
draft: true
---

If you are a functional programming practitioner or an enthusiast, you might know that **functional programming favors expressions over statements**.

We are unable to use a `if` statement as an expression in Java as we can do in other programming languages, for example, in Kotlin we can use *if expressions*[^2].

- You might be wondering: what about the `?` ternary operator.  
- Alternative to `?` - `switch` expressions

### Factortial function example

`if` statement example

```java {linenos=table}
public static int factorial(int n) {
    int result;
    if (n == 0) {
        result = 1;
    } else {
        result = n * factorial(n-1);
    }
    return result;
}
```


```java {linenos=table}
public static int factorial(int n) {
    if (n == 0) {
        return 1;
    } else {
        return n * factorial(n-1);
    }
}
```

```java {linenos=table}
public static int factorial(int n) {
    return n == 0 ? 1 : n * factorial(n-1);
}
```

```java {linenos=table}
public static int factorial(int n) {
    return switch (n) {
        case 0 -> 1;
        default -> n * factorial(n-1);
    };
}
```


### Switch expressions

Write about switch expressions


### Conclusion



[^1]: [JEP 361: Switch Expressions](https://openjdk.org/jeps/361)
[^2]: [Kotlin - if expression](https://kotlinlang.org/docs/control-flow.html#if-expression)