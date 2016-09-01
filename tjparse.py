#!/usr/bin/env python
from TrafficJuggler.builders.dbbuilder import session
from TrafficJuggler.builders.imagebuilder import ImageBuilder
from TrafficJuggler.parser import Parser
from config import FULL_PATH, HOSTS
from time import strftime, sleep
import logging, sys

for HOST in HOSTS:
    parser = Parser(HOST)
    rb = ImageBuilder(HOST, session, parser)
    rb.parse()
