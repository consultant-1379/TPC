'''
Created on May 28, 2019

@author: XARJSIN
'''

import CLI
import datetime
import logging
import Utils

class Debug(object):
    '''Debug use cases for TPC. '''        
    
    def MakeXlsx(self, params,logger):
        '''Create XLSX from input TPI''' 
        
        logger.info('** LOADING THE TPI FILE **')
        model = CLI.Model()
        loadedmodel, interfaces = model._load(params,logger)
        logger.info('** SUCCESSFULLY LOADED TPI FILE **')
        
        logger.info('** WRITING THE MODEL **')
        if params['ModelType'] == 'INTF':
            model._write(interfaces, params,logger)
        else:
            model._write(loadedmodel, params,logger)
        
        logger.info('** CONVERSION COMPLETE **')
        
        
    def convertVector(self, params, logger):
        '''Create new compact vector page'''
        if 'InputFilePath' not in params:
            logger.error('InputFilePath was not defined as a property')
            raise Exception('InputFilePath was not defined as a property')
        if 'SourceType' not in params:
            logger.error('InputFilePath was not defined as a property')
            raise Exception('InputFilePath was not defined as a property')
        if 'OutputPath' not in params:
            logger.error('InputFilePath was not defined as a property')
            raise Exception('InputFilePath was not defined as a property')
        if params['SourceType'].upper() != 'LEGACY_XLSX':
            logger.error('Only legacy MODEL-T format supported')
            raise Exception('Only legacy MODEL-T format supported')
        
        logger.info('** LOADING XLS MODEL-T **')
        vectors = Utils.convVect(logger)
        oldRows = vectors.readOldVectors(params['InputFilePath'])
        logger.info('Input Vectors sheet rows - ' + str(oldRows))
        logger.info('** SUCCESSFULLY LOADED MODEL-T **')
        
        logger.info('** WRITING NEW VECTOR SHEET **')
        newRows = vectors.createNewVectors(params['OutputPath'])
        logger.info('Output Vectors sheet rows - ' + str(newRows))
        logger.info('** SUCCESSFULLY COMPLETED NEW VECTOR SHEET **')
        
        percent = round((float(oldRows - newRows)/float(oldRows) * 100),2)
        logger.info('Percentage reduction in sheet size - ' + str(percent) + '%')
        
        