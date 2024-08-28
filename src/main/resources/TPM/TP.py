'''
Created on May 30, 2016

@author: ebrifol
'''

import TPM
import INTFM
import UM
import re
import Utils
from copy import deepcopy
from java.io import File, FileOutputStream
from org.apache.poi.xssf.usermodel import XSSFWorkbook

class TechPackVersion(object):
    ''' Class to represent a version of a TechPack in TPC. '''

    def __init__(self,logger,versionID=None):
        self.versionID = None
        self.tpname = None
        self.name = None
        self.versionNumber = None
        self.versionNo = None
        self._intialiseVersion(versionID)
        self.versioning = Utils.odict()
        self.supportedVendorReleases = []
        self.measurementTables = Utils.odict()
        self.referenceTables = Utils.odict()
        self.dependencyTechPacks = Utils.odict()
        self.busyHours = Utils.odict()
        self.externalStatements = Utils.odict()
        self.universes = Utils.odict()
        self.manmods = Utils.odict()
        self.log = logger
        
        self.isVector = False
    
    def _intialiseVersion(self, versionID):
        '''Initialise the TechPackVersion versionID.
        If versionID string is none, the TechPackVersion versionID is populated with a default value of UNINITIALISED:((0))
        TechPackVersion tpname and versionNumber,versionNo properties are set by parsing the versionID string.
        '''
        
        if versionID == None:
            versionID = 'UNINITIALISED:((0))'
        self.tpname = versionID.rsplit(':')[0]
        self.versionNumber = versionID.rsplit(':')[1]
        try:
            self.versionNo = re.search('\(\((.*)\)\)',versionID).group(1)
        except:
            self.log.error('Could not get versionNo from versionID ' + versionID)
        
        self.versionID = versionID
        self.name = self.tpname
    
    def getPropertiesFromServer(self,DbAccess):
        '''Populates the model of the TechPackVersion from metadata on the server
        
        This is a container method for triggering a sequence of methods that populate
        individual parts of the model.
        '''
        
        DbCursor = DbAccess.getCursor()
        self._getVersioningFromServer(DbCursor)    
        self._getTablesFromServer(DbCursor)
        self._getBusyHoursFromServer(DbCursor)
        
        DbCursor = DbAccess.getCursor()
        self._getExternalStatementsFromServer(DbCursor)
        self._getSupportedVendorReleasesFromServer(DbCursor)
        self._getInterfaceNamesFromServer(DbCursor)
        
        DbCursor = DbAccess.getCursor()
        self._getUniversesFromServer(DbCursor)
        
    def _getVersioningFromServer(self,DbCursor):
        '''Populate the versioning dictionary of the TechPackVersion from the server
        
        SQL Statement:
                 SELECT * from Versioning where VERSIONID =?
        Exceptions:
                 Raised if the Techpack is not present on the server
        ''' 

        DbCursor.execute("SELECT * from Versioning where VERSIONID =?", (self.versionID,))
        desc = DbCursor.description
        row = DbCursor.fetchone()
        if row is not None:
            self.versioning = {}
            i = 0
            for x in desc:
                value = str(row[i])
                if x[0] != 'STATUS':
                    if value != None and value != 'None':
                        self.versioning[x[0]] = value
                i+=1
        else:
            strg = self.versionID + ": Techpack not installed on server"
            raise Exception(strg)
        
        DbCursor.execute("SELECT TECHPACKNAME, VERSION from TechPackDependency where VERSIONID =?", (self.versionID,))
        resultset = DbCursor.fetchall()
        for row in resultset:
            self.dependencyTechPacks[row[0]] = row[1]
            
        # Force compulsory values
        if 'TECHPACK_TYPE' not in self.versioning:
            self.versioning['TECHPACK_TYPE'] = 'Not set'
        if 'TECHPACK_VERSION' not in self.versioning:
            self.versioning['TECHPACK_VERSION'] = self.versionID
    
    def _getTablesFromServer(self,DbCursor):
        '''Populate measurementTableNames list with the table names from the server
    
        SQL Statement:
                SELECT TYPENAME from MeasurementType where VERSIONID =?
        
        SQL Statement:
                SELECT TYPENAME from ReferenceTable where VERSIONID =?
        
        '''
        DbCursor.execute("SELECT TYPENAME from MeasurementType where VERSIONID =?", (self.versionID,))
        for row in DbCursor.fetchall():
            tablename = row[0]
            ft = TPM.Table(self.versionID, tablename, 'Measurement')
            ft._getPropertiesFromServer(DbCursor)
            self.measurementTables[ft.name] = ft
        
        DbCursor.execute("SELECT TYPENAME from ReferenceTable where VERSIONID =?", (self.versionID,))
        for row in DbCursor.fetchall():
            tablename = row[0]
            rt = TPM.Table(self.versionID, tablename, 'Reference')
            rt._getPropertiesFromServer(DbCursor)
            self.referenceTables[rt.name] = rt
    
    def _getBusyHoursFromServer(self,DbCursor):
        '''Get the list of all busy hour object names associated with the TP from the server

        The Busy Hour names are appended to busyHourNames list. This list of name is used to 
        create Busy Hour objects in the TechPackVersion model
        
        SQL Statement:
                    SELECT DISTINCT BHOBJECT from busyhour where VERSIONID =?
        
        '''
        DbCursor.execute("SELECT DISTINCT BHOBJECT from busyhour where VERSIONID =?", (self.versionID,))
        for row in DbCursor.fetchall():
            BHname = row[0]
            bho = TPM.BusyHour(self.versionID, BHname)
            bho._getPropertiesFromServer(DbCursor)
            self.busyHours[bho.name] = bho
            
    def _getExternalStatementsFromServer(self,DbCursor):
        '''Create External Statement objects associated with the TechPackVersion
        
        Fetches the names of statements from the server, initialises the objects,
        calls the TPAPI_ExternalStatement.getPropertiesFromServer() and appends the objects to the
        externalStatementObjects dictionary
        
        SQL Statement:
            SELECT STATEMENTNAME FROM ExternalStatement WHERE VERSIONID =?"   
        '''
        NoOfBaseES = 0
        DbCursor.execute("SELECT EXECUTIONORDER FROM ExternalStatement WHERE VERSIONID =? and BASEDEF =?", (self.versionID,'1',))
        resultset = DbCursor.fetchall()
        for row in resultset:
            if int(row[0]) > NoOfBaseES:
                NoOfBaseES = int(row[0])
            
            
        DbCursor.execute("SELECT STATEMENTNAME FROM ExternalStatement WHERE VERSIONID =? and BASEDEF =? ORDER BY EXECUTIONORDER", (self.versionID,'0',))
        for row in DbCursor.fetchall():
            name = str(row[0])
            ext = TPM.ExternalStatement(self.versionID, name)
            ext._getPropertiesFromServer(DbCursor, NoOfBaseES)
            self.externalStatements[name] = ext

    def _getSupportedVendorReleasesFromServer(self, DbCursor):
        ''' Gets the vendor releases associated with a TechPackVersion from the server
        
        Vendor Releases are appended to the supportedVendorReleases list
        
        SQL Statement:
                    SELECT VENDORRELEASE FROM SupportedVendorRelease WHERE VERSIONID =?"                    
        '''
        DbCursor.execute("SELECT VENDORRELEASE FROM SupportedVendorRelease WHERE VERSIONID =?", (self.versionID,))
        for row in DbCursor.fetchall():
            self.supportedVendorReleases.append(str(row[0]))
    
    def _getInterfaceNamesFromServer(self,DbCursor):
        '''Gets the interfaces dependent on the techpack
        
        Gets all interface information from the server for the techpack, and does a comparison using TPAPI.compareRStates to discover
        if the particular interface is dependent on the techpack version. If it is dependent a self.interfaces dictionary is
        populated with interface name and the InterfaceVersion object. This information is used to instantiate interface objects.
        
        SQL Statement:
                SELECT TECHPACKVERSION, INTERFACENAME FROM dwhrep.InterfaceTechpacks WHERE TECHPACKNAME =?  
        '''
        DbCursor.execute("SELECT TECHPACKVERSION, INTERFACENAME FROM dwhrep.InterfaceTechpacks WHERE TECHPACKNAME =?", (self.tpname,) )
        resultset = DbCursor.fetchall()
        for row in resultset:
            tpVersion=str(row[0])
            if Utils.compareRStates(self.versioning['TECHPACK_VERSION'], tpVersion) >=0:
                self.versioning['Interfaces'].append(str(row[2]))
    
    def _getUniversesFromServer(self,crsr):
        '''Gets the universes objects associated with the Techpack Version from the server'''
        crsr.execute("SELECT UNIVERSENAME FROM dwhrep.UniverseName WHERE VERSIONID =?", (self.versionID,))
        rows = crsr.fetchall()
        unvname = ''
        for row in rows:
            unvname = row[0]
            unv = UM.Universe(self.versionID,unvname)
            unv._getPropertiesFromServer(crsr)
            self.universes[unvname]= unv

    def getPropertiesFromTPI(self,tpiDict=None,filename=None): 
        '''Populate the objects contents from a tpiDict object or tpi file.
        
        If a tpi file is passed it is converted to a tpiDict object before processing.

        Exceptions: 
                   Raised if tpiDict and filename are both None (ie nothing to process)
                   Raised if there is tpi dict key error'''

        propsdict = {'Versioning' : self._tpiVersioning,
        'Measurementtype' : self._tpiMeasurementType,
        'Referencetable' : self._tpiReferenceTable,
        'Busyhour' : self._tpiBusyHour,
        'Supportedvendorrelease' : self._tpiSupportedVendorRelease,
        'Externalstatement' : self._tpiExternalStatement,
        #'InterfaceTechpacks' : self._tpiInterfaceTechpacks,
        #'META_COLLECTION_SETS' : self._tpiMetaCollectionSets,
        'Universename' : self._tpiUniverses,
        }
        
        if tpiDict==None and filename==None:
            strg = 'Nothing to Process'
            raise Exception(strg)
        else:
            if filename is not None:
                tpiDict = Utils.TpiDict(filename).returnTPIDict()
            self._tpiVersioning(tpiDictionary=tpiDict)
            for key in tpiDict: 
                if key in propsdict:
                    propsdict.get(key)(tpiDictionary=tpiDict)
    
    def _tpiUniverses(self,tpiDictionary):
        '''Extracts Universe Info from the tpiDictionary'''
        self.log.info('Universes')
        for row in tpiDictionary['Universename']['UNIVERSENAME']:
            name = tpiDictionary['Universename']['UNIVERSENAME'][row]
            unv = UM.Universe(self.versionID,name)
            unv._getPropertiesFromTPI(tpidict=tpiDictionary)
            self.universes[name] = unv
    
    def _tpiMeasurementType(self, tpiDictionary):
        '''Extracts MeasurementType information from the tpiDictionary'''
        self.log.info('Measurement Type')
        for row in tpiDictionary['Measurementtype']['TYPENAME']:
            ft = TPM.Table(self.versionID,tpiDictionary['Measurementtype']['TYPENAME'][row])
            ft.tableType = 'Measurement'
            ft._getPropertiesFromTPI(tpiDictionary)
            self.measurementTables[ft.name] = ft
            
    def _tpiReferenceTable(self, tpiDictionary):    
        '''Extracts referenceType information from the tpiDictionary'''
        self.log.info('Reference Table')
        for row in tpiDictionary['Referencetable']['TYPENAME']:
            if tpiDictionary['Referencetable']['BASEDEF'][row] != '1':
                ft = TPM.Table(self.versionID,tpiDictionary['Referencetable']['TYPENAME'][row])
                ft.tableType = 'Reference'
                ft._getPropertiesFromTPI(tpiDictionary)
                self.referenceTables[ft.name] = ft
                    
    def _tpiBusyHour(self, tpiDictionary):
        '''Extracts BusyHour information from the tpiDictionary'''
        self.log.info('Busy Hour')        
        busyHourNames = []
        for row in tpiDictionary['Busyhour']['BHOBJECT']:
            if tpiDictionary['Busyhour']['BHOBJECT'][row] not in busyHourNames:
                busyHourNames.append(tpiDictionary['Busyhour']['BHOBJECT'][row])

        for bh in busyHourNames:
            bho = TPM.BusyHour(self.versionID,bh)
            bho._getPropertiesFromTPI(tpiDictionary)
            self.busyHours[bh] = bho  
                  
    def _tpiSupportedVendorRelease(self, tpiDictionary):
        '''Extracts SupportedVendorRelease information from the tpiDictionary'''
        self.log.info('Supported Vendor Release')
        for row in tpiDictionary['Supportedvendorrelease']['VENDORRELEASE']:
            self.supportedVendorReleases.append(tpiDictionary['Supportedvendorrelease']['VENDORRELEASE'][row])
                     
    def _tpiExternalStatement(self, tpiDictionary):
        '''Extracts ExternalStatement information from the tpiDictionary'''
        self.log.info('External Statement')
        ExecOrder = 1
        for order in sorted(tpiDictionary['Externalstatement']['BASEDEF']):
            if tpiDictionary['Externalstatement']['BASEDEF'][order] != '1':
                ext = TPM.ExternalStatement(self.versionID, tpiDictionary['Externalstatement']['STATEMENTNAME'][order])
                ext._getPropertiesFromTPI(tpiDict=tpiDictionary, ExecOrder=ExecOrder)
                self.externalStatements[tpiDictionary['Externalstatement']['STATEMENTNAME'][order]] = ext
                ExecOrder = ExecOrder + 1             

