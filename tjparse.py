#!/usr/bin/env python
from TrafficJuggler.builders.dbbuilder import session
from TrafficJuggler.builders.imagebuilder import ImageBuilder
from TrafficJuggler.parser import Parser
from config import FULL_PATH, HOSTS
from time import strftime, sleep
import logging, sys

# logging.basicConfig(stream=sys.stdout)
for HOST in HOSTS:
    parser = Parser(HOST)
    rb = ImageBuilder(HOST, session, parser)
    rb.parse()

    # with open('{path}/tjparse.log'.format(path=FULL_PATH),'a') as f:
    #     f.write('Parsed: '+strftime("%Y-%m-%d %H:%M:%S")+'\n')
