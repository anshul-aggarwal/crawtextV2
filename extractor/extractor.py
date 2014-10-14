#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from copy import deepcopy
from parsers import Parser
from cleaners import StandardDocumentCleaner
from formatters import StandardOutputFormatter
from extractors import StandardContentExtractor
import datetime
from BeautifulSoup import BeautifulSoup as bs
import nltk
from utils.url import check_url
from packages.requests import requests
from random import choice
#from page import Page

class Page(object):
	'''Generic Extractor'''
	def __init__(self, url, depth = 0):
		self.url = url
		self.depth = depth
		self.date = datetime.datetime.now()
		#self.type = type
		self._logs = {"msg":None, "status": True, "code": None, "step": "page creation", "url": self.url}
		
	def check_status(self):
		if self.check():
			if self.request(): 
				if self.control():
					return True
		print self._logs
		return False

		

	def xtract(self, type="article"):
		if self.check_status():
			rety


			# 	if self.control():
			# 		print "Ok"
		
		# 	self.run(type)
		# else:
		# 	print self._logs["status"]

	def check(self):
		self._logs["step"] = "check page"
		self._logs["status"], self._logs["code"], self._logs["msg"], self._logs["url"] = check_url(self.url)
		self.url = self._logs["url"]
		return self._logs['status']
		
	def request(self):
		'''Bool request a webpage: return boolean and update raw_html'''
		self._logs["step"] = "request page"
		try:
			requests.adapters.DEFAULT_RETRIES = 2
			# user_agents = [u'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1', u'Mozilla/5.0 (Windows NT 6.1; rv:15.0) Gecko/20120716 Firefox/15.0a2', u'Mozilla/5.0 (compatible; MSIE 10.6; Windows NT 6.1; Trident/5.0; InfoPath.2; SLCC1; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729; .NET CLR 2.0.50727) 3gpp-gba UNTRUSTED/1.0', u'Opera/9.80 (Windows NT 6.1; U; es-ES) Presto/2.9.181 Version/12.00']
			# headers = {'User-Agent': choice(user_agents),}
			proxies = {"https":"77.120.126.35:3128", "https":'88.165.134.24:3128', }
			try:

				# self._req = requests.get((self.url), headers = headers ,allow_redirects=True, proxies=None, timeout=5)
				self._req = requests.get(self.url, allow_redirects=True, timeout=5)
				try:
					self.raw_html = self._req.text
					self._logs["msg"] = "Request is Ok"
					self._logs["status"] = True
					self._logs["code"] = 200
					return self._logs["status"]
					
				except Exception as e:
					self._logs["msg"] = "Request answer was not understood %s" %e
					self._logs["code"] = 400
					self._logs["status"] = False
					return self._logs["status"]
					
			except Exception as e:
				self._logs["msg"] = "Request answer was not understood %s" %e
				self._logs["code"] = 400
				self._logs["status"] = False
				return self._logs["status"]
				
		except requests.exceptions.MissingSchema:
			self._logs["msg"] = "Incorrect url - Missing sheme for : %s" %self.url
			self._logs["code"] = 406
			self._logs["status"] = False
			return self._logs["status"]
		except Exception as e:
			self._logs["msg"] = "Another wired exception: %s %s" %(e, e.args)
			self._logs["code"] = 204
			self._logs["status"] = False
			return self._logs["status"]
		
	def control(self):
		'''Bool control the result if text/html or if content available'''
		self._logs["step"] = "control"
		#Content-type is not html 
		try:
			self._req.headers['content-type']
			if 'text/html' not in self._req.headers['content-type']:
				self._logs["msg"]="Content type is not TEXT/HTML"
				self._logs["code"] = 404
				self._logs["status"] = False
				
			#Error on ressource or on server
			elif self._req.status_code in range(400,520):
				self._logs["code"] = self.req.status_code
				self._logs["msg"]="Request error on connexion no ressources or not able to reach server"
				self._logs["status"] = False
				
			#Redirect
			#~ elif len(self.req.history) > 0 | self.req.status_code in range(300,320): 
				#~ self.error_type="Redirection"
				#~ self.bad_status()
				#~ return False
			else:
				self._logs["msg"] = "Control is Ok"
				self._logs["status"] = True
		#Headers problems		
		except Exception as e:
			print e
			self._logs["msg"]="Request headers were not found"
			self._logs["code"] = 403
			self._logs["status"] = False
		return self._logs["status"]
	
	
	def run(type):
		if type == "article":
			return Article(self.url, self.raw_html, self.depth)
		elif type == "defaut":
			raise TypeError
		else:
			raise TypeError
		 	