#     def _tpiInterfaceTechpacks(self, tpiDictionary):                
#         '''Extracts InterfaceTechpacks information from the tpiDictionary'''
#         for row in tpiDictionary['InterfaceTechpacks']['interfacename']:
#             self.interfaceNames[tpiDictionary['InterfaceTechpacks']['interfacename'][row]] = tpiDictionary['InterfaceTechpacks']['interfaceversion'][row]
#         for intf in self.interfaceNames:
#             intfObject = INTFM.InterfaceVersion(intf,self.interfaceNames[intf])
#             intfObject.getPropertiesFromTPI(tpiDict=tpiDictionary)
#             self.interfaces[intf] = intfObject            
                   
    def _tpiVersioning(self, tpiDictionary):
        '''Extracts Versioning information from the tpiDictionary'''
        self.log.info('Versioning')
        self._intialiseVersion(tpiDictionary['Versioning']['VERSIONID'][1])
        properties = [ 'DESCRIPTION', 'STATUS', 'TECHPACK_NAME', 'TECHPACK_VERSION', 'TECHPACK_TYPE', 'PRODUCT_NUMBER', 'LOCKEDBY', 'LOCKDATE', 'ENIQ_LEVEL', 'LICENSENAME']
        self.manmods['ManModsFile'] = ''
        for column in tpiDictionary['Versioning']:
            if column in properties:
                self.versioning[column] = Utils.checkNull(tpiDictionary['Versioning'][column][1])
        
        if 'Techpackdependency' in tpiDictionary:
            for column in tpiDictionary['Techpackdependency']['VERSIONID']:
                self.dependencyTechPacks[tpiDictionary['Techpackdependency']['TECHPACKNAME'][column]] = tpiDictionary['Techpackdependency']['VERSION'][column]
   
    def toTPM(self, outputPath):
        fileStream = open(outputPath+'/' + self.tpname + '.tpm','w')
        
        fileStream.writelines('@TP:*:' + self.versionID)
        for key, value in self.properties.iteritems():
            fileStream.writelines(':*:' + key + ';*;' + value)
        fileStream.writelines(':*:\n')
        
        fileStream.writelines('@SupportedVendorReleases:*:')
        fileStream.writelines(':*:'.join(self.supportedVendorReleases)+':*:\n')
        
        fileStream.writelines('@Dependencies')
        for key, value in sorted(self.dependencyTechPacks.iteritems()):
            fileStream.writelines(':*:' + key + ';*;' + value)
        fileStream.writelines(':*:\n')
        
        #Tables
        for table in sorted(self.measurementTables.iterkeys()):
            self.measurementTables[table]._toTPM(fileStream)
        for table in sorted(self.referenceTables.iterkeys()):
            self.referenceTables[table]._toTPM(fileStream)
        
        #Busy Hours  
        for bh in sorted(self.busyHours.iterkeys()):
            outputXML += self.busyHours[bh]._toTPM(fileStream)
        
        #External Statements   
        tempDict = {}
        for ES in self.externalStatements:
            exeorder = self.externalStatements[ES].properties['EXECUTIONORDER']
            tempDict[exeorder] = self.externalStatements[ES]
        
        for ES in sorted(tempDict.iterkeys()): 
            outputXML += tempDict[ES]._toTPM(fileStream)
            
        #Universe
        
    def getPropertiesFromXls(self,xlsDict=None,filename=None):
        '''Populate the objects contents from a XlsDict object or xls file.
        
        If a xls file is passed it is converted to a XlsDict object before processing.

        Exceptions: 
                   Raised if XlsDict and filename are both None (ie nothing to process)
        '''
        if xlsDict==None and filename==None:
            strg = 'getPropertiesFromXls() Nothing to Process'
            raise Exception(strg)
        else:
            if filename is not None:
                xlsDict = Utils.XlsDict(filename).returnXlsDict()
            
            
            versionID = xlsDict['Versioning']['TECHPACK_NAME'] + ':((' + Utils.strFloatToInt(xlsDict['Versioning']['BUILD_NUMBER']) + '))'
            self._intialiseVersion(versionID)
            
            for entry in xlsDict['Versioning']:
                if entry != 'BUILD_NUMBER' and entry != 'VENDORRELEASE' and entry != 'Dependency' and entry != 'ManModsFile':
                    self.versioning[entry] = Utils.checkNull(xlsDict['Versioning'][entry])
                elif entry == 'ManModsFile':
                    self.manmods[entry] = Utils.checkNull(xlsDict['Versioning'][entry])

            #Supported Vendor Releases
            self.supportedVendorReleases = xlsDict['Versioning']['VENDORRELEASE']
            
            deps = xlsDict['Versioning']['Dependency'] + ','
            entries = deps.split(',')
            for item in entries:
                tp = item.split(':')
                if tp[0] != '':
                    self.dependencyTechPacks[tp[0]] = tp[1]
            
            
            elemBHsupport = []
            #Tables and BH
            for Name, Values in xlsDict['Tables'].iteritems():
                ft = TPM.Table(self.versionID, Name)
                ft.tableType = Values['TABLETYPE']
                ft._getPropertiesFromXls(xlsDict)
                if Values['TABLETYPE'] == 'Measurement':
                    self.measurementTables[ft.name] = ft
                elif Values['TABLETYPE'] == 'Reference':
                    self.referenceTables[ft.name] = ft
                      
                #ELEM BusyHour handling
                if 'RANKINGTABLE' in Values.keys() and 'ELEMENTBHSUPPORT' in Values.keys():
                    if Values['RANKINGTABLE'] == '1' and Values['ELEMENTBHSUPPORT'] == '1':
                        bho = TPM.BusyHour(self.versionID,'ELEM')
                        bho.rankingTable = Name
                        bho._getPropertiesFromXls(xlsDict)
                        bho._createDefaultBusyHourTypes()
                        self.busyHours['ELEM'] = bho
                    
                    if Values['RANKINGTABLE'] != '1' and Values['ELEMENTBHSUPPORT'] == '1':
                        elemBHsupport.append(Name)
                    
                #Object BusyHour support
                if 'OBJECTBH' in Values.keys():
                	if Values['OBJECTBH'] != None:
	                    BHobjs = Values['OBJECTBH']+','
	                    BHobjs = BHobjs.split(',')
	                    for bh in BHobjs:
	                        if bh != None and bh != '':
	                            if bh not in self.busyHours:
	                                bho = TPM.BusyHour(self.versionID,bh)
	                                bho._getPropertiesFromXls(xlsDict)
	                                bho._createDefaultBusyHourTypes()
	                                self.busyHours[bh] = bho 
	                            
	                            if Values['RANKINGTABLE'] != '1':
	                                self.busyHours[bh].supportedTables.append(Name)              
	                            else:
	                                self.busyHours[bh].rankingTable = Name
           
            if len(elemBHsupport)>0:
                self.busyHours['ELEM'].supportedTables = elemBHsupport
            
            if 'Universe' in xlsDict.keys():   
                for Name,  Values in xlsDict['Universe'].iteritems():
                    unv=UM.Universe(self.versionID,Name)
                    unv._getPropertiesFromXls(xlsDict)
                    self.universes[unv.universeName]=unv
            
            if 'ExternalStatements' in xlsDict.keys():           
                for Name, Values in xlsDict['ExternalStatements'].iteritems():
                    ext = TPM.ExternalStatement(self.versionID, Name)
                    ext._getPropertiesFromXls(xlsDict)
                    self.externalStatements[Name] = ext
            
            if 'Interfaces' in xlsDict.keys():
                interfaces = []
                for Name in xlsDict['Interfaces'].keys():
                    items = Name.split(':')
                    if 'Interfaces' in self.versioning:
                        interfaces = self.versioning['Interfaces'] 
                    interfaces.append(items[0])
                    self.versioning['Interfaces'] = interfaces
    
    def getPropertiesFromXlsx(self,xlsxDict):
        '''Populate the objects contents from a XlsxDict object.
        
        Exceptions: 
                   Raised if XlsDict and filename are both None (ie nothing to process)
        '''
        
        if xlsxDict==None:
            raise Exception('Nothing to process')
        
        versionID = xlsxDict['Versioning']['TECHPACK_NAME'] + ':((' + Utils.strFloatToInt(xlsxDict['Versioning']['BUILD_NUMBER']) + '))'
        self._intialiseVersion(versionID)
        
        for entry in xlsxDict['Versioning']:
            if entry == 'Interfaces':
                interfaces = xlsxDict['Versioning']['Interfaces']
                if interfaces != None:
                    self.versioning['Interfaces'] = interfaces.split(',')
            
            elif entry == 'Dependency':
                for item in (xlsxDict['Versioning']['Dependency'] + ',').split(','):
                    tp = item.split(':')
                    if tp[0] != '':
                        self.dependencyTechPacks[tp[0]] = tp[1]
            elif entry == 'VENDORRELEASE':
                self.supportedVendorReleases = xlsxDict['Versioning']['VENDORRELEASE'].split(',')

            elif entry == 'ManModsFile':
                self.manmods['ManModsFile'] = Utils.checkNull(xlsxDict['Versioning'][entry])
            elif entry != 'BUILD_NUMBER':
                self.versioning[entry] = Utils.checkNull(xlsxDict['Versioning'][entry])
        
        
        elemBHsupport = []
        #Tables and BH
        for Name, Values in xlsxDict['Tables'].iteritems():
            ft = TPM.Table(self.versionID, Name)
            ft.tableType = Values['TABLETYPE']
            ft._getPropertiesFromXlsx(xlsxDict)
            if Values['TABLETYPE'] == 'Measurement':
                self.measurementTables[ft.name] = ft
            elif Values['TABLETYPE'] == 'Reference':
                self.referenceTables[ft.name] = ft
            
            #ELEM BusyHour handling
            if 'RANKINGTABLE' in Values.keys() and 'ELEMENTBHSUPPORT' in Values.keys():
                if Values['RANKINGTABLE'] == '1' and Values['ELEMENTBHSUPPORT'] == '1':
                    bho = TPM.BusyHour(self.versionID,'ELEM')
                    bho.rankingTable = Name
                    bho._getPropertiesFromXlsx(xlsxDict)
                    bho._createDefaultBusyHourTypes()
                    self.busyHours['ELEM'] = bho
                
                if Values['RANKINGTABLE'] != '1' and Values['ELEMENTBHSUPPORT'] == '1':
                    elemBHsupport.append(Name)
                
            #Object BusyHour support                
            if 'OBJECTBH' in Values.keys():
                if Values['OBJECTBH'] != None:
    	            BHobjs = Values['OBJECTBH']+','
    	            BHobjs = BHobjs.split(',')
    	            for bh in BHobjs:
    	                if bh != None and bh != '':
    	                    if bh not in self.busyHours:
    	                        bho = TPM.BusyHour(self.versionID,bh)
    	                        bho._getPropertiesFromXlsx(xlsxDict)
    	                        bho._createDefaultBusyHourTypes()
    	                        self.busyHours[bh] = bho 
    	                    if Values['RANKINGTABLE'] != '1':
    	                        self.busyHours[bh].supportedTables.append(Name)              
    	                    else:
    	                        self.busyHours[bh].rankingTable = Name
       
        if len(elemBHsupport)>0:
            self.busyHours['ELEM'].supportedTables = elemBHsupport
        
        if 'uni' in xlsxDict.keys():   
            for Name,  Values in xlsxDict['uni'].iteritems():
                if Name not in self.universes:
                    unv=UM.Universe(self.versionID,Name)
                    unv._getPropertiesFromXlsx(xlsxDict)
                    self.universes[unv.universeName]=unv
        
        if 'ES' in xlsxDict.keys():           
            for Name, Values in xlsxDict['ES'].iteritems():
                ext = TPM.ExternalStatement(self.versionID, Name)
                ext._getPropertiesFromXlsx(xlsxDict)
                self.externalStatements[Name] = ext
                
        if 'Vectors' in xlsxDict.keys():
            if len(xlsxDict['Vectors']) != 0:
                self.isVector = True
        
    
    def toXLSX(self, outputPath):
        ''' Converts the object to an excel document
            
        Parent toXLSX() method is responsible for triggering child object toXLSX() methods
        '''
        
        workbookPath = outputPath + '\\' + self.tpname + '_' + str(self.versionNo) + '_' + self.versioning['TECHPACK_VERSION'] + '_TEST.xlsx'
        workbook = XSSFWorkbook()
 
        xlsxFile = Utils.XlsxFile()
        workbook = xlsxFile.createXlsDoc(workbook, 'TP')
                    
        sheet = workbook.getSheet('Coversheet')
        self.log.info('Coversheet')
        for FDColumn in xlsxFile.VersioningList:
            headercell = xlsxFile.findValue(sheet, FDColumn)
            if FDColumn == 'VENDORRELEASE':
                self.writeToWorkbook(sheet, headercell, ",".join(self.supportedVendorReleases))
            elif FDColumn == 'BUILD_NUMBER':
                self.writeToWorkbook(sheet, headercell, str(self.versionNo))
            elif FDColumn == 'Dependency':
                dependencies = []
                for key, value in self.dependencyTechPacks.iteritems():
                    dependencies.append(key + ':' + value)
                self.writeToWorkbook(sheet, headercell, ",".join(dependencies))
            elif FDColumn == 'Interfaces' and 'Interfaces' in self.versioning:
                self.writeToWorkbook(sheet, headercell, ",".join(self.versioning[FDColumn]))
            elif FDColumn == 'ManModsFile':
                self.writeToWorkbook(sheet, headercell, self.manmods[FDColumn])
            else:
                if FDColumn in self.versioning:
                    self.writeToWorkbook(sheet, headercell, self.versioning[FDColumn])
        
        TransformationCollection = {} #This is required to ensure the sequence of transformations for multiple parsers
        self.log.info('Measurement Tables')
        for MeasTable in self.measurementTables.itervalues():
            TransformationCollection = MeasTable._toXLSX(xlsxFile, workbook, TransformationCollection)
        
        self.log.info('Topology Tables')
        for RefTable in self.referenceTables.itervalues():   
            TransformationCollection = RefTable._toXLSX(xlsxFile, workbook, TransformationCollection)
        
        self.log.info('Parser information')
        for parser, transcollection in TransformationCollection.iteritems():
            for orderNum in sorted(transcollection.keys()):
                transcollection[orderNum]._toXLSX(xlsxFile, workbook)
        
        self.log.info('Busy Hours')
        for BH in self.busyHours.itervalues():   
            BH._toXLSX(xlsxFile, workbook)
        
        self.log.info('External Statements')
        for ES in self.externalStatements.itervalues():   
            ES._toXLSX(xlsxFile, workbook, workbookPath)
        
        self.log.info('Universes')
        for Uni in self.universes.itervalues():   
            Uni._toXLSX(xlsxFile, workbook)
