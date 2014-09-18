#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import os, sys, shutil


from datetime import datetime as dt
#import datetime as dt
from database import *
from page import Page
from utils.url import *
from query import Query
#from scrapper.article import Article		
from utils import *
import subprocess
import requests
from page import Source

class Job(object):
	
	__DB__ = Database(TASK_MANAGER_NAME)
	__COLL__ = __DB__.use_coll(TASK_COLL)
	
	def __init__(self, doc): 
		
		self.name = doc['name']
		self.action = doc["action"]
		self.__data__ = self.__COLL__.find_one({"name":self.name})		
		self.project_name = re.sub('[^0-9a-zA-Z]+', '_', self.name)
		now = dt.now()
		self.date = now.replace(second=0, microsecond=0)
		
		#value from db
		self.__db__ = Database(self.project_name)
		self.__db__.create_colls(["results","sources", "logs", "queue", "treated"])
		self.active = True
		self.date = dt.now()
		self._doc = doc
		self._logs = {}
		self._logs["date"] = self.date
		self.active = True
		
	def __update_logs__(self):
		try:
			print self._logs["msg"]
		except KeyError:
			self._logs["msg"] = ""
			
		if self.__data__ is None:
			if self._logs["status"] is True:
				self._logs["msg"]  = "No active '%s' job for project '%s'found" %(self.action, self.name)
				
				self.create()
			
		try:		
			_id = self.__data__['_id']
			self.__COLL__.update({"_id":_id}, {"$set":{"active":self._logs["status"]}})
			self.__COLL__.update({"_id":_id}, {"$push":{"status":self._logs}})
		except KeyError:
			pass
		
		return self._logs["status"]
		
										
	def create(self):
		self._logs['step'] = "creation"
		question = "Do you want to create a new project with a %s job?" %self.action
		if ask_yes_no(question):
			
			for k,v in self._doc.items():
				 if k[0] != "_" and k[0] != "-" and k not in ["add", "delete", "expand"]:
					 setattr(self,k,v)
			_id = self.__COLL__.insert(self.__repr__())
			self.__data__ = self.__COLL__.find_one({"_id":_id})
			self._logs['status'] = True
			self._logs["msg"] = "Sucessfully created project %s with task %s" %(self.name,self.action)
			return self.__update_logs__()
		
	def update(self):
		if self.__data__ is None:
			self._logs["msg"]  = "No active '%s' job for project '%s'found" %(self.action, self.name)
			self.create()
		else:	
			self._logs["step"] = "Updating %s job of project %s"%(self.action, self.name)
			
		self.updated_value = []	
		for k,v in self._doc.items():
			if k[0] != "_" and v not in self.__data__.values():
				self.updated_value.append(k)
				self.__COLL__.update({"_id":self.__data__["_id"]}, {"$set":{k:v}})
		if len(self.updated_value) == 0:
			self._logs["msg"] = "No change for '%s' job project %s. Parameters given are the same." %(self.action, self.name)
			self._logs["status"] = False
		else:	
			self._logs["status"] = True
			self._logs["msg"] = "Successfully updated '%s' job  for project '%s' with parameters: %s" %(self.action, self.name, ", ".join(self.updated_value))
		self.__update_logs__()	
		return self._logs['status']
	
	def start(self):
		if self.__data__ is None:
			print "No project %s found: job %s could not be started"%(self.name, self.action)
			return False
		else:
			_class = (self.action).capitalize()
			instance = globals()[_class]
			job = instance(self.__data__)
			return job.start()
			
	def stop(self):
		self._logs["step"] = "Stopping execution of job"
		self.__COLL__.update({"name":self.name, "action":self.action}, {"$push": {"status": self._logs}})
		for doc in self.job_list:
			func = doc["action"].capitalize()
			instance = globals()[func]
			job = instance(self.name)		
			self.__get_config__(job)
			job.stop()
			self.COLL.update({"name":self.name, "action":self.action}, {"$push": {"status": job.logs}})
			print (job.logs["msg"])
			self.COLL.update({"name":self.name}, {"$set": {"active": "False"}})	
			return self.COLL.update({"name":self.name, "action":self.action}, {"$push": {"status": self._logs}})
			
	def schedule(self):
		self._logs["step"] = "Scheduling project"
		if self.update():
			
			self._logs["status"] = True
			self._logs["msg"] = "Sucessfully schedule project"
		
		else:
			self._logs["status"] = True
			self._logs["msg"] = "No schedule done for project"
		return self.__update_logs__()
		
	def unschedule(self):
		self._logs["step"] = "Unscheduling job"
		
		
		if self.name in self.__COLL__.distinct("name"):
			for n in self.__COLL__.find({"name": self.name}):
				self.__COLL__.remove({"name":n['name']})
			self._logs["msg"] = "All tasks of project %s has been sucessfully unscheduled." %(self.name)
			self._logs["status"] = False
			
		else:
			self._logs["msg"] = "No project %s found" %(self.name)	
			self._logs["status"] = False
		
		return self.__update_logs__()
	
	
	def delete(self):
		'''delete project and archive results'''
		self._logs["step"] = "Deleting job"
		self.active = False
		print self._logs["step"]
		if self.__data__ is None:
			print "No project %s found. check the name of your project" %(self.name)
			return
		
		
		if self.__db__.use_coll("results").count() > 0 or self.__db__.use_coll("sources").count()> 0 or self.__db__.use_coll("logs").count()> 0:
			
			if ask_yes_no("Do you want to export first all data from project?"):
				job = Export(self.__repr__())
				job.start()
			if ask_yes_no("Do you want to delete all data from project?"):
				self.__db__.drop("collection", "results")
				self.__db__.drop("collection", "logs")
				self.__db__.drop("collection", "sources")
				self.__db__.client.drop_database(self.name)
			if ask_yes_no("Do you want to delete directory of the project?"):
				try:
					shutil.rmtree("%s") %("/"+self._project_name)
				except OSError:
					print "No directory for project found"
		else:
			print "No data found for project %s"%(self.name)
			try:
				shutil.rmtree(self.project_name)
				print "Deleting directory %s" %(self.project_name)
			except OSError:
				print "No directory %s for project found" %(self.project_name)
		self.unschedule()
		#self.__COLL__.update({"name":self.name}, {"$set": {"active": "False"}})	
		self._logs["msg"] = "Project %s sucessfully deleted." %self.project_name
		self._logs["status"] = False
		self.__update_logs__()
		return
	
	def show(self):
		
		print "\n===================="
		print (self.name.upper())
		print "===================="
		
		print "Activated job:%i\n" %(self.__COLL__.find({"name": self.name, "active":True}).count())
		for i, job in enumerate(self.__COLL__.find({"name": self.name})):
			i = i+1
			print "%i) Job: %s"%(i, job["action"])
			print "--------------"
			for k,v in job.items():
				if k == '_id' or k == 'status':
					continue
				if v is not False or v is not None:
					print k+":", v			
			print "--------------"
		
		print "____________________\n"
		return 
		
	
	def __repr__(self):
		'''representing public info'''
		self.__data__ = {}
		for k,v in self.__dict__.items():
			if k.startswith("_"):
				pass
			else:
				self.__data__[k] = v
		print self.__data__	
		return self.__data__
		
	def list(self):
		for doc in self.__COLL__.find({"name":self.project_name}):
			print doc['name'], doc['action'], doc['active']
