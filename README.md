# mesi-simulator
A MESI cache coherence protocol simulator written in Python3 to illustrate how the protocol works on a block of cache.

Written for a master's Multicore Computing class.
## Project Description:
The goal in this project is to implement the MESI cache coherence protocol in your favorite
programming language (such C, C++, Java, etc.). How the protocol works and state transitions on the protocol
can be found in the required reading part of Lecture 4 (in Blackboard).The Wikipedia also has a high level
description on the protocol.  Consider only one level of cache which is a write back cache.
Moreover, assume that there are 4 processing cores working on a single shared memory. 
To simplify, assume that you are writing the code for only one block of cache and that block can hold 4 different memory locations.