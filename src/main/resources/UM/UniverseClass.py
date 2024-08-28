'''
Created on Jun 1, 2016

@author: ebrifol
'''

import Utils
import UM
from copy import deepcopy

class UniverseClass(object):
            
    def __init__(self,versionID,universeExtension,universeClassName):
        self.versionID = versionID
        self.universeClassName = universeClassName
        self.universeExtension = universeExtension
        self.universeObjObjects = Utils.odict()
        self.universeConditionObjects = Utils.odict()
        self.properties = Utils.odict()
    
    def _getPropertiesFromServer(self,DbCursor):
        DbCursor.execute("SELECT DESCRIPTION,PARENT,ORDERNRO FROM dwhrep.UniverseClass where versionid =? and CLASSNAME =?",(self.versionID, self.universeClassName,))
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
        self._getUniverseObjects(DbCursor)
        self._getUniverseConditions(DbCursor)

    def _getUniverseObjects(self,DbCursor):
        DbCursor.execute('SELECT OBJECTNAME FROM dwhrep.UniverseObject where versionid=? and classname=?',(self.versionID,self.universeClassName,))
        resultset = DbCursor.fetchall()
        for row in resultset: 
            unvObj = UM.UniverseObject(self.versionID,self.universeExtension,self.universeClassName,row[0])
            unvObj._getPropertiesFromServer(DbCursor)
            self.universeObjObjects[row[0]] = unvObj                   
    
    def _getUniverseConditions(self,DbCursor):
        DbCursor.execute("SELECT UNIVERSECONDITION FROM dwhrep.UniverseCondition where versionid =? and CLASSNAME=?",(self.versionID,self.universeClassName,))
        resultset = DbCursor.fetchall()
        for row in resultset:
            unvCond= UM.UniverseCondition(self.versionID,self.universeExtension,self.universeClassName,row[0])
            unvCond._getPropertiesFromServer(DbCursor)
            self.universeConditionObjects[row[0]] = unvCond

    def _getPropertiesFromTPI(self,tpiDict):
        for row in tpiDict['Universeclass']['CLASSNAME']:
            if self.universeClassName == tpiDict['Universeclass']['CLASSNAME'][row] and self.universeExtension.upper() in tpiDict['Universeclass']['UNIVERSEEXTENSION'][row].upper():
                self.properties['ORDERNRO'] = Utils.strFloatToInt(tpiDict['Universeclass']['ORDERNRO'][row])
                self.properties['DESCRIPTION'] = Utils.safeNull(tpiDict['Universeclass']['DESCRIPTION'][row])
                self.properties['PARENT'] = str(tpiDict['Universeclass']['PARENT'][row])

        #create objects
        if 'Universeobject' in tpiDict:
            for row in tpiDict['Universeobject']['UNIVERSEEXTENSION']:
                #extensionList = tpiDict['Universeobject']['UNIVERSEEXTENSION'][row].split(',')
                if self.universeExtension.upper() == tpiDict['Universeobject']['UNIVERSEEXTENSION'][row].upper():
                    className = tpiDict['Universeobject']['CLASSNAME'][row]
                    if self.universeClassName == className:
                        objName = tpiDict['Universeobject']['OBJECTNAME'][row]
                        unvObj = UM.UniverseObject(self.versionID,self.universeExtension,self.universeClassName,objName)
                        unvObj._getPropertiesFromTPI(tpiDict)
                        self.universeObjObjects[objName] = unvObj
                
        if 'Universecondition' in tpiDict:
            for row in tpiDict['Universecondition']['UNIVERSECONDITION']:
                #extensionList = tpiDict['Universecondition']['UNIVERSEEXTENSION'][row].split(',')
                if self.universeExtension.upper() in tpiDict['Universecondition']['UNIVERSEEXTENSION'][row].upper():
                    className = tpiDict['Universecondition']['CLASSNAME'][row]
                    if self.universeClassName == className:
                        condName = tpiDict['Universecondition']['UNIVERSECONDITION'][row]
                        unvCond = UM.UniverseCondition(self.versionID,self.universeExtension,self.universeClassName,condName)
                        unvCond._getPropertiesFromTPI(tpiDict)
                        self.universeConditionObjects[condName] = unvCond
    
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
            
            
            for Name, Value in xlsDict['Class'][self.universeClassName].iteritems():
                if Name != 'UNIVERSEEXTENSION':
                    self.properties[Name] = Value
            

            if self.universeClassName in xlsDict['Object']:
                for Name,  Values in xlsDict['Object'][self.universeClassName].iteritems():
                    if Values['UniverseClass'] == self.universeClassName:
                        unobj = UM.UniverseObject(self.versionID,self.universeExtension,self.universeClassName,Name)                        
                        unobj._getPropertiesFromXls(Values)
                        self.universeObjObjects[Name] = unobj
                        
            if self.universeClassName in xlsDict['Conditions']:
                for Name,  Values in xlsDict['Conditions'][self.universeClassName].iteritems():
                    if Values['CONDOBJCLASS'] == self.universeClassName:
                        uncon = UM.UniverseCondition(self.versionID,self.universeExtension,self.universeClassName,Name)                        
                        uncon._getPropertiesFromXls(Values)
                        self.universeConditionObjects[Name] = uncon
    
    def _getPropertiesFromXlsx(self,xlsxDict):
        '''Populate the objects contents from a XlsxDict object.
        
        Exceptions: 
                   Raised if XlsDict and filename are both None (ie nothing to process)
        '''
        
        for Name, Value in xlsxDict['unvClass'][self.universeExtension][self.universeClassName].iteritems():
            if Name != 'UNIVERSEEXTENSION' and Name != 'CLASSNAME':
                self.properties[Name] = Value
        
        if self.universeClassName in xlsxDict['unvObjects']:
            for Name, Values in xlsxDict['unvObjects'][self.universeClassName].iteritems():
                unobj = UM.UniverseObject(self.versionID,self.universeExtension,self.universeClassName,Name)                        
                unobj._getPropertiesFromXlsx(Values)
                self.universeObjObjects[Name] = unobj
        
        if self.universeClassName in xlsxDict['unvConds']:  
            for Name, Values in xlsxDict['unvConds'][self.universeClassName].iteritems():
                uncon = UM.UniverseCondition(self.versionID,self.universeExtension,self.universeClassName,Name)                        
                uncon._getPropertiesFromXlsx(Values)
                self.universeConditionObjects[Name] = uncon
                    
    def _toXLSX(self, xlsxFile, workbook):
        ''' Converts the object to an excel document
        
        Parent toXLSX() method is responsible for triggering child object toXLSX() methods
        '''
        
        sheet = workbook.getSheet('Unv Class')
        rowNumber = sheet.getLastRowNum() + 1
        
        addRow = True
        cellNumber = xlsxFile.findValue(sheet, 'NAME').getColumnIndex()
        for row in sheet:
            if row.getCell(cellNumber).toString() == self.universeClassName:
                addRow = False
        
        if addRow:
            xlsxFile.writeToWorkbook(sheet, rowNumber, xlsxFile.findValue(sheet, 'NAME').getColumnIndex(), self.universeClassName)
            xlsxFile.writeToWorkbook(sheet, rowNumber, xlsxFile.findValue(sheet, 'UNIVERSEEXTENSION').getColumnIndex(), self.universeExtension)
            
            for FDColumn in xlsxFile.UniClassList:
                if FDColumn in self.properties.keys():
                    value = self.properties[FDColumn]
                    xlsxFile.writeToWorkbook(sheet, rowNumber, xlsxFile.findValue(sheet, FDColumn).getColumnIndex(), str(value))
            
            for object in self.universeObjObjects.itervalues():
                object._toXLSX(xlsxFile, workbook)
                
            for con in self.universeConditionObjects.itervalues():
                con._toXLSX(xlsxFile, workbook)
    
    def _getPropertiesFromXML(self,xmlelement):
        for elem1 in xmlelement:
            if elem1.tag == 'UniverseObjects':
                for elem2 in elem1:
                    if elem2.tag == 'UniverseObject':
                        uo = UM.UniverseObject(self.versionID,elem2.attrib['extension'],elem2.attrib['class'],elem2.attrib['name'])
                        uo._getPropertiesFromXML(elem2)
                        self.universeObjObjects[elem2.attrib['name']] = uo
                
            elif elem1.tag == 'UniverseConditions':
                for elem2 in elem1:
                    if elem2.tag == 'UniverseCondition':
                        uc = UM.UniverseCondition(self.versionID,elem2.attrib['extension'],elem2.attrib['class'],elem2.attrib['name'])
                        uc._getPropertiesFromXML(elem2)
                        self.universeConditionObjects[elem2.attrib['name']] = uc
            else:
                if elem1.text is None:
                    self.properties[elem1.tag] = ''
                else:
                    self.properties[elem1.tag] = Utils.safeNull(elem1.text)
    
    def _toXML(self,indent=0):
        offset = '    '
        os = "\n" + offset*indent
        os2 = os + offset
        
        outputXML =os+'<UniverseClass  name="'+self.universeClassName  + '" extension="'+self.universeExtension  +'">'
        for prop in self.properties:
            outputXML += os2+'<'+str(prop)+'>'+ Utils.escape(self.properties[prop]) +'</'+str(prop)+'>'
        outputXML += os2 +'<UniverseObjects>'
        for unvObj in self.universeObjObjects:
            outputXML += self.universeObjObjects[unvObj]._toXML(indent+2)
        outputXML += os2 + '</UniverseObjects>'
        outputXML += os2 +'<UniverseConditions>'
        for unvCondition in self.universeConditionObjects:
            outputXML += self.universeConditionObjects[unvCondition]._toXML(indent+2)
        outputXML += os2 +'</UniverseConditions>'
        outputXML += os+'</UniverseClass>'
        return outputXML
    
    def populateRepDbDicts(self):
        RepDbDict = {}        
        RepDbDict = deepcopy(self.properties)
        RepDbDict['VERSIONID'] = self.versionID
        RepDbDict['UNIVERSEEXTENSION'] = self.universeExtension
        RepDbDict['CLASSNAME'] = self.universeClassName
        RepDbDict['OBJ_BH_REL'] = 0
        RepDbDict['ELEM_BH_REL'] = 0
        RepDbDict['INHERITANCE'] = 0
        
        if self.universeClassName.upper().endswith('KEYS'):
            from java.lang import Long
            RepDbDict['ORDERNRO'] = Long.MAX_VALUE

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
        
        ################################################################
        # Universe Object Diff
        Delta = Utils.DictDiffer(self.universeObjObjects,UniObj.universeObjObjects)
        deltaObj.location.append('UniverseObject')
        for item in Delta.added():
            deltaObj.addChange('<Added>', UniObj.universeObjObjects[item].universeObjectName, '', item)
      
        for item in Delta.removed():
            deltaObj.addChange('<Removed>', self.universeObjObjects[item].universeObjectName, item, '')
        
        deltaObj.location.pop()
        
        for item in Delta.common():
            deltaObj.location.append('UniverseObject='+item)
            deltaObj = self.universeObjObjects[item].difference(UniObj.universeObjObjects[item],deltaObj)
            deltaObj.location.pop()
            
        ################################################################
        # Universe Conditions Diff
        Delta = Utils.DictDiffer(self.universeConditionObjects,UniObj.universeConditionObjects)
        deltaObj.location.append('UniverseCondition')
        for item in Delta.added():
            deltaObj.addChange('<Added>', UniObj.universeConditionObjects[item].universeConditionName, '', item)
      
        for item in Delta.removed():
            deltaObj.addChange('<Removed>', self.universeConditionObjects[item].universeConditionName, item, '')
        
        deltaObj.location.pop()
        
        for item in Delta.common():
            deltaObj.location.append('UniverseCondition='+item)
            deltaObj = self.universeConditionObjects[item].difference(UniObj.universeConditionObjects[item],deltaObj)
            deltaObj.location.pop() 
        
            
        return deltaObj