#          
#         for Intf in self.interfaces.itervalues():   
#             Intf._toXLS(workbook)
        
        self.log.info('Writing to file for ' + self.tpname)
        workbook.write(FileOutputStream(workbookPath))
    
    def writeToWorkbook(self, sheet, headercell, value):
        
        cellNumber = headercell.getColumnIndex() + 1
        rowNumber = headercell.getRowIndex()
        sheet.getRow(rowNumber).createCell(cellNumber).setCellValue(value)

    def getPropertiesFromXML(self,xmlElement=None,filename=None):
        '''Populates the objects content from an xmlElement or an XML file
        
        getPropertiesFromXML() method is responsible for triggering its child objects getPropertiesFromXML() method
        
        '''
        if filename is not None:
            xmlElement = Utils.fileToXMLObject(open(filename,'r'))
            
        self._intialiseVersion(xmlElement.attrib['name'])
        for elem1 in xmlElement:
            
            #Populate Versioning
            if elem1.tag=='Versioning':
                for elem2 in elem1:
                    if elem2.tag=='SupportedVendorReleases':
                        for elem3 in elem2:
                            if elem3.tag=='VendorRelease':
                                self.supportedVendorReleases.append(Utils.safeNull(elem3.text))
                    elif elem2.tag=='Dependencies':
                        for elem3 in elem2:
                            self.dependencyTechPacks[elem3.tag] = Utils.safeNull(elem3.text)
                    else:
                        self.versioning[elem2.tag] = Utils.safeNull(elem2.text)

            if elem1.tag=='ManModsFile':
                self.manmods['ManModsFile'] = elem1.text
                
            #Populate Tables
            if elem1.tag=='Tables':
                for elem2 in elem1:
                    if elem2.tag=='Table':
                        t = TPM.Table(self.versionID, elem2.attrib['name'])
                        t.tableType = elem2.attrib['tableType']
                        t._getPropertiesFromXML(elem2)

                        if elem2.attrib['tableType'] == 'Measurement':
                                self.measurementTables[elem2.attrib['name']] = t
                        if elem2.attrib['tableType'] == 'Reference':
                                self.referenceTables[elem2.attrib['name']] = t
                                            
            #Parsers (ENIQ 2.X, not used)                
            if elem1.tag=='Parsers':
                for elem2 in elem2:
                    if elem2.tag=='Parser':
                        if elem2.attrib['type'] not in self.parserNames:
                            self.parserNames.append(elem2.attrib['type'])
                        tpParser = TPM.Parser(self.versionID,self.tpname,elem2.attrib['type'])
                        tpParser.getPropertiesFromXML(elem2)
                        self.parsers[elem2.attrib['type']] = tpParser
                        
            #BusyHours
            if elem1.tag == 'BusyHours':
                for elem2 in elem1:
                    bhName =  elem2.attrib['name']
                    bh = TPM.BusyHour(self.versionID,bhName)
                    bh._getPropertiesFromXML(elem2)
                    self.busyHours[bhName] = bh
                    
