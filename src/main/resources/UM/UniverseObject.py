'''
Created on Jun 1, 2016

@author: ebrifol
'''

import Utils
import UM
from copy import deepcopy

class UniverseObject(object):
            
    def __init__(self,versionID,universeExtension,universeClassName,universeObjectName):
        self.versionID = versionID
        self.universeClassName = universeClassName
        self.universeExtension = universeExtension
        self.universeObjectName = universeObjectName
        self.properties = Utils.odict()
    
    def _getPropertiesFromServer(self,DbCursor):
        DbCursor.execute("SELECT DESCRIPTION,OBJECTTYPE,QUALIFICATION,AGGREGATION,OBJSELECT,OBJWHERE,PROMPTHIERARCHY,ORDERNRO FROM dwhrep.UniverseObject where versionid =? and CLASSNAME=? AND OBJECTNAME =?",(self.versionID,self.universeClassName,self.universeObjectName,))
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
        for row in tpiDict['Universeobject']['UNIVERSEEXTENSION']:
            if self.universeExtension.upper() in tpiDict['Universeobject']['UNIVERSEEXTENSION'][row].upper():
                if self.universeClassName == tpiDict['Universeobject']['CLASSNAME'][row] and self.universeObjectName == tpiDict['Universeobject']['OBJECTNAME'][row]:
                    self.properties['DESCRIPTION'] = tpiDict['Universeobject']['DESCRIPTION'][row]
                    self.properties['OBJECTTYPE'] = tpiDict['Universeobject']['OBJECTTYPE'][row]
                    self.properties['QUALIFICATION'] = tpiDict['Universeobject']['QUALIFICATION'][row]
                    self.properties['AGGREGATION'] = tpiDict['Universeobject']['AGGREGATION'][row]
                    self.properties['OBJSELECT'] = tpiDict['Universeobject']['OBJSELECT'][row]
                    self.properties['OBJWHERE'] = tpiDict['Universeobject']['OBJWHERE'][row]
                    self.properties['PROMPTHIERARCHY'] = tpiDict['Universeobject']['PROMPTHIERARCHY'][row]
                    self.properties['ORDERNRO'] = tpiDict['Universeobject']['ORDERNRO'][row]
    
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
                if Name != 'UNIVERSEEXTENSION' and Name != 'UniverseClass':                 
                    self.properties[Name] = Value
    
    def _getPropertiesFromXlsx(self,xlsxDict):
        '''Populate the objects contents from a XlsxDict object.
        
        Exceptions: 
                   Raised if XlsDict and filename are both None (ie nothing to process)
        '''
        
        for Name, Value in xlsxDict.iteritems():
            if Name != 'UNIVERSEEXTENSION' and Name != 'CLASSNAME' and Name != 'NAME':                 
                self.properties[Name] = Value
        
    
    def _toXLSX(self, xlsxFile, workbook):
        ''' Converts the object to an excel document
        
        Parent toXLSX() method is responsible for triggering child object toXLSX() methods
        '''
        
        sheet = workbook.getSheet('Unv Objects')
        rowNumber = sheet.getLastRowNum() + 1
        
        xlsxFile.writeToWorkbook(sheet, rowNumber, xlsxFile.findValue(sheet, 'CLASSNAME').getColumnIndex(), self.universeClassName)
        xlsxFile.writeToWorkbook(sheet, rowNumber, xlsxFile.findValue(sheet, 'NAME').getColumnIndex(), self.universeObjectName)
        xlsxFile.writeToWorkbook(sheet, rowNumber, xlsxFile.findValue(sheet, 'UNIVERSEEXTENSION').getColumnIndex(), self.universeExtension)
        
        for FDColumn in xlsxFile.UniObjList:
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
        
        outputXML = os +'<UniverseObject name="'+self.universeObjectName  +'" class="'+self.universeClassName  +'" extension="'+self.universeExtension  +'">'
        for prop in self.properties:
            outputXML += os2+'<'+str(prop)+'>'+ Utils.escape(self.properties[prop]) +'</'+str(prop)+'>'
        outputXML +=os +'</UniverseObject>'
        return outputXML
    
    def populateRepDbDicts(self):
        RepDbDict = {}        
        RepDbDict = deepcopy(self.properties)
        RepDbDict['VERSIONID'] = self.versionID
        RepDbDict['CLASSNAME'] = self.universeClassName
        RepDbDict['UNIVERSEEXTENSION'] = self.universeExtension
        RepDbDict['OBJECTNAME'] = self.universeObjectName
        RepDbDict['OBJ_BH_REL'] = 0
        RepDbDict['ELEM_BH_REL'] = 0
        RepDbDict['INHERITANCE'] = 0

        return RepDbDict
    
    def difference(self,UniObj,deltaObj=None):
        if deltaObj is None:
            deltaObj = Utils.Delta(self.universeObjectName,UniObj.universeObjectName)
         
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
    