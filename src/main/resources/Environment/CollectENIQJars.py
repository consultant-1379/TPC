'''
Created on Jun 7, 2016

@author: ebrifol
'''

import Utils
import os
import shutil
import sys

class EnvCollection(object):
    
    def __init__(self, ServerName, Username, Password, logger, Port=22):
        self.ServerName = ServerName
        self.UserName = Username
        self.Password = Password
        self.Port = Port
        self.requiredJars = ['repository','common','engine','scheduler','licensing', 'dwhmanager', 'libs', 'export', 'parser']
        self.required3PPs = ['velocity', 'slf4j', 'log4j', 'jsch']
        self.log = logger
    
    def collectJars(self, destDir):
        self.destDir = destDir
        
        #Open an FTP connection to the server
        ftp = Utils.getFTPConnection(self.ServerName, self.UserName, self.Password, self.Port)
        ftp.cwd('/eniq/sw/platform')
        dirlist= ftp.nlst()
        for dirName in dirlist:
            
            modulename = dirName.split('-')[0] #split the string to get the name of the module
            if modulename in self.requiredJars:
                if modulename == 'libs' or modulename == 'statlibs':
                    ftp.cwd(dirName+'/dclib')
                    jarlist = ftp.nlst()
                    
                    for jarName in jarlist: # for each of the 3PP jars on the system
                        for reqJar in self.required3PPs: #For each jar we want to collect
                            if reqJar in jarName: #Because the version of the 3pp might change, we must check if Velocity is in Velocity_2.4.jar for instance
                                DestFileName = self.destDir+'/env/' + jarName
                                SourceFileName = jarName
                                self._getFile(ftp, SourceFileName, DestFileName) 
                    ftp.cwd('/eniq/sw/platform')
                else:
                    DestFileName = self.destDir+'/env/' + dirName+'.jar'
                    SourceFileName = dirName+'/dclib/' + modulename+'.jar'
                    self._getFile(ftp, SourceFileName, DestFileName)
                    
                    if modulename == 'common':
                        ftp.cwd('/eniq/sw/platform/'+dirName+'/classes/5.2')
                        files = ftp.nlst()
                        for fileName in files:
                            if fileName.endswith('.vm'):
                                DestFileName = self.destDir+'/env/5.2/' + fileName
                                self._getFile(ftp, fileName, DestFileName)
                        ftp.cwd('/eniq/sw/platform')
                        
                    elif modulename == 'dwhmanager':
                        ftp.cwd('/eniq/sw/platform/'+dirName+'/classes/')
                        files = ftp.nlst()
                        for fileName in files:
                            if fileName.endswith('.vm'):
                                DestFileName = self.destDir+'/env/' + fileName
                                self._getFile(ftp, fileName, DestFileName)
                    
                    elif modulename == 'export':
                        ftp.cwd('/eniq/sw/platform/'+dirName+'/dclib')
                        files = ftp.nlst()
                        for fileName in files:
                            if 'dbunit' in fileName:
                                DestFileName = self.destDir+'/env/' + fileName
                                self._getFile(ftp, fileName, DestFileName)
                    ftp.cwd('/eniq/sw/platform')
        
        self._getFile(ftp, '/eniq/sw/runtime/ant/lib/ant.jar', self.destDir+'/env/ant.jar')
        
        self._getFile(ftp, '/eniq/sw/installer/lib/installer.jar', self.destDir+'/env/installer.jar')
        
        self._getFile(ftp, '/eniq/sw/conf/ETLCServer.properties', self.destDir+'/env/ETLCServer.properties')
                        
        self._getFile(ftp, '/eniq/sw/conf/static.properties', self.destDir+'/env/static.properties')
        
        self._getFile(ftp, '/eniq/admin/version/eniq_status', sys.getBaseProperties().getProperty("user.home")+'\\eniq_status.txt')
        
        ftp.close()
    
    def _getFile(self, ftp, SourceFileName, DestFileName):
#         fileName = open(DestFileName, 'wb+')
#         ftp.retrbinary('RETR '+SourceFileName, fileName.write)
#         ftp.retrbinary(SourceFileName)
#         ftp.close()
        ftp.get(SourceFileName, DestFileName)


        

        