'''
Created on Oct 20, 2016

@author: ebrifol
'''

import Utils
from ODict import odict
import traceback
import sys
from copy import deepcopy
from java.io import File, FileOutputStream
from org.apache.poi.hssf.util import HSSFColor
from org.apache.poi.ss.util import CellRangeAddress
from org.apache.poi.xssf.usermodel import XSSFWorkbook
from java.io import File
import os

class XlsxFile(object):
    
    Outputfilepath = ""
    
    VersioningList = ['TECHPACK_NAME', 'DESCRIPTION', 'TECHPACK_VERSION', 'PRODUCT_NUMBER', 'LICENSENAME', 'TECHPACK_TYPE',
                      'VENDORRELEASE', 'BUILD_NUMBER', 'Dependency', 'Interfaces', 'ManModsFile', 'UNIVERSE_DELIVERED', 'SUPPORTED_NODE_TYPES']
    InterfaceList = ['NAME', 'RSTATE', 'INTERFACETYPE', 'DESCRIPTION','INTFTECHPACKS', 'DEPENDENCIES', 'DATAFORMATTYPE', 'ELEMTYPE']
    FactTableList = ['NAME', 'DESCRIPTION', 'CLASSIFICATION', 'SIZING', 'TOTALAGG', 'OBJECTBH', 'ELEMENTBHSUPPORT', 
                    'RANKINGTABLE', 'DELTACALCSUPPORT', 'VECTORSUPPORT', 'PLAINTABLE', 'UNIVERSEEXTENSION', 'JOINABLE', 'FOLLOWJOHN']
    FTKeysList = ['TABLENAME', 'NAME', 'DESCRIPTION', 'DATATYPE', 'UNIQUEKEY', 'NULLABLE', 'INDEXES', 'UNIVOBJECT',
                  'ISELEMENT', 'INCLUDESQL']
    FTCountersList = ['TABLENAME', 'NAME', 'DESCRIPTION', 'DATATYPE', 'TIMEAGGREGATION','GROUPAGGREGATION', 'UNIVOBJECT', 'UNIVCLASS',
                  'COUNTERTYPE', 'INCLUDESQL', 'FOLLOWJOHN']
    VectorsList = ['TABLENAME', 'NAME', 'VENDORRELEASE', 'VINDEX', 'VFROM', 'VTO', 'MEASURE', 'QUANTITY']
    DataFormatList = ['TABLENAME', 'ATTRIBUTENAME']
    TopTableList = ['NAME', 'DESCRIPTION', 'UPDATE_POLICY']
    TopKeysList = ['TABLENAME', 'NAME', 'DESCRIPTION', 'DATATYPE', 'UNIQUEKEY', 'NULLABLE', 'UNIVERSECLASS', 'UNIVERSEOBJECT',
                   'UNIVERSECONDITION', 'INCLUDESQL', 'INCLUDEUPD']
    TransList = ['PARSERNAME','TABLENAME', 'TYPE', 'SOURCE', 'TARGET', 'CONFIG']
    BHList = ['BHNAME', 'PHNAME', 'DESCRIPTION', 'WHERECLAUSE', 'BHCRITERIA', 'AGGREGATIONTYPE', 'LOOKBACK', 'P_THRESHOLD', 'N_THRESHOLD', 'MAPPEDTABLES']
    BHRKList = ['BHNAME', 'PHNAME', 'KEYNAME', 'KEYVALUE', 'SOURCETABLENAME']
    ESList = ['NAME', 'DBCONNECTION', 'STATEMENT']

    UniExtList = ['UNVNAME', 'UNVEXTENSION', 'UNVEXTENSIONNAME']
    UniTableList = ['TABLENAME', 'OWNER', 'ALIAS', 'UNIVERSEEXTENSION']
    UniClassList = ['NAME', 'DESCRIPTION', 'PARENT', 'UNIVERSEEXTENSION']
    UniObjList = ['CLASSNAME', 'NAME', 'DESCRIPTION', 'OBJECTTYPE', 'QUALIFICATION', 'AGGREGATION', 'OBJSELECT', 'OBJWHERE', 'PROMPTHIERARCHY', 'UNIVERSEEXTENSION']
    UniConList = ['CLASSNAME', 'NAME', 'DESCRIPTION', 'CONDWHERE', 'AUTOGENERATE', 'CONDOBJCLASS', 'CONDOBJECT', 'PROMPTTEXT', 'MULTISELECTION', 
                  'FREETEXT', 'UNIVERSEEXTENSION']
    UniJoinsList = ['SOURCETABLE', 'SOURCELEVEL', 'SOURCECOLUMN', 'TARGETTABLE', 'TARGETLEVEL', 'TARGETCOLUMN', 'CARDINALITY', 'CONTEXT', 
                    'EXCLUDEDCONTEXTS', 'UNIVERSEEXTENSION']
    
    updatePolicylist = ["Static", "Predefined", "Dynamic", "Timed Dynamic", "History Dynamic" ]
    
    
    def parseXlsDoc(self, loadOption, filename, logger):
        workbook = XSSFWorkbook(File(filename))
        xlsxdict = odict()
        
        if loadOption == 'INTF':
            try:
                logger.info('Interface')
                sheet = workbook.getSheet('Interface')
                xlsxdict['intfConfig'] = odict()
                for rowNum in xrange(0, sheet.getLastRowNum() + 1):
                    key = self._getCellValue(sheet, rowNum, 0)
                    value = self._getCellValue(sheet, rowNum, 1)
    
                    if key in self.InterfaceList:
                        xlsxdict[key] = value
                    else:
                        if value != '' and value != None:
                            xlsxdict['intfConfig'][key] = value
            except:
                logger.error('Unable to parse the Interface')
                traceback.print_exc(file=sys.stdout)
                return None
            
        elif loadOption == 'TP':
            try:
                logger.info('Coversheet')
                sheet = workbook.getSheet('Coversheet')
                xlsxdict['Versioning'] = odict()
                for rowNum in xrange(0, sheet.getLastRowNum() + 1):
                    key = self._getCellValue(sheet, rowNum, 0)
                    value = self._getCellValue(sheet, rowNum, 1)
                    if key in self.VersioningList:
                        xlsxdict['Versioning'][key] = value
            except:
                logger.error('Unable to parse the Coversheet')
                traceback.print_exc(file=sys.stdout)
                return None
            
            try:
                logger.info('Fact Tables')
                sheet = workbook.getSheet('Fact Tables')
                if 'Tables' not in xlsxdict:
                    xlsxdict['Tables'] = odict()
                for rowNum in xrange(1, sheet.getLastRowNum() + 1): #For each row on the sheet where each row is a table
                    tableName = self._getCellValue(sheet, rowNum, 0)
                    if tableName != '':
                        xlsxdict['Tables'][tableName] = odict()
                        xlsxdict['Tables'][tableName]['TABLETYPE'] = 'Measurement'
                        xlsxdict['Tables'][tableName]['Parsers'] = odict()
                        for cell in sheet.getRow(0):            # For each cell on the row where each cell is a property of the table
                            value = self._getCellValue(sheet, rowNum, cell.getColumnIndex())
                            key = self._getCellValue(sheet, 0, cell.getColumnIndex())
                            
                            if key in self.FactTableList:   #If the key is not in the list above then it is a parser name
                                if value != None and value.upper() == 'Y':
                                    value = '1'
                                xlsxdict['Tables'][tableName][key] = value
                            else:
                                if value != None:
                                    xlsxdict['Tables'][tableName]['Parsers'][key] = value       
            except:
                logger.error('Unable to parse the Fact Tables')
                traceback.print_exc(file=sys.stdout)
                return None
                        
            try:
                logger.info('Keys')
                sheet = workbook.getSheet('Keys')
                if 'Attributes' not in xlsxdict:
                    xlsxdict['Attributes'] = odict()
                for rowNum in xrange(1, sheet.getLastRowNum() + 1): #For each row on the sheet where each row is a table
                    tableName = self._getCellValue(sheet, rowNum, 0)
                    keyName = self._getCellValue(sheet, rowNum, 1)
                    if tableName != '' and keyName != '':
                        if tableName not in  xlsxdict['Attributes']:
                            xlsxdict['Attributes'][tableName] = odict()
                        xlsxdict['Attributes'][tableName][keyName] = odict()
                        xlsxdict['Attributes'][tableName][keyName]['TYPE'] = 'measurementKey'
                        for cell in sheet.getRow(0):            # For each cell on the row where each cell is a property of the table
                            value = self._getCellValue(sheet, rowNum, cell.getColumnIndex())
                            key = self._getCellValue(sheet, 0, cell.getColumnIndex())
                            
                            if key in self.FTKeysList:   #If the key is not in the list above then it is a parser name
                                if value.upper() == 'Y':
                                    value = '1'
                                if key == 'DATATYPE':
                                    datatype, datasize, datascale = self.parseDataType(value)
                                    value = datatype
                                    xlsxdict['Attributes'][tableName][keyName]['DATASIZE'] = datasize
                                    xlsxdict['Attributes'][tableName][keyName]['DATASCALE'] = datascale
                                    xlsxdict['Attributes'][tableName][keyName]['DATATYPE'] = datatype
                                else:
                                    xlsxdict['Attributes'][tableName][keyName][key] = value
                        
                        if xlsxdict['Tables'][tableName]['JOINABLE'] == keyName:
                            xlsxdict['Attributes'][tableName][keyName]['JOINABLE'] = '1'
            except:
                logger.error('Unable to parse the Keys')
                traceback.print_exc(file=sys.stdout)
                return None
            
            try:
                logger.info('Counters')
                sheet = workbook.getSheet('Counters')
                if 'Attributes' not in xlsxdict:
                    xlsxdict['Attributes'] = odict()
                for rowNum in xrange(1, sheet.getLastRowNum() + 1): #For each row on the sheet where each row is a table
                    tableName = self._getCellValue(sheet, rowNum, 0)
                    counterName = self._getCellValue(sheet, rowNum, 1)
                    if tableName != '' and counterName != '':
                        if tableName not in  xlsxdict['Attributes']:
                            xlsxdict['Attributes'][tableName] = odict()
                        xlsxdict['Attributes'][tableName][counterName] = odict()
                        xlsxdict['Attributes'][tableName][counterName]['TYPE'] = 'measurementCounter'
                        for cell in sheet.getRow(0):            # For each cell on the row where each cell is a property of the table
                            value = self._getCellValue(sheet, rowNum, cell.getColumnIndex())
                            key = self._getCellValue(sheet, 0, cell.getColumnIndex())
                            
                            if key in self.FTCountersList:   #If the key is not in the list above then it is a parser name
                                if value.upper() == 'Y':
                                    value = '1'
                                if key == 'DATATYPE':
                                    datatype, datasize, datascale = self.parseDataType(value)
                                    value = datatype
                                    xlsxdict['Attributes'][tableName][counterName]['DATASIZE'] = datasize
                                    xlsxdict['Attributes'][tableName][counterName]['DATASCALE'] = datascale
                                    xlsxdict['Attributes'][tableName][counterName]['DATATYPE'] = datatype
                                else:
                                    xlsxdict['Attributes'][tableName][counterName][key] = value
            except:
                logger.error('Unable to parse the Counters')
                traceback.print_exc(file=sys.stdout)
                return None
            
            try:
                logger.info('Vectors')
                sheet = workbook.getSheet('Vectors')
                xlsxdict['Vectors'] = odict()
                for rowNum in xrange(1, sheet.getLastRowNum() + 1): #For each row on the sheet where each row is a table
                    tableName = self._getCellValue(sheet, rowNum, 0)
                    counterName = self._getCellValue(sheet, rowNum, 1)
                    vendRel = self._getCellValue(sheet, rowNum, 2)
                    index = self._getCellValue(sheet, rowNum, 3)
                    quantity = self._getCellValue(sheet, rowNum, 7)
                    if tableName != '' and counterName != '' and vendRel != '':
                        if tableName not in xlsxdict['Vectors']:
                            xlsxdict['Vectors'][tableName] = odict()
                        if counterName not in  xlsxdict['Vectors'][tableName]:
                            xlsxdict['Vectors'][tableName][counterName] = odict()
                        if quantity not in xlsxdict['Vectors'][tableName][counterName]:
                            xlsxdict['Vectors'][tableName][counterName][quantity] = odict()
                        if vendRel not in xlsxdict['Vectors'][tableName][counterName][quantity]:
                            xlsxdict['Vectors'][tableName][counterName][quantity][vendRel] = odict()
                            
                        xlsxdict['Vectors'][tableName][counterName][quantity][vendRel][index] = odict()   
                            
                        for cell in sheet.getRow(0):            # For each cell on the row where each cell is a property of the table
                            value = self._getCellValue(sheet, rowNum, cell.getColumnIndex())
                            key = self._getCellValue(sheet, 0, cell.getColumnIndex())
                            
                            if key in self.VectorsList:   #If the key is not in the list above then it is a parser name
                                if value.upper() == 'Y':
                                    value = '1'
                                xlsxdict['Vectors'][tableName][counterName][quantity][vendRel][index][key] = value
            except:
                logger.error('Unable to parse the Vectors')
                traceback.print_exc(file=sys.stdout)
                return None
            
            try:
                logger.info('Top Tables')
                sheet = workbook.getSheet('Top Tables')
                if 'Tables' not in xlsxdict:
                    xlsxdict['Tables'] = odict()
                for rowNum in xrange(1, sheet.getLastRowNum() + 1): #For each row on the sheet where each row is a table
                    tableName = self._getCellValue(sheet, rowNum, 0)
                    if tableName != '':
                        xlsxdict['Tables'][tableName] = odict()
                        xlsxdict['Tables'][tableName]['TABLETYPE'] = 'Reference'
                        xlsxdict['Tables'][tableName]['Parsers'] = odict()
                        for cell in sheet.getRow(0):            # For each cell on the row where each cell is a property of the table
                            value = self._getCellValue(sheet, rowNum, cell.getColumnIndex())
                            key = self._getCellValue(sheet, 0, cell.getColumnIndex())
                            
                            if key in self.TopTableList:   #If the key is not in the list above then it is a parser name
                                if key == 'UPDATE_POLICY':
                                    value = str(self.updatePolicylist.index(value))
                                xlsxdict['Tables'][tableName][key] = value
                            else:
                                if value != None:
                                    xlsxdict['Tables'][tableName]['Parsers'][key] = value       
            except:
                logger.error('Unable to parse the Top Tables')
                traceback.print_exc(file=sys.stdout)
                return None
            
            try:
                logger.info('Top Keys')
                sheet = workbook.getSheet('Top Keys')
                if 'Attributes' not in xlsxdict:
                    xlsxdict['Attributes'] = odict()
                for rowNum in xrange(1, sheet.getLastRowNum() + 1): #For each row on the sheet where each row is a table
                    tableName = self._getCellValue(sheet, rowNum, 0)
                    Keyname = self._getCellValue(sheet, rowNum, 1)
                    if tableName != '' and Keyname != '':
                        if tableName not in  xlsxdict['Attributes']:
                            xlsxdict['Attributes'][tableName] = odict()
                        xlsxdict['Attributes'][tableName][Keyname] = odict()
                        xlsxdict['Attributes'][tableName][Keyname]['TYPE'] = 'referenceKey'
                        for cell in sheet.getRow(0):            # For each cell on the row where each cell is a property of the table
                            value = self._getCellValue(sheet, rowNum, cell.getColumnIndex())
                            key = self._getCellValue(sheet, 0, cell.getColumnIndex())
                            
                            if key in self.TopKeysList:   #If the key is not in the list above then it is a parser name
                                if value.upper() == 'Y':
                                    value = '1'
                                if key == 'DATATYPE':
                                    datatype, datasize, datascale = self.parseDataType(value)
                                    value = datatype
                                    xlsxdict['Attributes'][tableName][Keyname]['DATASIZE'] = datasize
                                    xlsxdict['Attributes'][tableName][Keyname]['DATASCALE'] = datascale
                                    xlsxdict['Attributes'][tableName][Keyname]['DATATYPE'] = datatype
                                else:
                                    xlsxdict['Attributes'][tableName][Keyname][key] = value
            except:
                logger.error('Unable to parse the Top Keys')
                traceback.print_exc(file=sys.stdout)
                return None
            
            try:
                logger.info('Transformations')
                sheet = workbook.getSheet('Transformations')
                xlsxdict['Trans'] = odict()
                for rowNum in xrange(1, sheet.getLastRowNum() + 1): #For each row on the sheet where each row is a table
                    tableName = self._getCellValue(sheet, rowNum, 1)
                    parserName = self._getCellValue(sheet, rowNum, 0)
                    if tableName != '' and parserName != '':
                        if tableName not in xlsxdict['Trans']:
                            xlsxdict['Trans'][tableName] = odict()
                        if parserName not in xlsxdict['Trans'][tableName]:
                            xlsxdict['Trans'][tableName][parserName] = odict()
                        
                        xlsxdict['Trans'][tableName][parserName][rowNum-1] = odict()
                        for cell in sheet.getRow(0):            # For each cell on the row where each cell is a property of the table
                            value = self._getCellValue(sheet, rowNum, cell.getColumnIndex())
                            key = self._getCellValue(sheet, 0, cell.getColumnIndex())
                            
                            if key in self.TransList:   #If the key is not in the list above then it is a parser name
                                if value.upper() == 'Y':
                                    value = '1'
                                xlsxdict['Trans'][tableName][parserName][rowNum-1][key] = value
            except:
                logger.error('Unable to parse the Transformations')
                traceback.print_exc(file=sys.stdout)
                return None
            
            try:
                logger.info('Data Format')
                sheet = workbook.getSheet('Data Format')
                xlsxdict['DataFormat'] = odict()
                for rowNum in xrange(1, sheet.getLastRowNum() + 1): #For each row on the sheet where each row is a table
                    tableName = self._getCellValue(sheet, rowNum, 0)
                    attrName = self._getCellValue(sheet, rowNum, 1)
                    if tableName != '' and attrName != '':
                        if tableName not in xlsxdict['DataFormat']:
                            xlsxdict['DataFormat'][tableName] = odict()
                            
                        for cell in sheet.getRow(0):            # For each cell on the row where each cell is a property of the table
                            value = self._getCellValue(sheet, rowNum, cell.getColumnIndex())
                            key = self._getCellValue(sheet, 0, cell.getColumnIndex())
                            
                            if key not in self.DataFormatList:   #If the key is not in the list above then it is a parser name
                                if key not in xlsxdict['DataFormat'][tableName]:
                                    xlsxdict['DataFormat'][tableName][key] = odict()                               
                                xlsxdict['DataFormat'][tableName][key][attrName] = value
                        
                            if attrName in xlsxdict['Attributes'][tableName]:
                                xlsxdict['Attributes'][tableName][attrName]['DATAID'] = value
            except:
                logger.error('Unable to parse the Data Format')
                traceback.print_exc(file=sys.stdout)
                return None
            
            
            try:
                logger.info('BH')
                sheet = workbook.getSheet('BH')
                xlsxdict['BH'] = odict()
                for rowNum in xrange(1, sheet.getLastRowNum() + 1): #For each row on the sheet where each row is a table
                    BHName = self._getCellValue(sheet, rowNum, 0)
                    PHname = self._getCellValue(sheet, rowNum, 1)                    
                    if BHName != '' and PHname != '':
                        if BHName not in xlsxdict['BH']:
                            xlsxdict['BH'][BHName] = odict()
                        if PHname not in xlsxdict['BH'][BHName]:
                            xlsxdict['BH'][BHName][PHname] = odict()
                        
                        for cell in sheet.getRow(0):            # For each cell on the row where each cell is a property of the table
                            value = self._getCellValue(sheet, rowNum, cell.getColumnIndex())
                            key = self._getCellValue(sheet, 0, cell.getColumnIndex())
                            
                            if key in self.BHList:   #If the key is not in the list above then it is a parser name
                                xlsxdict['BH'][BHName][PHname][key] = value
            except:
                logger.error('Unable to parse the BH')
                traceback.print_exc(file=sys.stdout)
                return None
            
            try:
                logger.info('BH Rank Keys')
                sheet = workbook.getSheet('BH Rank Keys')
                xlsxdict['BHRKeys'] = odict()
                for rowNum in xrange(1, sheet.getLastRowNum() + 1): #For each row on the sheet where each row is a table
                    BHName = self._getCellValue(sheet, rowNum, 0)
                    PHname = self._getCellValue(sheet, rowNum, 1)                    
                    if BHName != '' and PHname != '':
                        if BHName not in xlsxdict['BHRKeys']:
                            xlsxdict['BHRKeys'][BHName] = odict()
                        if PHname not in xlsxdict['BHRKeys'][BHName]:
                            xlsxdict['BHRKeys'][BHName][PHname] = odict()
                        if 'Keys' not in xlsxdict['BHRKeys'][BHName][PHname]:
                            xlsxdict['BHRKeys'][BHName][PHname]['Keys'] = odict()
                        if 'TYPENAME' not in xlsxdict['BHRKeys'][BHName][PHname]:
                            xlsxdict['BHRKeys'][BHName][PHname]['TYPENAME'] = []
                        
                        Keyname = self._getCellValue(sheet, rowNum, 2)
                        Keyvalue = self._getCellValue(sheet, rowNum, 3)
                        SourceTable = self._getCellValue(sheet, rowNum, 4)
                        
                        xlsxdict['BHRKeys'][BHName][PHname]['Keys'][Keyname] = Keyvalue
                        if SourceTable != None and SourceTable != '':
                            tables = xlsxdict['BHRKeys'][BHName][PHname]['TYPENAME']
                            SourceTable = SourceTable+','
                            for table in SourceTable.split(','):
                                if table != '':
                                    if table not in tables:
                                        tables.append(table)
            except:
                logger.error('Unable to parse the BH Rank Keys')
                traceback.print_exc(file=sys.stdout)
                return None
            
            try:
                logger.info('External Statements')
                EStxtFileName = filename.replace('.xlsx', '.txt')
                ESCollection = Utils.loadEStxtFile(EStxtFileName)
                
                sheet = workbook.getSheet('External Statements')
                xlsxdict['ES'] = odict()
                for rowNum in xrange(1, sheet.getLastRowNum() + 1): #For each row on the sheet where each row is a table
                    ESName = self._getCellValue(sheet, rowNum, 0)                   
                    if ESName != '':
                        if ESName not in xlsxdict['ES']:
                            xlsxdict['ES'][ESName] = odict()
                            xlsxdict['ES'][ESName]['EXECUTIONORDER'] = str(rowNum)
                        
                        for cell in sheet.getRow(0):            # For each cell on the row where each cell is a property of the table
                            value = self._getCellValue(sheet, rowNum, cell.getColumnIndex())
                            key = self._getCellValue(sheet, 0, cell.getColumnIndex())
                            
                            if key == 'STATEMENT':
                                if value in EStxtFileName:
                                    if ESCollection != None:
                                        value = ESCollection[ESName]
                                    else:
                                        raise Exception(filename + " not found")

                            if key in self.ESList:   #If the key is not in the list above then it is a parser name
                                xlsxdict['ES'][ESName][key] = value
            except:
                logger.error('Unable to parse the External Statements')
                traceback.print_exc(file=sys.stdout)
                return None
            
            try:
                logger.info('Universe')
                sheet = workbook.getSheet('Universe')
                xlsxdict['uni'] = odict()
                for rowNum in xrange(1, sheet.getLastRowNum() + 1): #For each row on the sheet where each row is a table
                    UniName = self._getCellValue(sheet, rowNum, 0)                   
                    if UniName != '':
                        if UniName not in xlsxdict['uni']:
                            xlsxdict['uni'][UniName] = odict()
                            
                        Ext = self._getCellValue(sheet, rowNum, 1)
                        ExtName = self._getCellValue(sheet, rowNum, 2)
                        xlsxdict['uni'][UniName][Ext] = ExtName
            except:
                logger.error('Unable to parse the Universe')
                traceback.print_exc(file=sys.stdout)
                return None
            
            
            try:
                logger.info('Unv Tables')
                sheet = workbook.getSheet('Unv Tables')
                xlsxdict['unvTables'] = odict()
                for rowNum in xrange(1, sheet.getLastRowNum() + 1): #For each row on the sheet where each row is a table
                    TableName = self._getCellValue(sheet, rowNum, 0)
                    ExtName = self._getCellValue(sheet, rowNum, 3)                    
                    if TableName != '' and ExtName != '':
                        if ExtName not in xlsxdict['unvTables']:
                            xlsxdict['unvTables'][ExtName] = odict()
                        if TableName not in xlsxdict['unvTables'][ExtName]:
                            xlsxdict['unvTables'][ExtName][TableName] = odict()
                        
                        for cell in sheet.getRow(0):            # For each cell on the row where each cell is a property of the table
                            value = self._getCellValue(sheet, rowNum, cell.getColumnIndex())
                            key = self._getCellValue(sheet, 0, cell.getColumnIndex())
                            
                            if key in self.UniTableList:   #If the key is not in the list above then it is a parser name
                                xlsxdict['unvTables'][ExtName][TableName][key] = value
            except:
                logger.error('Unable to parse the Unv Tables')
                traceback.print_exc(file=sys.stdout)
                return None
            
            try:
                logger.info('Unv Class')
                sheet = workbook.getSheet('Unv Class')
                xlsxdict['unvClass'] = odict()
                for rowNum in xrange(1, sheet.getLastRowNum() + 1): #For each row on the sheet where each row is a table
                    ClassName = self._getCellValue(sheet, rowNum, 0)
                    ExtName = self._getCellValue(sheet, rowNum, 3)                    
                    if ClassName != '' and ExtName != '':
                        if ExtName not in xlsxdict['unvClass']:
                            xlsxdict['unvClass'][ExtName] = odict()
                        if ClassName not in xlsxdict['unvClass'][ExtName]:
                            xlsxdict['unvClass'][ExtName][ClassName] = odict()
                        
                        for cell in sheet.getRow(0):            # For each cell on the row where each cell is a property of the table
                            value = self._getCellValue(sheet, rowNum, cell.getColumnIndex())
                            key = self._getCellValue(sheet, 0, cell.getColumnIndex())
                            
                            if key in self.UniClassList:   #If the key is not in the list above then it is a parser name
                                xlsxdict['unvClass'][ExtName][ClassName][key] = value
            except:
                logger.error('Unable to parse the Unv Class')
                traceback.print_exc(file=sys.stdout)
                return None
            
            try:
                logger.info('Unv Objects')
                sheet = workbook.getSheet('Unv Objects')
                xlsxdict['unvObjects'] = odict()
                for rowNum in xrange(1, sheet.getLastRowNum() + 1): #For each row on the sheet where each row is a table
                    ClassName = self._getCellValue(sheet, rowNum, 0)
                    ObjName = self._getCellValue(sheet, rowNum, 1)                    
                    if ClassName != '' and ObjName != '':
                        if ClassName not in xlsxdict['unvObjects']:
                            xlsxdict['unvObjects'][ClassName] = odict()
                        if ObjName not in xlsxdict['unvObjects'][ClassName]:
                            xlsxdict['unvObjects'][ClassName][ObjName] = odict()
                        
                        for cell in sheet.getRow(0):            # For each cell on the row where each cell is a property of the table
                            value = self._getCellValue(sheet, rowNum, cell.getColumnIndex())
                            key = self._getCellValue(sheet, 0, cell.getColumnIndex())
                            
                            if key in self.UniObjList:   #If the key is not in the list above then it is a parser name
                                xlsxdict['unvObjects'][ClassName][ObjName][key] = value
            except:
                logger.error('Unable to parse the Unv Objects')
                traceback.print_exc(file=sys.stdout)
                return None
            
            try:
                logger.info('Unv Conditions')
                sheet = workbook.getSheet('Unv Conditions')
                xlsxdict['unvConds'] = odict()
                for rowNum in xrange(1, sheet.getLastRowNum() + 1): #For each row on the sheet where each row is a table
                    ClassName = self._getCellValue(sheet, rowNum, 0)
                    ConName = self._getCellValue(sheet, rowNum, 1)                    
                    if ClassName != '' and ConName != '':
                        if ClassName not in xlsxdict['unvConds']:
                            xlsxdict['unvConds'][ClassName] = odict()
                        if ConName not in xlsxdict['unvConds'][ClassName]:
                            xlsxdict['unvConds'][ClassName][ConName] = odict()
                        
                        for cell in sheet.getRow(0):            # For each cell on the row where each cell is a property of the table
                            value = self._getCellValue(sheet, rowNum, cell.getColumnIndex())
                            key = self._getCellValue(sheet, 0, cell.getColumnIndex())
                            
                            if key in self.UniConList:
                                if value.upper() == 'Y':
                                    value = '1'
                                xlsxdict['unvConds'][ClassName][ConName][key] = value
            except:
                logger.error('Unable to parse the Unv Conditions')
                traceback.print_exc(file=sys.stdout)
                return None
            
            try:
                logger.info('Unv Joins')
                sheet = workbook.getSheet('Unv Joins')
                xlsxdict['unvJoins'] = odict()
                for rowNum in xrange(1, sheet.getLastRowNum() + 1): #For each row on the sheet where each row is a table
                    ExtName = self._getCellValue(sheet, rowNum, 9)                   
                    if ExtName != '':
                        if ExtName not in xlsxdict['unvJoins']:
                            xlsxdict['unvJoins'][ExtName] = odict()
                            
                        xlsxdict['unvJoins'][ExtName][rowNum] = odict()
                        
                        for cell in sheet.getRow(0):            # For each cell on the row where each cell is a property of the table
                            value = self._getCellValue(sheet, rowNum, cell.getColumnIndex())
                            key = self._getCellValue(sheet, 0, cell.getColumnIndex())
                            
                            if key in self.UniJoinsList:   #If the key is not in the list above then it is a parser name
                                xlsxdict['unvJoins'][ExtName][rowNum][key] = value
            except:
                logger.error('Unable to parse the Unv Joins')
                traceback.print_exc(file=sys.stdout)
                return None
            
        return xlsxdict
                    
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
    
    def _getCellValue(self, sheet, rowNum, cellNum):
        CellValue = None
        try:
            CellValue = sheet.getRow(rowNum).getCell(cellNum).toString()
            CellValue = CellValue.encode('ascii', 'ignore')
        except:
            pass
        
        return CellValue
    
    def findValue(self, sheet, value):
        for row in sheet:
            for cell in row:
                if cell.toString() == value:
                    return cell
                
    def findHeaderValue(self, sheet, value):
        column = sheet.getRow(0)
        for cell in column:
            if cell.toString() == value:
                return cell
    
    def writeToWorkbook(self, sheet, rowNumber, cellNumber, value):
        try:
            sheet.getRow(rowNumber).createCell(cellNumber).setCellValue(value)
        except:
            sheet.createRow(rowNumber).createCell(cellNumber).setCellValue(value)
    
    def createXlsDoc(self, workbook, outputOption):
        
        font = workbook.createFont();
        font.setFontHeightInPoints(10);
        font.setFontName("Arial");
        font.setColor(9);
        
        style = workbook.createCellStyle();
        style.setFillForegroundColor(30)
        style.setFillPattern(1)
        style.setFont(font)
        
        if outputOption == 'TP':
            #CoverSheet
            spreadsheet = workbook.createSheet('Coversheet')
            count = 0
            for key in self.VersioningList:
                row = spreadsheet.createRow(count)
                row.setHeightInPoints(30)
                cell = row.createCell(0)
                cell.setCellValue(key)
                cell.setCellStyle(style)
                count = count+1
            
            self.createSheet('Transformations', self.TransList, style, workbook)
            self.createSheet('Fact Tables', self.FactTableList, style, workbook)
            self.createSheet('Keys', self.FTKeysList, style, workbook)
            self.createSheet('Counters', self.FTCountersList, style, workbook)
            self.createSheet('Vectors', self.VectorsList, style, workbook)
            self.createSheet('Top Tables', self.TopTableList, style, workbook)
            self.createSheet('Top Keys', self.TopKeysList, style, workbook)
            self.createSheet('Data Format', self.DataFormatList, style, workbook)
            self.createSheet('BH', self.BHList, style, workbook)
            self.createSheet('BH Rank Keys', self.BHRKList, style, workbook)
            self.createSheet('External Statements', self.ESList, style, workbook)
            
            self.createSheet('Universe', self.UniExtList, style, workbook)
            self.createSheet('Unv Tables', self.UniTableList, style, workbook)
            self.createSheet('Unv Class', self.UniClassList, style, workbook)
            self.createSheet('Unv Objects', self.UniObjList, style, workbook)
            self.createSheet('Unv Conditions', self.UniConList, style, workbook)
            self.createSheet('Unv Joins', self.UniJoinsList, style, workbook)
            
            spreadsheet.setColumnWidth(0, 8000)
            spreadsheet.setColumnWidth(1, 8000)
            
            return workbook
        
        elif outputOption == 'INTF':
            spreadsheet = workbook.createSheet('Interface')
            count = 0
            for key in self.InterfaceList:
                row = spreadsheet.createRow(count)
                row.setHeightInPoints(30)
                cell = row.createCell(0)
                cell.setCellValue(key)
                cell.setCellStyle(style)
                count = count+1
                
            spreadsheet.setColumnWidth(0, 8000)
            spreadsheet.setColumnWidth(1, 8000)
            return workbook
    
    def createSheet(self, sheetName, columns, style, workbook):
        spreadsheet = workbook.createSheet(sheetName)
        row = spreadsheet.createRow(0)
        row.setHeightInPoints(30)
        count = 0
        for key in columns:
            cell = row.createCell(count)
            cell.setCellValue(key)
            cell.setCellStyle(style)
            spreadsheet.setColumnWidth(count, 7000)
            count = count+1
    
    def setOutputfilepath(self, Outputfilepath):
        self.Outputfilepath = Outputfilepath
    
    def getOutputfilepath(self):
        return self.Outputfilepath
