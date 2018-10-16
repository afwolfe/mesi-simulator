# mesi-simulator
A MESI cache coherence protocol simulator written in Python to illustrate how the protocol works on a single block of cache.

Written for a master's Multicore Computing class.

## Usage
Run: `python mesi.py`

It will by default run 10 random instructions on the simulator and display the results.

Tested against Python 3, but should work in Python 2 as well. It only uses the built-in `logging` and `random` libraries.

## Project Description:
The goal in this project is to implement the MESI cache coherence protocol in your favorite programming language (such C, C++, Java, etc.).

Consider only one level of cache which is a write back cache.
Moreover, assume that there are 4 processing cores working on a single shared memory. 
To simplify, assume that you are writing the code for only one block of cache and that block can hold 4 different memory locations.