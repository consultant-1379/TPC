'''
Created on Jun 1, 2016

@author: ebrifol
'''

import Utils
import UM
from copy import deepcopy

class Universe(object):
    
    def __init__(self,versionID,universeName):
        self.versionID = versionID
        self.universeName = universeName
        self.universeClasses = Utils.odict()
        self.universeTables = Utils.odict()
        self.universeJoins = Utils.odict() 
        self.universeExtensions = Utils.odict()
    
    def _getPropertiesFromServer(self,DbCursor):
        DbCursor.execute("SELECT UNIVERSEEXTENSION,UNIVERSEEXTENSIONNAME FROM UniverseName WHERE VERSIONID =? AND UNIVERSENAME =?", (self.versionID, self.universeName))
        rows = DbCursor.fetchall()
        for row in rows:
            if row[0] != '':
                unvext=UM.UniverseExtension(self.versionID,self.universeName,row[0],row[1])
                unvext._getPropertiesFromServer(DbCursor)
                self.universeExtensions[row[0]]=unvext 
        
        self._getUniverseJoins(DbCursor,'ALL')
        self._getUniverseTables(DbCursor,'ALL')
        self._getUniverseClasses(DbCursor,'ALL')
    
    def _getUniverseTables(self,DbCursor,unvextension):
        if unvextension != None:
            DbCursor.execute("SELECT TABLENAME FROM UniverseTable where versionid =? and UNIVERSEEXTENSION like ?",(self.versionID,'ALL',))
            resultset = DbCursor.fetchall()
            for row in resultset:
                unvTab = UM.UniverseTable(self.versionID,'ALL',row[0])
                unvTab._getPropertiesFromServer(DbCursor)
                self.universeTables[row[0]] = unvTab
    
    def _getUniverseClasses(self,DbCursor,unvextension):
        DbCursor.execute("SELECT CLASSNAME FROM dwhrep.UniverseClass where versionid =? and UNIVERSEEXTENSION like ?",(self.versionID,'ALL',))
        resultset = DbCursor.fetchall()
        for row in resultset:
            unvClass = UM.UniverseClass(self.versionID,unvextension,row[0])
            unvClass._getPropertiesFromServer(DbCursor)
            self.universeClasses[row[0]] = unvClass
    
    def _getUniverseJoins(self,DbCursor,unvextension):
        DbCursor.execute("SELECT UNIVERSEEXTENSION,SOURCECOLUMN,SOURCETABLE,TARGETCOLUMN,TARGETTABLE,TMPCOUNTER FROM dwhrep.UniverseJoin where versionid =?",(self.versionID,))
        resultset = DbCursor.fetchall()
        for row in resultset:
            if row[0] == None or row[0] == '' or row[0].upper() == 'ALL':
                unvjoin = UM.UniverseJoin(self.versionID,unvextension,row[1],row[2],row[3],row[4],row[5],)
                unvjoin._getPropertiesFromServer(DbCursor)
                self.universeJoins[unvjoin.getJoinId()] = unvjoin
                
    def _getPropertiesFromTPI(self,tpidict=None,filename=None):
        '''Populate the objects contents from a tpiDict object or tpi file.
        
        If a tpi file is passed it is converted to a tpiDict object before processing.
    
        Exceptions: 
                   Raised if tpiDict and filename are both None (ie nothing to process)'''
        if tpidict==None and filename==None:
            strg = 'getPropertiesFromTPI() Nothing to Process'
            raise Exception(strg)
        else:
            if filename is not None:
                tpidict = Utils.TpiDict(filename).returnTPIDict()
            tmpCounter=0
            for row in tpidict['Universename']['UNIVERSEEXTENSION']:
                ext = tpidict['Universename']['UNIVERSEEXTENSION'][row]
                if ext != '' :
                    extName = tpidict['Universename']['UNIVERSEEXTENSIONNAME'][row]
                    unv = UM.UniverseExtension(self.versionID,self.universeName,ext,extName)
                    tmpCounter=unv._getPropertiesFromTPI(tpidict,tmpCounter)
                    self.universeExtensions[ext] = unv
            
            if 'Universetable' in tpidict:        
                for row in tpidict['Universetable']['UNIVERSEEXTENSION']:
                    ext = tpidict['Universetable']['UNIVERSEEXTENSION'][row]
                    if ext.upper() == 'ALL' or ext == '':
                        unvTab = UM.UniverseTable(self.versionID,'ALL',tpidict['Universetable']['TABLENAME'][row])
                        unvTab._getPropertiesFromTPI(tpidict)
                        self.universeTables[tpidict['Universetable']['TABLENAME'][row]] = unvTab
            
            if 'Universeclass' in tpidict:    
                for row in tpidict['Universeclass']['CLASSNAME']:
                    ext = tpidict['Universeclass']['UNIVERSEEXTENSION'][row]
                    if ext.upper() == 'ALL' or ext == '':
                        unvClass = UM.UniverseClass(self.versionID,'ALL',tpidict['Universeclass']['CLASSNAME'][row])
                        unvClass._getPropertiesFromTPI(tpidict)
                        self.universeClasses[tpidict['Universeclass']['CLASSNAME'][row]] = unvClass
            
            if 'Universejoin' in tpidict: 
                for row in tpidict['Universejoin']['SOURCECOLUMN']:
                    ext = 'ALL'
                    try:
                        ext = tpidict['Universejoin']['UNIVERSEEXTENSION'][row]
                    except:
                        pass
                    if ext.upper() == 'ALL' or ext == '':
                        #for row in tpidict['Universejoin']['CONTEXT']:
                            tmpCounter +=1 
                            srcc = tpidict['Universejoin']['SOURCECOLUMN'][row]
                            srct = tpidict['Universejoin']['SOURCETABLE'][row]
                            tgtc = tpidict['Universejoin']['TARGETCOLUMN'][row]
                            tgtt = tpidict['Universejoin']['TARGETTABLE'][row]
                            unvJoin = UM.UniverseJoin(self.versionID,'ALL',srcc,srct,tgtc,tgtt,tmpCounter)
                            unvJoin._getPropertiesFromTPI(tpidict)
                            self.universeJoins[unvJoin.getJoinId()] = unvJoin
    
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
            
            if 'Tables' in xlsDict['Universe'][self.universeName]:
                for Name,  Values in xlsDict['Universe'][self.universeName]['Tables'].iteritems():
                    if Values['UNIVERSEEXTENSION'].upper() == 'ALL' or Values['UNIVERSEEXTENSION'].upper() == '':
                        unvtab=UM.UniverseTable(self.versionID,'ALL',Name)
                        unvtab._getPropertiesFromXls(Values)
                        self.universeTables[Name]=unvtab
            
            if 'Class' in xlsDict['Universe'][self.universeName]:
                for Name,  Values in xlsDict['Universe'][self.universeName]['Class'].iteritems():  
                    if Values['UNIVERSEEXTENSION'].upper() == 'ALL' or Values['UNIVERSEEXTENSION'].upper() == '':
                        unvclass=UM.UniverseClass(self.versionID,'ALL',Name)                               
                        unvclass._getPropertiesFromXls(xlsDict['Universe'][self.universeName])                           
                        self.universeClasses[unvclass.universeClassName]=unvclass
            
            if 'Joins' in xlsDict['Universe'][self.universeName]:  
                for Name,  Values in xlsDict['Universe'][self.universeName]['Joins'].iteritems(): 
                    if Values['UNIVERSEEXTENSION'].upper() == 'ALL' or Values['UNIVERSEEXTENSION'].upper() == '':
                        sourcecolumn = Values['SOURCECOLUMN']
                        sourcetable = Values['SOURCETABLE']
                        targetcolumn = Values['TARGETCOLUMN']
                        targettable = Values['TARGETTABLE']
                        unvJoin=UM.UniverseJoin(self.versionID,'ALL',sourcecolumn,sourcetable,targetcolumn,targettable,Name)
                        unvJoin._getPropertiesFromXls(Values)
                        self.universeJoins[unvJoin.getJoinId()]=unvJoin
            
            if 'Extensions' in xlsDict['Universe'][self.universeName]:        
                for Name,  Values in xlsDict['Universe'][self.universeName]['Extensions'].iteritems():
                    unvextname = Values['UNIVERSEEXTENSIONNAME']
                    unvext=UM.UniverseExtension(self.versionID,self.universeName,Name,unvextname) 
                    unvext._getPropertiesFromXls(xlsDict)
                    self.universeExtensions[Name]=unvext
    
    def _getPropertiesFromXlsx(self,xlsxDict):
        '''Populate the objects contents from a XlsxDict object.
        
        Exceptions: 
                   Raised if XlsDict and filename are both None (ie nothing to process)
        '''
        
        for Name, Values in xlsxDict['uni'][self.universeName].iteritems():
            if Name.upper() != 'ALL':
                unvext=UM.UniverseExtension(self.versionID,self.universeName,Name,Values)
                unvext._getPropertiesFromXlsx(xlsxDict)
                self.universeExtensions[Name]=unvext
        
        for Name, Values in xlsxDict['unvTables'].iteritems():
            if Name.upper() == 'ALL' or Name.upper() == '':
                for tableName, properties in Values.iteritems():
                    if Name.upper() == 'ALL' or Name.upper() == '':
                        unvtab=UM.UniverseTable(self.versionID,'ALL',tableName)
                    else:
                        unvtab=UM.UniverseTable(self.versionID,Name,tableName)
                        
                    unvtab._getPropertiesFromXlsx(properties)
                    self.universeTables[tableName]=unvtab
        
        for Name, Values in xlsxDict['unvClass'].iteritems():
            if Name not in self.universeExtensions.keys():
                for ClassName, properties in Values.iteritems():
                    if Name.upper() == 'ALL' or Name.upper() == '':
                        unvclass=UM.UniverseClass(self.versionID,'ALL',ClassName)
                    else:
                        unvclass=UM.UniverseClass(self.versionID,Name,ClassName)
                    
                    unvclass._getPropertiesFromXlsx(xlsxDict)
                    self.universeClasses[unvclass.universeClassName]=unvclass

        for Name, Values in xlsxDict['unvJoins'].iteritems():
            if Name not in self.universeExtensions.keys():
                for join, properties in Values.iteritems():
                    sourcecolumn = properties['SOURCECOLUMN']
                    sourcetable = properties['SOURCETABLE']
                    targetcolumn = properties['TARGETCOLUMN']
                    targettable = properties['TARGETTABLE']
                    if Name.upper() == 'ALL' or Name.upper() == '':
                        unvJoin=UM.UniverseJoin(self.versionID,'ALL',sourcecolumn,sourcetable,targetcolumn,targettable,str(int(join) - 1))
                    else:
                        unvJoin=UM.UniverseJoin(self.versionID,Name,sourcecolumn,sourcetable,targetcolumn,targettable,str(int(join) - 1))
                    
                    unvJoin._getPropertiesFromXlsx(properties)
                    self.universeJoins[unvJoin.getJoinId()]=unvJoin
        
                   
    def _toXLSX(self, xlsxFile, workbook):
        ''' Converts the object to an excel document
        
        Parent toXLSX() method is responsible for triggering child object toXLSX() methods
        '''
                
        for table in self.universeTables.itervalues():
            table._toXLSX(xlsxFile, workbook)
            
        for uniclass in self.universeClasses.itervalues():
            uniclass._toXLSX(xlsxFile, workbook)
        
        for join in self.universeJoins.itervalues():
            join._toXLSX(xlsxFile, workbook)
        
        if len(self.universeExtensions) != 0:   
            for ext in self.universeExtensions.itervalues():
                ext._toXLSX(xlsxFile, workbook)
        else:
            sheet = workbook.getSheet('Universe')
            rowNumber = sheet.getLastRowNum() + 1
            xlsxFile.writeToWorkbook(sheet, rowNumber, xlsxFile.findValue(sheet, 'UNVNAME').getColumnIndex(), self.universeName)
            xlsxFile.writeToWorkbook(sheet, rowNumber, xlsxFile.findValue(sheet, 'UNVEXTENSION').getColumnIndex(), 'ALL')
            
    def _getPropertiesFromXML(self,xmlElement):
        '''Populates the objects content from an xmlElement.
            
            The method is also responsible for triggering its child objects getPropertiesFromXML() method'''
        for elem in xmlElement:
            tmpCounter = 0
            if elem.tag == 'UniverseExtensions':
                for elem1 in elem:
                    if elem1.tag == 'UniverseExtension':
                        unvExtension= UM.UniverseExtension(self.versionID,self.universeName,elem1.attrib['name'],Utils.unescape(elem1.attrib['ExtensionName']))
                        tmpCounter=unvExtension._getPropertiesFromXML(elem1,tmpCounter)
                        self.universeExtensions[elem1.attrib['name']] = unvExtension
                    
            if elem.tag == 'UniverseTables':
                for elem1 in elem:
                    if elem1.tag == 'UniverseTable':
                        unvTable = UM.UniverseTable(self.versionID,elem1.attrib['extension'],elem1.attrib['name'])
                        unvTable._getPropertiesFromXML(elem1)
                        self.universeTables[elem1.attrib['name']] = unvTable
            if elem.tag == 'UniverseClasses':
                for elem1 in elem:
                    if elem1.tag == 'UniverseClass':
                        unvClass = UM.UniverseClass(self.versionID,elem1.attrib['extension'],elem1.attrib['name'])
                        unvClass._getPropertiesFromXML(elem1)
                        self.universeClasses[elem1.attrib['name']] =  unvClass
            if elem.tag == 'UniverseJoins':
                for elem1 in elem:
                    if elem1.tag == 'UniverseJoin':
                        unvJoin = UM.UniverseJoin(self.versionID,'ALL',elem1.attrib['sourceColumn'],elem1.attrib['sourceTable'],elem1.attrib['targetColumn'],elem1.attrib['targetTable'],tmpCounter)                        
                        unvJoin._getPropertiesFromXML(elem1)
                        self.universeJoins[unvJoin.getJoinId()] = unvJoin
                        tmpCounter += 1
    
    def _toXML(self,indent=0):
        offset = '    '
        os = "\n" + offset*indent

        outputXML = os +'<UniverseExtensions>'
        for unvExt in self.universeExtensions:
            outputXML += self.universeExtensions[unvExt]._toXML(indent+1)
        outputXML += os +'</UniverseExtensions>'
        outputXML += os +'<UniverseTables>'
        for unvTable in self.universeTables:
            outputXML += str(self.universeTables[unvTable]._toXML(indent+1))
        outputXML += os +'</UniverseTables>'
        outputXML += os +'<UniverseClasses>'           
        for unvClass in self.universeClasses:
            outputXML += self.universeClasses[unvClass]._toXML(indent+1)
        outputXML += os +'</UniverseClasses>' 
        outputXML += os +'<UniverseJoins>'
        for unvJoin in self.universeJoins:
            outputXML += self.universeJoins[unvJoin]._toXML(indent+1)
        outputXML += os +'</UniverseJoins>'
        return outputXML

    def populateRepDbDicts(self):
        RepDbDict = {}
        RepDbDict['UNIVERSEEXTENSION']= ''
        RepDbDict['VERSIONID']=self.versionID
        RepDbDict['UNIVERSENAME']=self.universeName
        RepDbDict['UNIVERSEEXTENSIONNAME']=''

        return RepDbDict

    def difference(self,UniObj,deltaObj=None):
        if deltaObj is None:
            deltaObj = Utils.Delta(self.name,UniObj.universeName)
            
        ################################################################
        # Universe Extension Diff
        Delta = Utils.DictDiffer(self.universeExtensions,UniObj.universeExtensionObjects)
        deltaObj.location.append('UniverseExtension')
        for item in Delta.added():
            deltaObj.addChange('<Added>', UniObj.universeExtensionObjects[item].universeExtension, '', UniObj.universeExtensionObjects[item].universeExtensionName)
      
        for item in Delta.removed():
            deltaObj.addChange('<Removed>', self.universeExtensions[item].universeExtension, self.universeExtensions[item].universeExtensionName, '')
        
        deltaObj.location.pop()
        
        for item in Delta.common():
            deltaObj.location.append('UniverseExtension='+item)
            deltaObj = self.universeExtensions[item].difference(UniObj.universeExtensionObjects[item],deltaObj)
            deltaObj.location.pop() 
            
        ################################################################
        # Universe Class Diff
        Delta = Utils.DictDiffer(self.universeClasses,UniObj.universeClassObjects)
        deltaObj.location.append('UniverseClass')
        for item in Delta.added():
            deltaObj.addChange('<Added>', UniObj.universeClassObjects[item].universeClassName, '', item)
      
        for item in Delta.removed():
            deltaObj.addChange('<Removed>', self.universeClasses[item].universeClassName, item, '')
        
        deltaObj.location.pop()
        
        for item in Delta.common():
            deltaObj.location.append('UniverseClass='+item)
            deltaObj = self.universeClasses[item].difference(UniObj.universeClassObjects[item],deltaObj)
            deltaObj.location.pop() 
        
        ################################################################
        # Universe Table Diff
        Delta = Utils.DictDiffer(self.universeTables,UniObj.universeTableObjects)
        deltaObj.location.append('UniverseTable')
        for item in Delta.added():
            deltaObj.addChange('<Added>', UniObj.universeTableObjects[item].tableName, '', item)
      
        for item in Delta.removed():
            deltaObj.addChange('<Removed>', self.universeTables[item].tableName, item, '')
        
        deltaObj.location.pop()
        
        for item in Delta.common():
            deltaObj.location.append('UniverseTable='+item)
            deltaObj = self.universeTables[item].difference(UniObj.universeTableObjects[item],deltaObj)
            deltaObj.location.pop()  
        
        
        ################################################################
        # Universe Joins Diff
        Delta = Utils.DictDiffer(self.universeJoins,UniObj.universeJoinObjects)
        deltaObj.location.append('UniverseJoin')
        for item in Delta.added():
            deltaObj.addChange('<Added>', UniObj.universeJoinObjects[item].joinID, '', item)
      
        for item in Delta.removed():
            deltaObj.addChange('<Removed>', self.universeJoins[item].joinID, item, '')
        
        deltaObj.location.pop()
        
        for item in Delta.common():
            deltaObj.location.append('UniverseJoin='+item)
            deltaObj = self.universeJoins[item].difference(UniObj.universeJoinObjects[item],deltaObj)
            deltaObj.location.pop()   
        
        return deltaObj