#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os, re
from .database import *
from .job import *



class Worker(object):
	''' main access to Job Database'''
	__DB__ = Database(TASK_MANAGER_NAME)
	__COLL__ = __DB__.use_coll(TASK_COLL)
	_ACTION_LIST = ["report", "extract", "export", "archive", "user", "debug", "wos", "list", "crawl"]
	_TASK_LIST = ["start","stop", "delete",'schedule', "unschedule"]
	_PROJECT_LIST = ["--user", "--repeat", "--format", "--coll_type"]
	_CRAWL_LIST = ["--query", "--key"]	
	_OPTION_lIST	= ['add', 'delete', 'expand']
	
	
	def __init__(self,user_input):
		'''Job main config'''
		self.name = user_input['<name>']
		self.action = None
		self._logs = {}
		
		self.active = True
		self.__get_input__(user_input)
		self.dispatch()
	
		
	def __get_input__(self, user_input):
		'''mapping user input into job parameters'''
		
		self.name = user_input['<name>']
		
		if self.name in self._ACTION_LIST :
			self.action = self.name
			self._task = "show"
			print "Name error: You can't call your project with the name of an instruction.\n Forbidden name:"
			for n in self._ACTION_LIST:
				print "\t-%s" %n
			return self
			
		if self.name in self._TASK_LIST :
			self._task = self.name
			self.name = None
			print "Name error: You can call a project with the name of and instruction"	
			return self
			
		self._task = [k for k,v in user_input.items() if v is True and k in self._TASK_LIST]
		self.action = [k for k,v in user_input.items() if v is True and k in self._ACTION_LIST]
		print self._TASK_LIST
		print self._task
		if len(self._task) == 0:
			self._task = None
		else:
			self._task = self._task[0]
		if len(self.action) == 0:
			self.action  = None
		else:
			self.action = self.action[0]
		
		print self._task
		if self.action is None:
		#user
			if validate_email(self.name) is True:
				self.user = self.name
				self._task = self.action
				self.action = "user"
			
			#archive
			elif validate_url(self.name) is True:
				self.url = self.name
				self._task = self.action
				self.action = "archive"
				
			#crawl update	
			elif user_input["-s"] is True:
				self.action = "crawl"
				for k,v in user_input.items():
					if v is True and k in self._OPTION_lIST:
						self._task = k+"_sources"
					if v is not None and v is not False:
						setattr(self,re.sub("<|>|--","", k), v)
			else:
				if self.action is None and self._task is None:
					self.action = "crawl"
				
		for k,v in user_input.items():
			if v is not None and k in self._CRAWL_LIST:	
				self._task ="update"
				self.action = "crawl"
			if v is not None and k in self._PROJECT_LIST:	
				self._task = "update"
			if v is not None and v is not False and k != "<name>":
				setattr(self, re.sub("--|<|>","", k), v)
				
			else:
				pass
		if self.action is None:
			self.action = "job"
		return self
							
	def dispatch(self):
		
		if self.action == "user":
			item = self.__COLL__.find_one({"user":self.name})
		else:	
			item = self.__COLL__.find_one({"name":self.name})
		
		if self._task is None:
			if self.action not in ['crawl', 'archive', 'user']:
				self._task = "start"
			elif item is not None:
				self._task = "show"
			else:
				self._task = "create"
			
		
				
		_class = (self.action).capitalize()
		instance = globals()[_class]
		
		job = instance(self.__dict__)
		print instance, self._task
		instanciate = getattr(job,self._task)
		'''
		descr = self._task
		if descr[-1] == "e":
			descr = "".join(descr[:-1])
		
		print "\n%sing %s for project %s"%(descr.capitalize(),self.action, self.name)
		'''
		
		return instanciate()
		
		
