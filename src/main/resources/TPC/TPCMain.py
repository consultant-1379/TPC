from com.ericsson.eniq.tpc import TPCMain

import Utils
import sys
import os
import CLI
import inspect
import traceback
import logging
import datetime

class TPCMainClass(TPCMain):


	def __init__(self):
		self.parameters = Utils.odict()	
		self.modules = {}
		
		#Configuring logging
		self.logger = Utils.Logger().getLog('TPC')
		
		
	def run(self, parameters):
		try:	
			
			for name, obj in inspect.getmembers(sys.modules[CLI.__name__]):
				if inspect.isclass(obj):
					self.modules[obj] = obj()
			
			if type(parameters) is unicode:
				if parameters == 'help':
					self.printHelp()
					raise Exception()
				self.parseParametersFile(parameters)
			else:
				self.parametersDict = parameters
			
			foundMethod = False
			for moduleName, params in self.parameters.iteritems():
				moduleElements = moduleName.split('.')
				for module in self.modules:
					if module.__name__ == moduleElements[0]:
						for classmember, location in inspect.getmembers(self.modules[module], inspect.isclass):
							for rule, rulelocation in inspect.getmembers(location, inspect.ismethod):
								if rule == moduleElements[1]:
									foundMethod = True
									getattr(location(),moduleElements[1])(params,self.logger)
						if not foundMethod:
							self.logger.error("ERROR! Unable to find " + moduleName + ". Please check the configuration.")
							raise Exception("ERROR! Unable to find " + moduleName + ". Please check the configuration. \n")
		
		except Exception as e:
			print str(e)
			traceback.print_exc(file=sys.stdout)
			#self.printHelp()
	
	
	def printHelp(self):
		print '\n --TPC help documentation--'
		
		for module in self.modules:
			for classmember, location in inspect.getmembers(self.modules[module], inspect.isclass):
				print 'Module Name: ' + str(module.__name__)
				print '  Description: ' + str(location.__doc__)
				for rule, rulelocation in inspect.getmembers(location, inspect.ismethod):
					if not rule.startswith('_'):
						print '\t- ' + str(rule)
						doc = str(rulelocation.__doc__)
						if doc != None and doc != 'None':
							print '\t ' + str(doc) + '\n'
						else:
							print '\t  No description available\n'
				

	def parseParametersFile(self, parametersFilePath):
		try:
			in_file = open(parametersFilePath, 'r')
			
			module = ''
			paramsDict = {}
			for line in in_file.readlines():
				if not line.startswith('-') and line.strip() != '':
					elements = line.strip().split('::')
					if elements[0] == 'ModuleName':
						if module != '':
							self.parameters[module] = paramsDict
							paramsDict={}
							module = elements[1]
						else:
							module = elements[1]
					else:
						paramsDict[elements[0]] = elements[1]
			
			if module != '':
				self.parameters[module] = paramsDict

		except:
			traceback.print_exc(file=sys.stdout)
		
		finally:
			in_file.close()
		
		