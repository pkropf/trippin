#! /usr/bin/env python

# Copyright (c) 2013 Peter Kropf. All rights reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.


import sys
import optparse
from twisted.internet import reactor
import txosc
import txosc.dispatch
import txosc.async
from time import time
import RPi.GPIO as gpio


GPIO.setmode(GPIO.BCM)

def unhandled(message, address):
    print "%s from %s @ %s" % (message, address, str(time()))


class receiver(object): 
    def __init__(self, port):
        self.receiver = txosc.dispatch.Receiver()
        self._server_port = reactor.listenUDP(port, txosc.async.DatagramServerProtocol(self.receiver))
        self.safety = False
        self.left_pin = 4
        self.left_state = gpio.LOW
        self.right_pin = 5
        self.right_state = gpio.HIGH
        self.states = {0.0: gpio.LOW, 1.0: gpio.HIGH}

        host = "localhost"

        GPIO.setup(self.left_pin,  GPIO.OUT, initial=self.left_state)
        GPIO.setup(self.right_pin, GPIO.OUT, initial=self.right_state)

        print "Listening on osc.udp://%s:%s" % (host, port)
        
        self.receiver.addCallback("/*/left",   self.left_handler)
        self.receiver.addCallback("/*/right",  self.right_handler)
        self.receiver.addCallback("/*/safety", self.safety_handler)

        self.receiver.setFallback(unhandled)


    def left_handler(self, message, address):
        if self.safety:
            #print 'left_handler'
            #print '    Got %s from %s' % (message, address)
            self.left_state = self.states[message.getValues()[0]]
            gpio.output(self.left_pin, self.left_state)


    def right_handler(self, message, address):
        if self.safety:
            #print 'right_handler'
            #print '    Got %s from %s' % (message, address)
            self.right_state = self.states[message.getValues()[0]]
            gpio.output(self.right_pin, self.right_state)


    def safety_handler(self, message, address):
        #print 'safety_handler'
        #print '    Got %s from %s' % (message, address)
        val = message.getValues()[0]
        self.safety = val == 1.0



if __name__ == "__main__":
    parser = optparse.OptionParser(usage="%prog", version=txosc.__version__.strip(), description=__doc__)
    parser.add_option("-p", "--port", type="int", default=8000, help="Port for incoming packets")
    (options, args) = parser.parse_args()


    def _later():
        app = receiver(options.port)

    reactor.callLater(0.01, _later)
    reactor.run()
