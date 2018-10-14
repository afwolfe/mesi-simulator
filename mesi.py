#!/usr/bin/env python3
"""
    Name:   mesi.py
    Author: Alex Wolfe
    Desc:   Main file for a MESI cache simulator in Python.

    Some function descriptions are taken from the Wikipedia article on MESI protocol.
"""
import logging
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
        logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

        self.memory = Memory()
        self.bus = Bus(self.memory)

        self.processors = {}
        for x in range(4):
            self.processors[x] = Processor(x, self.bus, self.memory)

    def instruction(self, processor, r_w, address):
        """
        Performs the specified request in the cache.

        :param processor: processor number (0 to 3)
        :param r_w: 0 for read 1 for write
        :param address: address to access (0 to 3)
        :return: The result of the specified operation.
        """

        if r_w is 0:
            logging.info('P{}: PrRd {}'.format(processor, address))
            instruction = self.processors[processor].pr_rd(address)
        else:
            logging.info('P{}: PrWr {}'.format(processor, address))
            instruction = self.processors[processor].pr_wr(address)

        logging.info('P{}: Cache: {}'.format(processor, instruction))
        return instruction

    def random_test(self):
        """
        Performs a random test on the MESI simulator.

        :return: The result of the instruction.
        """
        instruction = self.instruction(randint(0, 3), randint(0, 1), randint(0, 3))
        return instruction


class Processor:
    """
    Processor for a MESI simulator. Handles its operations and cache.
    """

    def __init__(self, number, bus, memory):
        """
        Initializes a simulated processor and its cache.
        """

        logging.debug("Initializing processor " + str(number))
        self.cache = {'state': 'I', 'values': [0 for x in range(4)]}
        self.number = number
        self.bus = bus
        self.bus.processors.append(self)
        self.memory = memory

    def pr_rd(self, address):
        """
        Reads a cache block.

        :return: The cache
        """

        if self.cache['state'] is 'I':  # If we're in the invalid state
            # Issue a bus_rd and store the values.
            # self.cache['state'], self.cache['values'] = self.bus.bus_rd(self.number)
            self.cache['state'], self.cache['values'] = self.bus.transaction([self.number, 'bus_rd'])

        else:
            # We already have a valid copy of the information.
            pass

        logging.info("Value: " + str(self.cache['values'][address]))
        return self.cache

    def pr_wr(self, address):
        """
        Writes to a cache block.

        :param address: The address in memory
        :return: The cache.
        """
        if self.cache['state'] is 'I':
            self.cache['values'] = self.bus.transaction([self.number, 'bus_rd_x'])
        self.cache['state'] = 'M'

        self.cache['values'][address] = randint(0, 1000)

        return self.cache

    def snooper(self):
        """
        Snoops on the bus for changes in the cache.

        :return: the states of the item in other caches.
        """
        logging.debug('P{} snooping'.format(self.number))

        last_transaction = self.bus.transactions[-1]
        logging.debug('last_transaction: ' + str(last_transaction))

        if last_transaction[0] is not self.number:
            # logging.debug("not issued by self.")

            # BusRd
            if last_transaction[1] is "bus_rd":
                if self.cache['state'] is 'E':
                    # Transition to Shared (Since it implies a read taking place in other cache).
                    # Put FlushOpt on bus together with contents of block.

                    # logging.debug("Transitioning from E to S")
                    self.cache['state'] = 'S'
                    self.bus.block = self.cache['values']
                    self.bus.transaction([self.number, 'flush_opt'])

                elif self.cache['state'] is 'S':
                    # No State change (other cache performed read on this block, so still shared).
                    # May put FlushOpt on bus together with contents of block
                    # (design choice, which cache with Shared state does this).
                    self.bus.block = self.cache['values']
                    self.bus.transaction([self.number, 'flush_opt'])

                elif self.cache['state'] is 'M':
                    # Transition to (S)Shared.
                    # Put FlushOpt on Bus with data. Received by sender of BusRd and Memory Controller,
                    # which writes to Main memory.

                    self.cache['state'] = 'S'
                    self.bus.block = self.cache['values']
                    self.bus.transaction([self.number, 'flush_opt'])

            # BusRdX
            elif last_transaction is 'bus_rd_x':
                if self.cache['state'] is 'E':
                    # Transition to Invalid.
                    # Put FlushOpt on Bus, together with the data from now-invalidated block.
                    self.cache['state'] = 'I'

                    self.bus.block = self.cache['values']
                    self.bus.transaction([self.number, 'flush_opt'])
                elif self.cache['state'] is 'S':
                    # Transition to Invalid (cache that sent BusRdX becomes Modified)
                    # May put FlushOpt on bus together with contents of block
                    # (design choice, which cache with Shared state does this)
                    self.cache['state'] = 'I'
                    self.bus.block = self.cache['values']
                    self.bus.transaction([self.number, 'flush_opt'])

                elif self.cache['state'] is 'M':
                    # Transition to (I)Invalid.
                    # Put FlushOpt on Bus with data. Received by sender of BusRdx and Memory Controller,
                    # which writes to Main memory.

                    self.cache['state'] = 'I'
                    self.bus.block = self.cache['values']
                    self.bus.transaction(self.number, 'flush_opt')

        return self.bus.status


