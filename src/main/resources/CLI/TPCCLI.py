'''
Created on Jun 10, 2016

@author: ebrifol
'''

import CLI
import datetime
import logging
import CreateUnv

class TPC(object):
    '''Common use cases for TPC. '''
    
    def convert(self, params,logger):
        '''Convert the model from one format to another ''' 
        logger.info('** LOADING THE MODEL **')
        model = CLI.Model()
        loadedmodel, interfaces = model._load(params,logger)
        logger.info('** SUCCESSFULLY LOADED MODEL **')
        logger.info('** WRITING THE MODEL **')
        model._write(loadedmodel, params,logger)
        
        if len(interfaces) > 0:
            logger.info('Conversion from legacy. Creating Interface output')
            for interface in interfaces:
                model._write(interface, params,logger)
        
        logger.info('** Conversion complete **')
    
    
    def difference(self, params,logger):
        ''' Finds the difference between two models '''
        
        logger.info('** SPLIT PARAMETERS FOR LOADING **')
        baseParams = {}
        compParams = {}
        for key, value in params.iteritems():
            if key.startswith('base_'):
                baseParams[key.split('_')[1]] = value
            else:
                compParams[key.split('_')[1]] = value
        
        model = CLI.Model()
        logger.info('** LOADING BASE MODEL **')
        basemodel, baseinterface = model._load(baseParams,logger)
        
        logger.info('** LOADING COMPARISON MODEL **')
        compmodel, compinterface = model._load(compParams,logger)
        
        logger.info('** FINDING DIFFERENCE **')
        deltaObj = None
        if basemodel == None and compmodel == None:
            deltaObj = baseinterface.difference(compinterface)
        elif basemodel != None and compmodel != None: 
            deltaObj = basemodel.difference(compmodel)
        else:
            logger.info('Incompatible difference options. Please check configuration options')
        
        if deltaObj != None:
            logger.info('** WRITING DIFFERENCE OUTPUT **')
            filename = params['OutputPath'] + '\\difference.txt'
            fh = open(filename,"w")
            fh.writelines(deltaObj.toString().encode('ascii', 'ignore'))
            fh.close()
        
        logger.info('** DIFFERENCE COMPLETE **')


    def designRules(self, params,logger):
        '''Runs design rules '''
        pass
    
    
    def PushTP(self, params,logger):
        '''Create the TP '''
        
        starttime = datetime.datetime.now().replace(microsecond=0)
        params['createSets'] = True
        if 'SourceType' in params:
            if params['SourceType'] == 'LEGACY_XLSX':
                logger.error('Create TP from legacy XLSX is not supported')
                raise Exception('Create TP from legacy XLSX is not supported')
        
        logger.info('** LOADING MODEL **')
        model = CLI.Model()
        loadedmodel, interfaces = model._load(params,logger)
        logger.info('** SUCCESSFULLY LOADED MODEL **')
        
        ModelType = params['ModelType'].upper()
        if ModelType == 'TP':
            params['tpModel'] = loadedmodel
        elif ModelType == 'INTF':
            params['tpModel'] = interfaces
        
        logger.info('** DEPLOYING ENVIRONMENT **')
        env = CLI.Env()
        env_version, dbpath, envDir = env._DeployEnv(params,logger)
        params['env_version'] = env_version
        params['dbpath'] = dbpath
        params['envPath'] = envDir
        logger.info('** SUCCESSFULLY DEPLOYED ENVIRONMENT **')
        
        logger.info('** CREATING ' + ModelType +' **')
        push = CLI.Create()
        push._createTP(params,logger)
        logger.info('** SUCCESSFULLY CREATED ' + ModelType + ' **')
        
        endtime = datetime.datetime.now().replace(microsecond=0)
        logger.info('** TIME TAKEN: ' + str(endtime - starttime) +' **')
    
    
    def PackageEnv(self, params,logger):
        ''' Collect environment and DB from a server and package it into a tpce file '''
        
        env = CLI.Env()
        env._CollectEnv(params,logger)
        
    
    def PushUnv(self, params,logger):
        '''Create Universe'''
        
        starttime = datetime.datetime.now().replace(microsecond=0)
        params['createSets'] = False
        if 'SourceType' in params:
            if params['SourceType'] == 'LEGACY_XLSX':
                logger.error('Create TP from legacy XLSX is not supported')
                raise Exception('Create TP from legacy XLSX is not supported')
        
        logger.info('** LOADING MODEL **')
        model = CLI.Model()
        loadedmodel, interfaces = model._load(params,logger)
        logger.info('** SUCCESSFULLY LOADED MODEL **')
        
        params['tpModel'] = loadedmodel
        
        logger.info('** DEPLOYING ENVIRONMENT **')
        env = CLI.Env()
        env_version, dbpath, envDir = env._DeployEnv(params,logger)
        params['env_version'] = env_version
        params['dbpath'] = dbpath
        params['envPath'] = envDir
        logger.info('** SUCCESSFULLY DEPLOYED ENVIRONMENT **')
        
        logger.info('** CREATING TP IN DATABASE **')
        push = CLI.Create()
        push._createTP(params,logger)
        logger.info('** TP CREATED IN DATABASE **')
        
        logger.info('** CREATING UNIVERSE **')
        push._createUNV(params,logger)
        logger.info('** SUCCESSFULLY CREATED UNIVERSE **')
                
        endtime = datetime.datetime.now().replace(microsecond=0)
        logger.info('** TIME TAKEN: ' + str(endtime - starttime) +' **')
        
        
    def PushUnvDoc(self, params,logger):
        '''Create Universe Reference Document'''
        
        starttime = datetime.datetime.now().replace(microsecond=0)
             
        logger.info('** LOADING MODEL **')
        model = CLI.Model()
        loadedmodel, interfaces = model._load(params,logger)
        logger.info('** SUCCESSFULLY LOADED MODEL **')
        
        params['tpModel'] = loadedmodel
        
        logger.info('** DEPLOYING ENVIRONMENT **')
        env = CLI.Env()
        env_version, dbpath, envDir = env._DeployEnv(params,logger)
        params['env_version'] = env_version
        params['dbpath'] = dbpath
        params['envPath'] = envDir
        logger.info('** SUCCESSFULLY DEPLOYED ENVIRONMENT **')
        
        logger.info('** CREATING UNIVERSE REFERENCE **')
        unvDoc = CreateUnv.VBInterface(params,logger)
        unvDoc.createRefDoc()
        logger.info('** SUCCESSFULLY CREATED UNIVERSE REFERENCE **')
                
        endtime = datetime.datetime.now().replace(microsecond=0)
        logger.info('** TIME TAKEN: ' + str(endtime - starttime) +' **')
        
