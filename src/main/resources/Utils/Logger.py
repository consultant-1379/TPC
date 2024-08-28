'''
Created on 8 Feb 2018

@author: xarjsin
'''

import logging
import sys
import datetime
import os

class Logger(object):
    '''
    classdocs
    '''
    
    format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    def getLog(self, logName):
        '''
        Return a logger object to handle console and file logging.
        '''
        #Configuring logging
        logger = logging.getLogger(logName)
        logger.setLevel(logging.INFO)        
        logger.addHandler(self.getConsoleHandler())
        logger.addHandler(self.getFileHandler(self.getFilename(logName)))
        return logger
        
    
    #STDOUT handler
    def getConsoleHandler(self):
        cHandler = logging.StreamHandler(sys.stdout)
        cHandler.setLevel(logging.INFO)
        cHandler.setFormatter(self.format)
        return cHandler
    
    
    #File handler
    def getFileHandler(self,logFile):
        fHandler = logging.FileHandler(logFile)
        fHandler.setLevel(logging.INFO)
        fHandler.setFormatter(self.format)
        return fHandler
    
    
    #Create log folder and assign log filename
    def getFilename(self,logName):
        date = datetime.date.today()
        logDirectory = os.curdir + "/Logs"
        if not os.path.exists(logDirectory):
            os.makedirs(logDirectory)
            
        fileName = logDirectory + '/' + logName + '_' + str(date) + '.log'
        return fileName