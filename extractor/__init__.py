#~ from article import Extractor
#~ import cleaners
#~ import formatters
import parser
from query import Query
from article import Article
from filter import Filter
import  datetime
from utils.url import check_url
from packages.requests import requests

class Page(object):
	'''Generic data type for page'''
	def __init__(self, url, depth = 0):
		self.url = url
		self.depth = depth
		self.date = datetime.datetime.now()
		#self.type = type
		self._logs = {"msg":None, "status": True, "code": None, "step": "page creation", "url": self.url}
		self.status = self.check_status()
	
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
					self.html = self._req.text
					self.doc = self._req.text
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
			
	def check_status(self):
		if self.check():
			if self.request(): 
				if self.control():
					self.is_downloaded = True
					return True
		print self._logs
		return False
	
	def is_relevant(self, query):
		self.article = {"title":unicode(self.title), "content": unicode(self.content)}
		if self.woosh_query.match(self.article) is False:
			self._logs = {"url":self.url, "code": -1, "msg": "Not Relevant","status": False, "title": self.title, "content": self.article}
			return False
		else:
			return True

	def create(self, type):
		if type == "default":
			return Default(self.url, self.depth)
		else:
			'''not implemented yet'''
			raise TypeError
		# _class = (type).capitalize()
		# instance = globals()[_class]
		# job = instance(self.url, self.depth)

		# instanciate = getattr(job,type)
		# if debug is True:
		# 	print job
		# 	print instance, self._task

		# return instanciate(self.url, depth= depth)	 
	

class Default(Page):
	def __init__(self, url, depth):
		Page.__init__(self, url, depth)
		self.depth = depth
		article = Article(self.url, language="fr")
		article.parse()
		try:
			article.nlp()
		except UnicodeDecodeError:
			article.keywords = []
			article.summary = ""
		
		for k, v in article.__dict__.items():
			if k[0] != "_":
				setattr(self, k,v)
		
		

class Wiki(Page):
	pass