class Bus:
    """
    Simulates an inter-core bus on a multi-processor chip.
    """

    def __init__(self, memory):
        self.memory = memory

        # creates a list to hold references to the processors
        self.processors = []

        # holds all transactions on the bus in the form [processor_number, action]
        self.transactions = []

        self.block = None

        # creates a list containing each processor's cache status.
        # self.status = ['I' for p in range(4)]

    @property
    def status(self):
        status = []
        for x in self.processors:
            status.append(x.cache['state'])
        return status

    def transaction(self, action):
        """
        Performs the specified bus transaction and appends it to the history.
        :param action: transaction as [processor_number, action]
        :return: The result of the transaction.
        """
        self.transactions.append(action)
        self.processor_snooping()
        return getattr(self, action[1])()

    def bus_rd(self):
        """
        Snooped request that indicates there is a read request to a Cache block
        made by another processor.

        :return: block from memory or another cache
        """
        logging.debug("BusRd")

        if self.block:
            cache_block = self.block
            self.block = None
            return 'S', cache_block
        else:
            return 'E', self.memory.data

    def bus_rd_x(self):
        """
        Snooped request that indicates there is a write request to a Cache block
        made by another processor which doesn't already have the block.

        :return: the block from another cache or memory.
        """

        logging.debug("BusRdX")

        if self.block:
            cache_block = self.block
            self.block = None
            return cache_block
        else:
            return self.memory.data


    def bus_upgr(self):
        """
        Snooped request that indicates that there is a write request to a Cache block
        made by another processor but that processor already has that Cache block
        resident in its Cache.

        :return:
        """

        return None

    def flush(self):
        """
        Snooped request that indicates that an entire cache block is written back
        to the main memory by another processor.

        :return: The current values in memory.
        """

        self.memory.data = self.block
        return self.memory.data

    def flush_opt(self):
        """
        Snooped request that indicates that an entire cache block is posted on the bus
        in order to supply it to another processor (Cache to Cache transfers).

        :return: The current values in memory.
        """

        self.memory.data = self.block
        return self.memory.data

    def processor_snooping(self):
        """
        Has all processors perform their snooping and respond appropriately.

        :return:
        """

        for x in self.processors:
            x.snooper()

        return None


class Memory:
    """
    Simulated shared memory block for MESI simulator.
    """

    def __init__(self):
        self.data = [randint(0, 1000) for x in range(4)]


if __name__ == "__main__":
    mesi = Mesi()

    for x in range(10):
        print("----- TEST #{} -----".format(x))
        mesi.random_test()
        print("STATES: " + str(mesi.bus.status))
        print("MEM:    " + str(mesi.memory.data))
    print("BUS TRANSACTIONS:")
    for transaction in mesi.bus.transactions:
        print(transaction)