#             #Interfaces    
#             if elem1.tag == 'Interfaces':
#                     for elem2 in elem1:
#                         if elem2.tag == 'Interface':   
#                             name = elem2.attrib['name']
#                             version = elem2.attrib['version']
#                             self.interfaceNames[name] = version

            #External Statements
            if elem1.tag == 'ExternalStatement':
                for elem2 in elem1:
                    if elem2.tag == 'ExternalStatement':
                        name = elem2.attrib['name']
                        es = TPM.ExternalStatement(self.versionID, name)
                        es._getPropertiesFromXML(elem2)
                        self.externalStatements[name] = es
            
            #BO details                             
            if elem1.tag == 'BO':
                for elem2 in elem1:
                    if elem2.tag == 'Universes':
                        for elem3 in elem2:
                            if elem3.tag == 'Universe':
                                uo = UM.Universe(self.versionID,elem3.attrib['name'])
                                uo._getPropertiesFromXML(elem3)
                                self.universes[elem3.attrib['name']] = uo
    
    def toXML(self,indent=1):
        '''Converts the object to an xmlString representation
        
        Indent value is used for string indentation. Default to 1
        Parent toXML() method is responsible for triggering child object toXML() methods.

        Return Value: xmlString 
        '''       
        
        offset = '    '
        os = "\n" + offset*indent
        os2 = os + offset
        os3 = os2 + offset
        os4 = os3 + offset
        
        outputXML = ''
        outputXML += '<Techpack name="' + self.versionID +'">'
        
        #Versioning Information
        outputXML += os+'<Versioning>'
        for item in sorted(self.versioning.iterkeys()):
            outputXML += os2+'<'+str(item)+'>'+Utils.escape(self.versioning[item])+'</'+str(item)+'>'
        
        outputXML += os2+'<SupportedVendorReleases>'
        for item in self.supportedVendorReleases:
            outputXML += os3+'<VendorRelease>' + item + '</VendorRelease>'
        outputXML += os2+'</SupportedVendorReleases>'
        
        outputXML += os2+'<Dependencies>'
        for item in sorted(self.dependencyTechPacks.iterkeys()):
            outputXML += os3+'<'+str(item)+'>'+ self.dependencyTechPacks[item] +'</'+str(item)+'>'
        outputXML += os2+'</Dependencies>'
        
        outputXML += os+'</Versioning>'
        
        if len(self.manmods) != 0: 
            outputXML += os+'<ManModsFile>'+self.manmods['ManModsFile']+'</ManModsFile>'
        
        #Tables
        outputXML += os+'<Tables>'
        for table in sorted(self.measurementTables.iterkeys()):
            outputXML += self.measurementTables[table]._toXML(indent+1)
        for table in sorted(self.referenceTables.iterkeys()):
            outputXML += self.referenceTables[table]._toXML(indent+1)
        outputXML += os+'</Tables>'
        
        
        #BusyHours
        outputXML += os+'<BusyHours>'
        for bh in sorted(self.busyHours.iterkeys()):
            outputXML += self.busyHours[bh]._toXML(indent+1)
        outputXML += os+'</BusyHours>'
        
        
        #External Statements
        outputXML += os+'<ExternalStatement>'
        tempDict = {}
        for ES in self.externalStatements:
            exeorder = self.externalStatements[ES].properties['EXECUTIONORDER']
            tempDict[exeorder] = self.externalStatements[ES]._toXML(indent+1)
        
        for ES in sorted(tempDict.iterkeys()): 
            outputXML += tempDict[ES]
        
        outputXML += os+'</ExternalStatement>'   
     
        #Business Objects information
        outputXML += os+'<BO>'
        outputXML += os2+'<Universes>'
        for unv in sorted(self.universes.iterkeys()):
            outputXML += os3+'<Universe name="' + unv +'">'
            outputXML += self.universes[unv]._toXML(indent+3)
            outputXML += os3+'</Universe>'
        outputXML += os2+'</Universes>'
        outputXML += os+'</BO>'
            
