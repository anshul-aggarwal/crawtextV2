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
from scrapper.article import Article		
from utils import *

class Job(object):
	
	__DB__ = Database(TASK_MANAGER_NAME)
	__COLL__ = __DB__.use_coll(TASK_COLL)
	
	def __init__(self, name, doc): 
		self.name = name
		self.action = doc["action"]
		self.__data__ = self.__COLL__.find_one({"name":self.name})		
		self.project_name = re.sub('[^0-9a-zA-Z]+', '_', self.name)
		now = dt.now()
		self.date = now.replace(second=0, microsecond=0)
		self.status = []
		#value from db
		self.__db__ = Database(self.project_name)
		self.active = True
		self.date = dt.now()
		self._doc = doc
		self.logs = {}
		self.logs["date"] = self.date
		self.logs["active"] = True
		
	def __update_logs__(self):
		self.__COLL__.update({"_id":self.__data__["_id"]}, {"$push":{"status":self.logs}})
		print self.logs["msg"]
		return self.logs["status"]
										
	def create(self):
		if self.action == "job":
			self.action = "crawl"
		if not os.path.exists(self.project_name):
			os.makedirs(self.project_name)
		if ask_yes_no("Do you want to create a new project?"):
			added_value = []
			self.logs["step"] = "Creating %s job of project %s"%(self.action, self.name)
			print self.logs["step"]
			for k,v in self._doc.items():
				if k[0] != "_" and k not in self.__dict__.keys():
					self.added_value.append(k)
					setattr(self,k,v)
			self.__COLL__.insert(self.__repr__())
			self.logs["status"] = True
			if len(added_value) == 0:
				self.logs["msg"] = "Successfully created new '%s' job  for project '%s'" %(self.action, self.name)
				
				if self.action == "crawl":
					print "Be careful, crawl jobs needs more parameters to be active such as query and at least one source url. Check documentation on how to proceed and update this current job"
			else:
				self.logs["msg"] = "Successfully created new '%s' job  for project '%s' with parameters:" %(self.action, self.name, ", ".join(self.added_values))
				
			return self.__update_logs__()
		
	def update(self):
		if self.action == "job":
			self.action = "crawl"
		if self.__data__ is None:
			print "No active '%s' job fro project '%s'found" %(self.action, self.name)
			self.create()
		else:	
			self.logs["step"] = "Updating %s job of project %s"%(self.action, self.name)
			print self.logs["step"]
			self.updated_value = []
			
			for k,v in self._doc.items():
				if k[0] != "_" and v not in self.__data__.values():
					self.updated_value.append(k)
					self.__COLL__.update({"_id":self.__data__["_id"]}, {"$set":{k:v}})
			if len(self.updated_value) == 0:
				self.logs["msg"] = "No change for '%s' job project %s. Parameters given are the same." %(self.action, self.name)
				self.logs["status"] = False
			else:	
				self.logs["status"] = True
				self.logs["msg"] = "Successfully updated '%s' job  for project '%s' with parameters: %s" %(self.action, self.name, ", ".join(self.updated_value))
		self.__update_logs__()	
		return self.logs['status']
		
	def start(self):
		self.logs["step"] = "Executing job"
		if self.job_list is None:
			self.logs["msg"] =  "No active job found for %s" %(self.name)
			print self.logs["msg"]
			return self.create_job()
		else:
			for doc in self.__items__:
				func = doc["action"].capitalize()
				instance = globals()[func]
				
				job = instance(self.name)
				
				self.__get_config__(job)
				if job.run_job() is False:
					self.COLL.update({"name":self.name}, {"$set": {"active": "False"}})
					self.logs = job.logs
				self.COLL.update({"name":self.name, "action":self.action}, {"$push": {"status": job.logs}})
				print self.logs["msg"]
				return self.COLL.update({"name":self.name, "action":self.action}, {"$push": {"status": self.logs}})
			#~ self.COLL.update({"name":self.name, "action":"crawl"}, {"$inc": {"nb_run": 1}})	
			#~ self.COLL.update({"name":self.name, "action":"crawl"},  {"$set":{"next_run":self.next_run, 'last_run': self.last_run}})
			#~ self.refresh_task()
			#~ return self.update_status()		
	def stop(self):
		self.logs["step"] = "Stopping execution of job"
		self.COLL.update({"name":self.name, "action":self.action}, {"$push": {"status": self.logs}})
		for doc in self.job_list:
			func = doc["action"].capitalize()
			instance = globals()[func]
			job = instance(self.name)		
			self.__get_config__(job)
			job.stop()
			self.COLL.update({"name":self.name, "action":self.action}, {"$push": {"status": job.logs}})
			print (job.logs["msg"])
			self.COLL.update({"name":self.name}, {"$set": {"active": "False"}})	
			return self.COLL.update({"name":self.name, "action":self.action}, {"$push": {"status": self.logs}})
			
	def schedule(self):
		self.logs["step"] = "Scheduling project"
		if self.update():
			
			self.logs["status"] = True
			self.logs["msg"] = "Sucessfully schedule project"
		else:
			self.logs["status"] = True
			self.logs["msg"] = "No schedule done for project"
		return self.__update_logs__()
		
	def unschedule(self):
		self.logs["step"] = "Unscheduling job"
		
		print self.logs["msg"]
		if self.name in self.__COLL__.distinct("name"):
			for n in self.__COLL__.find({"name": self.name}):
				self.__COLL__.remove({"name":n['name']})
			self.logs["msg"] = "All tasks of project %s has been sucessfully unscheduled." %(self.name)
			self.logs["status"] = True
		else:
			self.logs["msg"] = "No project %s found" %(self.name)	
			self.logs["status"] = False
		self.__COLL__.update({"name":self.name}, {"$set": {"active": "False"}})	
		return self.__COLL__.update({"name":self.name, "action":self.action}, {"$push": {"status": self.logs}})	
	
	def debug(self):
		print "\n===================="
		print "DEBUG:", (self.name.upper())
		print "===================="
		
		for job in self.__COLL__.find({"name": self.name}):
			print "Job is still active?", job["active"]
			status = job['status']
			for i, row in enumerate(status):
				print i, ",".join([row['step'], row['msg'], str(row['status'])])
		return
		
	def delete(self):
		'''delete project and archive results'''
		if self.__data__ is None:
			print "No project %s found. check the name of your project" %(self.name)
			return
		self.logs["step"] = "Deleting job"
		self.logs["msg"] = "Project %s sucessfully deleted." %self.project_name
		self.logs["status"] = True
		print self.logs["step"]
		if self.__db__.use_coll("results").count() > 0 or self.__db__.use_coll("sources").count()> 0 or self.__db__.use_coll("logs").count()> 0:
			
			if ask_yes_no("Do you want to export first all data from project?"):
				job = Export(self.project_name)
				job.run_job()
			if ask_yes_no("Do you want to delete all data from project?"):
				self.__db__.drop(collection, "results")
				self.__db__.drop(collection, "logs")
				self.__db__.drop(collection, "sources")
				self.__db__.client.drop_database(self.name)
			if ask_yes_no("Do you want to delete directory of the project?"):
				shutil.rmtree("%s") %("/"+self._project_name)
		else:
			print "No data found for project %s"%(self.name)
			shutil.rmtree(self.project_name)
			print "Deleting directory %s" %(self.project_name)
		self.__COLL__.update({"name":self.name}, {"$set": {"active": "False"}})	
		return self.logs["status"]
	
	def show(self, debug=False):
		if debug:
			self.debug()
		else:		
			print "\n===================="
			print (self.name.upper())
			print "===================="
			for job in self.__COLL__.find({"name": self.name}):
				if job["active"] !=  "False":
					print "Job: ", job["action"]
					print "--------------"
					for k,v in job.items():
						if k == '_id' or k == 'status':
							continue
						if v is not False or v is not None:
							print k+":", v
						
							
					print "--------------"
				else:
					status = job['status']
					
					print "Job: ", job["action"], "is inactive."
					print "Last task was :", job["status"][-1]['step']
					print "Error on :", job["status"][-1]['msg']
			print "____________________\n"
			return 
			pass
	
	def __repr__(self):
		'''representing public info'''
		self.__data__ = {}
		for k,v in self.__dict__.items():
			if k.startswith("_"):
				pass
			else:
				self.__data__[k] = v	
		return self.__data__
		
	def list(self):
		for doc in self.__COLL__.find({"name":self.name}):
			print doc
