#!/usr/bin/env python3
"""
    Name:   mesi.py
    Author: Alex Wolfe
    Desc:   Main file for a MESI cache simulator in Python.

    Some function descriptions are taken from the Wikipedia article on MESI protocol.
"""
import logging
from random import randint

class Mesi:
    """
    Main MESI simulator class. Can be seen as the chip that contains all of the Processors, Bus, and Memory.
    """

    def __init__(self):
        """
        Initializes bus, memory, and processors.
        """
        logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
        # logging.basicConfig(level=logging.DEBUG, format="%(message)s")

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
            logging.info('P{}: PrRd addr {}'.format(processor, address))
            instruction = self.processors[processor].pr_rd(address)
        else:
            logging.info('P{}: PrWr addr {}'.format(processor, address))
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
        self.cache = {'state': 'I', 'values': [0, 0, 0, 0]}
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
            # Issue BusRd to the bus
            # other Caches see BusRd and check if they have a non-invalid copy, inform sending cache
            # State transition to (S)Shared, if other Caches have non-invalid copy.
            # State transition to (E)Exclusive, if none (must ensure all others have reported).
            # If other Caches have copy, one of them sends value, else fetch from Main Memory
            self.cache['state'], self.cache['values'] = self.bus.transaction([self.number, 'bus_rd'])

        else:  # M, S, and E
            # We already have a valid copy of the information.
            # No bus transactions generated
            # State remains the same.
            # Read to the block is a Cache hit
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
            # Issue BusRdX signal on the bus
            # State transition to (M)Modified in the requestor Cache.
            # If other Caches have copy, they send value, otherwise fetch from Main Memory
            # If other Caches have copy, they see BusRdX signal and Invalidate their copies.
            # Write into Cache block modifies the value.
            self.cache['values'] = self.bus.transaction([self.number, 'bus_rd_x'])

        elif self.cache['state'] is 'S':
            self.bus.transaction([self.number, 'bus_upgr'])

        self.cache['state'] = 'M'

        self.cache['values'][address] = randint(0, 1000)

        return self.cache

    def snooper(self, last_transaction):
        """
        Snoops on the bus for changes in the cache.

        :return: the states of the item in other caches.
        """
        logging.debug('P{} snooping'.format(self.number))

        logging.debug('last_transaction: ' + str(last_transaction))

        if last_transaction[0] is not self.number:
            # logging.debug("not issued by self.")

            # BusRd
            if last_transaction[1] is "bus_rd":
                if self.cache['state'] is 'E':
                    logging.debug('BusRd E->S')
                    # Transition to Shared (Since it implies a read taking place in other cache).
                    # Put FlushOpt on bus together with contents of block.

                    # logging.debug("Transitioning from E to S")
                    self.cache['state'] = 'S'
                    self.bus.block = self.cache['values']
                    self.bus.transaction([self.number, 'flush_opt'])

                elif self.cache['state'] is 'S':
                    logging.debug('BusRd S->S')
                    # No State change (other cache performed read on this block, so still shared).
                    # May put FlushOpt on bus together with contents of block
                    # (design choice, which cache with Shared state does this).
                    self.bus.block = self.cache['values']
                    self.bus.transaction([self.number, 'flush_opt'])

                elif self.cache['state'] is 'M':
                    # Transition to (S)Shared.
                    # Put FlushOpt on Bus with data. Received by sender of BusRd and Memory Controller,
                    # which writes to Main memory.
                    logging.debug('BusRd M->S')

                    self.cache['state'] = 'S'
                    self.bus.block = self.cache['values']
                    self.bus.transaction([self.number, 'flush_opt'])

            # BusRdX
            elif last_transaction[1] is 'bus_rd_x':
                if self.cache['state'] is not 'I':
                    logging.debug("BusRdX has valid copy.")
                    logging.debug('state was: {}'.format(self.cache['state']))
                    # If we had a valid copy of the data (E,M,S)
                    # Transition to Invalid.
                    # Put FlushOpt on Bus, together with the data from now-invalidated block.
                    self.cache['state'] = 'I'

                    self.bus.block = self.cache['values']
                    self.bus.transaction([self.number, 'flush_opt'])
            # BusUpgr
            elif last_transaction[1] is "bus_upgr":
                if self.cache['state'] is 'S':
                    logging.debug('BusUpgr S->I')
                    self.cache['state'] = 'I'

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

        # A variable to temporarily store a block of cache for another processor.
        self.block = None

    @property
    def status(self):
        """
        Gets the current state of all of the processor's caches.
        :return: list of states for all processors
        """
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
        logging.debug(action)

        self.transactions.append(action)
        self.processor_snooping()
        return getattr(self, action[1])()

    def bus_rd(self):
        """
        Snooped request that indicates there is a read request to a Cache block
        made by another processor.

        :return: block from memory or another cache
        """

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

        :return: None
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
        Has all processors perform their snooping and respond appropripyately.

        :return: None
        """
        last_action = self.transactions[-1]
        for x in self.processors:
            x.snooper(last_action)

        return None


class Memory:
    """
    Simulated shared memory block for MESI simulator.
    """

    def __init__(self):
        self.data = [randint(0, 1000) for x in range(4)]


def random_test(n):
    """
    Performs the specified number of random tests on the MESI simulator.
    :param n: number of random instructions to perform.
    :return: None
    """
    mesi = Mesi()

    for x in range(n):
        logging.info("----- INSTRUCTION #{} -----".format(x+1))
        mesi.random_test()
        logging.info("STATES: " + str(mesi.bus.status))
        logging.info("MEM:    " + str(mesi.memory.data))
    # logging.info("BUS TRANSACTIONS:")
    # for transaction in mesi.bus.transactions:
    #     logging.info(transaction)


def wikipedia_test():
    """
    Performs the operations outlined in "Illustration of MESI protocol operations" on the MESI protocol Wikipedia page.

    :return: None
    """
    mesi = Mesi()
    tests = [
        [0, 0],
        [0, 1],
        [2, 0],
        [2, 1],
        [0, 0],
        [2, 0],
        [1, 0]
    ]

    for n in range(len(tests)):
        logging.info("----- INSTRUCTION #{} -----".format(n+1))
        t = tests[n]
        mesi.instruction(t[0], t[1], 0)
        logging.info("STATES: " + str(mesi.bus.status))
        logging.info("MEM:    " + str(mesi.memory.data))

    # Uncomment to see bus transactions
    # logging.info("BUS TRANSACTIONS:")
    # for transaction in mesi.bus.transactions:
    #     logging.info(transaction)


if __name__ == "__main__":
    random_test(10)

    # wikipedia_test()
