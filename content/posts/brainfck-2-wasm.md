---
title: "From Brainfuck to WebAssembly"
date: 2021-03-29T21:50:33+01:00
draft: true
---

This post attempts to illustrate the basic aspects of a compiler, using the **bf-wasm**[^1] compiler as an example; and also share some of the design decisions I took while implementing **bf-wasm**.

### bf-wasm

bf-wasm is a Braincfuck compiler targeting WebAssembly. Written in Go.

> bf-wasm compiles Brainfuck source code from the standard input into a WASM module. The  WASM module is written to the standard ouput. The WASM module is written in WebAssembly  text format.
>
> in [bf-wasm README](https://github.com/hiddenbyte/bf-wasm/blob/main/README.md "README")

#### Brainfuck
TBW

#### WebAssembly
TBW

### Compiler Design (HIGH LEVEL)
Lexical analysis -- Token --> Semantic analysis -- AST --> Emit

### Lexical analysis
TBW

#### Tokenization
TBW

### Semantic analysis
TBW

### WASM
TBW

[^1]: [https://github.com/hiddenbyte/bf-wasm](https://github.com/hiddenbyte/bf-wasm)