class Crawl(Job):
	#~ def __init__(self, name): 
		#~ self.Job.__init__(self, name)
		#~ self.name = name
		#~ self.option = None
		#~ self.file = None
		#~ self.key = None
		#~ self.query = None		
		#~ self.db = Database(self.name)
		#~ self.db.create_colls(['sources', 'results', 'logs', 'queue'])	
		#~ self.logs = {}
		#~ self.logs["step"] = "crawl init"
		#~ date = dt.now()
		#~ self.date = date.strftime('%d-%m-%Y_%H:%M')
	def update_sources(self):
		print ("udpate sources")
		pass
	
	def get_bing(self, key=None):
		''' Method to extract results from BING API (Limited to 5000 req/month) automatically sent to sources DB ''' 
		self.logs["step"] = "bing extraction"
		if key is not None:
			self.key = key
		
		#~ print "There is already %d sources in database" %nb
		#~ print "and %d sources with a bad status" %self.db.sources.find({"status":"false"}).count()
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
			for url in url_list:
				self.insert_url(url,origin="bing",depth=0)
			count = self.db.sources.count() - nb
			self.logs["msg"] =  "Inserted %s urls from Bing results. Sources nb is now : %d" %(count, nb)
			self.logs["status"] = True
		
		except Exception as e:
			#raise requests error if not 200
			try:
				if r.status_code is not None:
					self.logs["code"] = r.status_code
					self.logs["status"] = False
					self.logs["msg"] = "Error requestings new sources from Bing :%s" %e
					#~ print "Error requestings new sources from Bing :%s" %e
					
			except Exception as e:
				#~ print "Error requestings new sources from Bing :%s" %e
				self.logs["code"] = float(str(601)+"."+str(e.args[0]))
				self.logs["msg"] = "Error fetching results from BING API. %s" %e.args
				self.logs["status"] = False
		
		return self.logs["status"]		
		
		
	def get_local(self, afile = None):
		''' Method to extract url list from text file'''
		self.logs["step"] = "local file extraction"
		if afile is None:
			afile = self.file
		try:
			for url in open(afile).readlines():
				if url == "\n":
					continue
				url = re.sub("\n", "", url)
				status, status_code, error_type, url = check_url(url)
				self.insert_url(url, origin="file", depth=0)
				
			self.logs["status"] = True
			self.logs["msg"] = "Urls from file %s have been successfuly added to sources" %(afile)
			
		
		except Exception as e:
			#~ print "Please verify that your file is in the current directory. To set up a correct filename and add directly to sources:\n\t crawtext.py %s -s append your_sources_file.txt" %(e.args[1],self.file, self.name)
			self.logs["code"] = float(str(602)+"."+str(e.args[0]))
			self.logs["status"] = False
			self.logs["msg"]= "Failed inserting url for file %s : %s '." %(self.file, e.args[1])
		return self.logs["status"]		
		
	def delete_local(self):
		'''delete sources contained in self.file'''
		self.logs["step"] = "deleting sources from file"
		self.logs["status"] = True
		self.logs["msg"] = "Urls sucessfully deleted"
		#~ print "Removing the list of url contained in the file %s" %self.file
		try:
			for url in open(self.file).readlines():
				url = re.sub("\n", "", url)
				self.db.sources.remove({"url":url})	
		except Exception as e:
			#~ print "Please verify that your file is in the current directory. To set up a correct filename and add directly to sources:\n\t crawtext.py %s -s append your_sources_file.txt" %(e.args[1],self.file, self.name)
			self.logs["code"] = float(str(602)+"."+str(e.args[0]))
			self.logs["status"] = False
			self.logs["msg"]= "Failed deleting url for file %s failed : %s '." %(self.file, e.args[1])
		return self.logs["status"]
		
	def expand_sources(self):
		'''Expand sources url adding results urls collected from previous crawl'''
		self.logs["step"] = "expanding sources from results"
		self.logs["status"] = True
		self.logs["msg"] = "Urls from results sucessfully inserted into sources"
		for url in self.db.results.distinct("url"):
			self.insert_url(url, "automatic", depth=0)
		
		if len(self.db.results.distinct("url")) == 0 :
			self.logs["status"] = False
			self.logs["code"] = 603
			self.logs["msg"] = "No results to put in seeds. Expand option failed"
		return self.logs["status"]
			
	def add_sources(self):
		self.logs["step"] = "adding sources from user_input"
		self.logs["status"] = True
		self.logs["msg"] = "Urls sucessfully inserted into sources"
		if hasattr(self, 'url'):
			ext = (self.url).split(".")[-1]
			if ext == "txt":
				self.file = self.url
				self.get_local()
			else:
				self.logs["msg"] = "Url %s sucessfully inserted into sources" %self.url
				url = check_url(self.url)[-1]
				self.insert_url(url,"manual", depth=0)			
		return self.logs["status"]
		
	def delete_sources(self):
		self.logs["step"] = "deleting sources from user_input"
		self.logs["status"] = True
		self.logs["msg"] = "Urls sucessfully deleted"
		if hasattr(self, 'url'):
			ext = (self.url).split(".")[-1]
			if ext == "txt":
				self.file = self.url
				self.delete_local()
			else:
				url = check_url(self.url)[-1]
				if url in self.db.sources.distinct("url"):
					self.db.sources.remove({"url":url})
					self.logs["msg"] = "Succesfully deleted url %s to sources db of project %s"%(url, self.name)
				else:
					self.logs["msg"] = "No url %s found in sources db of %s project"%(url, self.name)
		else:
			self.db.sources.drop()
			self.logs["msg"] = "Succesfully deleted every url %s to seeds of crawl job %s"%(url, self.name)
		return self.logs["status"]
		
	def insert_url(self, url, origin="default", depth=0):
		'''Insert or updated url into sources if false inserted or updated into logs'''
		self.logs["step"] = "inserting url"
		self.logs["status"] = True
		self.logs["msg"] = "Urls sucessfully inserted"
		status, status_code, error_type, url = check_url(url)
		is_source = self.db.sources.find_one({"url": url})
		
		#incorrect url
		if status is False:
			self.logs["status"] = False
			#existing
			if url in self.db.logs.distinct("url"):
				self.logs["msg"] = "Error inserting url: updated url %s in logs" %url
				self.db.logs.update({"url":url}, {"$push":{"date": self.date, "scope": self.logs["scope"], "msg":self.logs["msg"], "code": status_code}})
			#new
			else:
				self.logs["msg"] = "Error inserting url: inserted url %s in logs"%url
				self.db.logs.insert({"url":url, "status": status, "code": [status_code], "msg":[error_type], "origin":origin, "depth":depth,"scope":[self.logs["scope"]], "date": self.date})
			self.logs['msg'] = "Incorrect url %s.\n%s\n Not inserted into sources" %(url, error_type)
		
		#existing url
		elif is_source is not None:
			self.db.sources.update({"url":url},{"$set":{"status": status, "code": status_code, "msg":error_type, "origin":origin, "depth":depth, "scope":"inserting"},"$push":{"date": self.date}})
			self.logs['msg'] = "Succesfully updated existing url %s into sources" %url
		
		#new url
		else:
			self.db.sources.insert({"url":url, "status": status, "code": status_code, "msg":error_type, "origin":origin, "depth":depth,"scope":"inserting", "date": [self.date]})
			self.logs['msg'] = "Succesfully inserted new url %s into sources" %url
		return self.logs["status"] 
		
	def delete_url(self, url):
		self.logs["step"] = "Deleting url"
		self.logs["status"] = True
		self.logs["msg"] = "Urls sucessfully deleted"
		if self.db.sources.find_one({"url": url}) is not None:
			self.db.sources.remove({"url":url})
			
		else:
			self.logs["msg"] = "Url can't be deleted. Url %s was not in sources. Check url format" %url
			self.logs["status"] = False
		
		return self.logs["status"]
					
	def delete(self):
		''' Deleting sources from user_input'''
		self.logs["step"] = "Deleting sources"
		#~ e = Export(self.name, "json","sources")
		#~ e.run_job()
		self.db.sources.drop()
		self.logs["msg"] = 'Every single source has been deleted from project %s.'%self.name		
		return self.logs["status"]
		
	def collect_sources(self):
		''' collect sources from options expand key or file'''
		self.logs["step"] = "Collecting sources"
		self.logs["status"] = True
		if self.option == "expand_sources":
			self.expand_sources()
			
				
		if self.file is not None:
			#print "Getting seeds from file %s" %self.file
			self.get_local(self.file)
				
		if self.key is not None:
			if self.query is None:
				self.logs["msg"] = "Unable to collect sources from Bing search no query has been set."
				self.logs["code"] = 600.1
				self.logs["status"] = False
				
			else:
				self.get_bing() 
		return self.logs["status"]
			
	def send_seeds_to_queue(self):
		self.logs["step"] = "Sending seeds urls to start crawl"
		for doc in self.db.sources.find():
			self.db.queue.insert({"url":doc["url"], "depth":doc["depth"], "status": doc["status"]})
		if self.db.queue.count() == 0:
			self.logs["msg"] = "Error while sending urls into queue: queue is empty"
			self.logs["code"] = 600.1
			self.logs["status"] = False
		return self.logs["status"]	
				
	def config(self):
		'''initializing  the crawl job with required params'''
		self.logs["scope"] = "config crawl job"
		if self.query is not None:
			self.query = Query(self.query)
		
		self.collect_sources()
		
		if self.db.sources.count() == 0:
			self.logs["msg"] = "Unable to start crawl: no seeds have been set."
			self.logs["code"] = 600.2
			self.logs["status"] = False
			print (self.logs)
		else:
			self.send_seeds_to_queue()			
		
		return self.logs["status"]
		
	def run_job(self):
		if self.config() is False:
			return self.logs
		
		self.logs["msg"] = "Running crawl job  on %s" %self.date
		start = dt.now()
		for doc in self.db.queue.find():
			if doc["url"] != "":
				page = Page(doc["url"],doc["depth"])
				page = Page(doc["url"],0)
					
				if page.check() and page.request() and page.control():
					article = Article(page.url, page.raw_html, page.depth)
					if article.get() is True:
						print (article.status)
						if article.is_relevant(self.query):		
							if article.status not in self.db.results.find(article.status):
								self.db.results.insert(article.status)
							else:
								article["status"] = False
								article["msg"]= "article already in db"
								self.db.logs.insert(article.status)	
							
							if article.outlinks is not None and len(article.outlinks) > 0:
								#if article.outlinks not in self.db.results.find(article.outlinks) and article.outlinks not in self.db.logs.find(article.outlinks) and article.outlinks not in self.db.queue.find(article.outlinks):
								for url in article.outlinks:
									if url not in self.db.queue.distinct("url"):
										self.db.queue.insert({"url":url, "depth": page.depth+1})
								
					else:
						self.db.logs.insert(article.status)	
				else:	
					self.db.logs.insert(article.status)
			else:
				self.db.logs.insert(page.status)
			self.db.queue.remove({"url": doc["url"]})
					
		end = dt.now()
		elapsed = end - start
		delta = end-start

		self.logs["msg"] = "%s. Crawl done sucessfully in %s s" %(self.logs["msg"],str(elapsed))
		self.logs["status"] = True
		return self.logs
	
	def stop(self):
		self.logs["step"] = "Stopping exec of job of %s project %s" %(self.action, self.name)
		self.logs["msg"] = "Stopping crawl job on %s" %self.date
		self.db.queue.drop()
		self.logs["status"] = True	
		return self.logs["status"]
		#~ r = Report(self.name)
		#~ r.run_job()
		
				