class Crawl(Job):
	
	def update_sources(self):
		if self.__data__ is None:
			print "No existing project %s with %s job" %(self.name, self.action)
			self.create()
			return self.__update_logs__()
	
	def get_bing(self, key=None):
		''' Method to extract results from BING API (Limited to 5000 req/month) automatically sent to sources DB ''' 
		self._logs["step"] = "bing extraction"
		if key is not None:
			self.key = key
		if self.key == None:
			return
		
		print self.__db__.sources.count(), "sources in db"
		#~ print "There is already %d sources in database" %nb
		#~ print "and %d sources with a bad status" %self.__db__.sources.find({"status":"false"}).count()
		
		try:
			#defaut is Web could be composite Web + News
			#defaut nb for web is 50 could be more if manipulating offset
			#defaut nb for news is 15 could be more if manipulating offset
			#see doc https://onedrive.live.com/view.aspx?resid=9C9479871FBFA822!112&app=Word&authkey=!ANNnJQREB0kDC04
			r = requests.get(
					'https://api.datamarket.azure.com/Bing/Search/v1/Web', 
					params={
						'$format' : 'json',
						'$top' : 50,
						'Query' : '\'%s\'' %self.query,
					},	
					auth=(self.key, self.key)
					)
			
			r.raise_for_status()
			url_list =  [e["Url"] for e in r.json()['d']['results']]
			for i, url in enumerate(url_list):
				i = i+1
				self.insert_url(url,origin="bing",depth=0)
			
			
			self._logs["msg"] =  "Inserted %s urls from Bing results. Sources nb is now : %d" %(i, self.__db__.sources.count())
			self._logs["status"] = True
			return self.__update_logs__()
			
		except Exception as e:
			
			try:
				self._logs["code"] = r.status_code
				if r.status_code == 401:
					self._logs["msg"] = "Wrong credentials from BING check your API Key"
				else:
					self._logs["msg"] = "Error requestings new sources from Bing :%s" %e
				self._logs["status"] = False
				
				
					#~ 
			except Exception as e:
				
				self._logs["code"] = "601"+"."+str(e.args[0])
				self._logs["msg"] = "Error adding sources from BING: %s" %e.args
				self._logs["status"] = False
		
			return self.__update_logs__()	
		
		
	def get_local(self, afile = None):
		''' Method to extract url list from text file'''
		self._logs["step"] = "local file extraction"
		if afile is None:
			afile = self.file
		try:
			for url in open(afile).readlines():
				if url == "\n":
					continue
				url = re.sub("\n", "", url)
				status, status_code, error_type, url = check_url(url)
				self.insert_url(url, origin="file", depth=0)
				
			self._logs["status"] = True
			self._logs["msg"] = "Urls from file %s have been successfuly added to sources" %(afile)
			
		
		except Exception as e:
			#~ print "Please verify that your file is in the current directory. To set up a correct filename and add directly to sources:\n\t crawtext.py %s -s append your_sources_file.txt" %(e.args[1],self.file, self.name)
			self._logs["code"] = float(str(602)+"."+str(e.args[0]))
			self._logs["status"] = False
			self._logs["msg"]= "Failed inserting url for file %s : %s '." %(self.file, e.args[1])
		return self.__update_logs__()	
		
	def delete_local(self):
		'''delete sources contained in self.file'''
		self._logs["step"] = "deleting sources from file"
		self._logs["status"] = True
		self._logs["msg"] = "Urls sucessfully deleted"
		#~ print "Removing the list of url contained in the file %s" %self.file
		try:
			for url in open(self.file).readlines():
				url = re.sub("\n", "", url)
				self.__db__.sources.remove({"url":url})	
		except Exception as e:
			#~ print "Please verify that your file is in the current directory. To set up a correct filename and add directly to sources:\n\t crawtext.py %s -s append your_sources_file.txt" %(e.args[1],self.file, self.name)
			self._logs["code"] = float(str(602)+"."+str(e.args[0]))
			self._logs["status"] = False
			self._logs["msg"]= "Failed deleting url for file %s failed : %s '." %(self.file, e.args[1])
		return self.__update_logs__()
		
	def expand_sources(self):
		'''Expand sources url adding results urls collected from previous crawl'''
		self._logs["step"] = "expanding sources from results"
		self._logs["status"] = True
		self._logs["msg"] = "Urls from results sucessfully inserted into sources"
		for url in self.__db__.results.distinct("url"):
			self.insert_url(url, "automatic", depth=0)
		
		if len(self.__db__.results.distinct("url")) == 0 :
			self._logs["status"] = False
			self._logs["code"] = 603
			self._logs["msg"] = "No results to put in seeds. Expand option failed"
		return self.__update_logs__()
			
	def add_sources(self):
		self.update_sources()
		self._logs["step"] = "adding sources from user_input"
		self._logs["status"] = True
		self._logs["msg"] = "Urls sucessfully inserted into sources"
		if hasattr(self, 'url'):
			ext = (self.url).split(".")[-1]
			if ext == "txt":
				self.file = self.url
				self.get_local()
			else:
				self._logs["msg"] = "Url %s sucessfully inserted into sources" %self.url
				url = check_url(self.url)[-1]
				
				self.insert_url(url,"manual", depth=0)			
		self.__COLL__.update({"_id": self.__data__["_id"]},{"$unset":{"url": self.url}})
		return self.__update_logs__()
		
	def delete_sources(self):
		self._logs["step"] = "deleting sources from user_input"
		self._logs["status"] = True
		self._logs["msg"] = "Urls sucessfully deleted"
		if hasattr(self, 'url'):
			ext = (self.url).split(".")[-1]
			if ext == "txt":
				self.file = self.url
				self.delete_local()
			else:
				url = check_url(self.url)[-1]
				if url in self.__db__.sources.distinct("url"):
					self.__db__.sources.remove({"url":url})
					self._logs["msg"] = "Succesfully deleted url %s to sources db of project %s"%(url, self.name)
				else:
					self._logs["msg"] = "No url %s found in sources db of %s project"%(url, self.name)
		else:
			self.__db__.sources.drop()
			self._logs["msg"] = "Succesfully deleted every url %s to seeds of crawl job %s"%(url, self.name)
		return self.__update_logs__()
		
	def insert_url(self, url, origin="default", depth=0):
		'''Insert or updated url into sources if false inserted or updated into logs'''
		self._logs["step"] = "inserting url"
		self._logs["status"] = True
		self._logs["msg"] = "Urls sucessfully inserted"
		status, status_code, error_type, url = check_url(url)
		is_source = self.__db__.sources.find_one({"url": url})
		
		#incorrect url
		if status is False:
			self._logs["status"] = False
			#existing
			if url in self.__db__.logs.distinct("url"):
				self._logs["msg"] = "Error inserting url: updated url %s in logs" %url
				self.__db__.logs.update({"url":url}, {"$push":{"date": self.date, "scope": self._logs["scope"], "msg":self._logs["msg"], "code": status_code}})
			#new
			else:
				#self._logs["msg"] = "Status is false error inserting url"
				self.__db__.logs.insert({"url":url, "status": status, "code": [status_code], "msg":[error_type], "origin":[origin], "depth":[depth],"scope":[self._logs["scope"]], "date": [self.date]})
			#self._logs['msg'] = "Incorrect url %s.\n%s\n Not inserted into sources" %(url, error_type)
		
		#existing url
		elif is_source is not None:
			self.__db__.sources.update({"url":url},{"$set":{"status": status, "code": status_code, "msg":error_type, "origin":origin, "depth":depth, "scope":"inserting"},"$push":{"date": self.date}})
			self._logs['msg'] = "Succesfully updated existing url %s into sources" %url
		
		#new url
		else:
			self.__db__.sources.insert({"url":url, "status": status, "code": status_code, "msg":error_type, "origin":origin, "depth":depth,"scope":"inserting", "date": [self.date]})
			self._logs['msg'] = "Succesfully inserted new url %s into sources" %url
		return self
		
	def delete_url(self, url):
		self._logs["step"] = "Deleting url"
		self._logs["status"] = True
		self._logs["msg"] = "Urls sucessfully deleted"
		if self.__db__.sources.find_one({"url": url}) is not None:
			self.__db__.sources.remove({"url":url})
			
		else:
			self._logs["msg"] = "Url can't be deleted. Url %s was not in sources. Check url format" %url
			self._logs["status"] = False
		
		return self.__update_logs__()
					
	
			
	def send_seeds_to_queue(self):
		self._logs["step"] = "Sending seeds urls to start crawl"
		for doc in self.__db__.sources.find():
			self.__db__.queue.insert({"url":doc["url"], "depth":doc["depth"], "status": doc["status"]})
		if self.__db__.queue.count() == 0:
			self._logs["msg"] = "Error while sending urls into queue: queue is empty"
			self._logs["code"] = 600.1
			self._logs["status"] = False
		return self._logs["status"]	
				
	def config(self):
		'''initializing  the crawl job with required params'''
		self._logs["scope"] = "config crawl job"
		self.query = None
		self.file = None
		self.option = None
		self.key = None
		for k, v in self.__data__.items():
			setattr(self,k,v)
			
		if self.query is not None:
			self.woosh_query = Query(self.query)
		if self.option == "expand_sources":
			self.expand_sources()
			
		if self.file is not None:
			print "Getting seeds from file %s" %self.file
			self.get_local(self.file)
				
		if self.key is not None:
			if self.query is None:
				self._logs["msg"] = "Unable to collect sources from Bing search no query has been set."
				self._logs["code"] = 600.1
				self._logs["status"] = False
			else:
				self.get_bing()
		
		
		
		
		if self.__db__.sources.count() == 0:
			self._logs["msg"] = "Unable to start crawl: no seeds have been set."
			self._logs["code"] = 600.2
			self._logs["status"] = False
			self.__update_logs__()
		else:
			self.send_seeds_to_queue()			
		self.__update_logs__()
		return "Config ok" 
		
	def start(self):
		print self.config()
		self._logs["msg"] = "Running crawl job  on %s" %self.date
		print self._logs["msg"] 
		start = dt.now()
		for doc in self.__db__.queue.find():
			print doc["url"], doc["depth"]
			if doc["url"] != "":
				s = Source(doc["url"])
					
				'''
				page = Page(doc["url"],doc["depth"])
				
					
				if page.check() and page.request() and page.control():
					
					#~ article = Article(page.url, page.raw_html, page.depth)
					#~ article.get()
					page.extract()
					#~ if  article.status is True:
						#~ print (article.status)
						#~ if article.is_relevant(self.query):		
							#~ if article.__repr__() not in self.__db__.results.find(article.__repr__()):
								#~ self.__db__.results.insert(article.__repr())
							#~ else:
								#~ article["status"] = False
								#~ article["msg"]= "article already in db"
								#~ self.__db__.logs.insert(article.__repr__())	
							#~ 
							#~ if article.outlinks is not None and len(article.outlinks) > 0:
								#~ #if article.outlinks not in self.__db__.results.find(article.outlinks) and article.outlinks not in self.__db__.logs.find(article.outlinks) and article.outlinks not in self.__db__.queue.find(article.outlinks):
								#~ for url in article.outlinks:
									#~ if url not in self.__db__.queue.distinct("url"):
										#~ self.__db__.queue.insert({"url":url, "depth": page.depth+1})
								#~ 
					#~ else:
						#~ print article.status
						#~ self.__db__.logs.insert(article.__repr__())	
				else:	
					self.__db__.logs.insert(article.__repr__())
			else:
				self.__db__.logs.insert(page.__repr__())
			'''
			self.__db__.queue.remove({"url": doc["url"]})
					
		end = dt.now()
		elapsed = end - start
		delta = end-start

		self._logs["msg"] = "%s. Crawl done sucessfully in %s s" %(self._logs["msg"],str(elapsed))
		self._logs["status"] = True
		return self.__update_logs__()
	
	def stop(self):
		self._logs["step"] = "Stopping exec of job of %s project %s" %(self.action, self.name)
		self._logs["msg"] = "Stopping crawl job on %s" %self.date
		self.__db__.queue.drop()
		self._logs["status"] = True	
		return self._logs["status"]
		#~ r = Report(self.name)
		#~ r.run_job()
		
				
