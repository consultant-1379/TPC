'''
Created on Jun 1, 2016

@author: ebrifol
'''

import Utils
import UM
from copy import deepcopy

class UniverseExtension(object):
    
    def __init__(self,versionID,universeName,universeExtension=None,universeExtensionName=None):
        self.versionID = versionID
        self.universeName = universeName
        self.universeExtension = universeExtension
        self.universeExtensionName = universeExtensionName
        self.universeClassObjects = Utils.odict()
        self.universeTableObjects = Utils.odict()
        self.universeJoinObjects = Utils.odict() 
        self.properties = Utils.odict()
    
    def _getPropertiesFromServer(self,DbCursor):
        self._getUniverseJoins(DbCursor)
        self._getUniverseTables(DbCursor)
        self._getUniverseClasses(DbCursor)
    
    def _getUniverseTables(self,DbCursor):
        DbCursor.execute("SELECT TABLENAME,UNIVERSEEXTENSION FROM UniverseTable where versionid =?",(self.versionID,))
        resultset = DbCursor.fetchall()
        for row in resultset:
            if self.universeExtension in row[1]:
                unvTab = UM.UniverseTable(self.versionID,row[1],row[0])
                unvTab._getPropertiesFromServer(DbCursor)
                self.universeTableObjects[row[0]] = unvTab

    def _getUniverseClasses(self,DbCursor):
        DbCursor.execute("SELECT CLASSNAME,UNIVERSEEXTENSION FROM UniverseClass where versionid =?",(self.versionID,))
        resultset = DbCursor.fetchall()
        for row in resultset:
            if self.universeExtension in row[1]:
                unvClass = UM.UniverseClass(self.versionID,row[1],row[0])
                self.universeClassObjects[row[0]] = unvClass
                self.universeClassObjects[row[0]]._getPropertiesFromServer(DbCursor)

    def _getUniverseJoins(self,DbCursor):
        DbCursor.execute("SELECT UNIVERSEEXTENSION,SOURCECOLUMN,SOURCETABLE,TARGETCOLUMN,TARGETTABLE,TMPCOUNTER FROM UniverseJoin where versionid =?",(self.versionID,))
        resultset = DbCursor.fetchall()
        for row in resultset:
            if self.universeExtension in row[0]:
                unvjoin = UM.UniverseJoin(self.versionID,row[0],row[1],row[2],row[3],row[4],row[5],)
                unvjoin._getPropertiesFromServer(DbCursor)
                self.universeJoinObjects[unvjoin.getJoinId()] = unvjoin
    
    def _getPropertiesFromTPI(self,tpidict,tmpCounter):
        if 'Universetable' in tpidict:
            for row in tpidict['Universetable']['UNIVERSEEXTENSION']:
                extensionList = tpidict['Universetable']['UNIVERSEEXTENSION'][row].split(',')
                if self.universeExtension in extensionList:
                    unvTab = UM.UniverseTable(self.versionID,tpidict['Universetable']['UNIVERSEEXTENSION'][row],tpidict['Universetable']['TABLENAME'][row])
                    unvTab._getPropertiesFromTPI(tpidict)
                    self.universeTableObjects[tpidict['Universetable']['TABLENAME'][row]] = unvTab
        
        if 'Universeclass' in tpidict:        
            for row in tpidict['Universeclass']['CLASSNAME']:
                extensionList = tpidict['Universeclass']['UNIVERSEEXTENSION'][row].split(',')
                if self.universeExtension in extensionList:
                    unvClass = UM.UniverseClass(self.versionID,tpidict['Universeclass']['UNIVERSEEXTENSION'][row],tpidict['Universeclass']['CLASSNAME'][row])
                    unvClass._getPropertiesFromTPI(tpidict)
                    self.universeClassObjects[tpidict['Universeclass']['CLASSNAME'][row]] = unvClass
        
        if 'Universejoin' in tpidict:
            if 'UNIVERSEEXTENSION' in tpidict['Universejoin']:
                for row in tpidict['Universejoin']['UNIVERSEEXTENSION']:
                    extensionList = tpidict['Universejoin']['UNIVERSEEXTENSION'][row].split(',')
                    if self.universeExtension in extensionList:
                        tmpCounter +=1 
                        srcc = tpidict['Universejoin']['SOURCECOLUMN'][row]
                        srct = tpidict['Universejoin']['SOURCETABLE'][row]
                        tgtc = tpidict['Universejoin']['TARGETCOLUMN'][row]
                        tgtt = tpidict['Universejoin']['TARGETTABLE'][row]
                        unvJoin = UM.UniverseJoin(self.versionID,tpidict['Universejoin']['UNIVERSEEXTENSION'][row],srcc,srct,tgtc,tgtt,tmpCounter)
                        unvJoin._getPropertiesFromTPI(tpidict)
                        self.universeJoinObjects[unvJoin.getJoinId()] = unvJoin  
        return tmpCounter
    
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
                
                
            for Name,  Values in xlsDict['Universe'][self.universeName]['Tables'].iteritems():
                if self.universeExtension in Values['UNIVERSEEXTENSION']:
                    unvtab=UM.UniverseTable(self.versionID,Values['UNIVERSEEXTENSION'],Name)
                    unvtab._getPropertiesFromXls(Values)
                    self.universeTableObjects[Name]=unvtab
                
            for Name,  Values in xlsDict['Universe'][self.universeName]['Class'].iteritems():  
                if self.universeExtension in Values['UNIVERSEEXTENSION']:
                    unvclass=UM.UniverseClass(self.versionID,Values['UNIVERSEEXTENSION'],Name)                               
                    unvclass._getPropertiesFromXls(xlsDict['Universe'][self.universeName])                           
                    self.universeClassObjects[unvclass.universeClassName]=unvclass
                
            for Name,  Values in xlsDict['Universe'][self.universeName]['Joins'].iteritems():        
                if self.universeExtension in Values['UNIVERSEEXTENSION']:
                    sourcecolumn = Values['SOURCECOLUMN']
                    sourcetable = Values['SOURCETABLE']
                    targetcolumn = Values['TARGETCOLUMN']
                    targettable = Values['TARGETTABLE']
                    unvJoin=UM.UniverseJoin(self.versionID,Values['UNIVERSEEXTENSION'],sourcecolumn,sourcetable,targetcolumn,targettable,Name)
                    unvJoin._getPropertiesFromXls(Values)
                    self.universeJoinObjects[unvJoin.getJoinId()]=unvJoin
    
    def _getPropertiesFromXlsx(self,xlsxDict):
        '''Populate the objects contents from a XlsxDict object.
        
        Exceptions: 
                   Raised if XlsDict and filename are both None (ie nothing to process)
        '''
        
        for Name, Values in xlsxDict['unvTables'].iteritems():
            if Name == self.universeExtension:
                for tableName, properties in Values.iteritems():
                    unvtab=UM.UniverseTable(self.versionID,Name,tableName)
                    unvtab._getPropertiesFromXlsx(properties)
                    self.universeTableObjects[tableName]=unvtab
        
        for Name, Values in xlsxDict['unvClass'].iteritems():
            if Name == self.universeExtension:
                for ClassName, properties in Values.iteritems():
                    unvclass=UM.UniverseClass(self.versionID,Name,ClassName)                               
                    unvclass._getPropertiesFromXlsx(xlsxDict)                           
                    self.universeClassObjects[unvclass.universeClassName]=unvclass
        
        for Name, Values in xlsxDict['unvJoins'].iteritems():
            if Name == self.universeExtension:
                for join, properties in Values.iteritems():
                    sourcecolumn = properties['SOURCECOLUMN']
                    sourcetable = properties['SOURCETABLE']
                    targetcolumn = properties['TARGETCOLUMN']
                    targettable = properties['TARGETTABLE']
                    unvJoin=UM.UniverseJoin(self.versionID,Name,sourcecolumn,sourcetable,targetcolumn,targettable,join)
                    unvJoin._getPropertiesFromXlsx(properties)
                    self.universeJoinObjects[unvJoin.getJoinId()]=unvJoin
    
    def _toXLSX(self, xlsxFile, workbook):
        ''' Converts the object to an excel document
        
        Parent toXLSX() method is responsible for triggering child object toXLSX() methods
        '''
        
        sheet = workbook.getSheet('Universe')
        rowNumber = sheet.getLastRowNum() + 1
        
        xlsxFile.writeToWorkbook(sheet, rowNumber, xlsxFile.findValue(sheet, 'UNVNAME').getColumnIndex(), self.universeName)
        xlsxFile.writeToWorkbook(sheet, rowNumber, xlsxFile.findValue(sheet, 'UNVEXTENSION').getColumnIndex(), self.universeExtension)
        xlsxFile.writeToWorkbook(sheet, rowNumber, xlsxFile.findValue(sheet, 'UNVEXTENSIONNAME').getColumnIndex(), self.universeExtensionName)
        
        for table in self.universeTableObjects.itervalues():
            table._toXLSX(xlsxFile, workbook)
        
        for uniClass in self.universeClassObjects.itervalues():
            uniClass._toXLSX(xlsxFile, workbook)
            
        for join in self.universeJoinObjects.itervalues():
            join._toXLSX(xlsxFile, workbook)
    
    def _getPropertiesFromXML(self,xmlElement,tmpCounter):
        for elem in xmlElement:
            if elem.tag == 'UniverseTables':
                for elem1 in elem:
                    if elem1.tag == 'UniverseTable':
                        unvTable = UM.UniverseTable(self.versionID,elem1.attrib['extension'],elem1.attrib['name'])
                        unvTable._getPropertiesFromXML(elem1)
                        self.universeTableObjects[elem1.attrib['name']] = unvTable
            if elem.tag == 'UniverseClasses':
                for elem1 in elem:
                    if elem1.tag == 'UniverseClass':
                        unvClass = UM.UniverseClass(self.versionID,elem1.attrib['extension'],elem1.attrib['name'])
                        unvClass._getPropertiesFromXML(elem1)
                        self.universeClassObjects[elem1.attrib['name']] =  unvClass
            if elem.tag == 'UniverseJoins':
                for elem1 in elem:
                    if elem1.tag == 'UniverseJoin':
                        unvJoin = UM.UniverseJoin(self.versionID,self.universeExtension,elem1.attrib['sourceColumn'],elem1.attrib['sourceTable'],elem1.attrib['targetColumn'],elem1.attrib['targetTable'],tmpCounter)
                        unvJoin._getPropertiesFromXML(elem1)
                        self.universeJoinObjects[unvJoin.getJoinId()] = unvJoin
                        tmpCounter += 1
        return tmpCounter
    
    def _toXML(self,indent=0):
        offset = '    '
        os = "\n" + offset*indent
        os2 = os + offset
        
        outputXML = os + '<UniverseExtension  name="'+str(self.universeExtension)+ '" ExtensionName= "' + Utils.escape(self.universeExtensionName) +'">'
        outputXML += os2 +'<UniverseTables>'
        for unvTable in self.universeTableObjects:
            outputXML += str(self.universeTableObjects[unvTable]._toXML(indent+2))
        outputXML += os2 +'</UniverseTables>'
        outputXML += os2 +'<UniverseClasses>'           
        for unvClass in self.universeClassObjects:
            outputXML += self.universeClassObjects[unvClass]._toXML(indent+2)
        outputXML += os2 +'</UniverseClasses>'
        outputXML += os2 +'<UniverseJoins>'
        for unvJoin in self.universeJoinObjects:
            outputXML += self.universeJoinObjects[unvJoin]._toXML(indent+2)
        outputXML += os2 +'</UniverseJoins>' 
        outputXML += os +'</UniverseExtension>'
        return outputXML
    
    def populateRepDbDicts(self):
        RepDbDict = {}
        RepDbDict['UNIVERSEEXTENSION']=self.universeExtension
        RepDbDict['VERSIONID']=self.versionID
        RepDbDict['UNIVERSENAME']=self.universeName
        RepDbDict['UNIVERSEEXTENSIONNAME']=self.universeExtensionName

        return RepDbDict
    
    def difference(self,UniObj,deltaObj=None):
        
        if deltaObj is None:
            deltaObj = Utils.Delta(self.universeExtensionName,UniObj.universeExtensionName)
         
        #########################################################################################################################################
        # Properties diff
        Delta = Utils.DictDiffer(self.properties,UniObj.properties)
        deltaObj.location.append('Properties')
        for item in Delta.changed():
            deltaObj.addChange('<Changed>', item, self.properties[item], UniObj.properties[item])
        
        for item in Delta.added():
            deltaObj.addChange('<Added>', item, '', UniObj.properties[item])
                
        for item in Delta.removed():
            deltaObj.addChange('<Removed>', item, self.properties[item], '')

        deltaObj.location.pop()
        
        ################################################################
        # Universe Class Diff
        Delta = Utils.DictDiffer(self.universeClassObjects,UniObj.universeClassObjects)
        deltaObj.location.append('UniverseClass')
        for item in Delta.added():
            deltaObj.addChange('<Added>', UniObj.universeClassObjects[item].universeClassName, '', item)
      
        for item in Delta.removed():
            deltaObj.addChange('<Removed>', self.universeClassObjects[item].universeClassName, item, '')
        
        deltaObj.location.pop()
        
        for item in Delta.common():
            deltaObj.location.append('UniverseClass='+item)
            deltaObj = self.universeClassObjects[item].difference(UniObj.universeClassObjects[item],deltaObj)
            deltaObj.location.pop() 
        
        ################################################################
        # Universe Table Diff
        Delta = Utils.DictDiffer(self.universeTableObjects,UniObj.universeTableObjects)
        deltaObj.location.append('UniverseTable')
        for item in Delta.added():
            deltaObj.addChange('<Added>', UniObj.universeTableObjects[item].tableName, '', item)
      
        for item in Delta.removed():
            deltaObj.addChange('<Removed>', self.universeTableObjects[item].tableName, item, '')
        
        deltaObj.location.pop()
        
        for item in Delta.common():
            deltaObj.location.append('UniverseTable='+item)
            deltaObj = self.universeTableObjects[item].difference(UniObj.universeTableObjects[item],deltaObj)
            deltaObj.location.pop()  
        
        
        ################################################################
        # Universe Joins Diff
        Delta = Utils.DictDiffer(self.universeJoinObjects,UniObj.universeJoinObjects)
        deltaObj.location.append('UniverseJoin')
        for item in Delta.added():
            deltaObj.addChange('<Added>', UniObj.universeJoinObjects[item].joinID, '', item)
      
        for item in Delta.removed():
            deltaObj.addChange('<Removed>', self.universeJoinObjects[item].joinID, item, '')
        
        deltaObj.location.pop()
        
        for item in Delta.common():
            deltaObj.location.append('UniverseJoin='+item)
            deltaObj = self.universeJoinObjects[item].difference(UniObj.universeJoinObjects[item],deltaObj)
            deltaObj.location.pop()   
        
        return deltaObj
        