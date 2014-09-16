#!/usr/bin/env python
# -*- coding: utf-8 -*-


from configuration import CMD, ABSPATH
#from .packages import docopt
import docopt
from worker import wk

if __name__== "__main__":
	try:		
		w = Worker(docopt(__doc__))		
	except KeyboardInterrupt:
		sys.exit()