class Archive(Job):
	
	#~ def schedule(self):
		#~ #super(Job, schedule)
		#~ print "archive"
		#~ pass
	def run_job(self):
		print ("Archiving %s") %self.name
		return True

class Export(object):
	#~ def __init__(self, name, form=None, coll_type=None):
		#~ 
		#~ date = datetime.today()
		#~ self.date = date.strftime('%d-%m-%Y')
		#~ self.form = form
		#~ if self.form is None:
			#~ self.form = "json"
		#~ 
		#~ 
		#~ self.name = name
		#~ self.coll_type = coll_type
		#~ self.dict_values = {}
		#~ self.dict_values["sources"] = {
							#~ "filename": "export_%s_sources_%s.%s" %(self.name, self.date, self.form),
							#~ "format": self.form,
							#~ "fields": 'url,origin,date.date',
							#~ }
		#~ self.dict_values["logs"] = {
							#~ "filename": "export_%s_logs_%s.%s" %(self.name, self.date, self.form), 
							#~ "format":self.form,
							#~ "fields": 'url,code,scope,status,msg',
							#~ }
		#~ self.dict_values["results"] = {
							#~ "filename": "export_%s_results_%s.%s" %(self.name, self.date, self.form), 
							#~ "format":self.form,
							#~ "fields": 'url,domain,title,content.content,outlinks.url,crawl_date',
							#~ }	
		#~ 
			
	def export_all(self):
		datasets = ['sources', 'results', 'logs']
		filenames = []
		for n in datasets:
			dict_values = self.dict_values[str(n)]
			if self.form == "csv":
				print ("- dataset '%s' in csv:") %n
				c = "mongoexport -d %s -c %s --csv -f %s -o %s"%(self.name,n,dict_values['fields'], dict_values['filename'])	
				filenames.append(dict_values['filename'])		
			else:
				print ("- dataset '%s' in json:") %n
				c = "mongoexport -d %s -c %s -o %s"%(self.name,n,dict_values['filename'])				
				filenames.append(dict_values['filename'])
			subprocess.call(c.split(" "), stdout=open(os.devnull, 'wb'))
			#moving into report/name_of_the_project
			
			subprocess.call(["mv",dict_values['filename'], self.directory], stdout=open(os.devnull, 'wb'))
			print ("into file: '%s'") %dict_values['filename']
		ziper = "zip %s %s_%s.zip" %(" ".join(filenames), self.name, self.date)
		subprocess.call(ziper.split(" "), stdout=open(os.devnull, 'wb'))
		return "\nSucessfully exported 3 datasets: %s of project %s into directory %s" %(", ".join(datasets), self.name, self.directory)		
	
	def export_one(self):
		if self.coll_type is None:
			return "there is no dataset called %s in your project %s"%(self.coll_type, self.name)
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
			subprocess.call(["mv",dict_values['filename'], self.directory], stdout=open(os.devnull, 'wb'))
			return "Sucessfully exported %s dataset of project %s into %s/%s" %(str(self.coll_type), str(self.name), self.directory, str(dict_values['filename']))
		except KeyError:
			return "there is no dataset called %s in your project %s"%(self.coll_type, self.name)
			
	def run_job(self):
		if self.coll_type is not None:
			return self.export_one()
		else:
			return self.export_all()
			
					
class Report(object):
	def __init__(self, name, format="txt"):
		date = dt.now()
		self.name = name
		self.db = Database(self.name)
		self.date = date.strftime('%d-%m-%Y_%H-%M')
		self.format = format
	
	def txt_report(self):
		name = re.sub("[^0-9a-zA-Z]","_", self.name)
		self.directory = "%s/reports" %name
		if not os.path.exists(self.directory):
			os.makedirs(self.directory)
		filename = "%s/Report_%s_%s.txt" %(self.directory, self.name, self.date)
		with open(filename, 'a') as f:
			f.write(self.db.stats())
		print ("Successfully generated report for %s\nReport name is: %s") %(self.name, filename)
		return True
	
	def html_report(self):
		pass
	def email_report(self):
		pass			
	def run_job(self):
		if self.format == "txt":
			return self.txt_report()
		else:
			raise NotImplemented
			
class User(Job):
	pass


	
