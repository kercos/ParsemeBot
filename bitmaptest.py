# -*- coding: utf-8 -*-

from google.appengine.ext import ndb

import logging
from random import randint
import pickle
from bitmap import BitMap

class BitMapTest(ndb.Model):
    #bitmap = ndb.BlobProperty(indexed=False)  # compressed=True
    bitmap = ndb.PickleProperty(indexed=False) #compressed=True
    name = ndb.StringProperty()

def addBitMap(id, size):
    bm = BitMap(size)
    bmObj = BitMapTest(
        id=id,
        bitmap = bm,
        name = id
    )
    bmObj.put()
    return bmObj

def getBitMap(id):
    bmObj = BitMapTest.get_by_id(id)
    #bm = bmObj.bitmap
    return bmObj


def testBitMap(size, flips):
    id = 'test' + str(size)
    bmObj = addBitMap(id,size)
    bm = bmObj.bitmap
    logging.debug('Created ' + id + ':') # + bm.tostring()
    for i in range(0,flips):
        bm.flip(randint(0, size-1))
    logging.debug("Flipped some random bits") # + bm.tostring()
    logging.debug("Bit sets to 1: " + str(bm.count()))
    bmObj.put()
    logging.debug("Stored " + id)
    bmObj = getBitMap(id)
    logging.debug("Retrieved " + bmObj.name)
    logging.debug("Bit sets to 1: " + str(bmObj.bitmap.count()))

# - `BitMap(maxnum)`: construct a `BitMap` object with `maxnum` bits
# - `set(pos)`: set the bit at position `pos` to 1
# - `reset(pos)`: reset the bit at position `pos` to 1
# - `flip(pos)`: flip the bit at position `pos`
# - `count()`: return the number of 1s
# - `size()`: return the size of the `BitMap`
# - `test(pos)`: check if bit at position `pos` has been set to 1
# - `any()`: check if any bit in the `BitMap` has been set to 1
# - `none()`: check if none of the bits in the `BitMap` has been set to 1
# - `all()`: check if all bits in the `BitMap` has been set to 1
# - `nonzero()`: return indexes of all non-zero bits
# - `tostring()`: convert a `BitMap` object to `0` and `1` string
# - `fromstring(bitstring)`: create a `BitMap` object from `0` and `1` string

def testLocalBitMap(size, flips):
    id = 'test' + str(size)
    bm = BitMap(size)
    print('Created ' + id + ':') # + bm.tostring()
    print("Flipping some random bits:") #bm.tostring()
    for i in range(0,flips):
        rnd_index = randint(0, size-1)
        #print("\tflipping index: " + str(rnd_index))
        bm.flip(rnd_index)
    print("Bit sets to 1: " + str(bm.count()))
    print("Flipping some random bits:") #bm.tostring()
    for i in range(0, flips):
        rnd_index = randint(0, size - 1)
        #print("\tflipping index: " + str(rnd_index))
        bm.flip(rnd_index)
    print("Bit sets to 1: " + str(bm.count()))
    stringBM = pickle.dumps(bm)
    print("Size of the pickled string representing the bm: " + str(len(stringBM)))
    print("Loading bm from pickled string")
    bm = pickle.loads(stringBM)
    print("Bit sets to 1: " + str(bm.count()))


'''
def testBitArray(size, flips):
    id = 'test' + str(size)
    bmObj, ba = addBitMap(id,size)
    logging.debug('Created ' + id + ':') # + bm.tostring()
    for i in range(0,flips):
        ba.invert(randint(0, size-1))
    logging.debug("Flipped some random bits") # + bm.tostring()
    logging.debug("Bit sets to 1: " + str(ba.count(1)))
    bmObj.put()
    logging.debug("Stored " + id)
    bmObj, ba = getBitMap(id)
    logging.debug("Retrieved " + id)
    logging.debug("Bit sets to 1: " + str(ba.count(1)))
    for i in range(0, flips):
        ba.invert(randint(0, size-1))
    logging.debug("Flipped some random bits") # bm.tostring()
    logging.debug("Bit sets to 1: " + str(ba.count(1)))
    bmObj.put()
    logging.debug("Stored " + id)
'''

'''
def testLocalBitArray(size, flips):
    id = 'test' + str(size)
    ba = BitArray(size)
    print('Created ' + id + ':') # + bm.tostring()
    print("Flipping some random bits:") # + ba.tostring()
    for i in range(0,flips):
        rnd_index = randint(0, size-1)
        #print("\tflipping index: " + str(rnd_index))
        ba.invert(rnd_index)
    print("Bit sets to 1: " + str(ba.count(1)))
    print("Flipping some random bits:") #ba.tostring()
    for i in range(0, flips):
        rnd_index = randint(0, size - 1)
        #print("\tflipping index: " + str(rnd_index))
        ba.invert(rnd_index)
    print("Bit sets to 1: " + str(ba.count(1)))
    stringBa = ba.tobytes()
    print("Size of the bitarray represented in byte: " + str(len(stringBa)))
    ba = BitArray(bytes=stringBa)
    print("Loaded ba from string")
    print("Bit sets to 1: " + str(ba.count(1)))
'''

