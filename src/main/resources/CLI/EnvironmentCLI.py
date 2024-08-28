'''
Created on Jun 10, 2016

@author: ebrifol
'''

import os
import shutil
import sys
import Environment
import Utils
import traceback
import zipfile

class Env(object):
    ''' Create a tpce file from a server or deploy a tpce file to create a local ENIQ environment'''

    def _CollectEnv(self, params,logger):
        logger.info('Verifying parameters')
        requiredparams = ['Servername', 'Username', 'Password', 'OutputPath']
        for param in requiredparams:
            if param not in params:
                log.error(param + ' was not defined as a property')
                raise Exception(param + ' was not defined as a property')
        
        servername = params['Servername']
        username = params['Username']
        password = params['Password']
        outputpath = params['OutputPath']
        
        port = 22
        if 'Port' in params:
            port = params['Port']
        
        logger.info('Creating temp directory to collect environment in ' +os.path.expanduser('~')+'/tpce')
        destDir = os.path.expanduser('~')+'/tpce'
        
        #if the destination directory exists, then delete it
        if os.path.exists(destDir):
            shutil.rmtree(destDir)
        
        #create the destination directory structure
        os.makedirs(destDir)
        os.makedirs(destDir+'/env')
        os.makedirs(destDir+'/env/5.2') 
        
        os.makedirs(destDir+'/db') 
        
        logger.info('Starting jar file collection from ' + servername)
        jarcollection = Environment.EnvCollection(servername, username, password, logger, port)
        jarcollection.collectJars(destDir)
        logger.info('Jar file collection completed successfully.')
        
        logger.info('Adding jar files to the PYTHONPATH')
        #Add the jars to the python path to query the DB
        envfiles = os.listdir(destDir+'/env')
        for filename in envfiles:
            if filename.endswith('.jar'):
                sys.path.append(destDir+'/env/' + filename)
        
        #Getting the DB passwords from ENIQ server
        logger.info('Get the passwords for ENIQ DB')
        DbPasswords = Environment.PasswordCollect(servername,username,password,port,logger)
        dbPasswords = DbPasswords.getDbPasswords()
        logger.info('DB passwords have been collected')
        
        logger.info('Reading the schema of dwhrep and etlrep from ' + servername)                
        dbschema = Environment.SchemaCreator(servername,dbPasswords,logger)
        dbschema.getSchema(destDir)
        logger.info('DB schema successfully collected')
        
        logger.info('Collecting base TP\'s details from ' + servername)  
        baseTP = Environment.BaseTPRetrieval(servername,dbPasswords,logger)
        baseTP.getBaseTPInfo(destDir)
        logger.info('Base TP\'s details successfully collected')
        
        logger.info('Archiving Environment details')
        if not os.path.exists(outputpath):
            os.makedirs(outputpath)
        Eniqversion = Utils.getENIQversion(servername, username, password)
        shutil.make_archive(outputpath+'/TPC_ENIQ-'+Eniqversion, 'zip', destDir)
        logger.info('TPC Env file has been successfully created in ' + outputpath)
        

    def _DeployEnv(self, params,logger):
        if 'TpceFile' not in params:
            logger.error('TpceFile was not defined as a property')
            raise Exception('TpceFile was not defined as a property')
        if 'TpceCommonFiles' not in params:
            logger.error('TpceCommonFiles was not defined as a property')
            raise Exception('TpceCommonFiles was not defined as a property')
        if 'DeployPath' not in params:
            logger.error('DeployPath was not defined as a property')
            raise Exception('DeployPath was not defined as a property')
        
        env_version = ''
        dbpath = ''
        envDir = ''
        
        PathToTpceZip = params['TpceFile']
        PathToTpceZip = PathToTpceZip.replace('\\' , '/')
        zipDirPath = os.path.dirname(PathToTpceZip)
        env_version = PathToTpceZip.split('/')[-1].replace('.zip' , '')
        
        
        unzipDir = params['DeployPath']+'/tpce/' + env_version
        #if the destination directory exists, then delete it
        if os.path.exists(unzipDir):
            shutil.rmtree(unzipDir)
        
        unzipDir = params['DeployPath']+'/tpce/' + env_version
        os.makedirs(unzipDir)
        
        with zipfile.ZipFile(PathToTpceZip) as zip:
            zip.extractall(unzipDir)
        
        with zipfile.ZipFile(params['TpceCommonFiles']) as zip:
            zip.extractall(unzipDir)
        
        envDir = self._loadEnvironment(unzipDir,logger)
        
        deploy = Environment.CreateDB(unzipDir,logger)
        dbpath = deploy.createDB()
            
        return env_version, dbpath, envDir
        
    
    def _loadEnvironment(self, baseDir,logger):
        from com.ericsson.eniq.tpc import DynamicJarLoader
        import glob
        import sys
        envDir = baseDir + '/env'
        
        djl = DynamicJarLoader()
        for jar in glob.glob(envDir+'/*.jar'):
            sys.path.append(jar)
            djl.addLibrary(jar)
        
        sys.path.append(envDir)
        return envDir
         
