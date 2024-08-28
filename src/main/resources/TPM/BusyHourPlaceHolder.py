'''
Created on May 30, 2016

@author: ebrifol
'''

import TPM
import Utils

class BusyHourPlaceHolder(object):
    '''Class to represent Busy Hour Type (PLACEHOLDER). Child object of Busy Hour.
        Uniquely identified by the versionID, busy hour type, busy hour name.'''


    def __init__(self,versionID,bhobjectname,bhPlaceHolder):
        self.name = bhPlaceHolder
        self.versionID = versionID
        self.properties = Utils.odict()
        self.supportedTables = []
        self.BHOBjectName = bhobjectname
        self.BHSourceTables = []
        self.rankKeys = Utils.odict()
    
    def _getPropertiesFromServer(self,crsr):
        '''Get all the properties associated with the busy hourType object'''

        #AGGREGATIONTYPE
        crsr.execute("SELECT BHCRITERIA,WHERECLAUSE,DESCRIPTION,BHELEMENT,ENABLE,AGGREGATIONTYPE,LOOKBACK,P_THRESHOLD,N_THRESHOLD FROM BUSYHOUR where VERSIONID=? AND BHTYPE=? AND BHOBJECT=?",(self.versionID,self.name,self.BHOBjectName,))
        resultset = crsr.fetchall()
        for row in resultset:
            self.properties['BHCRITERIA'] = str(row[0])
            self.properties['WHERECLAUSE'] = str(row[1])
            self.properties['DESCRIPTION'] = str(row[2])
            self.properties['BHELEMENT'] = str(row[3])
            self.properties['ENABLE'] = str(row[4])
            self.properties['AGGREGATIONTYPE'] = str(row[5])
            self.properties['LOOKBACK'] = str(row[6])
            self.properties['P_THRESHOLD'] = str(row[7])
            self.properties['N_THRESHOLD'] = str(row[8])
                    
        #GET SOURCE TABLE
        crsr.execute("SELECT TYPENAME FROM BusyHourSource where VERSIONID=? AND BHTYPE=? AND BHOBJECT=?",(self.versionID,self.name,self.BHOBjectName,))
        resultset = crsr.fetchall()
        for row in resultset:
            self.BHSourceTables.append(row[0])
        
        crsr.execute("SELECT KEYNAME,KEYVALUE FROM BusyHourRankKeys where VERSIONID=? AND BHTYPE=? AND BHOBJECT=?",(self.versionID,self.name,self.BHOBjectName,))
        resultset = crsr.fetchall()
        for row in resultset:
            self.rankKeys[row[0]] = row[1]
            
        crsr.execute("SELECT DISTINCT BHTARGETTYPE FROM BUSYHOURMAPPING where VERSIONID=? AND BHTYPE=? AND BHOBJECT=? AND ENABLE=1",(self.versionID,self.name,self.BHOBjectName,))
        resultset = crsr.fetchall()
        for row in resultset:
            self.supportedTables.append(str(row[0]))
    
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
                if tpiDict['Busyhour']['BHOBJECT'][row] == self.BHOBjectName and tpiDict['Busyhour']['BHTYPE'][row] == self.name:
                    self.properties['BHCRITERIA'] = tpiDict['Busyhour']['BHCRITERIA'][row]
                    self.properties['WHERECLAUSE'] = tpiDict['Busyhour']['WHERECLAUSE'][row]
                    self.properties['DESCRIPTION'] = tpiDict['Busyhour']['DESCRIPTION'][row]
                    self.properties['BHELEMENT'] = tpiDict['Busyhour']['BHELEMENT'][row]
                    self.properties['ENABLE'] = tpiDict['Busyhour']['ENABLE'][row]
                    self.properties['P_THRESHOLD'] = tpiDict['Busyhour']['P_THRESHOLD'][row]
                    self.properties['N_THRESHOLD'] = tpiDict['Busyhour']['N_THRESHOLD'][row]
                    self.properties['LOOKBACK'] = tpiDict['Busyhour']['LOOKBACK'][row]
                    self.properties['AGGREGATIONTYPE'] = tpiDict['Busyhour']['AGGREGATIONTYPE'][row]
            
            if 'Busyhoursource' in tpiDict:
                for row in tpiDict['Busyhoursource']['BHOBJECT']:
                    if tpiDict['Busyhoursource']['BHOBJECT'][row] == self.BHOBjectName and tpiDict['Busyhoursource']['BHTYPE'][row] == self.name:
                        self.BHSourceTables.append(tpiDict['Busyhoursource']['TYPENAME'][row])
                    
            if 'Busyhourrankkeys' in tpiDict:        
                for row in tpiDict['Busyhourrankkeys']['BHOBJECT']:
                    if tpiDict['Busyhourrankkeys']['BHOBJECT'][row] == self.BHOBjectName and tpiDict['Busyhourrankkeys']['BHTYPE'][row] == self.name:
                        keyname = tpiDict['Busyhourrankkeys']['KEYNAME'][row]
                        keyvalue = tpiDict['Busyhourrankkeys']['KEYVALUE'][row]
                        if keyname == 'ELEMENT_TYPE' and not keyvalue.startswith("'"):
                            keyvalue = "'" + str(keyvalue) + "'"
                        self.rankKeys[keyname] = keyvalue
                        
            if 'Busyhourmapping' in tpiDict:
                for row in tpiDict['Busyhourmapping']['BHOBJECT']:
                    if tpiDict['Busyhourmapping']['BHOBJECT'][row] == self.BHOBjectName and tpiDict['Busyhourmapping']['BHTYPE'][row] == self.name:
                        if tpiDict['Busyhourmapping']['ENABLE'][row] == '1':
                            if tpiDict['Busyhourmapping']['BHLEVEL'][row] not in self.supportedTables:
                                self.rankingTable = tpiDict['Busyhourmapping']['BHLEVEL'][row]
    
    def _getPropertiesFromXls(self,xlsDict=None,filename=None):
        '''Create the default Properties of the BusyHour type'''
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
                if Name != 'TYPENAME' and Name != 'RANKINGKEYS' and Name != 'SupportedTables':
                    self.properties[Name] = Value
                
                elif Name == 'SupportedTables':
                    self.supportedTables = Value.split(',')
                else:
                    if Name == 'TYPENAME':
                        self.BHSourceTables = Value
                    if Name == 'RANKINGKEYS':
                        self.rankKeys = Value
            
            if self.BHOBjectName == 'ELEM':
                self.properties['BHELEMENT'] = '1'
            else:
                self.properties['BHELEMENT'] = '0'

            self.properties['ENABLE'] = '1'
    
    def _getPropertiesFromXlsx(self,xlsxDict):
        '''Populate the objects contents from a XlsxDict object.
        
        Exceptions: 
                   Raised if XlsDict and filename are both None (ie nothing to process)
        '''
        
        for Name, Value in xlsxDict['BH'][self.BHOBjectName][self.name].iteritems():
            if Name == 'MAPPEDTABLES':
                self.supportedTables = Value.split(',')
            elif Name != 'BHNAME' and Name != 'PHNAME':
                self.properties[Name] = Value
        
        for Name, Value in xlsxDict['BHRKeys'][self.BHOBjectName][self.name].iteritems():
            if Name == 'TYPENAME':
                self.BHSourceTables = Value
            elif Name == 'Keys':
                self.rankKeys = Value
        
        if self.BHOBjectName == 'ELEM':
            self.properties['BHELEMENT'] = '1'
        else:
            self.properties['BHELEMENT'] = '0'

        self.properties['ENABLE'] = '1'
        
        
    def _toXLSX(self, xlsxFile, workbook):
        ''' Converts the object to an excel document
        
        Parent toXLSX() method is responsible for triggering child object toXLSX() methods
        '''
        
        sheet = workbook.getSheet('BH')
        rowNumber = sheet.getLastRowNum() + 1
        
        if self.properties['BHCRITERIA'] != '':
            xlsxFile.writeToWorkbook(sheet, rowNumber, xlsxFile.findValue(sheet, 'BHNAME').getColumnIndex(), self.BHOBjectName)
            xlsxFile.writeToWorkbook(sheet, rowNumber, xlsxFile.findValue(sheet, 'PHNAME').getColumnIndex(), self.name)
            
            for FDColumn in xlsxFile.BHList:
                if FDColumn == 'MAPPEDTABLES':
                    xlsxFile.writeToWorkbook(sheet, rowNumber, xlsxFile.findValue(sheet, FDColumn).getColumnIndex(), ",".join(sorted(self.supportedTables)))
                elif FDColumn in self.properties.keys():
                    value = self.properties[FDColumn]
                    xlsxFile.writeToWorkbook(sheet, rowNumber, xlsxFile.findValue(sheet, FDColumn).getColumnIndex(), str(value))
        
            sheet = workbook.getSheet('BH Rank Keys')
            rowNumber = sheet.getLastRowNum() + 1
            for keyName, keyValue in self.rankKeys.iteritems():
                xlsxFile.writeToWorkbook(sheet, rowNumber, xlsxFile.findValue(sheet, 'BHNAME').getColumnIndex(), self.BHOBjectName)
                xlsxFile.writeToWorkbook(sheet, rowNumber, xlsxFile.findValue(sheet, 'PHNAME').getColumnIndex(), self.name)
                xlsxFile.writeToWorkbook(sheet, rowNumber, xlsxFile.findValue(sheet, 'KEYNAME').getColumnIndex(), keyName)
                xlsxFile.writeToWorkbook(sheet, rowNumber, xlsxFile.findValue(sheet, 'KEYVALUE').getColumnIndex(), keyValue)
                xlsxFile.writeToWorkbook(sheet, rowNumber, xlsxFile.findValue(sheet, 'SOURCETABLENAME').getColumnIndex(), ",".join(sorted(self.BHSourceTables)))
                
                rowNumber = rowNumber + 1
    
    def _getPropertiesFromXML(self,xmlElement):
        '''Populates the objects content from an xmlElement.
        
        The method is also responsible for triggering its child objects getPropertiesFromXML() method'''
        
        for prop1 in xmlElement:
            if  prop1.tag == 'BusyHourSourceTables':
                for prop2 in prop1:
                    self.BHSourceTables.append(prop2.text)
            elif prop1.tag == 'BusyHourSupportedTables':
                for prop2 in prop1:
                    self.supportedTables.append(prop2.text)
            elif prop1.tag == 'BusyHourRankKeys':
                for prop2 in prop1:
                    self.rankKeys[prop2.tag] = Utils.safeNull(prop2.text)
            else:
                self.properties[prop1.tag] = Utils.safeNull(prop1.text)
    
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
        
        outputXML = os+'<BusyHourPlaceholder name="' + self.name +'">'
        for prop in self.properties:
            outputXML += os2+'<'+str(prop)+'>'+ Utils.escape(self.properties[prop]) +'</'+str(prop)+'>'

        outputXML += os2+'<BusyHourSupportedTables>'
        for srct in self.supportedTables:
            outputXML += os3+'<BusyHourSupportedTable>'+srct+'</BusyHourSupportedTable>'
        outputXML += os2+'</BusyHourSupportedTables>'
        
        outputXML += os2+'<BusyHourSourceTables>'
        for srct in self.BHSourceTables:
            outputXML += os3+'<BusyHourSourceTable>'+srct+'</BusyHourSourceTable>'
        outputXML += os2+'</BusyHourSourceTables>'
        
        #write rankKeys    
        outputXML += os2+'<BusyHourRankKeys>'
        for rankKey in self.rankKeys:
            outputXML += os3+'<'+str(rankKey)+'>'+ self.rankKeys[rankKey] +'</'+str(rankKey)+'>'
        outputXML += os2+'</BusyHourRankKeys>'
        
        outputXML += os+'</BusyHourPlaceholder>'
        return outputXML
    
    def _getDefaultProperties(self):
        '''Create the default Properties of the BusyHour type
        Populate the objects contents not from a xlsDict object or xls file.
        
        If a xls file is passed it is converted to a xlsDict object before processing.

        Exceptions: 
                   Raised if xlsDict and filename are both None (ie nothing to process)'''
                       
        self.properties['BHCRITERIA'] = ''
        self.properties['WHERECLAUSE'] = ''
        self.properties['DESCRIPTION'] = ''
        self.properties['ENABLE'] = '0'
        self.properties['AGGREGATIONTYPE'] = 'RANKBH_TIMELIMITED'
        self.properties['LOOKBACK'] = '0'
        self.properties['P_THRESHOLD'] = '0'
        self.properties['N_THRESHOLD'] = '0'
        
        if self.BHOBjectName == 'ELEM': 
            self.properties['BHELEMENT'] = '1'
        else:
            self.properties['BHELEMENT'] = '0'
                   
        self.BHSourceTables.append('')
    
    def populateRepDbDicts(self):
        busyhour = {}
        for key,value in self.properties.iteritems():
            busyhour[key] = value   
        busyhour['VERSIONID'] = self.versionID
        busyhour['TARGETVERSIONID'] = self.versionID
        busyhour['BHTYPE'] = self.name
        busyhour['BHOBJECT'] = self.BHOBjectName
        busyhour['REACTIVATEVIEWS'] = 0
        
        zeroOffset = ['RANKBH_TIMELIMITED','RANKBH_TIMECONSISTENT']
        fifteenOffset = ['RANKBH_SLIDINGWINDOW','RANKBH_TIMECONSISTENT_SLIDINGWINDOW','RANKBH_PEAKROP']
        if busyhour['AGGREGATIONTYPE'] in zeroOffset:
            busyhour['OFFSET'] = 0
        elif busyhour['AGGREGATIONTYPE'] in fifteenOffset:
            busyhour['OFFSET'] = 15  
        
        if busyhour['AGGREGATIONTYPE'] == 'RANKBH_PEAKROP':
            busyhour['WINDOWSIZE']= 15
        else:
            busyhour['WINDOWSIZE']= 60
            
        busyhour['GROUPING'] = 'None'
        busyhour['PLACEHOLDERTYPE']= self.name[0:2]
        busyhour['CLAUSE']= ''
        
        BhSources=[]
        for table in self.BHSourceTables:
            if table != '' and table != None:
                BhSource={}
                BhSource['VERSIONID']=self.versionID
                BhSource['BHTYPE']=self.name
                BhSource['TYPENAME']=table
                BhSource['TARGETVERSIONID']=self.versionID
                BhSource['BHOBJECT']=self.BHOBjectName
                BhSources.append(BhSource)
        
        BHRankKeys=[]
        orderNo = 0 
        for key,value in self.rankKeys.iteritems():
            if key != '':
                BHRankKey={}
                BHRankKey['KEYNAME']=key
                BHRankKey['KEYVALUE']=value
                BHRankKey['VERSIONID']=self.versionID
                BHRankKey['BHTYPE']=self.name
                BHRankKey['TARGETVERSIONID']=self.versionID
                BHRankKey['BHOBJECT']=self.BHOBjectName
                BHRankKey['ORDERNBR'] = orderNo
                orderNo = orderNo + 1
                BHRankKeys.append(BHRankKey)
        
        return busyhour, BhSources, BHRankKeys
    
    def difference(self,bhTypeObject,deltaObj=None):
        '''Calculates the difference between two busy hour type objects
        
        Method takes bhTypeObject,deltaObj and deltaTPV as inputs.
        bhTypeObject: The Busy Hour Type object to be compared against
        DeltaObj: The single object that gets passed through the entire diff recording the changes.
        DeltaTPV: A TechPackVersion Object that gets passed through the entire diff recording only new content.
        
        The Difference method will trigger the difference method of its child objects, passing
        in the object to compare, deltaObj and deltaTPV. After calculating the diff the child object passes these objects
        back in conjunction with a flag to say whether a (only new or changed content.. not deleted) was found or not. This flag is used to decide
        whether a child object should be added to the parent object in the DeltaTPV.
        
        Note: BHType does not have any child objects
        
        Returns:
                diffFlag (Boolean indicating where a change was found or not)
                deltaObj
                deltaTPV 
        
        '''
        
        if deltaObj is None:
            deltaObj = Utils.Delta(self.name,bhTypeObject.name)
        
        Delta = Utils.DictDiffer(self.properties,bhTypeObject.properties)
        deltaObj.location.append('Properties')
        for item in Delta.changed():
            deltaObj.addChange('<Changed>', item, self.properties[item], bhTypeObject.properties[item])
        
        for item in Delta.added():
            deltaObj.addChange('<Added>', item, '', bhTypeObject.properties[item])
                
        for item in Delta.removed():
            deltaObj.addChange('<Removed>', item, self.properties[item], '')

        deltaObj.location.pop()
        
        
        ################################################################
        # BH Mapped Tables Diff
        deltaObj.location.append('Mapped Table')
        Delta = list(set(bhTypeObject.supportedTables) - set(self.supportedTables))
        for table in Delta:
            deltaObj.addChange('<Added>', 'Properties', '', table)
        
        Delta = list(set(self.supportedTables) - set(bhTypeObject.supportedTables))
        for table in Delta:
            deltaObj.addChange('<Removed>', 'Properties', table, '')
        
        deltaObj.location.pop()
        
    
        return deltaObj
    