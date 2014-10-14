class Log(object):
	
	def __init__(self):
		self.status = True
		self.msg = None 
		self.code = None
		self.step = None
		sel.url = None
		dict_step = {}
	
	def update(self):
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