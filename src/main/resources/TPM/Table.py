'''
Created on May 30, 2016

@author: ebrifol
'''

import TPM
import Utils
from copy import deepcopy

class Table(object):
    '''Class to represent a table in a Tech Pack Version. Child of TechPackVersion class. Uniquely identified by its
        name and versionid (combined these are know as the typeid). Tables can be of either 'Measurement' or 'Reference' type
        '''
    def __init__(self, versionID, tablename, tableType=None):
        self.versionID = versionID
        self.tableType = tableType
        self.name = tablename
        self.properties = Utils.odict() 
        self.attributes = Utils.odict()
        self.parsers = Utils.odict() 
        self.universeClass = ''
        self.typeid = versionID + ":" + tablename
        self.typeClassID = '' 
        self.mtableIDs = []
        
    def _getPropertiesFromServer(self,DbCursor):
        '''Gets all properties (and child objects) of the table from the server
        
        This method triggers multiple sub methods for retrieving information
        from the dwhrep
        '''          
        self._getTablePropertiesFromServer(DbCursor)
        self._getAttributesFromServer(DbCursor)
        self._getParsersFromServer(DbCursor)
    
    def _getTablePropertiesFromServer(self,DbCursor):
        '''Populates the properties dictionary of the table from the server
        
        SQL Executed:
                    SELECT DESCRIPTION,UPDATE_POLICY,TABLE_TYPE,DATAFORMATSUPPORT from ReferenceTable WHERE TYPEID =?

        SQL Executed:
                    SELECT TYPECLASSID,DESCRIPTION,JOINABLE,SIZING,TOTALAGG,ELEMENTBHSUPPORT,RANKINGTABLE,DELTACALCSUPPORT,PLAINTABLE,UNIVERSEEXTENSION,VECTORSUPPORT,
                    DATAFORMATSUPPORT,ONEMINAGG,MIXEDPARTITIONSTABLE,EVENTSCALCTABLE,LOADFILE_DUP_CHECK,FIFTEENMINAGG from MeasurementType WHERE TYPEID =?
        
        '''
        
        if self.tableType == 'Reference':
            DbCursor.execute("SELECT DESCRIPTION,UPDATE_POLICY,DATAFORMATSUPPORT from ReferenceTable WHERE TYPEID =? AND BASEDEF=0", (self.typeid,)) 
            row = DbCursor.fetchone()
            self.properties['DESCRIPTION'] = str(row[0]).strip()
            self.properties['UPDATE_POLICY'] = Utils.strFloatToInt(str(row[1]))
            self.properties['DATAFORMATSUPPORT'] = str(row[2])
            
            
        elif self.tableType == 'Measurement':
            DbCursor.execute("SELECT TYPECLASSID,DESCRIPTION,JOINABLE,SIZING,TOTALAGG,ELEMENTBHSUPPORT,RANKINGTABLE,DELTACALCSUPPORT,PLAINTABLE,UNIVERSEEXTENSION,VECTORSUPPORT,DATAFORMATSUPPORT,ONEMINAGG,MIXEDPARTITIONSTABLE,EVENTSCALCTABLE,LOADFILE_DUP_CHECK,FIFTEENMINAGG from MeasurementType WHERE TYPEID =?", (self.typeid,)) 
            row = DbCursor.fetchone()
            self.typeClassID = str(row[0])
            self.properties['TYPECLASSID'] = str(row[0])
            self.properties['DESCRIPTION'] = str(row[1])
            self.properties['JOINABLE'] = str(row[2])
            self.properties['SIZING'] = str(row[3])
            self.properties['TOTALAGG'] = str(row[4])
            self.properties['ELEMBHSUPPORT'] = str(row[5])
            self.properties['RANKINGTABLE'] = str(row[6])
            self.properties['DELTACALCSUPPORT'] = str(row[7])
            self.properties['PLAINTABLE'] = str(row[8])
            self.properties['UNIVERSEEXTENSION'] = str(row[9])
            self.properties['VECTORSUPPORT'] = str(row[10])
            self.properties['DATAFORMATSUPPORT'] = str(row[11])
            self.properties['ONEMINAGG'] = str(row[12])
            self.properties['MIXEDPARTITIONSTABLE'] = str(row[13])
            self.properties['EVENTSCALCTABLE'] = str(row[14])
            self.properties['LOADFILEDUPCHECK'] = str(row[15])
            self.properties['FIFTEENMINAGG'] = str(row[16])
            
            if self.typeClassID != '':
                DbCursor.execute("SELECT DESCRIPTION from measurementTypeClass where TYPECLASSID =?", (self.typeClassID ,))
                row = DbCursor.fetchone()
                self.universeClass = str(row[0])

    def _getAttributesFromServer(self,DbCursor):
        '''Get attributes information associated with the table from the server.
        
         Creates a child attribute object and adds the object to the self.attributeObjects dictionary'''
            
        if self.tableType == 'Reference':
            DbCursor.execute("SELECT DATANAME FROM ReferenceColumn where TYPEID=? AND BASEDEF=? ORDER BY COLNUMBER",(self.typeid,0,))
            row = DbCursor.fetchall()
            for refKey in row:
                att = TPM.Attribute(str(refKey[0]),self.typeid,'referenceKey')
                att._getPropertiesFromServer(DbCursor)
                self.attributes[str(refKey[0])] = att
        elif self.tableType == 'Measurement':
            DbCursor.execute("SELECT DATANAME FROM MeasurementKey where TYPEID=? ORDER BY COLNUMBER",(self.typeid,))
            row = DbCursor.fetchall()
            for measKey in row:
                att = TPM.Attribute(str(measKey[0]),self.typeid,'measurementKey')
                att._getPropertiesFromServer(DbCursor)
                self.attributes[str(measKey[0])] = att
            DbCursor.execute("SELECT DATANAME FROM MeasurementCounter where TYPEID=? ORDER BY COLNUMBER",(self.typeid,))
            row = DbCursor.fetchall()
            for measCounter in row:
                att = TPM.Attribute(str(measCounter[0]),self.typeid,'measurementCounter')
                att._getPropertiesFromServer(DbCursor)
                self.attributes[str(measCounter[0])] = att 
    
    def _getParsersFromServer(self,DbCursor):
        '''Get a list of parser names (ie mdc,ascii) associated with the measurement table from the server
        
        Names are appended to self.parserNames list
        ''' 
        DbCursor.execute("SELECT DISTINCT DATAFORMATTYPE FROM DataFormat WHERE TYPEID =?", (self.typeid,)) 
        resultset = DbCursor.fetchall()
        for row in resultset:
            parserName = str(row[0]) 
            parser = TPM.Parser(self.versionID,self.name,parserName)
            parser.setAttributeNames(self.attributes.keys())
            parser._getPropertiesFromServer(DbCursor)
            self.parsers[parserName] = parser

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
                if self.tableType =='Measurement':
                    if 'Measurementtype' in tpidict:
                        for row in tpidict['Measurementtype']['TYPEID']:
                            if self.typeid == tpidict['Measurementtype']['TYPEID'][row]:
                                self.tableType = 'Measurement'
                                self.properties['TYPECLASSID'] = tpidict['Measurementtype']['TYPECLASSID'][row]
                                self.properties['DESCRIPTION'] = tpidict['Measurementtype']['DESCRIPTION'][row]
                                self.properties['JOINABLE'] = tpidict['Measurementtype']['JOINABLE'][row]
                                self.properties['SIZING'] = tpidict['Measurementtype']['SIZING'][row]
                                self.properties['TOTALAGG'] = tpidict['Measurementtype']['TOTALAGG'][row]
                                self.properties['ELEMENTBHSUPPORT'] = tpidict['Measurementtype']['ELEMENTBHSUPPORT'][row]
                                self.properties['RANKINGTABLE'] = tpidict['Measurementtype']['RANKINGTABLE'][row]
                                self.properties['DELTACALCSUPPORT'] = tpidict['Measurementtype']['DELTACALCSUPPORT'][row]
                                self.properties['PLAINTABLE'] = tpidict['Measurementtype']['PLAINTABLE'][row]
                                self.properties['UNIVERSEEXTENSION'] = tpidict['Measurementtype']['UNIVERSEEXTENSION'][row]
                                self.properties['VECTORSUPPORT'] = Utils.checkNull(tpidict['Measurementtype']['VECTORSUPPORT'][row])
                                self.properties['DATAFORMATSUPPORT'] = tpidict['Measurementtype']['DATAFORMATSUPPORT'][row]
                                self.properties['TYPEID']=tpidict['Measurementtype']['TYPEID'][row]
                                self.properties['VERSIONID']=tpidict['Measurementtype']['VERSIONID'][row]
                                
                                
                                if self.properties['DELTACALCSUPPORT'] == '1':
                                    if 'Supportedvendorrelease' in tpidict:
                                        supportedVendorReleases = []
                                        for row in tpidict['Supportedvendorrelease']['VENDORRELEASE']:
                                            supportedVendorReleases.append(tpidict['Supportedvendorrelease']['VENDORRELEASE'][row])
                                    
                                    if 'Measurementdeltacalcsupport' in tpidict:
                                        for row in tpidict['Measurementdeltacalcsupport']['TYPEID']:
                                            if self.typeid == tpidict['Measurementdeltacalcsupport']['TYPEID'][row]:
                                                supportedVendorReleases.remove(tpidict['Measurementdeltacalcsupport']['VENDORRELEASE'][row])
                                            
                                    self.properties['DELTACALCSUPPORT'] = ",".join(supportedVendorReleases)
                                
                                if 'Measurementtypeclass' in tpidict:
                                    for row in tpidict['Measurementtypeclass']['TYPECLASSID']:
                                        if self.properties['TYPECLASSID'].lower() == tpidict['Measurementtypeclass']['TYPECLASSID'][row].lower():
                                            self.universeClass = tpidict['Measurementtypeclass']['DESCRIPTION'][row]
                                    
                                if 'Measurementkey' in tpidict:
                                    colOrder = {}
                                    for row in tpidict['Measurementkey']['TYPEID']:
                                        if self.typeid == tpidict['Measurementkey']['TYPEID'][row]:
                                            colOrder[tpidict['Measurementkey']['COLNUMBER'][row]] = row
                                    for row in sorted(colOrder.itervalues()):
                                        if self.typeid == tpidict['Measurementkey']['TYPEID'][row]:
                                            att = TPM.Attribute(tpidict['Measurementkey']['DATANAME'][row],self.typeid,'measurementKey')
                                            att._getPropertiesFromTPI(tpidict)
                                            self.attributes[tpidict['Measurementkey']['DATANAME'][row]] = att
                                
                                if 'Measurementcounter' in tpidict:
                                    colOrder = {}
                                    for row in tpidict['Measurementcounter']['TYPEID']:
                                        if self.typeid == tpidict['Measurementcounter']['TYPEID'][row]:
                                            colOrder[tpidict['Measurementcounter']['COLNUMBER'][row]] = row
                                    for row in sorted(colOrder.itervalues()):
                                        if self.typeid == tpidict['Measurementcounter']['TYPEID'][row]:
                                            att = TPM.Attribute(tpidict['Measurementcounter']['DATANAME'][row],self.typeid,'measurementCounter')
                                            att._getPropertiesFromTPI(tpidict)
                                            self.attributes[tpidict['Measurementcounter']['DATANAME'][row]] = att                     
                                    break
         
                elif self.tableType == 'Reference':
                    if 'Referencetable' in tpidict:
                        for row in tpidict['Referencetable']['TYPEID']:
                            if self.typeid == tpidict['Referencetable']['TYPEID'][row]:
                                self.typeFlag = 'Reference'
                                self.properties['DESCRIPTION'] = tpidict['Referencetable']['DESCRIPTION'][row]
                                self.properties['UPDATE_POLICY'] = tpidict['Referencetable']['UPDATE_POLICY'][row]
                                self.properties['DATAFORMATSUPPORT'] = tpidict['Referencetable']['DATAFORMATSUPPORT'][row]
                                
                                if 'Referencecolumn' in tpidict:
                                    colOrder = {}
                                    for row in tpidict['Referencecolumn']['TYPEID']:
                                        if self.typeid == tpidict['Referencecolumn']['TYPEID'][row]:
                                            colOrder[tpidict['Referencecolumn']['COLNUMBER'][row]] = row
                                        
                                    for row in sorted(colOrder.itervalues()):
                                        if self.typeid == tpidict['Referencecolumn']['TYPEID'][row]:
                                            if tpidict['Referencecolumn']['BASEDEF'][row] == '0':
                                                att = TPM.Attribute(tpidict['Referencecolumn']['DATANAME'][row],self.typeid,'referenceKey')
                                                att._getPropertiesFromTPI(tpidict)
                                                self.attributes[tpidict['Referencecolumn']['DATANAME'][row]] = att
                                    break

                if 'Dataformat' in tpidict:
                    parserNames = []
                    for row in tpidict['Dataformat']['DATAFORMATTYPE']: 
                        if tpidict['Dataformat']['DATAFORMATTYPE'][row] not in parserNames:
                            parserNames.append(tpidict['Dataformat']['DATAFORMATTYPE'][row])    
                    for prsr in parserNames:
                        parser = TPM.Parser(self.versionID,self.name,prsr)
                        parser.setAttributeNames(self.attributes.keys())
                        parser._getPropertiesFromTPI(tpidict)
                        self.parsers[prsr] = parser
                    
            self._completeModel()              
            
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
                
                for Name, Values in xlsDict['Tables'][self.name].iteritems():
                    if Name == 'measurementKey' or Name == 'measurementCounter' or Name == 'referenceKey':
                        for entry, properties in Values.iteritems():                                
                            att = TPM.Attribute(entry,self.typeid,Name)
                            att._getPropertiesFromXls(properties)
                            self.attributes[entry] = att
                    elif Name == 'Parser':
                        for entry, properties in Values.iteritems():
                            if self.tableType == 'Measurement':
                                if 'DATATAGS' in xlsDict['Tables'][self.name]:
                                    properties['DATATAGS'] = xlsDict['Tables'][self.name]['Parser'][entry]['DATATAGS']
                            elif self.tableType == 'Reference':
                                if 'DATATAGS' in xlsDict['Tables'][self.name]['Parser'][entry]:
                                    properties['DATATAGS'] = xlsDict['Tables'][self.name]['Parser'][entry]['DATATAGS']

                            parser = TPM.Parser(self.versionID,self.name,entry)
                            parser._getPropertiesFromXls(properties)
                            self.parsers[entry] = parser
                    elif Name == 'CLASSIFICATION':
                        self.universeClass = Values
                    elif Name == 'OBJECTBH':
                        pass
                    else:
                        if Name != 'TABLETYPE':
                            self.properties[Name] = Values

            self._completeModel()
    
    def _getPropertiesFromXlsx(self,xlsxDict):
        '''Populate the objects contents from a XlsxDict object.
        
        Exceptions: 
                   Raised if XlsDict and filename are both None (ie nothing to process)
        '''
        
        for Name, Values in xlsxDict['Tables'][self.name].iteritems():
            if Name == 'Parsers':
                for parserName, datatag in Values.iteritems():
                    parser = TPM.Parser(self.versionID, self.name, parserName)
                    parser._getPropertiesFromXlsx(xlsxDict)
                    self.parsers[parserName] = parser
            elif Name == 'CLASSIFICATION':
                self.universeClass = Values
            elif Name != 'OBJECTBH' and Name != 'TABLETYPE' and Name != 'Name':
                self.properties[Name] = Values
            
        if self.name in xlsxDict['Attributes']:
            for Name, Values in xlsxDict['Attributes'][self.name].iteritems():
                attributeType = xlsxDict['Attributes'][self.name][Name]['TYPE']
                att = TPM.Attribute(Name, self.typeid, attributeType)
                att._getPropertiesFromXlsx(xlsxDict)
                self.attributes[Name] = att
            
        self._completeModel()        
    
    
    def _toXLSX(self, xlsxFile, workbook, TransformationCollection):
        ''' Converts the object to an excel document
        
        Parent toXLSX() method is responsible for triggering child object toXLSX() methods
        '''
        
        if self.tableType == 'Measurement':
            sheet = workbook.getSheet('Fact Tables')
            list = xlsxFile.FactTableList
            rowNumber = sheet.getLastRowNum() + 1
            xlsxFile.writeToWorkbook(sheet, rowNumber, xlsxFile.findValue(sheet, 'NAME').getColumnIndex(), self.name)
            
        elif self.tableType == 'Reference':
            sheet = workbook.getSheet('Top Tables')
            list = xlsxFile.TopTableList
            rowNumber = sheet.getLastRowNum() + 1
            xlsxFile.writeToWorkbook(sheet, rowNumber, xlsxFile.findValue(sheet, 'NAME').getColumnIndex(), self.name)
        
        for FDColumn in list:
            if FDColumn in self.properties.keys():
                value = self.properties[FDColumn]
                if FDColumn == 'UPDATE_POLICY':
                    value = xlsxFile.updatePolicylist[int(value)]
                
                if FDColumn != 'FOLLOWJOHN':
                    if value == 1 or value == '1':
                        value = 'Y'
                    elif value == 0 or value == '0':
                        value = ''
                        
                xlsxFile.writeToWorkbook(sheet, rowNumber, xlsxFile.findValue(sheet, FDColumn).getColumnIndex(), str(value))
            elif FDColumn == 'CLASSIFICATION':
                xlsxFile.writeToWorkbook(sheet, rowNumber, xlsxFile.findValue(sheet, FDColumn).getColumnIndex(), str(self.universeClass))
                
        for attribute in self.attributes.itervalues():
            attribute._toXLSX(xlsxFile, workbook, self.name)
        
        for parser in self.parsers.itervalues():
            parser._toXLSX(xlsxFile, workbook, TransformationCollection)
        
        return TransformationCollection
    
    def _getPropertiesFromXML(self,xmlElement):
        '''Populates the objects content from an xmlElement.
        
        The method is also responsible for triggering its child objects getPropertiesFromXML() method'''
        
        self.tableType = xmlElement.attrib['tableType']
        self.universeClass = Utils.unescape(xmlElement.attrib['universeClass']) 
        for elem1 in xmlElement:
            if elem1.tag=='Attributes':
                    for elem2 in elem1:
                        if elem2.tag=='Attribute':
                            tpAttrb = TPM.Attribute(elem2.attrib['name'],self.typeid,elem2.attrib['attributeType'])
                            tpAttrb._getPropertiesFromXML(elem2)
                            self.attributes[elem2.attrib['name']] = tpAttrb  
            elif elem1.tag=='Parsers':
                    for elem2 in elem1:
                        if elem2.tag=='Parser':
                            tpParser = TPM.Parser(self.versionID,self.name,elem2.attrib['type'])
                            tpParser._getPropertiesFromXML(elem2)
                            self.parsers[elem2.attrib['type']] = tpParser
            else:
                self.properties[elem1.tag] = Utils.safeNull(elem1.text)
    
    def _toXML(self,indent=0):
        '''Write the object to an xml formatted string
        
        Indent value is used for string indentation. Default to 0
        Parent toXML() method is responsible for triggering child object toXML() methods.

        Return Value: xmlString 
        '''
        
        offset = '    '
        os = "\n" + offset*indent
        os2 = os + offset

        outputXML =os+'<Table name="'+self.name+ '" tableType="'+self.tableType+ '" universeClass= "'+Utils.escape(self.universeClass) +'">'
        for prop in self.properties:
            outputXML += os2+'<'+str(prop)+'>'+ Utils.escape(self.properties[prop]) +'</'+str(prop)+'>'
        outputXML  += os2 + '<Attributes>'
        for attribute in self.attributes:
            outputXML += self.attributes[attribute]._toXML(indent+2)
        outputXML  += os2 + '</Attributes>'
        outputXML  += os2 + '<Parsers>' 
        for parser in self.parsers:
            outputXML += self.parsers[parser]._toXML(indent+2)
        outputXML  += os2 + '</Parsers>'
        outputXML +=os+'</Table>'
        return outputXML
    
    def _getTypeClassID(self):
        self.typeClassID = self.versionID + ":" + self.versionID.rsplit(':')[0] + "_" + self.universeClass
        return self.typeClassID
    
    def populateRepDbDicts(self):
        if self.tableType == 'Measurement':
            #MeasurementTypeClass
            MeasurementTypeClass = {}
            MeasurementTypeClass = deepcopy(self.properties)
            MeasurementTypeClass['DESCRIPTION'] = self.universeClass
            MeasurementTypeClass['TYPECLASSID'] = self._getTypeClassID()
            MeasurementTypeClass['VERSIONID'] = self.versionID
            
            DELTACALCSUPPORT = 0
            #Measurementdeltacalcsupport
            deltacalcSupport = {}
            if 'DELTACALCSUPPORT' in self.properties:
                if self.properties['DELTACALCSUPPORT'] != None and self.properties['DELTACALCSUPPORT'].strip() != '0':
                    deltacalcSupport['TYPEID'] = self.versionID + ":" + self.name
                    deltacalcSupport['VERSIONID'] = self.versionID
                    deltacalcSupport['VENDORRELEASE'] = self.properties['DELTACALCSUPPORT']
                    DELTACALCSUPPORT = 1
            
            #MeasurementType
            MeasurementType = {}
            MeasurementType = deepcopy(self.properties)
            MeasurementType['TYPEID'] = self.versionID + ":" + self.name
            MeasurementType['TYPENAME'] = self.name
            MeasurementType['VENDORID'] = self.versionID.rsplit(':')[0]
            MeasurementType['FOLDERNAME'] = self.name
            MeasurementType['OBJECTID'] = self.versionID + ":" + self.name
            MeasurementType['OBJECTNAME'] = self.name
            MeasurementType['DELTACALCSUPPORT'] = DELTACALCSUPPORT
            MeasurementType['TYPECLASSID'] = self._getTypeClassID()
            MeasurementType['VERSIONID'] = self.versionID
            
            return MeasurementTypeClass, deltacalcSupport, MeasurementType
            
        if self.tableType == 'Reference':
            RefTable = {}
            RefTable = deepcopy(self.properties)
            RefTable['VERSIONID'] = self.versionID
            RefTable['TYPEID'] = self.versionID + ":" + self.name
            RefTable['TYPENAME'] = self.name
            RefTable['OBJECTID'] = self.versionID + ":" + self.name
            RefTable['OBJECTNAME'] = self.name
            RefTable['BASEDEF'] = 0
            
            return RefTable
    
    def difference(self,tableObject,deltaObj=None):
        '''Calculates the difference between two table objects
        
        Method takes tableObject,deltaObj and deltaTPV as inputs.
        TableObject: The table to be compared against
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
            deltaObj = Utils.Delta(self.typeid,tableObject.typeid)
        
        ############################################## Properties Difference #####################################################
        deltaObj.location.append('Properties') 
        if self.universeClass != tableObject.universeClass:
            deltaObj.addChange('<Changed>', 'Classification', self.universeClass, tableObject.universeClass)

        Delta = Utils.DictDiffer(self.properties,tableObject.properties)
        for item in Delta.changed():
            if item != 'TYPEID' and item !=  'TYPECLASSID' and item !=  'VERSIONID':
                deltaObj.addChange('<Changed>', item, self.properties[item], tableObject.properties[item])
    
        for item in Delta.added():
            if item != 'TYPEID' and item !=  'TYPECLASSID' and item !=  'VERSIONID':
                deltaObj.addChange('<Added>', item, '', tableObject.properties[item])
                
        for item in Delta.removed():
            if item != 'TYPEID' and item !=  'TYPECLASSID' and item !=  'VERSIONID':
                deltaObj.addChange('<Removed>', item, self.properties[item], '')
        
        deltaObj.location.pop()
        
        ############################################## Attributes Difference #####################################################
        Delta = Utils.DictDiffer(self.attributes,tableObject.attributes)
        deltaObj.location.append('Attribute')
        for item in Delta.added():
            deltaObj.addChange('<Added>', tableObject.attributes[item].attributeType, '', item)
      
        for item in Delta.removed():
            deltaObj.addChange('<Removed>', self.attributes[item].attributeType, item, '')
        
        deltaObj.location.pop()
          
        for item in Delta.common():
            deltaObj.location.append('Attribute='+item)
            deltaObj = self.attributes[item].difference(tableObject.attributes[item],deltaObj)
            deltaObj.location.pop()
        
        
        ############################################## Parser Difference #####################################################
        Delta = Utils.DictDiffer(self.parsers,tableObject.parsers)
        deltaObj.location.append('Parser')
        for item in Delta.added():
            deltaObj.addChange('<Added>', tableObject.parsers[item].parserType, '', item)
      
        for item in Delta.removed():
            deltaObj.addChange('<Removed>', self.parsers[item].parserType, item, '')
        
        deltaObj.location.pop()
          
        for item in Delta.common():
            deltaObj.location.append('Parser='+item)
            deltaObj = self.parsers[item].difference(tableObject.parsers[item],deltaObj)
            deltaObj.location.pop()
        
        return deltaObj
    
    def _completeModel(self):
        if self.tableType == 'Measurement':
            if 'ELEMENTBHSUPPORT' not in self.properties or self.properties['ELEMENTBHSUPPORT'] == '':
                self.properties['ELEMENTBHSUPPORT'] = '0'
            if 'PLAINTABLE' not in self.properties or self.properties['PLAINTABLE'] == '':
                self.properties['PLAINTABLE'] = '0'
            if 'RANKINGTABLE' not in self.properties or self.properties['RANKINGTABLE'] == '':
                self.properties['RANKINGTABLE'] = '0'
            if 'TOTALAGG' not in self.properties or self.properties['TOTALAGG'] == '':
                self.properties['TOTALAGG'] = '0'            
            if 'VECTORSUPPORT' not in self.properties or self.properties['VECTORSUPPORT'] == '':
                self.properties['VECTORSUPPORT'] = '0'
            if 'JOINABLE' not in self.properties or self.properties['JOINABLE'] == '':
                self.properties['JOINABLE'] = ''
            if 'DELTACALCSUPPORT' not in self.properties or self.properties['DELTACALCSUPPORT'] == '':
                self.properties['DELTACALCSUPPORT'] = '0'
        
        self.properties['DATAFORMATSUPPORT'] = '1'
            
            