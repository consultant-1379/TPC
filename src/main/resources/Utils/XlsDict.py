'''
Created on May 31, 2016

@author: ebrifol
'''

from ODict import odict
import Utils
import os
import sys
import traceback
from java.io import File
from org.apache.poi.xssf.usermodel import XSSFWorkbook
from os import path

class XlsDict(object):
    '''Class for extraction and intermediate storage of metadata from inside a xls file.'''
    
    _instance = None
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(XlsDict, cls).__new__(
                                cls, *args, **kwargs)
        return cls._instance
    
    VersioningDict = {'Name': 'TECHPACK_NAME', 'Description': 'DESCRIPTION', 'Release': 'TECHPACK_VERSION',
                      'Product number': 'PRODUCT_NUMBER', 'License': 'LICENSENAME', 'Type': 'TECHPACK_TYPE',
                      'Supported Versions': 'VENDORRELEASE', 'Build Number': 'BUILD_NUMBER', 'Dependency TechPack': 'Dependency',
                      'ManModsFile':'ManModsFile', 'Universe Delivered': 'UNIVERSE_DELIVERED', 'Supported Node Types': 'SUPPORTED_NODE_TYPES'}
    InterfaceDict = {'Interface R-State': 'RSTATE', 'Interface Type': 'INTERFACETYPE', 'Description': 'DESCRIPTION',
                     'Tech Pack': 'intfTechpacks', 'Dependencies': 'dependencies', 'Parser Name': 'DATAFORMATTYPE',
                     'Element Type': 'ELEMTYPE'}
    FactTableDict = {'Fact Table Description': 'DESCRIPTION', 'Universe Class': 'CLASSIFICATION',
                  'Table Sizing': 'SIZING', 'Total aggregation': 'TOTALAGG', 'Object BHs': 'OBJECTBH', 'Element BHs': 'ELEMENTBHSUPPORT',
                  'Rank Table': 'RANKINGTABLE', 'Count Table': 'DELTACALCSUPPORT', 'Vector Table': 'VECTORSUPPORT', 'Plain Table': 'PLAINTABLE',
                  'Universe Extension': 'UNIVERSEEXTENSION', 'Joinable': 'JOINABLE', 'FOLLOWJOHN': 'FOLLOWJOHN'}
    FTKeysDict = {'Key Description': 'DESCRIPTION', 'Data type': 'DATATYPE', 'Duplicate Constraint': 'UNIQUEKEY',
                  'Nullable': 'NULLABLE', 'IQ Index': 'INDEXES', 'Universe object': 'UNIVOBJECT',
                  'Element Column': 'ISELEMENT', 'IncludeSQL': 'INCLUDESQL'}
    FTCountersDict = {'Counter Description': 'DESCRIPTION', 'Data type': 'DATATYPE', 'Time Aggregation': 'TIMEAGGREGATION',
                  'Group Aggregation': 'GROUPAGGREGATION', 'Universe Object': 'UNIVOBJECT', 'Universe Class': 'UNIVCLASS',
                  'Counter Type': 'COUNTERTYPE', 'IncludeSQL': 'INCLUDESQL', 'FOLLOWJOHN': 'FOLLOWJOHN'}
    #Removed 'QUANTITY' as part of fix EQEV-57773
    VectorsDict = {'From': 'VFROM', 'To': 'VTO', 'Vector Description': 'MEASURE'}
    TopTableDict = {'Topology Table Description': 'DESCRIPTION', 'Source Type': 'UPDATE_POLICY'}
    TopKeysDict = {'Key Description': 'DESCRIPTION', 'Data type': 'DATATYPE', 'Duplicate Constraint': 'UNIQUEKEY',
                   'Nullable': 'NULLABLE', 'Universe Class': 'UNIVERSECLASS', 'Universe Object': 'UNIVERSEOBJECT',
                   'Universe Condition': 'UNIVERSECONDITION', 'IncludeSQL': 'INCLUDESQL', 'Include Update': 'INCLUDEUPD'}
    TransDict = {'Transformation Type': 'TYPE', 'Transformation Source': 'SOURCE', 'Transformation Target': 'TARGET',
                 'Transformation Config': 'CONFIG'}
    BHDict = {'Description': 'DESCRIPTION', 'Where Clause': 'WHERECLAUSE', 'Criteria': 'BHCRITERIA',
              'Aggregation Type': 'AGGREGATIONTYPE', 'Loopback': 'LOOKBACK', 'P Threshold': 'P_THRESHOLD', 'N Threshold': 'N_THRESHOLD', 'SupportedTables': 'SupportedTables'}
    ESDict = {'Database Name': 'DBCONNECTION', 'Definition': 'STATEMENT'}
    RODict = {'Fact Table': 'MEASTYPE', 'Level': 'MEASLEVEL', 'Object Class': 'OBJECTCLASS', 'Object Name': 'OBJECTNAME'}
    RCDict = {'Fact Table': 'FACTTABLE', 'Level': 'VERLEVEL', 'Condition Class': 'CONDITIONCLASS', 'Condition': 'VERCONDITION',
              'Prompt Name (1)': 'PROMPTNAME1', 'Prompt Value (1)': 'PROMPTVALUE1', 'Prompt Name (2)': 'PROMPTNAME2',
              'Prompt Value (2)': 'PROMPTVALUE2', 'Object Condition': 'OBJECTCONDITION', 'Prompt Name (3)': 'PROMPTNAME3',
              'Prompt Value (3)': 'PROMPTVALUE3'}
    UniExtDict = {'Universe Ext Name': 'UNIVERSEEXTENSIONNAME'}
    UniTableDict = {'Topology Table Owner': 'OWNER', 'Table Alias': 'ALIAS', 'Universe Extension': 'UNIVERSEEXTENSION'}
    UniClassDict = {'Class Description': 'DESCRIPTION', 'Parent Class Name': 'PARENT', 'Universe Extension': 'UNIVERSEEXTENSION'}
    UniObjDict = {'Unv. Class': 'UniverseClass', 'Unv. Description': 'DESCRIPTION', 'Unv. Type': 'OBJECTTYPE', 'Unv. Qualification': 'QUALIFICATION',
                  'Unv. Aggregation': 'AGGREGATION', 'Select statement': 'OBJSELECT', 'Where Clause': 'OBJWHERE',
                  'Prompt Hierarchy': 'PROMPTHIERARCHY', 'Universe Extension': 'UNIVERSEEXTENSION'}
    UniConDict = {'Condition Description': 'DESCRIPTION', 'Where Clause': 'CONDWHERE', 'Auto generate': 'AUTOGENERATE',
                  'Condition object class': 'CONDOBJCLASS', 'Condition object': 'CONDOBJECT', 'Prompt Text': 'PROMPTTEXT',
                  'Multi selection': 'MULTISELECTION', 'Free text': 'FREETEXT', 'Universe Extension': 'UNIVERSEEXTENSION'}
    UniJoinsDict = {'Source Table': 'SOURCETABLE', 'Source Level': 'SOURCELEVEL', 'Source Columns': 'SOURCECOLUMN',
                    'Target Table': 'TARGETTABLE', 'Target Level': 'TARGETLEVEL', 'Target Columns': 'TARGETCOLUMN',
                    'Join Cardinality': 'CARDINALITY', 'Contexts': 'CONTEXT', 'Excluded contexts': 'EXCLUDEDCONTEXTS',
                    'Universe Extension': 'UNIVERSEEXTENSION'}
    verObjDict = {'Fact Table': 'MEASTYPE', 'Level': 'MEASLEVEL', 'Object Class': 'OBJECTCLASS', 'Object Name': 'OBJECTNAME'}
    verConDict = {'Fact Table': 'FACTTABLE', 'Level': 'VERLEVEL', 'Condition Class': 'CONDITIONCLASS', 'Condition': 'VERCONDITION',
                  'Prompt Name (1)': 'PROMPTNAME1', 'Prompt Value (1)': 'PROMPTVALUE1', 'Prompt Name (2)': 'PROMPTNAME2', 'Prompt Value (2)': 'PROMPTVALUE2',
                  'Object Condition': 'OBJECTCONDITION', 'Prompt Name (3)': 'PROMPTNAME3', 'Prompt Value (3)': 'PROMPTVALUE3'}
    
    updatePolicylist = ["Static", "Predefined", "Dynamic", "Timed Dynamic", "History Dynamic" ]

    
    def parse(self, logger, filename=None):
        if filename == None:
            return

        from java.io import File
        workbook = XSSFWorkbook(File(filename))
        self.xlsxdict = odict()
        
        # CoverSheet and Versioning information
        logger.info('Coversheet')
        sheet = workbook.getSheet('Coversheet')
        self.xlsxdict['Versioning'] = odict()
        
        # Check For Manual Modifications
        manMods = self.findValue(sheet, 'ManModsFile')
        if manMods != None:
            manModRow = manMods.getRowIndex()
            fileIndex = filename.index(".")
            subFileName = filename[:fileIndex]
            value = self.getCellValue(sheet,manModRow,1).strip()
            if (value != ""):
                if (value.find(subFileName+"_SetsModifications_TPC.xml") != -1):
                    self.xlsxdict['Versioning']['ManModsFile'] = value
                else:
                    logger.error("Manual Modification File is not present or File Format is not correct. Please follow Manual Modification file name in the specific format. For example <Model-TName>_SetsModifications_TPC.xml")
                    raise Exception("Manual Modification File is not present or File Format is not correct. Please follow Manual Modification file name in the specific format. For example <Model-TName>_SetsModifications_TPC.xml")
            else:
                self.xlsxdict['Versioning']['ManModsFile'] = ""
                logger.info("Manual Modification details are not provided in the Model-T. So proceeding without Manual Modifications")
        else:
            logger.error("Please check 'Coversheet' contains 'ManModsFile' row or syntax is correct. Please add 'ManModsFile' row in the 'Coversheet' of Model-T.")
            raise Exception("Please check 'Coversheet' contains 'ManModsFile' row or syntax is correct. Please add 'ManModsFile' row in the 'Coversheet' of Model-T.")
            
        #check for Adding description
        universeDeliveredCell = self.findValue(sheet, 'Universe Delivered')
        if universeDeliveredCell != None:
            universeDeliveredRowIndex = universeDeliveredCell.getRowIndex()
            value = self.getCellValue(sheet,universeDeliveredRowIndex,1).strip()
            if (value != "" and (value.upper() == 'YES' or value.upper() == 'NO')):
                if value.upper() == 'YES':
                    logger.info('Universe is being delivered for this Techpack, so Counter and key description will not be added for this Techpack Document')
                self.xlsxdict['Versioning']['UNIVERSE_DELIVERED'] = value.upper()
            else:
                self.xlsxdict['Versioning']['UNIVERSE_DELIVERED'] = value
                logger.info("Universe Delivered details are not correct in the Model-T. So proceeding without adding counter and key description in Techpack Document ")
        else:
            logger.error("Please check 'Coversheet' contains 'Universe Delivered' row or syntax is correct. Please add 'Universe Delivery' row in the 'Coversheet' of Model-T.")
            raise Exception("Please check 'Coversheet' contains 'Universe Delivered' row or syntax is correct. Please add 'Universe Delivered' row in the 'Coversheet' of Model-T.")
        
        for FDColumn, Parameter in self.VersioningDict.iteritems():
            rowNumber = self.findValue(sheet, FDColumn).getRowIndex()
            if (Parameter != 'ManModsFile' and Parameter != 'UNIVERSE_DELIVERED'):
                value = ''
                cell = sheet.getRow(rowNumber).getCell(1)
                if(cell != None):
                    value = cell.toString()
                    value = value.strip()
            
                if Parameter == 'VENDORRELEASE':
                    value = value.split(',')
                    value = [val.strip() for val in value] # removing leading and trailing whitespace from cell value
                self.xlsxdict['Versioning'][Parameter] = value

        # Interfaces
        logger.info('Interfaces')
        sheet = workbook.getSheet('Interfaces')
        self.xlsxdict['Interfaces'] = odict()
        sheet.getRow(0).removeCell(sheet.getRow(0).getCell(0))
        for intfNameCell in sheet.getRow(0):
            intfName = intfNameCell.toString()
            if intfName != '':
                self.xlsxdict['Interfaces'][intfName] = odict()
                self.xlsxdict['Interfaces'][intfName]['intfConfig'] = odict()    
                for rowNum in xrange(1, sheet.getLastRowNum() + 1):
                    headerValue = self.getCellValue(sheet, rowNum, 0)
                    value = ''
                    if headerValue != '':
                        try:
                            value = sheet.getRow(rowNum).getCell(intfNameCell.getColumnIndex()).toString()
                            self.xlsxdict['Interfaces'][intfName][self.InterfaceDict[headerValue]] = self.encodeValue(value)
                        except:
                            self.xlsxdict['Interfaces'][intfName]['intfConfig'][headerValue] = self.encodeValue(value)

        # Fact Tables
        logger.info('Fact Tables')
        f=open('TagId.txt','w')
        sheet = workbook.getSheet('Fact Tables')
        self.xlsxdict['Tables'] = odict()
        sheet.getRow(0).removeCell(sheet.getRow(0).getCell(0))
        l=["Fact Table Name","Fact Table Description","Universe Class","Table Sizing","Total aggregation","Object BHs","Element BHs","Rank Table","Count Table","Vector Table","Plain Table","Universe Extension","Joinable","FOLLOWJOHN"]
        for rowNum in xrange(1, sheet.getLastRowNum() + 1):
            tableName = self.getCellValue(sheet, rowNum, 0)
            if tableName != '':
                self.xlsxdict['Tables'][tableName] = odict()
                self.xlsxdict['Tables'][tableName]['TABLETYPE'] = 'Measurement'
                s="Fact Table:"+tableName+"\n"
                f.write(s)
            for cell in sheet.getRow(0):
                headerValue = cell.toString()
                value = ''
                try:
                    value = self.getCellValue(sheet, rowNum, cell.getColumnIndex())
                    if value == 'Y' or value == 'y':
                        value = 1
                    
                    if headerValue == 'FOLLOWJOHN':
                        value = int(float(value))
                        
                    if headerValue == 'Count Table': # removing leading and trailing whitespace from cell value
                        if ',' in value:
                            relCount = value.split(',')
                            relCount = [rel.strip() for rel in relCount]
                            value = ",".join(relCount)
                            
                    self.xlsxdict['Tables'][tableName][self.FactTableDict[headerValue]] = self.encodeValue(value)
                except:
                    if value != '':
                        if 'Parser' not in self.xlsxdict['Tables'][tableName]:
                            self.xlsxdict['Tables'][tableName]['Parser'] = odict()
                        if headerValue not in self.xlsxdict['Tables'][tableName]['Parser']:
                            self.xlsxdict['Tables'][tableName]['Parser'][headerValue] = odict()
                        if 'DATATAGS' not in self.xlsxdict['Tables'][tableName]['Parser'][headerValue]:
                            self.xlsxdict['Tables'][tableName]['Parser'][headerValue]['DATATAGS'] = odict()
                        self.xlsxdict['Tables'][tableName]['Parser'][headerValue]['DATATAGS'] = value
                        s=headerValue+":"+value+"\n"
                        f.write(s)
                    elif headerValue not in l and tableName!='':
                    	s=headerValue+":\n"
                    	f.write(s)
        # Fact Table Keys
        logger.info('Fact Tables Keys')
        sheet = workbook.getSheet('Keys')
        for rowNum in xrange(1, sheet.getLastRowNum() + 1):
            KeyName = sheet.getRow(rowNum).getCell(1).toString().strip()
            if KeyName.strip() != '':
                tableName = sheet.getRow(rowNum).getCell(0).toString().strip()
                if 'measurementKey' not in self.xlsxdict['Tables'][tableName]:
                    self.xlsxdict['Tables'][tableName]['measurementKey'] = odict()
                self.xlsxdict['Tables'][tableName]['measurementKey'][KeyName] = odict()
                tempDict = self.parseFDRows(self.FTKeysDict, sheet, self.xlsxdict['Tables'][tableName]['measurementKey'], KeyName, False, rowNum)
                self.xlsxdict['Tables'][tableName]['measurementKey'] = tempDict
                    
                if self.xlsxdict['Tables'][tableName]['JOINABLE'] == KeyName:
                    self.xlsxdict['Tables'][tableName]['measurementKey'][KeyName]['JOINABLE'] = '1'
                
        # Fact table Counters
        logger.info('Fact Tables Counters')
        sheet = workbook.getSheet('Counters')
        for rowNum in xrange(1, sheet.getLastRowNum()+1):
            CounterName = self.getCellValue(sheet, rowNum, 1)
            if CounterName != '':
                tableName = sheet.getRow(rowNum).getCell(0).toString().strip()
                if 'measurementCounter' not in self.xlsxdict['Tables'][tableName]:
                    self.xlsxdict['Tables'][tableName]['measurementCounter'] = odict()
                self.xlsxdict['Tables'][tableName]['measurementCounter'][CounterName] = odict()
                tempDict = self.parseFDRows(self.FTCountersDict, sheet, self.xlsxdict['Tables'][tableName]['measurementCounter'], CounterName, False, rowNum)
                self.xlsxdict['Tables'][tableName]['measurementCounter'] = tempDict

        # Vectors
        logger.info('Vectors')
        sheet = workbook.getSheet('Vectors')
        for rowNum in xrange(1, sheet.getLastRowNum() + 1):   
            index = self.getCellValue(sheet, rowNum, 3)
            if index != '':
                quantity = sheet.getRow(rowNum).getCell(6).toString().strip()
                vendRel = sheet.getRow(rowNum).getCell(2).toString().strip()
                CounterName = sheet.getRow(rowNum).getCell(1).toString().strip()
                tableName = sheet.getRow(rowNum).getCell(0).toString().strip()
                if 'Vectors' not in self.xlsxdict['Tables'][tableName]['measurementCounter'][CounterName]:
                    self.xlsxdict['Tables'][tableName]['measurementCounter'][CounterName]['Vectors'] = odict()
                
                if 'QUANTITY' not in self.xlsxdict['Tables'][tableName]['measurementCounter'][CounterName]['Vectors']:
                    self.xlsxdict['Tables'][tableName]['measurementCounter'][CounterName]['Vectors']['QUANTITY'] = odict()
                
                if quantity not in self.xlsxdict['Tables'][tableName]['measurementCounter'][CounterName]['Vectors']['QUANTITY']:
                    self.xlsxdict['Tables'][tableName]['measurementCounter'][CounterName]['Vectors']['QUANTITY'][quantity] = odict()
                
                if vendRel not in self.xlsxdict['Tables'][tableName]['measurementCounter'][CounterName]['Vectors']['QUANTITY'][quantity]:
                    self.xlsxdict['Tables'][tableName]['measurementCounter'][CounterName]['Vectors']['QUANTITY'][quantity][vendRel] = odict()
                    
                self.xlsxdict['Tables'][tableName]['measurementCounter'][CounterName]['Vectors']['QUANTITY'][quantity][vendRel][index] = odict()    
                tempDict = self.parseFDRows(self.VectorsDict, sheet, self.xlsxdict['Tables'][tableName]['measurementCounter'][CounterName]['Vectors']['QUANTITY'][quantity][vendRel], index, False, rowNum)
                self.xlsxdict['Tables'][tableName]['measurementCounter'][CounterName]['Vectors']['QUANTITY'][quantity][vendRel] = tempDict
        
        # Topology Table
        logger.info('Topology Table')
        sheet = workbook.getSheet('Topology Tables')
        sheet.getRow(0).removeCell(sheet.getRow(0).getCell(0))
        for rowNum in xrange(1, sheet.getLastRowNum() + 1):  
            tableName = sheet.getRow(rowNum).getCell(0).toString()
            if tableName != '':
                self.xlsxdict['Tables'][tableName] = odict()
                self.xlsxdict['Tables'][tableName]['TABLETYPE'] = 'Reference'
            for cell in sheet.getRow(0):
                headerValue = sheet.getRow(0).getCell(cell.getColumnIndex()).toString()
                value = ''
                try:
                    value = sheet.getRow(rowNum).getCell(cell.getColumnIndex()).toString()
                    if self.TopTableDict[headerValue] == 'UPDATE_POLICY':
                        value = str(self.updatePolicylist.index(value))
                    self.xlsxdict['Tables'][tableName][self.TopTableDict[headerValue]] = value
                except:
                    if value != '':
                        if 'Parser' not in self.xlsxdict['Tables'][tableName]:
                            self.xlsxdict['Tables'][tableName]['Parser'] = odict()
                        if headerValue not in self.xlsxdict['Tables'][tableName]['Parser']:
                            self.xlsxdict['Tables'][tableName]['Parser'][headerValue] = odict()
                        if 'DATATAGS' not in self.xlsxdict['Tables'][tableName]['Parser'][headerValue]:
                            self.xlsxdict['Tables'][tableName]['Parser'][headerValue]['DATATAGS'] = odict()
                        self.xlsxdict['Tables'][tableName]['Parser'][headerValue]['DATATAGS'] = value
                    
        # Topology Keys
        logger.info('Topology Keys')
        sheet = workbook.getSheet('Topology Keys')
        for rowNum in xrange(1, sheet.getLastRowNum() + 1): 
            KeyName = sheet.getRow(rowNum).getCell(1).toString()      
            tableName = sheet.getRow(rowNum).getCell(0).toString()
            if 'referenceKey' not in self.xlsxdict['Tables'][tableName]:
                self.xlsxdict['Tables'][tableName]['referenceKey'] = odict()
            self.xlsxdict['Tables'][tableName]['referenceKey'][KeyName] = odict()            
            tempDict = self.parseFDRows(self.TopKeysDict, sheet, self.xlsxdict['Tables'][tableName]['referenceKey'], KeyName, False, rowNum)
            self.xlsxdict['Tables'][tableName]['referenceKey'] = tempDict   
                    
        # Transformations
        logger.info('Transformations')
        sheet = workbook.getSheet('Transformations')
        for rowNum in xrange(1, sheet.getLastRowNum()+1): 
            parserName = sheet.getRow(rowNum).getCell(0).toString()
            if parserName != '':
                tableName = sheet.getRow(rowNum).getCell(1).toString()
                if 'Parser' not in self.xlsxdict['Tables'][tableName]:
                    self.xlsxdict['Tables'][tableName]['Parser'] = odict()
                if parserName not in self.xlsxdict['Tables'][tableName]['Parser']:
                    self.xlsxdict['Tables'][tableName]['Parser'][parserName] = odict()
                if rowNum not in self.xlsxdict['Tables'][tableName]['Parser'][parserName]:
                    self.xlsxdict['Tables'][tableName]['Parser'][parserName][rowNum - 1] = odict()
                for FDColumn, Parameter in self.TransDict.iteritems():
                    cellNum = self.findValue(sheet, FDColumn).getColumnIndex()
                    value = self.getCellValue(sheet, rowNum, cellNum)
                    self.xlsxdict['Tables'][tableName]['Parser'][parserName][rowNum - 1][Parameter] = self.encodeValue(value)
                    
        # DataFormat
        logger.info('DataFormat')
        sheet = workbook.getSheet('Data Format')
        attrList = ['measurementCounter', 'measurementKey' , 'referenceKey']
        for cell in sheet.getRow(0):
            parserName = cell.toString()
            cellNum = cell.getColumnIndex()
            if parserName != 'Table Name' and  parserName != 'Counter/key Name':
                for rowNum in xrange(1, sheet.getLastRowNum() + 1): 
                    format = self.getCellValue(sheet, rowNum, cellNum)
                    tableName = self.getCellValue(sheet, rowNum, 0).strip()
                    attrName = self.getCellValue(sheet, rowNum, 1).strip()
                    if tableName != '' and attrName != '':
                        if 'Parser' not in self.xlsxdict['Tables'][tableName]:
                            self.xlsxdict['Tables'][tableName]['Parser'] = odict()
                            
                        if parserName not in self.xlsxdict['Tables'][tableName]['Parser']:
                            self.xlsxdict['Tables'][tableName]['Parser'][parserName] = odict()
                            
                        if 'ATTRTAGS' not in self.xlsxdict['Tables'][tableName]['Parser'][parserName]:
                            self.xlsxdict['Tables'][tableName]['Parser'][parserName]['ATTRTAGS'] = odict()
                            
                        self.xlsxdict['Tables'][tableName]['Parser'][parserName]['ATTRTAGS'][str(attrName)] = self.encodeValue(format)
                        for attrtype in attrList:
                            if attrtype in self.xlsxdict['Tables'][tableName]:
                                if attrName in self.xlsxdict['Tables'][tableName][attrtype]:
                                    self.xlsxdict['Tables'][tableName][attrtype][attrName]['DATAID'] = self.encodeValue(format)

        # BH
        logger.info('BH')
        sheet = workbook.getSheet('BH')
        self.xlsxdict['BHOBJECT'] = odict()
        for rowNum in xrange(1, sheet.getLastRowNum() +1):
            if sheet.getRow(rowNum) != None:
                PHName = sheet.getRow(rowNum).getCell(1).toString()
                BHName = sheet.getRow(rowNum).getCell(0).toString()
                if BHName != '':
                    if BHName not in self.xlsxdict['BHOBJECT']:
                        self.xlsxdict['BHOBJECT'][BHName] = odict()
                    self.xlsxdict['BHOBJECT'][BHName][PHName] = odict()
                    tempDict = self.parseFDRows(self.BHDict, sheet, self.xlsxdict['BHOBJECT'][BHName], PHName, False, rowNum)
                    self.xlsxdict['BHOBJECT'][BHName] = tempDict
                    
        # BH Rank Keys
        logger.info('BH Rank Keys')
        sheet = workbook.getSheet('BH Rank Keys')
        for rowNum in xrange(1, sheet.getLastRowNum() + 1):
            PHName = sheet.getRow(rowNum).getCell(1).toString()
            BHName = sheet.getRow(rowNum).getCell(0).toString()
            if BHName != '':
                if 'RANKINGKEYS' not in self.xlsxdict['BHOBJECT'][BHName][PHName]:
                    self.xlsxdict['BHOBJECT'][BHName][PHName]['RANKINGKEYS'] = odict()
                if 'TYPENAME' not in self.xlsxdict['BHOBJECT'][BHName][PHName]:
                    self.xlsxdict['BHOBJECT'][BHName][PHName]['TYPENAME'] = []
                    tables = []
                
                try:
                    KeyName = sheet.getRow(rowNum).getCell(2).toString()
                    KeyValue = sheet.getRow(rowNum).getCell(3).toString().strip()
                except:
                    KeyName = ''
                    KeyValue = ''
                
                SourceTable = None
                try:
                    SourceTable = sheet.getRow(rowNum).getCell(4).toString().strip()
                except:
                    pass
                
                # self._getRankKeyValue(SourceTable, KeyName, KeyValue)
                self.xlsxdict['BHOBJECT'][BHName][PHName]['RANKINGKEYS'][KeyName] = KeyValue
                if SourceTable != None and SourceTable != '':
                    tables = self.xlsxdict['BHOBJECT'][BHName][PHName]['TYPENAME']
                    if ',' in SourceTable:
                        for table in SourceTable.split(','):
                            if table not in tables:
                                tables.append(table)
                    else:
                        if SourceTable not in tables:
                            tables.append(SourceTable)
        
                    self.xlsxdict['BHOBJECT'][BHName][PHName]['TYPENAME'] = tables   
                    
        # External Statments
        logger.info('External Statements')
        EStxtFileName = path.splitext(filename)[0] + ".txt"
        ESCollection = Utils.loadEStxtFile(EStxtFileName)

        sheet = workbook.getSheet('External Statement')
        self.xlsxdict['ExternalStatements'] = odict()   
        for rowNum in xrange(1, sheet.getLastRowNum() + 1):
            if sheet.getRow(rowNum).getCell(0) != None:
                ESName = sheet.getRow(rowNum).getCell(0).toString()
                if ESName != '':
                    self.xlsxdict['ExternalStatements'][ESName] = odict()
                    self.xlsxdict['ExternalStatements'][ESName]['EXECUTIONORDER'] = str(rowNum)
                for FDColumn, Parameter in self.ESDict.iteritems():
                    cellNum = self.findValue(sheet, FDColumn).getColumnIndex()
                    try:
                        value = sheet.getRow(rowNum).getCell(cellNum).toString()
                    except:
                        value = ''
                    
                    if Parameter == 'STATEMENT':
                        if value in EStxtFileName:
                            if ESCollection != None:
                                value = ESCollection[ESName]
                            else:
                                raise Exception(filename + " not found")
                        
                    self.xlsxdict['ExternalStatements'][ESName][Parameter] = self.encodeValue(value)
        
        UniName = '' 
        # Universe Extensions
        logger.info('Universe Extensions')
        sheet = workbook.getSheet('Universe Extension')
        self.xlsxdict['Universe'] = odict()
        for rowNum in xrange(1, sheet.getLastRowNum() + 1):
            UniExtName = sheet.getRow(rowNum).getCell(1).toString()
            if UniExtName != '':
                UniName = sheet.getRow(rowNum).getCell(0).toString()
                if UniName not in self.xlsxdict['Universe']:
                    self.xlsxdict['Universe'][UniName] = odict()
                    self.xlsxdict['Universe'][UniName]['Extensions'] = odict()
                        
                if UniExtName != '' and UniExtName.upper() != 'ALL':  
                    self.xlsxdict['Universe'][UniName]['Extensions'][UniExtName] = odict()
                    tempDict = self.parseFDRows(self.UniExtDict, sheet, self.xlsxdict['Universe'][UniName]['Extensions'], UniExtName, True, rowNum)
                    self.xlsxdict['Universe'][UniName]['Extensions'] = tempDict
                                
        if UniName != None and UniName != '':
            
            logger.info('Universe Tables')
            # Universe Tables
            sheet = workbook.getSheet('Universe Topology Tables')
            self.xlsxdict['Universe'][UniName]['Tables'] = odict()
            for rowNum in xrange(1, sheet.getLastRowNum() + 1):
                tableName = sheet.getRow(rowNum).getCell(0).toString()
                if tableName != '':
                    self.xlsxdict['Universe'][UniName]['Tables'][tableName] = odict()
                tempDict = self.parseFDRows(self.UniTableDict, sheet, self.xlsxdict['Universe'][UniName]['Tables'], tableName, True, rowNum)
                self.xlsxdict['Universe'][UniName]['Tables'] = tempDict
            
            logger.info('Universe Class')        
            # Universe Class
            sheet = workbook.getSheet('Universe Class')
            self.xlsxdict['Universe'][UniName]['Class'] = odict()
            for rowNum in xrange(1, sheet.getLastRowNum() + 1):
                ClassName = self.getCellValue(sheet, rowNum, 0)
                if ClassName != '':
                    self.xlsxdict['Universe'][UniName]['Class'][ClassName] = odict()
                tempDict = self.parseFDRows(self.UniClassDict, sheet, self.xlsxdict['Universe'][UniName]['Class'], ClassName, True, rowNum)
                self.xlsxdict['Universe'][UniName]['Class'] = tempDict
            
            logger.info('Universe Objects')    
            # Universe Objects
            sheet = workbook.getSheet('Universe Topology Objects')
            self.xlsxdict['Universe'][UniName]['Object'] = odict()
            for rowNum in xrange(1, sheet.getLastRowNum() + 1):
                ObjName = self.getCellValue(sheet, rowNum, 1)
                className = self.getCellValue(sheet, rowNum, 0)
                if className not in self.xlsxdict['Universe'][UniName]['Object']:
                    self.xlsxdict['Universe'][UniName]['Object'][className] = odict()
                if ObjName != '':
                    self.xlsxdict['Universe'][UniName]['Object'][className][ObjName] = odict()
                tempDict = self.parseFDRows(self.UniObjDict, sheet, self.xlsxdict['Universe'][UniName]['Object'][className], ObjName, True, rowNum)
                self.xlsxdict['Universe'][UniName]['Object'][className] = tempDict
            
            logger.info('Universe Conditions')          
            # Universe Conditions
            sheet = workbook.getSheet('Universe Conditions')
            self.xlsxdict['Universe'][UniName]['Conditions'] = odict()
            for rowNum in xrange(1, sheet.getLastRowNum() + 1):
                ConName = self.getCellValue(sheet, rowNum, 1)
                className = self.getCellValue(sheet, rowNum, 0)
                if className not in self.xlsxdict['Universe'][UniName]['Conditions']:
                    self.xlsxdict['Universe'][UniName]['Conditions'][className] = odict()
                if ConName != '':
                    self.xlsxdict['Universe'][UniName]['Conditions'][className][ConName] = odict()
                
                tempDict = self.parseFDRows(self.UniConDict, sheet, self.xlsxdict['Universe'][UniName]['Conditions'][className], ConName, True, rowNum)
                self.xlsxdict['Universe'][UniName]['Conditions'][className] = tempDict
            
            logger.info('Universe Joins')        
            # Universe Joins
            sheet = workbook.getSheet('Universe Joins')
            self.xlsxdict['Universe'][UniName]['Joins'] = odict()
            for rowNum in xrange(1, sheet.getLastRowNum() + 1):
                join = sheet.getRow(rowNum).getCell(0).toString()
                if join != None and join.strip() != '':
                    self.xlsxdict['Universe'][UniName]['Joins'][rowNum] = odict()
                    for FDColumn, Parameter in self.UniJoinsDict.iteritems():
                        cellNum = self.findValue(sheet, FDColumn).getColumnIndex()
                        try:
                            value = sheet.getRow(rowNum).getCell(cellNum).toString()
                        except:
                            value = ''
                        self.xlsxdict['Universe'][UniName]['Joins'][rowNum][Parameter] = self.encodeValue(value)
        
        return self.xlsxdict
        
    def findValue(self, sheet, value):
        for row in sheet:
            for cell in row:
                if cell.toString() == value:
                    return cell
    
    def getCellValue(self, sheet, rowNum, cellNum):
        CellValue = ''
        try:
            CellValue = sheet.getRow(rowNum).getCell(cellNum).toString()
        except:
            pass
        
        return CellValue
      
    def parseFDRows(self, mappingDict, FDsheet, destinationDict, KeyName, getOrderNo, rowNumber):
        if KeyName != '':
            if getOrderNo:
                destinationDict[KeyName]['ORDERNRO'] = str(rowNumber)
                
            for FDColumn, Parameter in mappingDict.iteritems(): 
                value = ''
                
                cellNum = self.findValue(FDsheet, FDColumn).getColumnIndex()
                try:
                    value = FDsheet.getRow(rowNumber).getCell(cellNum).toString()
                except:
                    pass

                if value == 'Y' or value == 'y':
                    value = 1
                if Parameter == 'DATATYPE':
                    datatype, datasize, datascale = self.parseDataType(value)
                    value = datatype
                    destinationDict[KeyName]['DATASIZE'] = datasize
                    destinationDict[KeyName]['DATASCALE'] = datascale
                if Parameter != 'DESCRIPTION':
                    value = Utils.strFloatToInt(str(value).strip())
                destinationDict[KeyName][Parameter] = self.encodeValue(value)
                    
        return destinationDict
    
    def encodeValue(self, value):
        try:
            value = str(value).strip()
        except:
            value = value.encode('ascii', 'ignore')
        return value
    
    def _getRankKeyValue(self, SourceTable, KeyName, KeyValue):
        Value = KeyName
        Table = SourceTable
        
        if KeyValue != None and KeyValue.strip() != '':
            Value = KeyValue
            
        if SourceTable != None:
            if ',' in SourceTable:
                Table = SourceTable.split(',')[0]
                return Table + '.' + Value
        
        return Value
            
    def parseDataType(self, datatype):
        #datatype(datasize,datascale)
        #datatype(datascale)
        #datatype
            
        datasize = '0'
        datascale = '0'
            
        if '(' in datatype:
            parts = datatype.split('(')
            datatype = parts[0]
            if ',' in parts[1]:
                datasize = parts[1].split(',')[0]
                datascale = parts[1].split(',')[1].replace(')','')
            else:
                datasize = parts[1].replace(')','')
            
        return datatype, datasize, datascale
    
    def createXlsDoc(self, workbook, outputOption):
        if outputOption == 'TP':
            #CoverSheet
            spreadsheet = workbook.createSheet("Coversheet")
            row = spreadsheet.createRow(0)
            row.createCell(0).setCellValue("set cell type string")
            
            self.VersioningDict
            
    
    def returnXlsDict(self):
        return self.xlsxdict
    
        