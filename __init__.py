#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
"""
A thing of beauty is a joy for ever. James Joyce
"""
__title__ = 'crawtext'
__author__ = 'Constance de Quatrebarbes'
__license__ = 'MIT'
__copyright__ = 'Copyright 2014, Constance de Quatrebarbes'
__credits__ = "Lucas Ou-Yang"


from .configuration import cmdargs, ABSPATH
from docopt import docopt
from .wk import Worker

if __name__== "__main__":
	
	try:		
		w = Worker()
		print w.run(docopt(__doc__))
	except KeyboardInterrupt:
		sys.exit()