class Archive(Job):
	
	#~ def schedule(self):
		#~ #super(Job, schedule)
		#~ print "archive"
		#~ pass
	def config(self):
		if self.__db__.queue.count() > 0:
			self.__db__.queue.drop()
		self.__db__.queue.insert({"url":self.name, "depth":0})
		return 
	def start(self):
		self.config()
		for doc in self.__db__.queue.find():
			if doc['url'] not in self.__db__.treated.find({"url":doc["url"]}):
				doc['status'], doc['status_code'], doc['error_type'], doc['url'] = check_url(doc['url'])
				if doc['status'] is False:
					self.__db__.logs.insert(doc)
				else:
					page = Page(doc["url"],doc["depth"])
					if page.check() and page.request() and page.control():
						article = Article(page.url, page.raw_html, page.depth)
						if article.get() is True:
							print article.links
						else:
							self.__db__.logs.insert(article.__repr__())
					else:
						self.__db__.logs.insert(page.__repr__())
			
			self.__db__.treated.insert(doc)
			self.__db__.queue.remove({"url": doc["url"]})				
			#put url in queue
			#page.extract()
		#~ except Exception as e:
			#~ print "Error in config %s" %e
			#~ self.delete()
		return True

class Export(Job):
	def __init__(self,doc):
		
		Job.__init__(self, doc)
		
		try:
			self.format = self.format
		except AttributeError:
			self.format = "json"
		try:
			self.coll_type = self.coll_type
		except AttributeError:
			self.coll_type = None
		
		self._dict_values = {}
		self._dict_values["sources"] = {
							"filename": "%s/export_%s_sources_%s.%s" %(self.project_name, self.name, self.date, self.format),
							"format": self.format,
							"fields": 'url,origin,date.date',
							}
		self._dict_values["logs"] = {
							"filename": "%s/export_%s_logs_%s.%s" %(self.project_name,self.name, self.date, self.format), 
							"format":self.format,
							"fields": 'url,code,scope,status,msg',
							}
		self._dict_values["results"] = {
							"filename": "%s/export_%s_results_%s.%s" %(self.project_name,self.name, self.date, self.format), 
							"format":self.format,
							"fields": 'url,domain,title,content.content,outlinks.url,crawl_date',
							}	
							
	def create(self):
		self._logs['step'] = "creating export"
		if self.__data__ is None:
			self._logs['msg'] =  "No active project found for %s" %self.name
			self._logs['status'] = False
			self.__update_logs__()
			return False
		else:
			self._logs['msg'] =  "Exporting"
			self._logs['status'] = True
			self.__update_logs__()
			if self.coll_type is not None:
				return self.export_one()
			else:
				return self.export_all()
		
			
	def export_all(self):
		self._logs['step'] = "export all"
		datasets = ['sources', 'results', 'logs']
		filenames = []
		for n in datasets:
			dict_values = self.dict_values[str(n)]
			if self.format == "csv":
				print ("- dataset '%s' in csv:") %n
				c = "mongoexport -d %s -c %s --csv -f %s -o %s"%(self.name,n,dict_values['fields'], dict_values['filename'])	
				filenames.append(dict_values['filename'])		
			else:
				print ("- dataset '%s' in json:") %n
				c = "mongoexport -d %s -c %s -o %s"%(self.name,n,dict_values['filename'])				
				filenames.append(dict_values['filename'])
			subprocess.call(c.split(" "), stdout=open(os.devnull, 'wb'))
			
			
			#subprocess.call(["mv",dict_values['filename'], self.project_name], stdout=open(os.devnull, 'wb'))
			print ("into file: '%s'") %dict_values['filename']
		
		ziper = "zip %s %s_%s.zip" %(" ".join(filenames), self.name, self.date)
		subprocess.call(ziper.split(" "), stdout=open(os.devnull, 'wb'))
		self._logs['status'] = True
		self._logs['msg']= "\nSucessfully exported 3 datasets: %s of project %s into directory %s" %(", ".join(datasets), self.name, self.project_name)		
		return self.__udpate_logs__()
	
	def export_one(self):
		self._logs['step'] = "export one"
		if self.coll_type is None:
			self._logs['status'] = False
			self._logs['msg'] =  "there is no dataset called %s in your project %s"%(self.coll_type, self.name)
			return self.__udpate_logs__()
		try:
			dict_values = self.dict_values[str(self.coll_type)]
			if self.form == "csv":
				print ("Exporting into csv")
				c = "mongoexport -d %s -c %s --csv -f %s -o %s"%(self.name,self.coll_type,dict_values['fields'], dict_values['filename'])
			else:
				print ("Exporting into json")
				c = "mongoexport -d %s -c %s --jsonArray -o %s"%(self.name,self.coll_type,dict_values['filename'])				
			subprocess.call(c.split(" "), stdout=open(os.devnull, 'wb'))
			#moving into report/name_of_the_project
			subprocess.call(["mv",dict_values['filename'], self.project_name], stdout=open(os.devnull, 'wb'))
			self._logs['status'] = False
			self._logs['msg'] =  "Sucessfully exported %s dataset of project %s into %s/%s" %(str(self.coll_type), str(self.name), self.project_name, str(dict_values['filename']))
			return self.__udpate__logs()
			
		except KeyError:
			self._logs['status'] = False
			self._logs['msg'] =  "there is no dataset called %s in your project %s"%(self.coll_type, self.name)
			return self.__udpate__logs()
			
	def start(self):
		if self.coll_type is not None:
			return self.export_one()
		else:
			return self.export_all()
			
					
