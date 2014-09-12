#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys, os
from database import *
import re
from job import *
#from abc import ABCMeta, abstractmethod
import docopt
from utils import *


class Worker(object):
	''' main access to Job Database'''
	__DB__ = Database(TASK_MANAGER_NAME)
	__COLL__ = __DB__.use_coll(TASK_COLL)
	ACTION_LIST = ["report", "extract", "export", "archive", "start","stop", "delete","list", 'schedule', "unschedule", "debug"]
	PROJECT_LIST = ["--user", "--repeat"]
	CRAWL_LIST = ["--query", "--key"]
	OPTION_lIST	= ['add', 'delete', 'expand']
	
	
	def __init__(self,user_input):
		'''Job main config'''
		self.name = user_input['<name>']
		self.action = None
		self.logs = {}
		
		self.logs["active"] = True
		self.__get_input__(user_input)
		self.dispatch()
	
		
	def __get_input__(self, user_input):
		'''mapping user input into job parameters'''
		
		self.name = user_input['<name>']
		self._task = None
		self.action = None
		#user
		if validate_email(self.name) is True:
			self.user = self.name
			self.action = "user"
			self._task = "show"
			return self
		else:
			for k,v in user_input.items():
				if v is True and k in self.ACTION_LIST:
					self.action = "job"
					self._task = k
				if v is not None and k in self.CRAWL_LIST:	
					self.action = "crawl"
					self._task ="update"
				if v is not None and k in self.PROJECT_LIST:	
					self.action = "job"
					self._task = "update"
				if v is not None and v is not False and k != "<name>":
					setattr(self, re.sub("--|<|>","", k), v)
			
			#archive	
			if validate_url(self.name) is True:
				self.action = "archive"
				try:
					self.format = self.format
					self._task = "update"
				except AttributeError:
					pass
				return self
			elif user_input["-s"] is True:
				self.action = "crawl"
				
				for k,v in user_input.items():
					if v is True and k in self.OPTION_lIST:
						self._task = k+"_sources"
					if v is not None and v is not False:
						setattr(self,re.sub("<|>","", k), v)
				return self
			else:
				return self
				
	def dispatch(self):
		item = self.__COLL__.find_one({"name":self.name})
		
		if self._task is None: 
			if item is not None:
				self._task = "show"
			else:
				self._task = "create"
			
		if self.action is None:
			self.action = "crawl"
		
				
		_class = (self.action).capitalize()
		instance = globals()[_class]
		
		job = instance(self.name, self.__dict__)
		
		instanciate = getattr(job,self._task)
		'''
		descr = self._task
		if descr[-1] == "e":
			descr = "".join(descr[:-1])
		
		print "\n%sing %s for project %s"%(descr.capitalize(),self.action, self.name)
		'''
		return instanciate()
		
			
	
	def export_job(self):	
		#next change self.action
		self.logs["step"] = "Export"
		self.logs["msg"] = "Exporting %s" %(self.name)
		self.__select_jobs__({"name":self.name, "action":"crawl"})
		if self.job_list is None:
			print "No active crawl job found for %s. Export can be executed" %self.name
			return
			#return self.__COLL__.update({"name":self.name, "action":self.action}, {"$push": {"status": self.logs}})
		else:
			job = Export(self.name)
			job.run_job()
			self.__COLL__.update({"name":self.name, "action":self.action}, {"$push": {"status": job.logs}})
			#self.status = e.status
			return self.__COLL__.update({"name":self.name, "action":self.action}, {"$push": {"status": self.logs}})
			
				
		