#         #Interfaces
#         outputXML += os+'<Interfaces>'
#         for intfName, intfVersion in self.interfaceNames.iteritems():
#             outputXML += os2+'<Interface name="' + intfName +'" version="' + intfVersion + '"/>'
#         outputXML += os+'</Interfaces>'
        
        outputXML +='\n</Techpack>'
        
        return outputXML
    
    def populateRepDbDicts(self):
        TpDependencies = []
        for tpname, Rstate in self.dependencyTechPacks.iteritems():
            TpDependency = {}
            TpDependency['VERSIONID'] = self.versionID
            TpDependency['TECHPACKNAME'] = tpname
            TpDependency['VERSION'] = Rstate
            TpDependencies.append(TpDependency)
        
        Versioning = deepcopy(self.versioning)
        Versioning['TECHPACK_NAME'] = self.tpname
        Versioning['VERSIONID'] = self.versionID
        
        return Versioning, TpDependencies, self.supportedVendorReleases
    
    def difference(self,tpvObject):
        ''' Calculates the difference between two TechPackVersion Objects
            
            Method takes the TechPackVersion to be compared against as input
            Prior to the diff a deltaObject is created for recording the differences
            A DeltaTPV (TechPackVersion Object) is created for capturing objects that have new or changed content (depreciated)
            
            The Difference method will trigger the difference method of its child objects, passing
            in the object to compare, deltaObj and deltaTPV. After calculating the diff the child object passes these objects
            back in conjunction with a flag to say whether a (only new or changed content.. not deleted) was found or not. This flag is used to decide
            whether a child object should be added to the parent object in the DeltaTPV.
            
            Returns:
                    deltaObj
            
        '''
        deltaObj = Utils.Delta(self.versionID,tpvObject.versionID)
        
        #########################################################################################################################################
        # Versioning diff
        Delta = Utils.DictDiffer(self.versioning,tpvObject.versioning)
        deltaObj.location.append('Versioning')
        excludedProperties = ['LOCKDATE', 'VERSIONID', 'LOCKEDBY', 'ENIQ_LEVEL', 'STATUS', 'BASEDEFINITION']
        for item in Delta.changed():
            if item not in excludedProperties:
                deltaObj.addChange('<Changed>', item, self.versioning[item], tpvObject.versioning[item])
        
        for item in Delta.added():
            if item not in excludedProperties:
                deltaObj.addChange('<Added>', item, '', tpvObject.versioning[item])
                
        for item in Delta.removed():
            if item not in excludedProperties:
                deltaObj.addChange('<Removed>', item, self.versioning[item], '')

        deltaObj.location.pop()
        
        #########################################################################################################################################
        # Dependency TP diff
        Delta = Utils.DictDiffer(self.dependencyTechPacks,tpvObject.dependencyTechPacks)
        deltaObj.location.append('DependencyTechPacks')
        for item in Delta.changed():
            deltaObj.addChange('<Changed>', item, self.dependencyTechPacks[item], tpvObject.dependencyTechPacks[item])
        
        for item in Delta.added():
            deltaObj.addChange('<Added>', item, '', tpvObject.dependencyTechPacks[item])
                
        for item in Delta.removed():
            deltaObj.addChange('<Removed>', item, self.dependencyTechPacks[item], '')

        deltaObj.location.pop()
        
        #########################################################################################################################################
        #Vendor Release Diff
        deltaObj.location.append('SupportedVendorReleases')
        Delta = list(set(tpvObject.supportedVendorReleases) - set(self.supportedVendorReleases))
        for item in Delta:
            deltaObj.addChange('<Added>', 'Properties', '', item)
        
        Delta = list(set(self.supportedVendorReleases) - set(tpvObject.supportedVendorReleases))
        for item in Delta:
            deltaObj.addChange('<Removed>', 'Properties', item, '')
        
        deltaObj.location.pop()
                
        ##############################################################################################################################################
        #Measurement Table Diff
        Delta = Utils.DictDiffer(self.measurementTables,tpvObject.measurementTables)
        deltaObj.location.append('Table')
        for item in Delta.added():
            deltaObj.addChange('<Added>', tpvObject.measurementTables[item].tableType, '', item)
      
        for item in Delta.removed():
            deltaObj.addChange('<Removed>', self.measurementTables[item].tableType, item, '')
        
        deltaObj.location.pop()
        
        for item in Delta.common():
            deltaObj.location.append('Table='+item)
            deltaObj = self.measurementTables[item].difference(tpvObject.measurementTables[item],deltaObj)
            deltaObj.location.pop()
            
        ##############################################################################################################################################
        #Reference Table Diff
        Delta = Utils.DictDiffer(self.referenceTables,tpvObject.referenceTables)
        deltaObj.location.append('Table')
        for item in Delta.added():
            deltaObj.addChange('<Added>', tpvObject.referenceTables[item].tableType, '', item)
      
        for item in Delta.removed():
            deltaObj.addChange('<Removed>', self.referenceTables[item].tableType, item, '')
        
        deltaObj.location.pop()
        
        for item in Delta.common():
            deltaObj.location.append('Table='+item)
            deltaObj = self.referenceTables[item].difference(tpvObject.referenceTables[item],deltaObj)
            deltaObj.location.pop()
        
        ##########################################################################################################################################
        #Busy Hour Diff
        Delta = Utils.DictDiffer(self.busyHours,tpvObject.busyHours)
        deltaObj.location.append('BusyHour')
        for item in Delta.added():
            deltaObj.addChange('<Added>', tpvObject.busyHours[item].rankingTable, '', item)
      
        for item in Delta.removed():
            deltaObj.addChange('<Removed>', self.busyHours[item].rankingTable, item, '')
        
        deltaObj.location.pop()
        
        for item in Delta.common():
            deltaObj.location.append('BusyHour='+item)
            deltaObj = self.busyHours[item].difference(tpvObject.busyHours[item],deltaObj)
            deltaObj.location.pop()
        
        ##########################################################################################################################################
        #External Statements Diff
        Delta = Utils.DictDiffer(self.externalStatements,tpvObject.externalStatements)
        deltaObj.location.append('ExternalStatement')
        for item in Delta.added():
            deltaObj.addChange('<Added>', tpvObject.externalStatements[item].name, '', item)
      
        for item in Delta.removed():
            deltaObj.addChange('<Removed>', self.externalStatements[item].name, item, '')
        
        deltaObj.location.pop()
        
        for item in Delta.common():
            deltaObj.location.append('ExternalStatement='+item)
            deltaObj = self.externalStatements[item].difference(tpvObject.externalStatements[item],deltaObj)
            deltaObj.location.pop()
        
        #########################################################################################################################################
        #Universe Diff
        deltaObj.location.append('Universe')
        Delta = list(set(tpvObject.universeNames) - set(self.universeNames))
        for item in Delta:
            deltaObj.addChange('<Added>', 'Properties', '', item)
        
        Delta = list(set(self.universeNames) - set(tpvObject.universeNames))
        for item in Delta:
            deltaObj.addChange('<Removed>', 'Properties', item, '')
        
        deltaObj.location.pop()
        
            
        #########################################################################################################################################
        #Interface Diff
        deltaObj.location.append('Interface')
        Delta = list(set(tpvObject.interfaceNames) - set(self.interfaceNames))
        for item in Delta:
            deltaObj.addChange('<Added>', 'Properties', '', item)
        
        Delta = list(set(self.interfaceNames) - set(tpvObject.interfaceNames))
        for item in Delta:
            deltaObj.addChange('<Removed>', 'Properties', item, '')
        
        deltaObj.location.pop()
        
        
        return deltaObj 
    
    