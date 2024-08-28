'''
Created on Jun 1, 2016

@author: ebrifol
'''

import Utils
import UM
from copy import deepcopy

class UniverseCondition(object):
    
    def __init__(self,versionID,universeExtension,universeClassName,universeConditionName):
        self.versionID = versionID
        self.universeExtension  = universeExtension
        self.universeClassName = universeClassName
        self.universeConditionName = universeConditionName
        self.properties = Utils.odict()
    
    def _getPropertiesFromServer(self,DbCursor):
        DbCursor.execute("SELECT DESCRIPTION,CONDWHERE,AUTOGENERATE,CONDOBJCLASS,CONDOBJECT,PROMPTTEXT,MULTISELECTION,FREETEXT,ORDERNRO FROM dwhrep.UniverseCondition where versionid =? and classname=? and universecondition=?",(self.versionID,self.universeClassName,self.universeConditionName,))
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
        for row in tpiDict['Universecondition']['UNIVERSEEXTENSION']:
            #extensionList = string.split(tpiDict['Universecondition']['UNIVERSEEXTENSION'][row],',')
            if self.universeExtension.upper() in tpiDict['Universecondition']['UNIVERSEEXTENSION'][row].upper():
                if (self.universeClassName == tpiDict['Universecondition']['CLASSNAME'][row]) and (self.universeConditionName == tpiDict['Universecondition']['UNIVERSECONDITION'][row]):
                    self.properties['DESCRIPTION'] = tpiDict['Universecondition']['DESCRIPTION'][row]
                    self.properties['CONDWHERE'] = tpiDict['Universecondition']['CONDWHERE'][row]
                    self.properties['AUTOGENERATE'] = tpiDict['Universecondition']['AUTOGENERATE'][row]
                    self.properties['CONDOBJCLASS'] = tpiDict['Universecondition']['CONDOBJCLASS'][row]
                    self.properties['CONDOBJECT'] = tpiDict['Universecondition']['CONDOBJECT'][row]
                    self.properties['PROMPTTEXT'] = tpiDict['Universecondition']['PROMPTTEXT'][row]
                    self.properties['MULTISELECTION'] = tpiDict['Universecondition']['MULTISELECTION'][row]
                    self.properties['FREETEXT'] = tpiDict['Universecondition']['FREETEXT'][row]                    
                    self.properties['ORDERNRO'] = tpiDict['Universecondition']['ORDERNRO'][row]
    
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
            
            self._completeModel()
    
    def _getPropertiesFromXlsx(self,xlsxDict):
        '''Populate the objects contents from a XlsxDict object.
        
        Exceptions: 
                   Raised if XlsDict and filename are both None (ie nothing to process)
        '''
        
        for Name, Value in xlsxDict.iteritems():
            if Name != 'UNIVERSEEXTENSION' and Name != 'NAME':                
                self.properties[Name] = Value
        
        self._completeModel()
    
    def _toXLSX(self, xlsxFile, workbook):
        ''' Converts the object to an excel document
        
        Parent toXLSX() method is responsible for triggering child object toXLSX() methods
        '''
        
    
    def _toXLSX(self, xlsxFile, workbook):
        ''' Converts the object to an excel document
        
        Parent toXLSX() method is responsible for triggering child object toXLSX() methods
        '''
        
        sheet = workbook.getSheet('Unv Conditions')
        rowNumber = sheet.getLastRowNum() + 1
        
        xlsxFile.writeToWorkbook(sheet, rowNumber, xlsxFile.findValue(sheet, 'CLASSNAME').getColumnIndex(), self.universeClassName)
        xlsxFile.writeToWorkbook(sheet, rowNumber, xlsxFile.findValue(sheet, 'NAME').getColumnIndex(), self.universeConditionName)
        xlsxFile.writeToWorkbook(sheet, rowNumber, xlsxFile.findValue(sheet, 'UNIVERSEEXTENSION').getColumnIndex(), self.universeExtension)
        
        for FDColumn in xlsxFile.UniConList:
            if FDColumn in self.properties.keys():
                value = self.properties[FDColumn]
                if value == 1 or value == '1':
                    value = 'Y'
                elif value == 0 or value == '0':
                    value = ''
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
        
        outputXML = os + '<UniverseCondition name="'+self.universeConditionName  +'" class="'+self.universeClassName  +'" extension="'+self.universeExtension  +'">'
        for prop in self.properties:
            outputXML += os2+'<'+str(prop)+'>'+ Utils.escape(self.properties[prop]) +'</'+str(prop)+'>'
        outputXML += os + '</UniverseCondition>'
        return outputXML
    
    def populateRepDbDicts(self):
        RepDbDict = {}        
        RepDbDict = deepcopy(self.properties)
        RepDbDict['VERSIONID'] = self.versionID
        RepDbDict['CLASSNAME'] = self.universeClassName
        RepDbDict['UNIVERSEEXTENSION'] = self.universeExtension
        RepDbDict['UNIVERSECONDITION'] = self.universeConditionName
        RepDbDict['OBJ_BH_REL'] = 0
        RepDbDict['ELEM_BH_REL'] = 0
        RepDbDict['INHERITANCE'] = 0

        return RepDbDict
    
    def difference(self,UniObj,deltaObj=None):
        
        if deltaObj is None:
            deltaObj = Utils.Delta(self.universeConditionName,UniObj.universeConditionName)
         
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
    
    def _completeModel(self):
        if 'MULTISELECTION' not in self.properties or self.properties['MULTISELECTION'] == '':
            self.properties['MULTISELECTION'] = '0'