class Report(Job):
	#~ def __init__(self, name, format="txt"):
		#~ date = dt.now()
		#~ self.name = name
		#~ self.db = Database(self.name)
		#~ self.date = date.strftime('%d-%m-%Y_%H-%M')
		#~ self.format = format
	def start(self):
		self._logs['step'] = "Generate report"
		if self.__data__ is None:
			self._logs['status']= False
			self._logs['msg'] =  "No active job found for %s. Enable to export" %self.name
			return self.__update_logs__()
		
		self._logs['status']= True
		self.report_date = self.date.strftime('%d-%m-%Y_%H-%M')
		self.directory = "%s/reports" %self.project_name
		if not os.path.exists(self.directory):
			os.makedirs(self.directory)
		filename = "%s/%s.txt" %(self.directory, self.report_date)
		d = Debug(self.__dict__)
		logs =  d.export()
		with open(filename, 'a') as f:
			f.write("\n======DATABASE INFO======\n")
			f.write(self.__db__.stats())
			f.write("\n======PROCESS INFO======\n")
			f.write(logs)
		self._logs['msg'] = ("Successfully generated report for %s\nReport name is: %s") %(self.name, filename)
		return self.__update_logs__()
	
			
class User(Job):
	def show(self):
		print "\n===================="
		print "USER:", (self.name.upper())
		print "===================="
		print "%i projects active" %(self.__COLL__.find({"user": self.name, "status":"active"}).count())
		if self.__COLL__.find({"user": self.name}) is None:
			print "User not registrated"
			return 
		for job in self.__COLL__.find({"user": self.name}):
			
			print "Job: ", job["action"]
			print "--------------"
			for k,v in job.items():
				if k == '_id' or k == 'status':
					continue
				if v is not False or v is not None:
					print k+":", v			
			print "--------------"
		
		print "____________________\n"
		return 
		
	def create(self):
		self._logs["step"] = "registering new user"
		self._logs["status"] = True
		self.user = self.name
		self.name = "none"
		self.action = "crawl"
		self.active = False
		j = Job(self.__dict__)
		return j.create()
	def delete(self):
		print self.name
		jobs = self.__COLL__.find({"user": self.name})
		if jobs is None:
			"No project found with user %s", self.name
		else:
			for job in jobs:
				print job
				j = Job(job)
				print j.delete()
		
	def unschedule(self):
		self._logs["step"] = "unscheduling user"
		self._logs["status"] = True
		
		if self.__COLL__.find({"user": self.name}) is None:
			self._logs["msg"] = "User not registrated"
			self._logs["status"] = True
			return 
		else:
			for job in self.__COLL__.find({"user": self.name}):
				print job["user"], job["name"]
				#print job.upsert({"_id": job['_id']}, {"$unset":{"user": self.name}})
				print self.__COLL__.insert({"_id": job['_id']}, {"$unset":{"user": self.name}})
			self._logs["msg"] = "User successfully unregistered from project"
		print self._logs["msg"]
		return self._logs
		
class Debug(Job):
	def export(self):
		msg_log = []
		for job in self.__COLL__.find({"name": self.name}):
			status = job['status']
			msg_log.append("Job is still active? "+str(job["active"]))
			for i, row in enumerate(status):
				m_row = str(i)+" "+",".join([row['step'], row['msg'], str(row['status'])])
				msg_log.append(m_row)
		return "\n".join(msg_log)		
	
	def start(self):
		msg_log = []
		msg_log.append("\n====================\nDEBUG:%s\n====================""%(self.name.upper()))
		
		for job in self.__COLL__.find({"name": self.name}):
			msg_log.append("Job is still active?\n"+ str(job["active"]))
			status = job['status']
			for i, row in enumerate(status):
				m_row = str(i)+" "+",".join([row['step'], row['msg'], str(row['status'])])
				msg_log.append(m_row)
		return "\n".join(msg_log)
			
class List(Job):
	def show(self):
		for job in self.__COLL__.find():
			try:
				print "-", job['name'], job['action'], job["active"], job["user"], job["date"].strftime('%d-%m-%Y')
			except KeyError:
				print job
				out = Job(job)
				out.delete()
