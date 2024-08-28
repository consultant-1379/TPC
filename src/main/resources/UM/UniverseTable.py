'''
Created on Jun 1, 2016

@author: ebrifol
'''

import Utils
import UM
from copy import deepcopy

class UniverseTable(object):
    
    def __init__(self,versionID,universeExtension,tableName):
        self.versionID = versionID
        self.extensionList = [] 
        self.universeExtension = universeExtension
        self.tableName = tableName
        self.properties = Utils.odict()
    
    def _getPropertiesFromServer(self,DbCursor):
        DbCursor.execute("SELECT OWNER,ALIAS,ORDERNRO FROM UniverseTable where versionid =? and TableName=?",(self.versionID,self.tableName,))
        resultset = DbCursor.fetchall()
        desc = DbCursor.description
        for row in resultset:
            i = 0
            for x in desc:
                value = str(row[i])
                if x[0] == 'ORDERNRO':
                    value = Utils.strFloatToInt(value)
                
                self.properties[x[0]] = value
                i+=1
    
    def _getPropertiesFromTPI(self,tpiDict):
        for row in tpiDict['Universetable']['TABLENAME']:
            if self.tableName == tpiDict['Universetable']['TABLENAME'][row]:
                #extensionList = tpiDict['Universetable']['UNIVERSEEXTENSION'][row].split(',')
                if self.universeExtension in tpiDict['Universetable']['UNIVERSEEXTENSION'][row] or self.universeExtension.upper() == 'ALL':
                    for col in tpiDict['Universetable']:
                        if col=='OWNER' or col=='ALIAS' or col=='ORDERNRO':
                            self.properties[col] = tpiDict['Universetable'][col][row]
    
    def _getPropertiesFromXls(self,xlsDict=None,filename=None):
        '''Populate the objects contents from a xlsDict object or xls file.
        
        If a xls file is passed it is converted to a xlsDict object before processing.

        Exceptions: 
                   Raised if xlsDict and filename are both None (ie nothing to process)'''
        
        if xlsDict==None and filename==None:
            strg = '_getPropertiesFromXls() Nothing to Process'
            raise Exception(strg)
        else:
            if filename is not None:
                xlsDict = Utils.XlsDict(filename).returnXlsDict()
            
            for Name, Value in xlsDict.iteritems(): 
                if Name != 'UNIVERSEEXTENSION':                
                    self.properties[Name] = Value
    
    def _getPropertiesFromXlsx(self,xlsxDict):
        '''Populate the objects contents from a XlsxDict object.
        
        Exceptions: 
                   Raised if XlsDict and filename are both None (ie nothing to process)
        '''
        
        for Name, Value in xlsxDict.iteritems():
            if Name != 'UNIVERSEEXTENSION' and Name != 'TABLENAME' :                 
                self.properties[Name] = Value
    
    def _toXLSX(self, xlsxFile, workbook):
        ''' Converts the object to an excel document
        
        Parent toXLSX() method is responsible for triggering child object toXLSX() methods
        '''

        sheet = workbook.getSheet('Unv Tables')
        rowNumber = sheet.getLastRowNum() + 1
        
        addRow = True
        cellNumber = xlsxFile.findValue(sheet, 'TABLENAME').getColumnIndex()
        for row in sheet:
            if row.getCell(cellNumber).toString() == self.tableName:
                addRow = False
            
        if addRow:
            xlsxFile.writeToWorkbook(sheet, rowNumber, xlsxFile.findValue(sheet, 'TABLENAME').getColumnIndex(), self.tableName)
            xlsxFile.writeToWorkbook(sheet, rowNumber, xlsxFile.findValue(sheet, 'UNIVERSEEXTENSION').getColumnIndex(), self.universeExtension)
            
            for FDColumn in xlsxFile.UniTableList:
                if FDColumn in self.properties.keys():
                    value = self.properties[FDColumn]
                    xlsxFile.writeToWorkbook(sheet, rowNumber, xlsxFile.findValue(sheet, FDColumn).getColumnIndex(), str(value))
    
    def _getPropertiesFromXML(self,xmlElement):
        for elem in xmlElement:
            if elem.text is None:
                self.properties[elem.tag] = ''
            else:
                self.properties[elem.tag] = Utils.safeNull(elem.text)
    
    def _toXML(self,indent=0):
        offset = '    '
        os = "\n" + offset*indent
        os2 = os + offset
        
        outputXML = os + '<UniverseTable name="'+self.tableName  +'" extension="'+self.universeExtension+'">'
        for prop in self.properties:
            outputXML += os2+'<'+str(prop)+'>'+ Utils.escape(self.properties[prop]) +'</'+str(prop)+'>'
        outputXML += os +'</UniverseTable>'
        
        return outputXML
    
    def populateRepDbDicts(self):
        RepDbDict = {}        
        RepDbDict = deepcopy(self.properties)
        RepDbDict['VERSIONID'] = self.versionID       
        RepDbDict['TABLENAME'] = self.tableName
        RepDbDict['OBJ_BH_REL'] = 0
        RepDbDict['ELEM_BH_REL'] = 0
        RepDbDict['INHERITANCE'] = 0
        RepDbDict['UNIVERSEEXTENSION'] = self.universeExtension

        return RepDbDict

    def difference(self,UniObj,deltaObj=None):
        
        if deltaObj is None:
            deltaObj = Utils.Delta(self.tableName,UniObj.tableName)
         
        #########################################################################################################################################
        # Properties diff
        Delta = Utils.DictDiffer(self.properties,UniObj.properties)
        deltaObj.location.append('Properties')
        for item in Delta.changed():
            if item != 'ORDERNRO':
                deltaObj.addChange('<Changed>', item, self.properties[item], UniObj.properties[item])
        
        for item in Delta.added():
            if item != 'ORDERNRO':
                deltaObj.addChange('<Added>', item, '', UniObj.properties[item])
                
        for item in Delta.removed():
            if item != 'ORDERNRO':
                deltaObj.addChange('<Removed>', item, self.properties[item], '')

        deltaObj.location.pop()
            
        return deltaObj