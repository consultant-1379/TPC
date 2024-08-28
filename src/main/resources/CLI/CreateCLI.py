'''
Created on Nov 24, 2016

@author: ebrifol
'''

import os
import shutil
import sys
import TPM
import Utils
import traceback
import ManMods
import INTFM
import UM
import CreateTP
import CreateUnv
import EncryptionDecryption


class Create(object):
    ''' Options to create the TP in the DB, apply modifications, create tpi and documents ''' 
    
    def _createTP(self, params,logger):
        tp = params['tpModel']
        pushtype = params['ModelType'].upper()
        dbPath = params['dbpath']
        envPath = params['envPath']
        createSets = params['createSets']
        
        from ssc.rockfactory import RockFactory
        self.dbAccess = Utils.DbAccess(dbPath, 'HSQL')
        self.dbDetails = self.dbAccess.getConnectionProperties('HSQL')
        self.dbConn = RockFactory(self.dbDetails['url'].replace('DBpath', dbPath), self.dbDetails['uid'], self.dbDetails['pid'], self.dbDetails['driver'], "TPC", True)
        
        logger.info('** PUSHING ' + pushtype + ' TO DB **')
        if pushtype == 'TP':
            push = CreateTP.PushTPtoDB(self.dbConn, dbPath, envPath, self.dbAccess, logger, createSets)
            push.pushData(tp)
        elif pushtype == 'INTF':
            push = CreateTP.PushIntftoDB(self.dbConn, dbPath, envPath, logger)
            push.pushData(tp)
        logger.info('** PUSH COMPLETE **') 
        
        if (('ManModsFile' in params) and createSets):
            self._applyModifications(params, logger)
            
        if 'tpiOutputPath' in params: 
            self._createTPI(params, logger)
            
        if (('UniOutputPath' in params) and createSets):
            self._createUNV(params, logger)
            

    def _applyModifications(self, params,logger):
        ''' Applying Manual Modifications '''
        inputFile = params['ManModsFile']
        tp = params['tpModel']
        logger.info('** APPLYING MODIFICATIONS **')
        modify = ManMods.ManualMods(self.dbConn, tp,logger)
        modify.applyModifications(inputFile)
        logger.info('** SUCCESSFULLY APPLIED MODIFICATIONS **')
    
    
    def _createTPI(self, params,logger):
        tp = params['tpModel']
        pushtype = params['ModelType'].upper()
        dbPath = params['dbpath']
        envPath = params['envPath']
        outputPath = params['tpiOutputPath']
        
        if pushtype == 'TP':
            outputPath = outputPath + '/' + (tp.versionID).replace(":","_")
            logger.info('** CREATING DESCRIPTION DOC **')
            interfaces = ''
            if 'Interfaces' in tp.versioning:
                interfaces = ', '.join(tp.versioning['Interfaces'])
            
            doc = CreateTP.DescriptionDoc(self.dbConn)
            doc.createTPdoc(tp.versionID, envPath, outputPath, interfaces, params, logger)
            logger.info('Created ' + outputPath)
            logger.info('** SUCCESSFULLY CREATED DESCRIPTION DOC **')
            logger.info('** CREATING TPI FILE **')
            tpiFile = CreateTP.TPInstallerFile(tp, self.dbConn, outputPath, envPath, self.dbAccess)
            tpiFile.createFile()
            outputFile = outputPath + '/' + tpiFile.getTpiFileName()
            encrypt = EncryptionDecryption.EncryptDecrypt(logger)
            encrypt.encryptTPI(outputFile)
            
        elif pushtype == 'INTF':
            outputPath = outputPath + '/' + (tp.intfVersionID).replace(":","_")
            tpiFile = CreateTP.IntfInstallerFile(tp.intfVersionID, self.dbConn, outputPath, envPath)
            tpiFile.createFile()
            outputFile = outputPath + '/' + tpiFile.getIntfFileName()

        logger.info('Created ' + outputFile)
        logger.info('** SUCCESSFULLY CREATED DESCRIPTION TPI **')
        
    
    def _createUNV(self, params, logger):
        '''Trigger creation of input for Unv create/update'''
        
        params['baseTP'] = Utils.getBaseTPName(self.dbAccess.getCursor())
        if not 'rState' in params:
            params['rState'] = ""
        
        logger.info('** CREATING UNV INPUT **')
        push = CreateUnv.PushUnvInput(params, logger)
        push.pushUnv()
        logger.info('** COMPLETED CREATION OF UNV INPUT **')
        
        logger.info('** UNIVERSE TASK START **')
        unv = CreateUnv.VBInterface(params,logger,self.dbConn)
        unv.runVbExec()
        logger.info('** UNIVERSE TASK END **')

