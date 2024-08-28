'''
Created on Nov 29, 2016

@author: ebrifol
'''

import Utils
import os
import sys
import subprocess
import datetime
import zipfile
import java.lang.System

class VBInterface(object):
    
    def __init__(self, params, logger, dbConn=None):
        self.params = params
        self.dbConn = dbConn
        self.log = logger
    
    def runVbExec(self):
        if 'UniOutputPath' not in self.params:
            self.log.error('UniOutputPath was not defined as a property')
            raise Exception('UniOutputPath was not defined as a property')
        
        if 'UniInputPath' not in self.params:
            self.log.error('UniInputPath was not defined as a property')
            raise Exception('UniInputPath was not defined as a property')
        
        if 'UniverseConnection' not in self.params:
            self.log.error('UniverseConnection was not defined as a property')
            raise Exception('UniverseConnection was not defined as a property')
        
        self.log.info('** GENERATING UNIVERSE **') 
        starttime = datetime.datetime.now().replace(microsecond=0)
                
        '''Build up all the parameters to execute the VB '''
        self.envPath = self.params['envPath']
        self.versionID = self.params['tpModel'].versionID
        self.userPath = sys.getBaseProperties().getProperty("user.home")
        self.boTemplateDir = self.userPath + '/My Business Objects Documents/templates/'
        self.name = self.versionID.split(":")[0]
        self.version = self.versionID.split("((",1)[1].split("))",1)[0]
        self.outputPath = self.params['UniOutputPath'] + "/" + self.versionID.replace(":","_")
        self.inputPath = self.params['UniInputPath']
        self.dummyConn = self.params['UniverseConnection']
        self.unvTask = self.params['UniverseTask']
        if not os.path.exists(self.outputPath):
            os.makedirs(self.outputPath , 0755)
        
        '''Either create or update a unv and then create the description doc for it'''
        self._backgroudinit(self.unvTask)
        self.log.info('** COMPLETED GENERATING UNIVERSE **')
        
        lockedby = 'TPC-' + java.lang.System.getProperty('TPCbuildNumber')
        self.createBOPackage(lockedby)
        
        endtime = datetime.datetime.now().replace(microsecond=0)
        self.log.info('** UNIVERSE TIME TAKEN: ' + str(endtime - starttime) +' **')
    
    
    def _backgroudinit(self, boAction):   
        '''Triggers the VB executable from TPC'''
        
        self.parameter = [];
        self.homeDir = os.path.expanduser('~')
        self.bointffile = self.envPath + "/bointf/TPIDE_BOIntf.exe"
        self.parameter.append(self.bointffile)
        self.parameter.append(boAction);
        self.parameter.append(self.versionID);
        self.parameter.append(str(self.params['baseTP']));
        self.parameter.append(self.outputPath);
        self.parameter.append(self.inputPath);
        self.parameter.append(self.dummyConn);
        bpr = subprocess.Popen(self.parameter, stdout=subprocess.PIPE)
        while bpr.poll() is None:
            output = bpr.stdout.readline()
            self.log.info(output)
    
    
    def createBOPackage(self, LockedBy):
        from com.distocraft.dc5000.etl.importexport import ETLCExport
        from org.apache.velocity import VelocityContext
        from org.apache.velocity.app import Velocity
        from org.apache.velocity.context import Context
        from java.util import Vector
        from java.io import StringWriter
        from java.util import Properties
        from tpapi.eniqInterface import VersionInfo
        from com.distocraft.dc5000.repository.dwhrep import Versioning
                
        versioning = Versioning(self.dbConn, self.versionID)
        if self.params['rState'] == "":
            rState = versioning.getTechpack_version() + '_b' + self.version
        else:
            rState = self.params['rState']
            
        #Create the version.properties file
        p = Properties();
        p.setProperty("file.resource.loader.path", self.envPath);
        Velocity.init(p);

        boPackageName = 'BO'+ self.name[2:]
        
        versionProps = open(self.outputPath+'/install/version.properties','w')
        vec = Vector()
        context = VelocityContext()
        context.put("metadataversion", "")
        context.put("techpackname", boPackageName)
        context.put("author", LockedBy)
        context.put("version", rState)
        context.put("buildnumber", self.version)
        context.put("buildtag", self.version)
        
        licenseName = ''
        if versioning.getLicensename() != None:
            licenseName = versioning.getLicensename()
            
        context.put("licenseName", licenseName)
        context.put("required_tech_packs", vec)
        
        strw = StringWriter()
        isMergeOk = Velocity.mergeTemplate('version.vm', Velocity.ENCODING_DEFAULT, context, strw)
        if isMergeOk:
            versionProps.write(strw.toString())
        versionProps.close()
        
        outputName = boPackageName + '_' + rState
        
        #Z = zipfile.ZipFile(self.outputPath + '\\' + outputName+'.tpi', 'w')
        #directories = ['install','unv','rep']
        #for directory in directories:
        #    for dirpath,dirs,files in os.walk(self.outputPath+'\\'+directory):
        #        for f in files:
        #            if not f.endswith('.tpi') or not f.endswith('.log'):
        #                fn = os.path.join(dirpath, f)
        #                Z.write(str(fn), str(outputName + '/' + directory + '/' + f), zipfile.ZIP_DEFLATED)
        #Z.close()
        
        
    def createRefDoc(self):
        self.envPath = self.params['envPath']
        self.versionID = self.params['tpModel'].versionID
        self.userPath = sys.getBaseProperties().getProperty("user.home")
        self.boTemplateDir = self.userPath + '/My Business Objects Documents/templates/'
        self.name = self.versionID.split(":")[0]
        self.version = self.versionID.split("((",1)[1].split("))",1)[0]
        self.outputPath = self.params['UniOutputPath'] + "/" + self.versionID.replace(":","_")
        if not os.path.exists(self.outputPath):
            os.makedirs(self.outputPath , 0755)
        
        self.parameter = [];
        self.homeDir = os.path.expanduser('~')
        self.bointffile = self.envPath + "/bointf/TPIDE_BOIntf.exe"
        self.parameter.append(self.bointffile)
        self.parameter.append('createDocOffline');
        self.parameter.append(self.versionID);
        self.parameter.append(self.outputPath);
        bpr = subprocess.Popen(self.parameter, stdout=subprocess.PIPE)
        while bpr.poll() is None:
            output = bpr.stdout.readline()
            self.log.info(output)
    
    