class Article(object):
	'''Article'''
	def __init__(self, url, raw_html, depth, language="fr"):
		self.status = True
		self.url = url
		self.depth = step
		self.lang = lang
		self.raw_html = raw_html
		# title of the article
		self.title = None	
		#text
		self.article = u""
		self.cleaned_text = u""
		# meta
		self.meta_description = u""
		self.meta_lang = u""
		self.meta_favicon = u""
		self.meta_keywords = u""
		#link and domain
		self.canonical_link = u""
		self.domain = u""
		# cleaned text
		self._top_node = None
		self.tags = []
		self.final_url = url
		self.raw_html = raw_html
		# the lxml Document object
		self._parser = Parser()
		self.raw_doc = u""
		self.publish_date = None
		self.additional_data = {}
		self.links = []
		self.outlinks = []
		self.inlinks = []
		self.start_date = datetime.datetime.today()

	def get(self):
		try:
			self._doc = self._parser.fromstring(self.raw_html)
			#init extractor method
			extractor = StandardContentExtractor(self,"en")	
			# init the document cleaner
			cleaner = StandardDocumentCleaner(self)
			# init the output formatter
			formatter = StandardOutputFormatter(self, stopwords_class="en")
			#doc
			#self.doc = doc
			self.raw_doc = deepcopy(self.raw_html)
			
			self.title = extractor.get_title()
			#self.title = self.title
			#meta
			self.meta_lang = extractor.get_meta_lang()
			#self.meta_favicon = extractor.get_favicon()
			self.meta_description = extractor.get_meta_description()
			self.meta_description = self.meta_description.decode("utf-8")
			self.meta_keywords = extractor.get_meta_keywords()
			
			#domain and url
			self.canonical_link = extractor.get_canonical_link()
			self.domain = extractor.get_domain()
			#~ 
			#~ #tag
			self.tags = extractor.extract_tags()
			#~ #text
			self._doc = cleaner.clean()
			
			self._top_node = extractor.calculate_best_node()
			if self._top_node is not None:
				# post cleanup
				self._top_node = extractor.post_cleanup(self._top_node)
				
			# clean_text
			#self.cleaned_text = formatter.get_formatted_text()
			
			
			#self.content = self.content.decode("utf-8")
			self.links = extractor.get_links()
			self.outlinks = [{"url":url, "step": self.step+1} for url in extractor.get_outlinks()]
			self.outlinks = [{"url":url, "step": self.step+1} for url in extractor.get_inlinks()]
			try:
				self.article = formatter.get_formatted_text()
				
			except Exception as e:
				try:
					self.article = bs(self.raw_html).getText()
					self.article = nltk.clean_html(self.article)
				except Exception as e:
					print e
					self.article  = re.sub(r'<.*?>', '', self.raw_html)
			#self.inlinks, self.inlinks_err = extractor.get_outlinks(self.links)
			# TODO
			# self.article.publish_date = self.extractor.get_pub_date(doc)
			# self.article.additional_data = self.extractor.more(doc)
			
			return True
			
		except Exception as e:
			
			self._logs = {
				"url": self.url,
				"scope": "article extraction",
				"msg": e.args,
				"status": False,
				"code": -2
				}
			return False
				
	
	def __repr__(self):
		for k, v in self.__dict__.items():
			if k.startswith("_"):
				delattr(self, k)
		
		return self.__dict__
		#~ self.status ={
				#~ "url": self.canonical_link,
				#~ "domain": self.domain,
				#~ "title": self.title.encode("utf-8"),
				#~ "content": self.content,
				#~ "description": self.meta_description.encode("utf-8"),
				#~ "outlinks": self.outlinks,
				#~ "crawl_date": self.start_date,
				#~ "raw_html": self.raw_html,
				#~ }
		#~ return self.status
	
	def is_relevant(self, query):
		self.article = {"title":unicode(self.title), "content": unicode(self.article)}
		if self.woosh_query.match(self.article) is False:
			self._logs = {"url":self.url, "depth": self.depth, "code": -1, "msg": "Not Relevant","status": False, "title": self.title, "content": self.article[0:500]}
			return False
		# elif self.woosh_query(self.url) is False:

		else:
			self.__repr__()
			return True
