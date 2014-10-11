#!/usr/bin/env python
# -*- coding: utf-8 -*-

#from __future__ import print_function

import datetime
from os.path import exists
import sys
import requests
import json
import re
#from goose import Goose
from pymongo import errors as mongo_err
#from bs4 import BeautifulSoup as bs
#import beautifulsoup4 as bs
from urlparse import urlparse
from random import choice
from tld import get_tld
#from scrapper import *
from utils.url import *
#from scrapper.article import Article
#~ from scrapper.parsers import Parser
#~ from scrapper.cleaners import StandardDocumentCleaner
#~ from scrapper.formatters import StandardOutputFormatter
#~ from scrapper.extractors import StandardContentExtractor

from newspaper import Article

class Source(object):
	def __init__(self, url): 
		self._logs = {}
		self.url = self.check(url)
		if self._logs["status"] is True:
			self.extract()
		else:
			print self._logs
	def check(self, url):
		self._logs["step"] = "check page"
		self._logs["status"], self._logs["code"], self._logs["msg"], self._logs["url"] = check_url(url)
		return self._logs["url"]
		
	def extract(self):
		article = Article(self.url, language="fr")
		article.download()
		article.parse()
		article.nlp()
		print article.title
		print len(article.links)
		print len(article.outlinks)
		try:
			article.nlp()
		except UnicodeDecodeError:
			article.keywords = []
			article.summary = ""
		
		for k, v in article.__dict__.items():
			if k[0] != "_":
				setattr(self, k,v)
		
		return self.__dict__
		#~ self.content = article.text
		#~ self.title = article.title
		#~ self.authors = article.authors	
		#~ self.images = article.images
		#~ self.movies = article.movies
		#~ 
		#~ self.keyword = article.keywords
		#~ self.summary = article.summary
		
			
		
		
class Page(object):
	'''Page factory'''
	def __init__(self, url, depth = 0, output_format="defaut"):
		self.url = url
		#~ if query is not None:
			#~ self.match_query = regexify(query)
		self.depth = depth
		self.crawl_date = datetime.datetime.now()
		self._logs = {"msg":None, "status": None, "code": None, "step": "page creation", "url": self.url}
		self.output_format = output_format
		
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
			user_agents = [u'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1', u'Mozilla/5.0 (Windows NT 6.1; rv:15.0) Gecko/20120716 Firefox/15.0a2', u'Mozilla/5.0 (compatible; MSIE 10.6; Windows NT 6.1; Trident/5.0; InfoPath.2; SLCC1; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729; .NET CLR 2.0.50727) 3gpp-gba UNTRUSTED/1.0', u'Opera/9.80 (Windows NT 6.1; U; es-ES) Presto/2.9.181 Version/12.00']
			headers = {'User-Agent': choice(user_agents),}
			proxies = {"https":"77.120.126.35:3128", "https":'88.165.134.24:3128', }
			try:
				self.req = requests.get((self.url), headers = headers,allow_redirects=True, proxies=None, timeout=5)
				
				try:
					self.raw_html = self.req.text
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
			self.req.headers['content-type']
			if 'text/html' not in self.req.headers['content-type']:
				self._logs["msg"]="Content type is not TEXT/HTML"
				self._logs["code"] = 404
				self._logs["status"] = False
				
			#Error on ressource or on server
			elif self.req.status_code in range(400,520):
				self._logs["code"] = self.req.status_code
				self._logs["msg"]="Request error on connexion no ressources or not able to reach server"
				self._logs["status"] = False
				
			#Redirect
			#~ elif len(self.req.history) > 0 | self.req.status_code in range(300,320): 
				#~ self.error_type="Redirection"
				#~ self.bad_status()
				#~ return False
			else:
				self._logs["status"] = True
		#Headers problems		
		except Exception:
			self._logs["msg"]="Request headers were not found"
			self._logs["code"] = 403
			self._logs["status"] = False
		return self._logs["status"]	
	
			
	def extract(self):
		'''Dict extract content and info of webpage return boolean and self.info'''	
		_class = self.output_format.capitalize()
		instance = globals()[_class](self.__repr__())()
		print instance
		return instance.extract()
		#self._logs["step"] = "extract %s" %type
		#if self.output_format
			
		#~ a = Article(self.url, self.raw_html)
		#~ return a.get()
	def __main__(self):
		if self.check() and self.request() and self.control():
			print self.extract()
		else:
			print self._logs
			return self._logs["status"]	
	def __repr__(self):	
		for k, v in self.__dict__.items():
			if k.startswith("_"):
				delattr(self, k)
		return self.__dict__
	'''
	def is_relevant(self, query, content):
		if query.match(self,unicode(content)) is False:
			self._logs = {"url":self.url, "code": -1, "msg": "Not Relevant","status": False, "title": self.title, "content": self.content}
			return False
		else:
			self._logs = 
			return True
							 	
	'''
class Link(Page):
	def __init__(self):
		Page.__init__(self)
		#parser
		self._parser = Parser()
		self._doc = self._parser.fromstring(self.raw_html)
		#init extractor method
		self._extractor = StandardContentExtractor(self,lang)	
		
class Defaut(object):
	def __init__(self, data):
		self._parser = Parser()
		self._doc = self._parser.fromstring(data['raw_html'])
		
		#init extractor method
		self._extractor = StandardContentExtractor(self,data['lang'])	
		# init the document cleaner
		self._cleaner = StandardDocumentCleaner(self)
		# init the output formatter
		self._formatter = StandardOutputFormatter(self, stopwords_class=data['lang'])
	
	def extract(self):
		self.title = extractor.get_title()
		self.links = set(extractor.get_links())
		self.outlinks = set(extractor.get_outlinks())
		self.inlinks = set(extractor.get_inlinks())
		return self.__repr__()
		
	def __repr__(self):
		for k,v in self.__dict__.items:
			if k[0] == "_":
				delattr(self, k, v)
		return self.__dict__
			
class ArticleB(Page):
	'''Article'''
	def __init__(self, url, raw_html, depth, lang="en"):
		page = Page.__init__(url, depth)
		
		self._logs = True
		self.url = url
		self.step = step
		self.lang = lang
		self.raw_html = page.extract()
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
			self.content = formatter.get_formatted_text()
			
			
			#self.content = self.content.decode("utf-8")
			self.links = extractor.get_links()
			self.outlinks = [{"url":url, "step": self.step+1} for url in extractor.get_outlinks()]
				
		except Exception as e:
			try:
				self.content = bs(self.content).getText()
				self.content = nltk.clean_html(self.content)
			except Exception as e:
				print e
				self.content  = re.sub(r'<.*?>', '', self.content)
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
		#~ self._logs ={
				#~ "url": self.canonical_link,
				#~ "domain": self.domain,
				#~ "title": self.title.encode("utf-8"),
				#~ "content": self.content,
				#~ "description": self.meta_description.encode("utf-8"),
				#~ "outlinks": self.outlinks,
				#~ "crawl_date": self.start_date,
				#~ "raw_html": self.raw_html,
				#~ }
		#~ return self._logs
	
	def is_relevant(self, query):
		self.article = {"title":unicode(self.title), "content": unicode(self.article)}
		if self.woosh_query.match(self.article) is False:
			self.logs = {"url":self.url, "code": -1, "msg": "Not Relevant","status": False, "title": self.title, "content": self.article}
			return False
		else:
			self.__repr__()
			return True

