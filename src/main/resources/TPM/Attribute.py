'''
Created on May 30, 2016

@author: ebrifol
'''

import TPM
import Utils
from copy import deepcopy

class Attribute(object):
    '''Class to represent any column in a table. Identified by its
    name and attributeType. attributeType property is either 'measurementCounter','referenceKey' or 'measurementKey'.
    '''

    def __init__(self,name,typeid,attributeType):          
        self.typeid = typeid
        self.attributeType = attributeType
        self.name = name
        self.properties = Utils.odict()
        self.vectors = Utils.odict()
        self._parentTableName = '' #this is set outside the class by the get properties from tpi method of the table class, NOT always populated
    
    def _getPropertiesFromServer(self,DbCursor):    
        if self.attributeType == 'referenceKey':                    
            self.key = True
            DbCursor.execute("SELECT DATATYPE,DATASIZE,DATASCALE,NULLABLE,UNIQUEKEY,INCLUDESQL,INCLUDEUPD,DESCRIPTION,DATAID,UNIVERSEOBJECT,UNIVERSECLASS,UNIVERSECONDITION  from ReferenceColumn WHERE TYPEID =? AND DATANAME=? AND BASEDEF=?", (self.typeid,self.name,0,))
        elif self.attributeType =='measurementKey':
            self.key = True
            DbCursor.execute("SELECT DESCRIPTION,ISELEMENT,UNIQUEKEY,DATATYPE,DATASIZE,DATASCALE,NULLABLE,INDEXES,INCLUDESQL,UNIVOBJECT,JOINABLE,DATAID from MeasurementKey WHERE TYPEID=? AND DATANAME=?",(self.typeid,self.name,))
        elif self.attributeType =='measurementCounter':                    
            self.key = False
            DbCursor.execute("SELECT DESCRIPTION,TIMEAGGREGATION,GROUPAGGREGATION,DATATYPE,DATASIZE,DATASCALE,INCLUDESQL,UNIVOBJECT,UNIVCLASS,COUNTERTYPE,DATAID from MeasurementCounter WHERE TYPEID=? AND DATANAME=?",(self.typeid,self.name,))
        else:
            raise "Error, attribute type %s is not recognised." % self.attributeType
        
        resultset = DbCursor.fetchall()
        desc = DbCursor.description
        for row in resultset: 
            i = 0
            for x in desc:                 
                self.properties[x[0]] = Utils.checkNull(str(row[i]).strip())
                i+=1
            
        if self.attributeType =='measurementCounter':
            if 'VECTOR' in self.properties['COUNTERTYPE'].upper():
                DbCursor.execute("SELECT VENDORRELEASE,VINDEX from MeasurementVector WHERE TYPEID=? AND DATANAME=?",(self.typeid,self.name,))
                rows = DbCursor.fetchall()
                for row in rows:
                    vendRel = Utils.checkNull(str(row[0]).strip())
                    index = Utils.strFloatToInt(str(row[1]).strip())
                    if vendRel not in self.vectors:
                        self.vectors[vendRel] = {}
                    vector = TPM.Vector(self.typeid, self.name, index, vendRel)
                    vector._getPropertiesFromServer(DbCursor)
                    self.vectors[vendRel][index] = vector
    
    def _getPropertiesFromTPI(self,tpidict=None,filename=None):
            '''Populate the objects contents from a tpiDict object or tpi file.
            
            If a tpi file is passed it is converted to a tpiDict object before processing
            
            Exceptions: 
                       Raised if tpiDict and filename are both None (ie nothing to process)'''
            
            if tpidict==None and filename==None:
                strg = 'getPropertiesFromTPI() Nothing to Process'
                raise Exception(strg)
            else:
                if filename is not None:
                    tpidict = Utils.TpiDict(filename).returnTPIDict()

                if self.attributeType =='measurementKey':
                    for row in tpidict['Measurementkey']['DATANAME']:
                        if tpidict['Measurementkey']['DATANAME'][row] == self.name and tpidict['Measurementkey']['TYPEID'][row] == self.typeid:
                            self.properties['DESCRIPTION'] = Utils.checkNull(tpidict['Measurementkey']['DESCRIPTION'][row])
                            self.properties['ISELEMENT'] = Utils.checkNull(tpidict['Measurementkey']['ISELEMENT'][row])
                            self.properties['UNIQUEKEY'] = Utils.checkNull(tpidict['Measurementkey']['UNIQUEKEY'][row])
                            self.properties['DATATYPE'] = Utils.checkNull(tpidict['Measurementkey']['DATATYPE'][row])
                            self.properties['DATASCALE'] = Utils.checkNull(tpidict['Measurementkey']['DATASCALE'][row])
                            self.properties['NULLABLE'] = Utils.checkNull(tpidict['Measurementkey']['NULLABLE'][row])
                            self.properties['INDEXES'] = Utils.checkNull(tpidict['Measurementkey']['INDEXES'][row])
                            self.properties['INCLUDESQL'] = Utils.checkNull(tpidict['Measurementkey']['INCLUDESQL'][row])
                            self.properties['UNIVOBJECT'] = Utils.checkNull(tpidict['Measurementkey']['UNIVOBJECT'][row])
                            self.properties['JOINABLE'] = Utils.checkNull(tpidict['Measurementkey']['JOINABLE'][row])
                            self.properties['DATAID'] = Utils.checkNull(tpidict['Measurementkey']['DATAID'][row])
                            self.properties['DATASIZE'] = Utils.checkNull(tpidict['Measurementkey']['DATASIZE'][row])

                elif self.attributeType == 'measurementCounter':
                    for row in tpidict['Measurementcounter']['DATANAME']:
                        if tpidict['Measurementcounter']['DATANAME'][row] == self.name and tpidict['Measurementcounter']['TYPEID'][row] == self.typeid:
                            self.properties['DESCRIPTION'] = Utils.checkNull(tpidict['Measurementcounter']['DESCRIPTION'][row])
                            self.properties['TIMEAGGREGATION'] = Utils.checkNull(tpidict['Measurementcounter']['TIMEAGGREGATION'][row])
                            self.properties['GROUPAGGREGATION'] = Utils.checkNull(tpidict['Measurementcounter']['GROUPAGGREGATION'][row])
                            self.properties['DATATYPE'] = Utils.checkNull(tpidict['Measurementcounter']['DATATYPE'][row])
                            self.properties['DATASIZE'] = Utils.checkNull(tpidict['Measurementcounter']['DATASIZE'][row])
                            self.properties['DATASCALE'] = Utils.checkNull(tpidict['Measurementcounter']['DATASCALE'][row])
                            self.properties['INCLUDESQL'] = Utils.checkNull(tpidict['Measurementcounter']['INCLUDESQL'][row])
                            self.properties['UNIVOBJECT'] = Utils.checkNull(tpidict['Measurementcounter']['UNIVOBJECT'][row])
                            self.properties['UNIVCLASS'] = Utils.checkNull(tpidict['Measurementcounter']['UNIVCLASS'][row])
                            self.properties['COUNTERTYPE'] = Utils.checkNull(tpidict['Measurementcounter']['COUNTERTYPE'][row])
                            self.properties['DATAID'] = Utils.checkNull(tpidict['Measurementcounter']['DATAID'][row])

                elif self.attributeType == 'referenceKey':
                    for row in tpidict['Referencecolumn']['DATANAME']:
                        if tpidict['Referencecolumn']['DATANAME'][row] == self.name and tpidict['Referencecolumn']['TYPEID'][row] == self.typeid:
                            self.properties['DATATYPE'] = Utils.checkNull(tpidict['Referencecolumn']['DATATYPE'][row])
                            self.properties['DATASIZE'] = Utils.checkNull(tpidict['Referencecolumn']['DATASIZE'][row])
                            self.properties['DATASCALE'] = Utils.checkNull(tpidict['Referencecolumn']['DATASCALE'][row])
                            self.properties['NULLABLE'] = Utils.checkNull(tpidict['Referencecolumn']['NULLABLE'][row])
                            self.properties['UNIQUEKEY'] = Utils.checkNull(tpidict['Referencecolumn']['UNIQUEKEY'][row])
                            self.properties['INCLUDESQL'] = Utils.checkNull(tpidict['Referencecolumn']['INCLUDESQL'][row])
                            self.properties['INCLUDEUPD'] = Utils.checkNull(tpidict['Referencecolumn']['INCLUDEUPD'][row])
                            self.properties['DESCRIPTION'] = Utils.checkNull(tpidict['Referencecolumn']['DESCRIPTION'][row])
                            self.properties['DATAID'] = Utils.checkNull(tpidict['Referencecolumn']['DATAID'][row])
                            self.properties['UNIVERSEOBJECT'] = Utils.checkNull(tpidict['Referencecolumn']['UNIVERSEOBJECT'][row])
                            self.properties['UNIVERSECLASS'] = Utils.checkNull(tpidict['Referencecolumn']['UNIVERSECLASS'][row])
                            self.properties['UNIVERSECONDITION'] = Utils.checkNull(tpidict['Referencecolumn']['UNIVERSECONDITION'][row])
                
                if self.attributeType == 'measurementCounter' and 'VECTOR' in self.properties['COUNTERTYPE'].upper():
                    if 'Measurementvector' in tpidict:
                        for row in tpidict['Measurementvector']['VINDEX']:
                            if self.name == tpidict['Measurementvector']['DATANAME'][row] and tpidict['Measurementvector']['TYPEID'][row] == self.typeid:
                                vendRel = tpidict['Measurementvector']['VENDORRELEASE'][row]
                                if vendRel not in self.vectors:
                                    self.vectors[vendRel] = {}
                                vector = TPM.Vector(self.typeid, self.name,tpidict['Measurementvector']['VINDEX'][row], vendRel)
                                vector._getPropertiesFromTPI(tpidict)
                                self.vectors[vendRel][tpidict['Measurementvector']['VINDEX'][row]] = vector

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
            
            for Name, Value in xlsDict.iteritems():
                if Name == 'Vectors':
                    for qtyLabel, qtyVal in Value.iteritems():
                        for qty, Val in qtyVal.iteritems():
                            for vendRel, indices in Val.iteritems():
                                if qty not in self.vectors:
                                    self.vectors[qty] = {}
                                
                                if vendRel not in self.vectors[qty]:
                                    self.vectors[qty][vendRel] = {}
                        
                                for index, properties in indices.iteritems():
                                    vector = TPM.Vector(self.typeid, self.name, index, vendRel, qty)
                                    vector._getPropertiesFromXls(properties)
                                    self.vectors[qty][vendRel][index] = vector
                        
                else:
                    self.properties[Name] = Value

        self._completeModel()

    def _getPropertiesFromXlsx(self,xlsxDict):
        '''Populate the objects contents from a XlsxDict object.
        
        Exceptions: 
                   Raised if XlsDict and filename are both None (ie nothing to process)
        '''
        
        tablename = self.typeid.split(':')[2]
        for Name, Value in xlsxDict['Attributes'][tablename][self.name].iteritems():
            if Name != 'TABLENAME' and Name != 'NAME':
                self.properties[Name] = Value
        
        if tablename in xlsxDict['Vectors']:   
            if self.name in xlsxDict['Vectors'][tablename]:
                for quant, Val in xlsxDict['Vectors'][tablename][self.name].iteritems():
                    for vendRel, indices in Val.iteritems():
                        if quant not in self.vectors:
                            self.vectors[quant] = {}
                            
                        if vendRel not in self.vectors[quant]:
                            self.vectors[quant][vendRel] = {}
                    
                        for index, properties in indices.iteritems():
                            vector = TPM.Vector(self.typeid, self.name, index, vendRel, quant)
                            vector._getPropertiesFromXlsx(properties)
                            self.vectors[quant][vendRel][index] = vector
                        
        self._completeModel()
                
    
    def _toXLSX(self, xlsxFile,  workbook, tableName):
        ''' Converts the object to an excel document
        
        Parent toXLSX() method is responsible for triggering child object toXLSX() methods
        '''
        if self.attributeType == 'measurementKey':
            sheet = workbook.getSheet('Keys')
            rowNumber = sheet.getLastRowNum() + 1
            list = xlsxFile.FTKeysList
            xlsxFile.writeToWorkbook(sheet, rowNumber, xlsxFile.findValue(sheet, 'TABLENAME').getColumnIndex(), tableName)
            xlsxFile.writeToWorkbook(sheet, rowNumber, xlsxFile.findValue(sheet, 'NAME').getColumnIndex(), self.name)
        
        if self.attributeType == 'measurementCounter':
            sheet = workbook.getSheet('Counters')
            rowNumber = sheet.getLastRowNum() + 1
            list = xlsxFile.FTCountersList
            xlsxFile.writeToWorkbook(sheet, rowNumber, xlsxFile.findValue(sheet, 'TABLENAME').getColumnIndex(), tableName)
            xlsxFile.writeToWorkbook(sheet, rowNumber, xlsxFile.findValue(sheet, 'NAME').getColumnIndex(), self.name)
        
        if self.attributeType == 'referenceKey':
            sheet = workbook.getSheet('Top Keys')
            rowNumber = sheet.getLastRowNum() + 1
            list = xlsxFile.TopKeysList
            xlsxFile.writeToWorkbook(sheet, rowNumber, xlsxFile.findValue(sheet, 'TABLENAME').getColumnIndex(), tableName)
            xlsxFile.writeToWorkbook(sheet, rowNumber, xlsxFile.findValue(sheet, 'NAME').getColumnIndex(), self.name)
        
        for FDColumn in list:
            if FDColumn in self.properties.keys():
                value = self.properties[FDColumn]
                
                if FDColumn != 'FOLLOWJOHN':
                    if value == 1 or value == '1':  
                        value = 'Y'
                    elif value == 0 or value == '0':
                        value = ''
                
                if FDColumn == 'DATATYPE':
                    value = self._createDataTypeForXls()
                xlsxFile.writeToWorkbook(sheet, rowNumber, xlsxFile.findValue(sheet, FDColumn).getColumnIndex(), str(value))
        
        for quant in self.vectors.itervalues():
            for indices in quant.itervalues():
                for vector in indices.itervalues():
                    vector._toXLSX(xlsxFile, workbook, tableName, self.name)

    def _getPropertiesFromXML(self,xmlElement):
        '''Populates the objects content from an xmlElement.
        The method is also responsible for triggering its child objects getPropertiesFromXML() method'''
        
        for elem1 in xmlElement:
            if elem1.tag=='Vectors':
                    for elem2 in elem1:
                        if elem2.tag=='Vector':
                            vendRel = elem2.attrib['VendorRelease']
                            index = elem2.attrib['index']
                            if vendRel not in self.vectors:
                                self.vectors[vendRel] = {}
                            vector = TPM.Vector(self.typeid, self.name, index, vendRel)
                            vector._getPropertiesFromXML(elem2)
                            self.vectors[vendRel][index] = vector

            elif elem1.text is None:
                self.properties[elem1.tag] = ''
            else:
                self.properties[elem1.tag] = Utils.safeNull(elem1.text)

    def _toXML(self,indent=0):
        '''Write the object to an xml formatted string
        Offset value is used for string indentation. Default to 0
        Parent toXML() method is responsible for triggering child object toXML() methods.
        Return Value: xmlString 
        '''
        offset = '    '
        os = "\n" + offset*indent
        os2 = os + offset

        outputXML = os+'<Attribute name="'+self.name+ '" attributeType ="'+self.attributeType +'">' 
        for attr in self.properties:
            outputXML += os2+'<'+str(attr)+'>'+Utils.escape(self.properties[attr])+'</'+str(attr)+'>'
        
        outputXML += os2+'<Vectors>'
        for vector in sorted(self.vectors.keys()):
            for index in sorted(self.vectors[vector].keys()):
                outputXML += self.vectors[vector][index]._toXML(indent+2)
        outputXML += os2+'</Vectors>'
        outputXML += os+'</Attribute>'
        return outputXML

    def difference(self,attObject,deltaObj=None):
        '''Calculates the difference between two attribute objects
        
        Method takes attObject,deltaObj and deltaTPV as inputs.
        attObject: The table to be compared against
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
            deltaObj = Utils.Delta(self.name,attObject.name)
        
        ############################################## Properties Difference #####################################################
        deltaObj.location.append('Properties') 

        Delta = Utils.DictDiffer(self.properties,attObject.properties)
        for item in Delta.changed():
            deltaObj.addChange('<Changed>', item, self.properties[item], attObject.properties[item])
    
        for item in Delta.added():
            deltaObj.addChange('<Added>', item, '', attObject.properties[item])
                
        for item in Delta.removed():
            deltaObj.addChange('<Removed>', item, self.properties[item], '')
        
        deltaObj.location.pop()
        
        ############################################## Vectors Difference #####################################################
        deltaObj.location.append('Vectors')

        Delta = Utils.DictDiffer(self.vectors,attObject.vectors)        
        for item in Delta.added():
            deltaObj.addChange('<Added>', item, '', item)
                
        for item in Delta.removed():
            deltaObj.addChange('<Removed>', item, item, '')
            
        for item in Delta.changed():
            indexDelta = Utils.DictDiffer(self.vectors[item],attObject.vectors[item])
            for entry in indexDelta.added():
                deltaObj.addChange('<Added>', item, '', entry)
                    
            for entry in indexDelta.removed():
                deltaObj.addChange('<Removed>', +entry, entry, '')
                
            for entry in indexDelta.changed():
                self.vectors[item][entry].difference(attObject.vectors[item][entry],deltaObj)

        
        deltaObj.location.pop()

        return deltaObj
    
    def populateRepDbDicts(self):
        RepDbDict = {}
        RepDbDict = deepcopy(self.properties)
        RepDbDict['DATANAME'] = self.name
        
        if self.attributeType == 'measurementCounter':
            RepDbDict['COUNTERPROCESS'] = self.properties['COUNTERTYPE']
            return RepDbDict
        
        elif self.attributeType == 'measurementKey':
            RepDbDict['UNIQUEVALUE'] = 255
            RepDbDict['ROPGRPCELL'] = 0
            return RepDbDict
        
        elif self.attributeType == 'referenceKey':
            RepDbDict['UNIQUEVALUE'] = 255
            RepDbDict['INDEXES'] = 'HG'
            RepDbDict['COLTYPE'] = 'COLUMN'
            RepDbDict['BASEDEF'] = 0
            return RepDbDict

    def _completeModel(self):
        if self.attributeType == 'measurementCounter':
            if 'INCLUDESQL' not in self.properties or self.properties['INCLUDESQL'] == '':
                self.properties['INCLUDESQL'] = '0'
        
        elif self.attributeType == 'measurementKey':
            if 'ISELEMENT' not in self.properties or self.properties['ISELEMENT'] == '':
                self.properties['ISELEMENT'] = '0'
            if 'UNIQUEKEY' not in self.properties or self.properties['UNIQUEKEY'] == '':
                self.properties['UNIQUEKEY'] = '0'
            if 'INCLUDESQL' not in self.properties or self.properties['INCLUDESQL'] == '':
                self.properties['INCLUDESQL'] = '0'
            if 'NULLABLE' not in self.properties or self.properties['NULLABLE'] == '':
                self.properties['NULLABLE'] = '0'
            if 'JOINABLE' not in self.properties or self.properties['JOINABLE'] == '':
                self.properties['JOINABLE'] = '0'
                 
        elif self.attributeType == 'referenceKey':
            if 'UNIQUEKEY' not in self.properties or self.properties['UNIQUEKEY'] == '':
                self.properties['UNIQUEKEY'] = '0'
            if 'NULLABLE' not in self.properties or self.properties['NULLABLE'] == '':
                self.properties['NULLABLE'] = '0'
                
        if 'DATAID' not in self.properties or self.properties['DATAID'] == '':
                self.properties['DATAID'] = ''
    
    def _createDataTypeForXls(self):
        dataype = self.properties['DATATYPE']
        if 'DATASIZE' in self.properties.keys():
            if self.properties['DATASIZE'] != '':
                dataype = dataype + '('+str(self.properties['DATASIZE'])
                if 'DATASCALE' in self.properties.keys():
                    if self.properties['DATASCALE'] != '':
                        dataype = dataype + ','+str(self.properties['DATASCALE'])
                dataype = dataype + ')'
        return dataype