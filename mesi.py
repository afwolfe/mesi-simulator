#!/usr/bin/env python3
"""
    Name:   mesi.py
    Author: Alex Wolfe
    Desc:   Main file for a MESI cache simulator in Python.
"""


class Mesi:
    """
    Main MESI simulator class. Can be seen as the chip that contains all of the Processors, Bus, and Memory.
    """

    def __init__(self):
        """
        Initializes bus, memory, and processors.
        """

        self.bus = Bus()

        self.memory = Memory()

        # Create a dict of Processors p0 through p3
        self.processors = {}
        for x in range(4):
            self.processors['p' + str(x)] = Processor()


class Processor:
    """
    Processor for a MESI simulator. Handles its operations and cache.
    """

    def __init__(self):
        """
        Initializes a simulated processor and its cache.
        """
        self.cache = [0, 0, 0, 0]
        self.status = [None, None, None, None]

    def pr_rd(self, address):
        """
        Reads an address in shared memory into its cache.
        :param address: The address in memory.
        :return: The value in memory
        """

        return self.memory[address]

    def pr_wr(self, address):
        """
        Writes an address from the cache to the shared memory.

        :param address: The address in memory
        :return: The value in memory.
        """

        self.memory[address] = self.cache[address]
        return self.memory[address]


class Bus:
    """
    Simulates an inter-core bus on a multi-processor chip.
    """

    def __init__(self):
        pass

    def bus_rd(self):
        """

        :return:
        """
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
        pass


if __name__ == "__main__":
    mesi = Mesi()
    print(mesi.processors)
