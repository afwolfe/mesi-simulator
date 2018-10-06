#!/usr/bin/env python3
"""
    Name:   mesi.py
    Author: Alex Wolfe
    Desc:   Main file for a MESI cache simulator in Python.
"""
from random import randint

def contains_valid_state(status):
    return ('M' in status) or ('E' in status) or ('S' in status)

class Mesi:
    """
    Main MESI simulator class. Can be seen as the chip that contains all of the Processors, Bus, and Memory.
    """

    def __init__(self):
        """
        Initializes bus, memory, and processors.
        """

        # Create a dict of Processors p0 through p3

        self.memory = Memory()
        self.bus = Bus(self.memory)

        self.processors = {}
        for x in range(4):
            self.processors[x] = Processor(self.bus, self.memory)

    def instruction(self, processor, r_w, address):
        """
        Performs the specified request in the cache.

        :param processor: processor number
        :param r_w: 0 for read 1 for write
        :param address: address to access
        :return: The result of the specified operation.
        """
        if r_w is 0:
            return self.processors[processor].pr_rd(address)
        else:
            return self.processors[processor].pr_wr(address)

    def random_test(self):
        """
        Performs a random test on the MESI simulator.
        :return:
        """
        return self.instruction(randint(0, 4), randint(0, 1), randint(0, 4))


class Processor:
    """
    Processor for a MESI simulator. Handles its operations and cache.
    """

    def __init__(self, bus, memory):
        """
        Initializes a simulated processor and its cache.
        """
        self.cache = [{'state': 'I', 'value': 0} for x in range(4)]
        self.bus = bus
        self.memory = memory

    def pr_rd(self, address):
        """
        Reads an address in shared memory into its cache.
        :param address: The address in memory.
        :return: The value in cache
        """
        cache_item = self.cache[address]
        if cache_item['state'] is 'I':
            bus_status = self.snooper(address)
            self.bus.bus_rd(address)
            if contains_valid_state(bus_status): # If in other caches
                cache_item['state'] = 'S'
                # Get value from other cache...
            else: # If no other caches have valid copy
                cache_item['state'] = 'E'
                self.cache[address]['value'] = self.memory.data[address]


        return cache_item

    def pr_wr(self, address):
        """
        Writes an address from the cache to the shared memory.

        :param address: The address in memory
        :return: The value in cache.
        """

        self.memory[address] = self.cache[address]
        return self.memory[address]

    def snooper(self, address):
        """
        Snoops on the bus for changes in the cache.
        Updates this processor's cache if necessary.
        :address: the address we're checking.
        :return: the states of the item in other caches.
        """

        return self.bus.status[address]


class Bus:
    """
    Simulates an inter-core bus on a multi-processor chip.
    """

    def __init__(self, memory):
        self.memory = memory
        #creates a dict containing each address and it's status.
        self.status = {}
        for address in range(4):
            self.status[address] = ['I' for p in range(4)]
        pass

    def bus_rd(self, address):
        """

        :return:
        """
        state = self.status[address]

        if state is 'I':
            pass
        elif state is 'E':
            self.status[address] = 'S'
        elif state is 'S':
            pass
        elif state is 'M':
            self.status[address] = 'S'

        return None

    def bus_rdx(self):
        """

        :return:
        """
        return None

    def bus_upgr(self):
        return None

    def flush(self):
        return None

    def flush_opt(self):
        return None


class Memory:
    """
    Simulated shared memory for MESI simulator.
    """

    def __init__(self):
        self.data = [randint(0, 1000) for x in range(4)]


if __name__ == "__main__":
    mesi = Mesi()
    print(mesi.processors[0].cache)
    print(mesi.memory.data)
    mesi.processors[0].pr_rd(0)
    print(mesi.processors[0].cache)