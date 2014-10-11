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
#from page import Page

class Extractor(object):
	'''Generic Extractor'''	
	@staticmethod
	def run( url, raw_html,type, lang="en"):
		if type == "article":
			content = Article(url, raw_html, lang)
		elif type == "defaut":
			raise NotImplementedError	
		else:
			raise NotImplementedError	
		 	
		return content.get()
		


class Article(Page):
	'''Article'''
	def __init__(self, url, raw_html, depth, lang="en"):
		page = Page.__init__(url, depth)
		
		self.status = True
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
			#self.cleaned_text = formatter.get_formatted_text()
			
			
			#self.content = self.content.decode("utf-8")
			self.links = extractor.get_links()
			self.outlinks = [{"url":url, "step": self.step+1} for url in extractor.get_outlinks()]
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
			self.logs = {"url":self.url, "code": -1, "msg": "Not Relevant","status": False, "title": self.title, "content": self.article}
			return False
		else:
			self.__repr__()
			return True
