'''
Created on Jun 10, 2016

@author: ebrifol
'''

import os
import shutil
import sys
import TPM
import Utils
import traceback
import INTFM
import UM
import EncryptionDecryption

class Model(object):
    'Loads TP models from XLSX, XML, TPI or from a server and can write a TP model to XLSX or XML'
    
    def _load(self, params,logger):
        if 'ModelType' not in params:
            logger.error('ModelType was not defined as a property')
            raise Exception('ModelType was not defined as a property')
        if 'SourceType' not in params:
            logger.error('SourceType was not defined as a property')
            raise Exception('SourceType was not defined as a property')
        
        loadType = params['ModelType'].upper() #should be TP or INTF
        SourceType = params['SourceType'].upper() #should be something like XLS, XML, SERVER
        
        interfaces = []
        if loadType == 'TP':
            if SourceType == 'LEGACY_XLSX' or SourceType == 'XML' or SourceType == 'TPI' or SourceType == 'XLSX':
                if 'InputFilePath' not in params:
                    logger.error('InputFilePath was not defined as a property')
                    raise Exception('InputFilePath was not defined as a property')
                FileLocation = params['InputFilePath']
                tp = TPM.TechPackVersion(logger,'DC_E_LOAD:((1))')
                
                if SourceType == 'XLSX':
                    xlsFile = Utils.XlsxFile()
                    xlsdict = xlsFile.parseXlsDoc(loadType, FileLocation,logger)
                    tp.getPropertiesFromXlsx(xlsxDict=xlsdict)
                    
                    if (xlsdict['Versioning']['ManModsFile'] != ""):
                        params['ManModsFile'] = xlsdict['Versioning']['ManModsFile']
                        
                    if (xlsdict['Versioning']['UNIVERSE_DELIVERED'] != ""):
                        params['UNIVERSE_DELIVERED'] = xlsdict['Versioning']['UNIVERSE_DELIVERED']
                        
                    if (xlsdict['Versioning']['SUPPORTED_NODE_TYPES'] != ""):
                        params['SUPPORTED_NODE_TYPES'] = xlsdict['Versioning']['SUPPORTED_NODE_TYPES']

                elif SourceType == 'LEGACY_XLSX':
                    xlsDict = Utils.XlsDict()
                    xlsxDict = xlsDict.parse(logger,FileLocation)
                    tp.getPropertiesFromXls(xlsDict=xlsxDict)
                    
                    if 'Interfaces' in xlsxDict.keys():
                        for Name, IntfDict in xlsxDict['Interfaces'].iteritems():
                            items = Name.split(':')
                            Interface = INTFM.InterfaceVersion(logger,items[0], items[1])
                            Interface.getPropertiesFromXls(IntfDict)
                            interfaces.append(Interface)
                                        
                elif SourceType == 'XML':
                    xmlElement = Utils.fileToXMLObject(open(FileLocation,'r'))
                    tp.getPropertiesFromXML(xmlElement=xmlElement)
                elif SourceType == 'TPI':
                	#self._decryptTPI(FileLocation)
                    decrypt = EncryptionDecryption.EncryptDecrypt(logger)
                    decrypt.decryptTPI(FileLocation)
                    tpiDict = Utils.TpiDict(logger,FileLocation).returnTPIDict()
                    tp.getPropertiesFromTPI(tpiDict=tpiDict)
                
                return tp, interfaces
                    
            elif SourceType == 'SERVER':
                if 'ServerName' not in params:
                    logger.error('ServerName was not defined as a property')
                    raise Exception('ServerName was not defined as a property')
                if 'VersionID' not in params:
                    logger.error('VersionID was not defined as a property')
                    raise Exception('VersionID was not defined as a property')
                
                ServerName = params['ServerName']
                VersionID = params['VersionID']
                tp = TPM.TechPackVersion(logger,VersionID)
                dbaccess = Utils.DbAccess(ServerName,'dwhrep')
                tp.getPropertiesFromServer(dbaccess)
                
                return tp, interfaces
            
            else:
                logger.error('SourceType ' + SourceType + ' is not supported')
                raise Exception('SourceType ' + SourceType + ' is not supported')
        
        elif loadType == 'INTF':
            tp = None
            if SourceType == 'LEGACY_XLSX' or SourceType == 'XML' or SourceType == 'TPI' or SourceType == 'XLSX':
                if 'InputFilePath' not in params:
                    logger.error('InputFilePath was not defined as a property')
                    raise Exception('InputFilePath was not defined as a property')
                FileLocation = params['InputFilePath']
                Interface = INTFM.InterfaceVersion(logger,'INTF_DC_E_LOAD', '((1))')
                
                if SourceType == 'XLSX':
                    xlsFile = Utils.XlsxFile()
                    xlsdict = xlsFile.parseXlsDoc(loadType, FileLocation, logger)
                    Interface.getPropertiesFromXlsx(xlsxDict=xlsdict)          
                elif SourceType == 'XML':
                    xmlElement = Utils.fileToXMLObject(open(FileLocation,'r'))
                    Interface.getPropertiesFromXML(xmlElement=xmlElement)
                elif SourceType == 'TPI':
                    decrypt = EncryptionDecryption.EncryptDecrypt(logger)
                    decrypt.decryptTPI(FileLocation)
                    tpiDict = Utils.TpiDict(logger,FileLocation).returnTPIDict()
                    Interface.getPropertiesFromTPI(tpiDict=tpiDict)
                
                return tp, Interface
                    
            elif SourceType == 'SERVER':
                if 'ServerName' not in params:
                    logger.error('ServerName was not defined as a property')
                    raise Exception('ServerName was not defined as a property')
                if 'VersionID' not in params:
                    logger.error('VersionID was not defined as a property')
                    raise Exception('VersionID was not defined as a property')
                
                ServerName = params['ServerName']
                VersionID = params['VersionID'].split(':')
                Interface = INTFM.InterfaceVersion(VersionID[0], VersionID[1])
                dbaccess = Utils.DbAccess(ServerName,'dwhrep')
                Interface.getPropertiesFromServer(dbaccess)
                
                return tp, Interface
                
        else:
            logger.error('loadType ' + loadType + ' is not supported')
            raise Exception('loadType ' + loadType + ' is not supported')
    
    def _write(self, model, params,logger):
        if 'WriteType' not in params:
            logger.error('WriteType was not defined as a property')
            raise Exception('WriteType was not defined as a property')
        if 'OutputPath' not in params:
            logger.error('OutputPath was not defined as a property')
            raise Exception('OutputPath was not defined as a property')
        
        writeType = params['WriteType'].upper() #should be something like XLS or XML
        OutputLocation = params['OutputPath'] + '\\'
        
        if writeType == 'XML':
            filename = OutputLocation + model.name + '.xml'
            fh = open(filename,"w")
            fh.writelines(model.toXML().encode('ascii', 'ignore'))
            fh.close()
        elif writeType == 'XLSX':
            model.toXLSX(OutputLocation)
        else:
            logger.error('WriteType ' + writeType + ' is not supported')
            raise Exception('WriteType ' + writeType + ' is not supported')
                 

