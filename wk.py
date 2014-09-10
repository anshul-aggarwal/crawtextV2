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
	_DB_ = Database(TASK_MANAGER_NAME)
	_COLL_ = _DB_.use_coll(TASK_COLL)
	#values for docopt and YAML?
	ACTION_LIST = ["report", "extract", "export", "archive", "start","stop", "delete","list", 'schedule', "unschedule"]
	PROJECT_LIST = ["--u", "--r"]
	CRAWL_LIST = ["--q", "--k"]
	OPTION_lIST	= ['add', 'delete', 'expand']
	
	
	def __init__(self,user_input):
		'''Job main config'''
		self.name = user_input['<name>']
		self.action = None
		self.logs = {}
		
		self.logs["active"] = True
		self.__get_input__(user_input)
		self.dispatch()
	
	def __select_jobs__(self, query):
		'''mapping job database'''
		job_list = [n for n in self._COLL_.find(query)]
		if len(job_list) == 0:
			return None
		else:	
			return job_list
	
	def __update_status__(self):
		'''insert current status of the job once shceduled'''
		raise NotImplementedError
		
		
	#~ def get_job(self, job):
		#~ '''mapping data parameters from db to job'''
		#~ return [setattr(job, k, v) for k, v in self.__dict__.items() if v is not None and v is not False and k != "name"]
	
	def __set_config__(self, job):
		'''mapping data parameters from current to job'''
		for k, v in self.__dict__.items():
			if v is not None and v is not False:
				setattr(job, k, v)
				
	def __get_config__(self, job):
		'''mapping task parameters to job'''
		config = self.__COLL__.find_one({"name":self.name, "action":self.action})
		if config is None:
			print ("No configuration found for this job")
		else:
			for k,v in config.items():
				if v is not None and v is not False and k != "name":
					setattr(job, k, v)
		return 
		
	def __get_input__(self, user_input):
		'''mapping user input into job parameters'''
		self.name = user_input['<name>']
		self.task = None
		#user
		if validate_email(self.name) is True:
			self.user = self.name
			self.action = "user"
			self.task = "show"
			return self
		else:
			for k,v in user_input.items():
				if v is True and k in self.ACTION_LIST:
					self.action = "job"
					self.task = k
				if v is not None and k in self.CRAWL_LIST:	
					self.action = "crawl"
					self.task ="update"
				if v is not None and k in self.PROJECT_LIST:	
					self.action = "job"
					self.task = "update"
				if v is not None and v is not False and k != "<name>":
					setattr(self, re.sub("--|<|>","", k), v)
			return self
			#archive	
			if validate_url(self.name) is True:
				self.action = "archive"
				return self
			elif user_input["-s"] is True:
				self.action = "crawl"
				
				for k,v in user_input.items():
					if v is True and k in self.OPTION_lIST:
						self.task = k+"_sources"
					if v is not None and v is not False:
						setattr(self,re.sub("<|>","", k), v)
				return self
			else:
				self.action = "crawl"
				self.task = None
				return self
				
	def dispatch(self):		
		
		job_list = self.__select_jobs__({"name":self.name})
		if self.task is None:
			self.action = "job"
			if job_list is None:
				self.task = "create"
			else:
				self.task = "show"
		
		#print (self.action, self.task)
		dynamic_class = (self.action).capitalize()
		instance = globals()[dynamic_class]
		job = instance(self.name)
		print self.action, self.task
		run = getattr(job,self.task)()
		return run
	
		
			
	
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
			
				
		
