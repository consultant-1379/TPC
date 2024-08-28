'''
Created on May 30, 2016

@author: ebrifol
'''

import TPM
import Utils

class BusyHour(object):
    '''Class to represent Busy Hour object associated with a techpack version.
    Uniquely identified by the Busy Hour object name and the techpack versionID.'''


    def __init__(self,versionID,name):
        self.versionID = versionID
        self.name = name
        self.supportedTables = []
        self.rankingTable = ''
        self.busyHourPlaceHolders = Utils.odict() 
    
    def _getPropertiesFromServer(self,DbCursor):
        '''Get the properties associated with the busy hour object'''
        self._getBusyHourPlaceHolders(DbCursor)
        self._getBusyHourSupportedTables(DbCursor)
        self._getBusyHourRankingTable(DbCursor)
        
    def _getBusyHourPlaceHolders(self,DbCursor):
        '''Gets the busyHour type information for the busy hour object
           
           This function will populate the busyHourPlaceHolders dictionary with child BusyHour placeholders
           
           SQL Executed: 
                       SELECT BHTYPE FROM dwhrep.BUSYHOUR where VERSIONID=? AND BHOBJECT=?
        
           '''
        DbCursor.execute("SELECT BHTYPE FROM BUSYHOUR where VERSIONID=? AND BHOBJECT=?",(self.versionID,self.name,))
        resultset = DbCursor.fetchall()
        for row in resultset:
            bt = TPM.BusyHourPlaceHolder(self.versionID,self.name,row[0])
            bt._getPropertiesFromServer(DbCursor)
            self.busyHourPlaceHolders[str(row[0])] = bt
    
    def _getBusyHourSupportedTables(self,crsr):
        '''Gets the list of measurement tables which load for (support) the busy hour object'''
        if self.name == 'ELEM':
            crsr.execute("SELECT DISTINCT TYPENAME FROM MeasurementType where VERSIONID=? AND ELEMENTBHSUPPORT like ? AND RANKINGTABLE =?",(self.versionID,'1','0',))
        else:
            crsr.execute("SELECT DISTINCT BHTARGETTYPE FROM BUSYHOURMAPPING where VERSIONID=? AND BHOBJECT=?",(self.versionID,self.name,))
            resultset = crsr.fetchall()
            for row in resultset:
                self.supportedTables.append(str(row[0]))
        
    def _getBusyHourRankingTable(self,crsr):
        '''Gets the Ranking Table associated with the busyhour object'''
        if self.name == 'ELEM':
            self.rankingTable = self.versionID.rsplit(':')[0] + "_ELEMBH"
        else:
            crsr.execute("SELECT DISTINCT BHLEVEL FROM BUSYHOURMAPPING where VERSIONID=? AND BHOBJECT=?",(self.versionID,self.name,))
            row = crsr.fetchone()
            if row is not None:
                self.rankingTable = str(row[0])
    
    def _getPropertiesFromTPI(self,tpiDict=None,filename=None):
        '''Populate the objects contents from a tpiDict object or tpi file.
        
        If a tpi file is passed it is converted to a tpiDict object before processing
        
        Exceptions: 
                   Raised if tpiDict and filename are both None (ie nothing to process)'''
        
        if tpiDict==None and filename==None:
            strg = 'getPropertiesFromTPI() Nothing to Process'
            raise Exception(strg)
        else:
            if filename is not None:
                tpiDict = Utils.TpiDict(filename).returnTPIDict()
            for row in tpiDict['Busyhour']['BHOBJECT']:
                if tpiDict['Busyhour']['BHOBJECT'][row] == self.name:
                    bht = TPM.BusyHourPlaceHolder(self.versionID,self.name,tpiDict['Busyhour']['BHTYPE'][row])
                    bht._getPropertiesFromTPI(tpiDict)
                    self.busyHourPlaceHolders[tpiDict['Busyhour']['BHTYPE'][row]] = bht            
            if 'Busyhourmapping' in tpiDict:         
                for row in tpiDict['Busyhourmapping']['BHOBJECT']:
                    if tpiDict['Busyhourmapping']['BHOBJECT'][row] == self.name: 
                        if tpiDict['Busyhourmapping']['BHTARGETTYPE'][row] not in self.supportedTables:
                            self.supportedTables.append(tpiDict['Busyhourmapping']['BHTARGETTYPE'][row])  
            if self.name == 'ELEM':
                self.rankingTable = self.versionID.rsplit(':')[0] + "_ELEMBH"
                
                for row in tpiDict['Measurementtype']['TYPEID']:
                    if tpiDict['Measurementtype']['RANKINGTABLE'][row] == '0' and tpiDict['Measurementtype']['ELEMENTBHSUPPORT'][row] == '1':
                        self.supportedTables.append(tpiDict['Measurementtype']['TYPENAME'][row])

            else:    
                if 'Busyhourmapping' in tpiDict:
                    for row in tpiDict['Busyhourmapping']['BHOBJECT']:
                        if tpiDict['Busyhourmapping']['BHOBJECT'][row] == self.name: 
                            if tpiDict['Busyhourmapping']['BHLEVEL'][row] not in self.supportedTables:
                                self.rankingTable = tpiDict['Busyhourmapping']['BHLEVEL'][row]
    
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
            
            if self.name in xlsDict['BHOBJECT']:
                for Name, Values in xlsDict['BHOBJECT'][self.name].iteritems():
                    att = TPM.BusyHourPlaceHolder(self.versionID,self.name,Name)
                    att._getPropertiesFromXls(Values)
                    self.busyHourPlaceHolders[Name] = att
    
    def _getPropertiesFromXlsx(self,xlsxDict):
        '''Populate the objects contents from a XlsxDict object.
        
        Exceptions: 
                   Raised if XlsDict and filename are both None (ie nothing to process)
        '''
        
        if self.name in xlsxDict['BH']:
            for Name, Values in xlsxDict['BH'][self.name].iteritems():
                att = TPM.BusyHourPlaceHolder(self.versionID, self.name, Name)
                att._getPropertiesFromXlsx(xlsxDict)
                self.busyHourPlaceHolders[Name] = att
    
    def _toXLSX(self, xlsxFile, workbook):
        ''' Converts the object to an excel document
        
        Parent toXLSX() method is responsible for triggering child object toXLSX() methods
        '''
        
        sheet = workbook.getSheet('Fact Tables')
        
        if self.name != 'ELEM':
            for tableName in self.supportedTables:
                #print tableName
                cellNumber = xlsxFile.findValue(sheet, 'OBJECTBH').getColumnIndex()
                rowNumber = xlsxFile.findValue(sheet, tableName).getRowIndex()
                
                try:
                    value = sheet.getRow(rowNumber).getCell(cellNumber).toString()
                except:
                    value = ''
                    
                if value != '' and value != None:
                    value = value + ','
                    
                xlsxFile.writeToWorkbook(sheet, rowNumber, cellNumber, value + self.name)
        
        xlsxFile.writeToWorkbook(sheet, xlsxFile.findValue(sheet, self.rankingTable).getRowIndex(), xlsxFile.findValue(sheet, 'OBJECTBH').getColumnIndex(), self.name)
        
        for BHT in self.busyHourPlaceHolders.itervalues():
            BHT._toXLSX(xlsxFile, workbook)
    
    def _getPropertiesFromXML(self,xmlElement):
        '''Populates the objects content from an xmlElement.
        
        The method is also responsible for triggering its child objects getPropertiesFromXML() method'''
        
        for elem in xmlElement:
            if elem.tag=='BusyHourObjectName':
                for elem1 in elem:
                    self.name = Utils.safeNull(elem1.text)
            if elem.tag=='RankingTable': 
                self.rankingTable = Utils.safeNull(elem.text)
            if elem.tag=='BusyHourSupportedTables':
                for elem3 in elem:
                        self.supportedTables.append(Utils.safeNull(elem3.text))
            if elem.tag== 'BusyHourPlaceholders':   
                for elem1 in elem:
                    bht = TPM.BusyHourPlaceHolder(self.versionID,self.name,elem1.attrib['name'])
                    bht._getPropertiesFromXML(elem1)
                    self.busyHourPlaceHolders[elem1.attrib['name']] = bht
    
    def _toXML(self,indent=0):
        '''Write the object to an xml formatted string
        
        Offset value is used for string indentation. Default to 0
        Parent toXML() method is responsible for triggering child object toXML() methods.

        Return Value: xmlString 
        '''
        
        offset = '    '
        os = "\n" + offset*indent
        os2 = os + offset
        os3 = os2 + offset
        
        outputXML = os+'<BusyHour name="' + str(self.name) +'">'
        outputXML += os2+'<RankingTable>'+ str(self.rankingTable) +'</RankingTable>'
        outputXML += os2+'<BusyHourSupportedTables>'  
        for table in self.supportedTables:  
                outputXML += os3+'<BHSupportedTable>'+ table +'</BHSupportedTable>'          
        outputXML += os2+'</BusyHourSupportedTables>'  
        outputXML += os2+'<BusyHourPlaceholders>' 
        for bhtype in self.busyHourPlaceHolders:
            outputXML += self.busyHourPlaceHolders[bhtype]._toXML(indent+2)
        outputXML += os2+'</BusyHourPlaceholders>'  
        outputXML += os2+'</BusyHour>'  
        return outputXML
    
    def difference(self,bhObject,deltaObj=None):
        '''Calculates the difference between two busy hour objects
        
        Method takes bhObject,deltaObj and deltaTPV as inputs.
        bhObject: The Busy Hour object to be compared against
        DeltaObj: The single object that gets passed through the entire diff recording the changes.
        DeltaTPV: A TechPackVersion Object that gets passed through the entire diff recording only new content.
        
        The Difference method will trigger the difference method of its child objects, passing
        in the object to compare, deltaObj and deltaTPV. After calculating the diff the child object passes these objects
        back in conjunction with a flag to say whether a (only new or changed content.. not deleted) was found or not. This flag is used to decide
        whether a child object should be added to the parent object in the DeltaTPV.
        
        Returns:
                diffFlag (Boolean indicating where a change was found or not)
                deltaObj
                deltaTPV 
        
        '''
        
        if deltaObj is None:
            deltaObj = Utils.Delta(self.name,bhObject.name)
        
        ################################################################
        # BH Rank Table Diff
        if self.rankingTable != bhObject.rankingTable:
            deltaObj.location.append('Rank Table')
            deltaObj.addChange('<Changed>', 'Properties', self.rankingTable, bhObject.rankingTable)
            deltaObj.location.pop()
        
        ################################################################
        # BH Support Tables Diff
        deltaObj.location.append('Supported Table')
        Delta = list(set(bhObject.supportedTables) - set(self.supportedTables))
        for table in Delta:
            deltaObj.addChange('<Added>', 'Properties', '', table)
        
        Delta = list(set(self.supportedTables) - set(bhObject.supportedTables))
        for table in Delta:
            deltaObj.addChange('<Removed>', 'Properties', table, '')
        
        deltaObj.location.pop()
        
        ################################################################
        # BH Type Diff
        Delta = Utils.DictDiffer(self.busyHourPlaceHolders,bhObject.busyHourPlaceHolders)
        deltaObj.location.append('BusyHourType')
        for item in Delta.added():
            deltaObj.addChange('<Added>', bhObject.busyHourPlaceHolders[item].name, '', item)
      
        for item in Delta.removed():
            deltaObj.addChange('<Removed>', self.busyHourPlaceHolders[item].name, item, '')
        
        deltaObj.location.pop()
        
        for item in Delta.common():
            deltaObj.location.append('BusyHourType='+item)
            deltaObj = self.busyHourPlaceHolders[item].difference(bhObject.busyHourPlaceHolders[item],deltaObj)
            deltaObj.location.pop()            
        
        return deltaObj
        
        
    def _createDefaultBusyHourTypes(self):
        '''Create the default ENIQ busy hour type objects associated with the Busy Hour Object'''
        
        customPlaceHolders = ['CP0','CP1','CP2','CP3','CP4']
        productPlaceHolders = ['PP0','PP1','PP2','PP3','PP4']
        
        for bhType in productPlaceHolders:   
            if bhType not in self.busyHourPlaceHolders:  
                bhTypeC = TPM.BusyHourPlaceHolder(self.versionID,self.name,bhType)
                bhTypeC._getDefaultProperties()
                self.busyHourPlaceHolders[bhType] = bhTypeC
                        
        for pholder in customPlaceHolders:
            bhTypeC = TPM.BusyHourPlaceHolder(self.versionID,self.name,pholder)
            bhTypeC._getDefaultProperties()
            self.busyHourPlaceHolders[pholder] = bhTypeC
    
    def populateRepDbDicts(self):
        objbhsupport = []
        if self.name != 'ELEM':
            for table in self.supportedTables:
                bhDict = {}
                bhDict['TYPEID'] = self.versionID + ":" +table
                bhDict['OBJBHSUPPORT'] = self.name
                objbhsupport.append(bhDict)
            
            bhDict = {}
            bhDict['TYPEID'] = self.versionID + ":" +self.rankingTable
            bhDict['OBJBHSUPPORT'] = self.name
            objbhsupport.append(bhDict)
        
        bhplaceholdersDict = {}
        #To populate busy hour place holder count
        bhplaceholdersDict['VERSIONID'] = self.versionID
        bhplaceholdersDict['BHLEVEL'] = self.rankingTable
        
        productPlaceHolderCount= 0
        customPlaceHolderCount= 0
        for key in self.busyHourPlaceHolders.iterkeys():
            if key.startswith('PP'):
                productPlaceHolderCount = productPlaceHolderCount + 1
            elif key.startswith('CP'):
                customPlaceHolderCount = customPlaceHolderCount + 1
                
        bhplaceholdersDict['PRODUCTPLACEHOLDERS'] = productPlaceHolderCount
        bhplaceholdersDict['CUSTOMPLACEHOLDERS'] = customPlaceHolderCount
        
        BHMapping = []
        for placeholderName, placeholder in sorted(self.busyHourPlaceHolders.iteritems()):
            if self.name != 'ELEM':
                for table in self.supportedTables:
                    if table != '' or table != None:
                        mappingDict = {}
                        mappingDict['VERSIONID'] = self.versionID
                        mappingDict['BHLEVEL'] = self.rankingTable
                        mappingDict['BHTYPE'] = placeholderName
                        mappingDict['TARGETVERSIONID'] = self.versionID
                        mappingDict['BHOBJECT'] = self.name
                        mappingDict['TYPEID'] = self.versionID + ":" + table
                        mappingDict['BHTARGETTYPE'] = table
                        mappingDict['BHTARGETLEVEL'] = self.name + "_" + placeholderName
                        mappingDict['ENABLE'] = 1
                        
                        if table not in placeholder.supportedTables and placeholder.properties['ENABLE'] == 0:
                            mappingDict['ENABLE'] = 0
                            
                        BHMapping.append(mappingDict)
        
        
        return objbhsupport, bhplaceholdersDict, BHMapping
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    