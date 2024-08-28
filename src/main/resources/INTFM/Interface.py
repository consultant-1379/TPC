'''
Created on May 31, 2016

@author: ebrifol
'''

import Utils
from copy import deepcopy
from java.io import File, FileOutputStream
from org.apache.poi.xssf.usermodel import XSSFWorkbook

class InterfaceVersion(object):
    '''Class to represent a version of an Interface'''
       
    def __init__(self,logger,intfName=None,intfVersion=None):        
        if (intfName == None and intfVersion !=None) or (intfName != None and intfVersion == None):
            raise TypeError("Cant set one and not the other")
        if intfName == None and intfVersion == None:
            self.name = 'UNINITIALISED'
            self.intfVersion = '0'     
        else:
            self.name = intfName
            self.intfVersion = intfVersion
            
            
        self.intfVersionID = self.name  + ":" + self.intfVersion
        self.versioning = Utils.odict()
        self.dependencies = Utils.odict()
        self.intfConfig = Utils.odict()
        self.intfTechpacks = Utils.odict()
        self.log = logger
    
    def _intialiseVersion(self,intfName,intfVersion):
        self.name = intfName
        self.intfVersion = intfVersion
        self.intfVersionID = self.name  + ":" + self.intfVersion
    
    def getPropertiesFromServer(self,DbCursorRep, DbCursorEtl):
        '''Get the properties of the techpack version object from the server'''    
        
        self._getVersioning(DbCursorRep)
        self._getInterfaceConfig(DbCursorEtl)
        self._getDependencies(DbCursorRep)
        self._getTechpacks(DbCursorRep)
    
    def _getVersioning(self,DbCursor):
        '''Populates the versioning dictionary for the interface version'''
        DbCursor.execute("SELECT * FROM DataInterface WHERE INTERFACENAME=? AND INTERFACEVERSION=?", (self.name,self.intfVersion,))
        desc = DbCursor.description
        row = DbCursor.fetchone()
        if row is not None:
            self.versioning = {}
            i = 0
            for x in desc:
                value = str(row[i])
                if x[0] != 'STATUS' and x[0] != 'INTERFACENAME':
                    if value != None and value != 'None':
                        self.versioning[x[0]] = value
                i+=1   

    def _getDependencies(self,DbCursor):
        '''Populates the dependencies dictionary for the interface version'''
        DbCursor.execute("SELECT TECHPACKNAME,TECHPACKVERSION FROM InterfaceDependency WHERE INTERFACENAME=? AND INTERFACEVERSION=?", (self.name,self.intfVersion,))
        for res in DbCursor.fetchall():
            tpName=str(res[0])
            tpVersion=str(res[1])
            self.dependencies[tpName] = tpVersion
    
    def _getTechpacks(self,DbCursor):
        '''Populate the intfTechpacks dictionary for the interface version. This is the list
        of techpacks that the interface can install'''
        DbCursor.execute("SELECT TECHPACKNAME,TECHPACKVERSION FROM InterfaceTechpacks WHERE INTERFACENAME =? AND INTERFACEVERSION=?", (self.name,self.intfVersion,))
        res = DbCursor.fetchall()
        if res:
            for row in res:
                tpName = str(row[0])
                tpVersion = str(row[1])
                self.intfTechpacks[tpName] = tpVersion
                
    def _getInterfaceConfig(self,DbCursor):
        '''Populate the intfConfig dictionary with configuration parameters for the interface version
        Dictionary is dynamically created as parameters can differ in number from interface to interface'''
        
        DbCursor.execute("SELECT COLLECTION_SET_ID FROM META_COLLECTION_SETS WHERE COLLECTION_SET_NAME = ? AND VERSION_NUMBER =?",(self.name,self.intfVersion,))
        etlrepCollectionSetID = str(DbCursor.fetchone()[0]) 
        
        DbCursor.execute("SELECT ACTION_CONTENTS_01 from META_TRANSFER_ACTIONS WHERE COLLECTION_SET_ID =? AND ACTION_TYPE = 'Parse'",(etlrepCollectionSetID,))
        config_list = DbCursor.fetchone()[0].replace('\r', '\n')
        config_list = config_list.rsplit('\n')[2:]
        for item in config_list:
            if item != '' and not item.startswith('#'):
                kvp = item.split("=",1)
                param = kvp[0]
                action = ''
                try:
                    action = kvp[1]
                except:
                    pass
                self.intfConfig[param]= action
        
        values = []
        DbCursor.execute("SELECT NAME, INTERVAL_HOUR, INTERVAL_MIN, SCHEDULING_HOUR, SCHEDULING_MIN from META_SCHEDULINGS WHERE COLLECTION_SET_ID =?",(etlrepCollectionSetID,))
        resultset = DbCursor.fetchall()
        for row in resultset:
            if 'TriggerAdapter_' in row[0]:
                for value in row:
                    if '.0' in str(value):
                        item = Utils.strFloatToInt(value)
                        if item == '0':
                            item = '00'
                        values.append(item)
                self.intfConfig['AS_Interval']= values[0] + ',' + values[1]
                self.intfConfig['AS_SchBaseTime']= values[2] + ',' + values[3]
             
        if 'outDir' in self.intfConfig:
            elementType = self.intfConfig['outDir'].split('/')
            elementType = elementType[len(elementType)-2]
            self.versioning['ELEMTYPE'] = elementType
    
    def toXLSX(self, outputPath):
        ''' Converts the object to an excel document
        
        Parent toXLSX() method is responsible for triggering child object toXLSX() methods
        '''
        
        workbookPath = outputPath + '\\' + self.name + '_' + str(self.intfVersion) + '_' + self.versioning['RSTATE'] + '_TEST.xlsx'
        workbook = XSSFWorkbook()
        
        xlsxFile = Utils.XlsxFile()
        workbook = xlsxFile.createXlsDoc(workbook, 'INTF')
        sheet = workbook.getSheet('Interface')
        cellNumber = sheet.getRow(0).getLastCellNum()
        
        xlsxFile.writeToWorkbook(sheet, xlsxFile.findValue(sheet, 'NAME').getRowIndex(), cellNumber, self.intfVersionID)
        
        self.log.info('Interface common information')
        for FDColumn in xlsxFile.InterfaceList:
            if FDColumn in self.versioning.keys():
                value = self.versioning[FDColumn]
                xlsxFile.writeToWorkbook(sheet, xlsxFile.findValue(sheet, FDColumn).getRowIndex(), cellNumber, str(value))
            if FDColumn == 'DEPENDENCIES':
                value = ','.join(['%s:%s' % (key, value) for (key, value) in self.dependencies.items()])
                xlsxFile.writeToWorkbook(sheet, xlsxFile.findValue(sheet, FDColumn).getRowIndex(), cellNumber, value)
            if FDColumn == 'INTFTECHPACKS':
                value = ','.join(['%s:%s' % (key, value) for (key, value) in self.intfTechpacks.items()])
                xlsxFile.writeToWorkbook(sheet, xlsxFile.findValue(sheet, FDColumn).getRowIndex(), cellNumber, value)
                    
        self.log.info('Interface specific information')
        for Parameter, value in self.intfConfig.iteritems():
            paramCell = xlsxFile.findValue(sheet, Parameter)
            if paramCell == None:
                paramRow = sheet.getLastRowNum() + 1
                xlsxFile.writeToWorkbook(sheet, paramRow, 0, Parameter)
            else:
                paramRow = paramCell.getRowIndex()
                
            xlsxFile.writeToWorkbook(sheet, paramRow, cellNumber, Utils.strFloatToInt(value))
        
        self.log.info('Writing to file for ' + self.name)
        workbook.write(FileOutputStream(workbookPath))
    
    def toXML(self,offset=0):
        '''Write the object to an xml formatted string
        
        Offset value is used for string indentation. Default to 0
        Parent toXML() method is responsible for triggering child object toXML() methods.

        Return Value: xmlString 
        '''
        offset += 4
        os = "\n" + " "*offset
        os2 = os+" "*offset
        os3 = os2+" "*offset
        os4 = os3+" "*offset
        outputXML = os2+'<Interface name="' + self.name + '" version="' + self.intfVersion + '">'
        outputXML +=os3+ '<Versioning>'
        for item in sorted(self.versioning.iterkeys()):
            outputXML += os4+'<'+str(item)+'>'+ str(self.versioning[item]) +'</'+str(item)+'>'
        outputXML += os3+'</Versioning>'
        outputXML += os3+'<Dependencies>'
        for item in sorted(self.dependencies.iterkeys()):
            outputXML += os4+'<'+str(item)+'>'+ self.dependencies[item] +'</'+str(item)+'>'
        outputXML += os3+'</Dependencies>'
        outputXML += os3+'<Techpacks>'
        for item in sorted(self.intfTechpacks.iterkeys()):
            outputXML += os4+'<'+str(item)+'>'+ self.intfTechpacks[item] +'</'+str(item)+'>'
        outputXML += os3+'</Techpacks>'
        outputXML += os3+'<Configuration>'
        for item in sorted(self.intfConfig.iterkeys()):
            outputXML += os4+'<'+Utils.escape(str(item))+'>'+ Utils.escape(str(self.intfConfig[item])) +'</'+Utils.escape(str(item))+'>'
        outputXML += os3+'</Configuration>'
        outputXML += os2+'</Interface>'

        return outputXML
    
    def getPropertiesFromXML(self,xmlElement):
        '''Populates the objects content from an xmlElement.
            
            The method is also responsible for triggering its child objects getPropertiesFromXML() method'''
        
        self._intialiseVersion(xmlElement.attrib['name'], xmlElement.attrib['version'])
        for element in xmlElement:
            if element.tag == 'Versioning':
                for elem1 in element:
                    self.versioning[elem1.tag] = Utils.safeNull(elem1.text)
            elif element.tag == 'Dependencies':
                for elem1 in element:
                    self.dependencies[elem1.tag]= Utils.safeNull(elem1.text)
            elif element.tag == 'Techpacks':
                for elem1 in element:
                    self.intfTechpacks[elem1.tag]= Utils.safeNull(elem1.text)
            elif element.tag == 'Configuration':
                for elem1 in element:
                    self.intfConfig[Utils.unescape(elem1.tag)] = Utils.unescape(Utils.safeNull(elem1.text))
            else:
                raise "Error, tag type %s not recognised." % element.tag
            
    def getPropertiesFromXls(self,xlsDict=None,filename=None):
        '''Populate the objects contents from a XlsDict object or xls file.
        
        If a xls file is passed it is converted to a XlsDict object before processing.

        Exceptions: 
                   Raised if XlsDict and filename are both None (ie nothing to process)
        '''
        intfName = ''
        for Name, Value in xlsDict.iteritems():
        	if Name == 'NAME':
        		intfName = Value
        		break
        if intfName != '':
        	iname = intfName[:intfName.index('(')-1]
        	iversion = intfName[intfName.index(':') + 1:]
        	self._intialiseVersion(iname, iversion)

        if xlsDict==None and filename==None:
            strg = 'getPropertiesFromXls() Nothing to Process'
            raise Exception(strg)
        else:
            if filename is not None:
                xlsDict = Utils.XlsDict(filename).returnXlsDict()
                
            for Name, Value in xlsDict.iteritems():
                if Name == 'dependencies':
                    deps = xlsDict['dependencies'] + ','
                    entries = deps.split(',')
                    for item in entries:
                        tp = item.split(':')
                        if tp[0] != '':
                            self.dependencies[tp[0]] = tp[1]
                        
                elif Name == 'intfConfig':
                    for key, value in xlsDict['intfConfig'].iteritems():
                        if value != '':
                            self.intfConfig[key.strip('\n\r')] = value
                        
                elif Name == 'intfTechpacks':
                    deps = xlsDict['intfTechpacks'] + ','
                    entries = deps.split(',')
                    for item in entries:
                        tp = item.split(':')
                        if tp[0] != '':
                            self.intfTechpacks[tp[0]] = tp[1]
                        
                else:
                    self.versioning[Name] = Value
    
    def getPropertiesFromXlsx(self,xlsxDict):
        '''Populate the objects contents from a XlsxDict object.
        
        Exceptions: 
                   Raised if XlsDict and filename are both None (ie nothing to process)
        '''
        intfName = ''
        for Name, Value in xlsxDict.iteritems():
        	if Name == 'NAME':
        		intfName = Value
        		break
        if intfName != '':
        	iname = intfName[:intfName.index('(')-1]
        	iversion = intfName[intfName.index(':') + 1:]
        	self._intialiseVersion(iname, iversion)

        if xlsxDict==None:
            raise Exception('Nothing to process')
        
        for Name, Value in xlsxDict.iteritems():
            if Name == 'DEPENDENCIES':
                deps = xlsxDict['DEPENDENCIES'] + ','
                entries = deps.split(',')
                for item in entries:
                    tp = item.split(':')
                    if tp[0] != '':
                        self.dependencies[tp[0]] = tp[1]
                    
            elif Name == 'intfConfig':
                for key, value in xlsxDict['intfConfig'].iteritems():
                    if value != '':
                        self.intfConfig[key.strip('\n\r')] = value
                    
            elif Name == 'INTFTECHPACKS':
                deps = xlsxDict['INTFTECHPACKS'] + ','
                entries = deps.split(',')
                for item in entries:
                    tp = item.split(':')
                    if tp[0] != '':
                        self.intfTechpacks[tp[0]] = tp[1]
                    
            else:
                self.versioning[Name] = Value
            
    def getPropertiesFromTPI(self,tpiDict=None,filename=None):
        '''Populate the objects contents from a tpiDict object or tpi file.
        
        If a tpi file is passed it is converted to a tpiDict object before processing.

        Exceptions: 
                   Raised if tpiDict and filename are both None (ie nothing to process)
                   Raised if there is a tpi dict key error'''
                   

        methodsDict = {'Datainterface' : self._tpiDataInterface,
                'Interfacedependency' : self._tpiInterfaceDependency,
                'Interfacetechpacks' : self._tpiInterfaceTechpacks,
                'META_TRANSFER_ACTIONS' : self._tpiMetaTransferActions,
        }
            
        if tpiDict==None and filename==None:
            strg = 'getPropertiesFromTPI() Nothing to Process'
            raise Exception(strg)
        else:
            if filename is not None:
                tpiDict = Utils.TpiDict(filename).returnTPIDict()
            for key in tpiDict:
                try:
                    if key in methodsDict:
                        methodsDict.get(key)(tpiDictionary=tpiDict)
                except Exception as err:
                    strg  = 'getPropertiesFromTPI() tpi dict key error = ' + key
                    self.log.error('Error at - ' + err)
                    self.log.error(strg)
                    raise Exception(strg)
                    
                    
    def _tpiDataInterface(self, tpiDictionary):
        self.log.info('Data Interface')
        self.name = tpiDictionary['Datainterface']['INTERFACENAME'][1]
        self.intfVersion = tpiDictionary['Datainterface']['INTERFACEVERSION'][1]
        self.intfVersionID = self.name  + ":" + self.intfVersion
        
        for column in tpiDictionary['Datainterface']:
            self.versioning[column] = tpiDictionary['Datainterface'][column][1]

    def _tpiInterfaceDependency(self, tpiDictionary):
        self.log.info('Interface Dependency')
        for row in tpiDictionary['Interfacedependency']['INTERFACENAME']:
            for row2 in tpiDictionary['Interfacedependency']['INTERFACEVERSION']:
                self.dependencies[tpiDictionary['Interfacedependency']['TECHPACKNAME'][row]] = tpiDictionary['Interfacedependency']['TECHPACKVERSION'][row]      

    def _tpiInterfaceTechpacks(self, tpiDictionary):
        self.log.info('Interface Techpacks')
        for row in tpiDictionary['Interfacetechpacks']['INTERFACENAME']:
            self.intfTechpacks[tpiDictionary['Interfacetechpacks']['TECHPACKNAME'][row]] = tpiDictionary['Interfacetechpacks']['TECHPACKVERSION'][row]
            
    def _tpiMetaTransferActions(self, tpiDictionary):          
        '''Reading Interface sets in model'''
        self.log.info('Interface Sets')
        for row in tpiDictionary['META_TRANSFER_ACTIONS']['ACTION_CONTENTS']:
            if tpiDictionary['META_TRANSFER_ACTIONS']['ACTION_TYPE'][row]=="Parse":
                configs =  tpiDictionary['META_TRANSFER_ACTIONS']['ACTION_CONTENTS'][row]
                configs = Utils.unescape(configs)
                config_list = configs.rsplit() # split to list on newline
                config_list = config_list[2:]
                for line in config_list:
                    my_list = line.split(';')
                    for line in my_list:
                        if '=' in line:
                            line = line.lstrip(';')
                            line = line.strip('&#xD')
                            line = line.strip('&#xA')
                            param,action = line.split("=",1) # split the parameters and actions on first equals
                            try:
                                isInt = int(param)
                                continue
                            except ValueError:
                                pass
                            self.intfConfig[param]= action
                            
        for rows in tpiDictionary['META_SCHEDULINGS']['NAME']:
            if tpiDictionary['META_SCHEDULINGS']['NAME'][rows].startswith('TriggerAdapter_'):
                intHour = tpiDictionary['META_SCHEDULINGS']['INTERVAL_HOUR'][rows]
                intMin = tpiDictionary['META_SCHEDULINGS']['INTERVAL_MIN'][rows]
                schHour = tpiDictionary['META_SCHEDULINGS']['SCHEDULING_HOUR'][rows]
                schMin = tpiDictionary['META_SCHEDULINGS']['SCHEDULING_MIN'][rows]
                self.intfConfig['AS_Interval'] = intHour + ',' + intMin
                self.intfConfig['AS_SchBaseTime'] = schHour + ',' + schMin
        
        if 'outDir' in self.intfConfig:
            elementType = self.intfConfig['outDir'].split('/')
            elementType = elementType[len(elementType)-2]
            self.versioning['ELEMTYPE'] = elementType
    
    def populateRepDbDicts(self):
        intfTechpacks = []
        for tpName, Rstate in self.intfTechpacks.iteritems():
            intfTechpack = {}
            intfTechpack['INTERFACENAME'] = self.name
            intfTechpack['INTERFACEVERSION'] = self.intfVersion
            intfTechpack['TECHPACKNAME'] = tpName
            intfTechpack['TECHPACKVERSION'] = Rstate
            intfTechpacks.append(intfTechpack)
        
        Dependencies = []
        for tpName, Rstate in self.dependencies.iteritems():
            dependency = {}
            dependency['INTERFACENAME'] = self.name
            dependency['INTERFACEVERSION'] = self.intfVersion
            dependency['TECHPACKNAME'] = tpName
            dependency['TECHPACKVERSION'] = Rstate
            Dependencies.append(dependency)
            
        Datainterface = deepcopy(self.versioning)
        Datainterface['INTERFACENAME'] = self.name
        Datainterface['STATUS'] = '1'
        Datainterface['INTERFACEVERSION'] = self.intfVersion
        Datainterface['PRODUCTNUMBER'] = ''
        Datainterface['INSTALLDESCRIPTION'] = ''
        
        setsDict = {}
        setsDict['intfConfig'] = deepcopy(self.intfConfig)
        setsDict['INTERFACENAME'] = self.name
        setsDict['INTERFACEVERSION'] = self.intfVersion
        setsDict['INTERFACETYPE'] = self.versioning['INTERFACETYPE']
        setsDict['DATAFORMATTYPE'] = self.versioning['DATAFORMATTYPE']
        if 'ELEMTYPE' in self.versioning:
            setsDict['ELEMTYPE'] = self.versioning['ELEMTYPE']
        else:
            setsDict['ELEMTYPE'] = self.intfTechpacks.keys()[0]
        

        return intfTechpacks, Dependencies, Datainterface, setsDict
        
    
    def difference(self,intfVerObject):
        '''Calculates the difference between two external interface version objects
            
            Method takes intfVerObject,deltaObj and deltaTPV as inputs.
            intfVerObject: The interface version to be compared against
            DeltaObj: The single object that gets passed through the entire diff recording the changes.
            DeltaTPV: A TechPackVersion Object that gets passed through the entire diff recording only new content.
            
            The Difference method will trigger the difference method of its child objects, passing
            in the object to compare, deltaObj and deltaTPV. After calculating the diff the child object passes these objects
            back in conjunction with a flag to say whether a (only new or changed content.. not deleted) was found or not. This flag is used to decide
            whether a child object should be added to the parent object in the DeltaTPV.
            
            Note: Interface Version does not have any child objects
            
            Returns:
                    diffFlag (Boolean indicating where a change was found or not)
                    deltaObj
                    deltaTPV 
        '''        
        
        deltaObj = Utils.Delta(self.intfVersionID,intfVerObject.intfVersionID)
        
        #########################################################################################################################################
        # Versioning diff
        Delta = Utils.DictDiffer(self.versioning,intfVerObject.versioning)
        excludedProperties = ['LOCKDATE', 'INTERFACEVERSION', 'LOCKEDBY', 'ENIQ_LEVEL', 'STATUS', 'INSTALLDESCRIPTION', 'ELEMTYPE', 'PRODUCTNUMBER']
        deltaObj.location.append('Versioning')
        for item in Delta.changed():
            if item not in excludedProperties:
                deltaObj.addChange('<Changed>', item, self.versioning[item], intfVerObject.versioning[item])
        
        for item in Delta.added():
            if item not in excludedProperties:
                deltaObj.addChange('<Added>', item, '', intfVerObject.versioning[item])
                
        for item in Delta.removed():
            if item not in excludedProperties:
                deltaObj.addChange('<Removed>', item, self.versioning[item], '')

        deltaObj.location.pop()
        
        #########################################################################################################################################
        # Dependencies diff
        Delta = Utils.DictDiffer(self.dependencies,intfVerObject.dependencies)
        deltaObj.location.append('Dependencies')
        for item in Delta.changed():
            deltaObj.addChange('<Changed>', item, self.dependencies[item], intfVerObject.dependencies[item])
        
        for item in Delta.added():
            deltaObj.addChange('<Added>', item, '', intfVerObject.dependencies[item])
                
        for item in Delta.removed():
            deltaObj.addChange('<Removed>', item, self.dependencies[item], '')

        deltaObj.location.pop()
        
        #########################################################################################################################################
        # IntfConfig diff        
        Delta = Utils.DictDiffer(self.intfConfig,intfVerObject.intfConfig)
        deltaObj.location.append('IntfConfig')
        for item in Delta.changed():
            deltaObj.addChange('<Changed>', item, self.intfConfig[item], intfVerObject.intfConfig[item])
        
        for item in Delta.added():
            deltaObj.addChange('<Added>', item, '', intfVerObject.intfConfig[item])
                
        for item in Delta.removed():
            deltaObj.addChange('<Removed>', item, self.intfConfig[item], '')

        deltaObj.location.pop()
        
        #########################################################################################################################################
        # IntfTechPacks diff        
        Delta = Utils.DictDiffer(self.intfTechpacks,intfVerObject.intfTechpacks)
        deltaObj.location.append('IntfConfig')
        for item in Delta.changed():
            deltaObj.addChange('<Changed>', item, self.intfTechpacks[item], intfVerObject.intfTechpacks[item])
        
        for item in Delta.added():
            deltaObj.addChange('<Added>', item, '', intfVerObject.intfTechpacks[item])
                
        for item in Delta.removed():
            deltaObj.addChange('<Removed>', item, self.intfTechpacks[item], '')

        deltaObj.location.pop()
        
        return deltaObj  