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
            self.processors[x] = Processor(x, self.bus, self.memory)

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

    def __init__(self, number, bus, memory):
        """
        Initializes a simulated processor and its cache.
        """
        self.cache = {'state': 'I', 'values': [0 for x in range(4)]}
        self.number = number
        self.bus = bus
        self.bus.processors.append(self)
        self.memory = memory

    def pr_rd(self, address):
        """
        Reads an address in shared memory into its cache.
        :param address: The address in memory.
        :return: The value in cache
        """
        if self.cache['state'] is 'I':  # If we're in the invalid state
            # bus_status = self.snooper()
            self.cache['state'], self.cache['values'] = self.bus.bus_rd(self.number)
            # if contains_valid_state(bus_status[:address] + bus_status[address+1:]):  # If in other caches
            #     self.cache['state'] = 'S'
            #     # Get value from other cache...
            # else:  # If no other caches have valid copy
            #     self.cache['state'] = 'E'
            #     self.cache['values'] = self.memory.data

        else:
            # We already have a valid copy of the information.
            pass

        return self.cache['values'][address]

    def pr_wr(self, address):
        """
        Writes to a cache block.

        :param address: The address in memory
        :return: The value in cache.
        """

        self.cache['state'] = 'M'
        self.cache['values'][address] = randint(0, 1000)

        return self.cache['values'][address]

    def snooper(self):
        """
        Snoops on the bus for changes in the cache.

        :return: the states of the item in other caches.
        """

        return self.bus.status


class Bus:
    """
    Simulates an inter-core bus on a multi-processor chip.
    """

    def __init__(self, memory):
        self.memory = memory

        # creates a list to hold references to the processors
        self.processors = []

        # creates a list containing each processor's cache status.
        self.status = ['I' for p in range(4)]

    def bus_rd(self, processor):
        """
        Handles a bus_rd request from the given processor.

        :param processor: processor requesting the block
        :return: state, block from memory or another cache
        """
        status = self.status[processor]
        if status is 'I':
            if 'E' in self.status:
                block = self.processors[self.status.index('E')].cache['values']
                self.status[processor] = 'S'
                for x in self.status:
                    if x is 'E':
                        self.status[self.status.index('E')] = 'S'
            else:
                self.status[processor] = 'E'
                block = self.memory.data

        elif status is 'E':
            # bus_rd only happens to E when another processor is requesting, therefore it is now 'S'
            block = self.processors[self.status.index('E')].cache['values']
            self.status[processor] = 'S'
            if 'E' in self.status:
                for x in self.status:
                    if x is 'E':
                        self.status[self.status.index('E')] = 'S'

        # No need to do anything on Shared

        elif status is 'M':
            # Transition to shared and put flush_opt on bus.
            self.status[processor] = 'S'
            self.flush_opt()

        return self.status[processor], block

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
    Simulated shared memory block for MESI simulator.
    """

    def __init__(self):
        self.data = [randint(0, 1000) for x in range(4)]


if __name__ == "__main__":
    mesi = Mesi()
    print(mesi.processors[0].cache)
    print(mesi.memory.data)
    mesi.processors[0].pr_rd(0)
    print(mesi.processors[0].cache)
    print(mesi.bus.status)
    mesi.processors[2].pr_rd(0)
    print(mesi.processors[1].cache)
    print(mesi.bus.status)