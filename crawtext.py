#!/usr/bin/env python
# -*- coding: utf-8 -*-


from configuration import CMD, ABSPATH
from packages.docopt import docopt
from manager import *
#from manager.worker import Worker

if __name__== "__main__":
	try:		
		w = Worker(docopt(CMD))		
	except KeyboardInterrupt:
		sys.exit()
