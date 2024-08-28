'''
Created on May 30, 2016

@author: ebrifol
'''

import Utils
from copy import deepcopy

class Vector(object):

    def __init__(self,typeid, parentAttName, Index, VendorRelease, Quantity):
        self.typeid = typeid
        self.parentAttName = parentAttName
        self.VendorRelease = VendorRelease
        self.Index = Index
        self.Qty = Quantity
        self.properties = Utils.odict()
    
    def _getPropertiesFromServer(self,DbCursor): 
        DbCursor.execute("SELECT VFROM,VTO,MEASURE,QUANTITY from dwhrep.MeasurementVector WHERE TYPEID=? AND DATANAME=? AND VINDEX=? AND VENDORRELEASE=?",(self.typeid, self.parentAttName,self.Index,self.VendorRelease,))
            
        resultset = DbCursor.fetchall()
        desc = DbCursor.description
        for row in resultset: 
            i = 0
            for x in desc:
                value = str(row[i]).strip()
                if x[0] == 'QUANTITY':
                    value = value.split('.')[0]
        
                self.properties[x[0]] = Utils.checkNull(value)
                i+=1
    
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
                
            for row in tpidict['Measurementvector']['VINDEX']:
                if self.parentAttName == tpidict['Measurementvector']['DATANAME'][row] and tpidict['Measurementvector']['TYPEID'][row] == self.typeid:
                    if self.Index == tpidict['Measurementvector']['VINDEX'][row] and tpidict['Measurementvector']['VENDORRELEASE'][row] == self.VendorRelease:
                        self.properties['VFROM'] = Utils.checkNull(tpidict['Measurementvector']['VFROM'][row])
                        self.properties['VTO'] = Utils.checkNull(tpidict['Measurementvector']['VTO'][row])
                        self.properties['MEASURE'] = Utils.checkNull(tpidict['Measurementvector']['MEASURE'][row])
                        self.properties['QUANTITY'] = Utils.checkNull(tpidict['Measurementvector']['QUANTITY'][row]).split('.')[0]
    
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
                self.properties[Name] = Value
    
    def _getPropertiesFromXlsx(self,xlsxDict):
        '''Populate the objects contents from a XlsxDict object.
        
        Exceptions: 
                   Raised if XlsDict and filename are both None (ie nothing to process)
        '''
        
        for Name, Value in xlsxDict.iteritems():
            if Name != 'TABLENAME' and Name != 'NAME' and Name != 'VENDORRELEASE' and Name != 'VINDEX' and Name != 'QUANTITY':
                self.properties[Name] = Value
        
    def _toXLSX(self, xlsxFile, workbook, tableName, AttName):
        ''' Converts the object to an excel document
        
        Parent toXLSX() method is responsible for triggering child object toXLSX() methods
        '''
        
        sheet = workbook.getSheet('Vectors')
        rowNumber = sheet.getLastRowNum() + 1
        
        xlsxFile.writeToWorkbook(sheet, rowNumber, xlsxFile.findValue(sheet, 'TABLENAME').getColumnIndex(), tableName)
        xlsxFile.writeToWorkbook(sheet, rowNumber, xlsxFile.findValue(sheet, 'NAME').getColumnIndex(), AttName)
        xlsxFile.writeToWorkbook(sheet, rowNumber, xlsxFile.findValue(sheet, 'VENDORRELEASE').getColumnIndex(), self.VendorRelease)
        xlsxFile.writeToWorkbook(sheet, rowNumber, xlsxFile.findValue(sheet, 'VINDEX').getColumnIndex(), self.Index)
        xlsxFile.writeToWorkbook(sheet, rowNumber, xlsxFile.findValue(sheet, 'QUANTITY').getColumnIndex(), self.Qty)
            
        for FDColumn in xlsxFile.VectorsList:
            if FDColumn in self.properties.keys():
                value = self.properties[FDColumn]
                xlsxFile.writeToWorkbook(sheet, rowNumber, xlsxFile.findValue(sheet, FDColumn).getColumnIndex(), str(value))
    
    def _getPropertiesFromXML(self,xmlElement):
        '''Populates the objects content from an xmlElement.
        The method is also responsible for triggering its child objects getPropertiesFromXML() method'''
        
        for elem in xmlElement:
            if elem.text is None:
                self.properties[elem.tag] = ''
            else:
                self.properties[elem.tag] = Utils.safeNull(elem.text)
    
    def _toXML(self,indent=0):
        '''Write the object to an xml formatted string
        Offset value is used for string indentation. Default to 0
        Parent toXML() method is responsible for triggering child object toXML() methods.
        Return Value: xmlString 
        '''
        offset = '    '
        os = "\n" + offset*indent
        os2 = os + offset

        outputXML  =os+'<Vector VendorRelease="'+self.VendorRelease+ '" index ="'+self.Index +'">' 
        for attr in self.properties:
            outputXML += os2+'<'+str(attr)+'>'+Utils.escape(self.properties[attr])+'</'+str(attr)+'>'

        outputXML +=os+'</Vector>'
        return outputXML
    
    def populateRepDbDicts(self):
        RepDbDict = {}
        RepDbDict = deepcopy(self.properties)
        RepDbDict['VINDEX'] = Utils.strFloatToInt(self.Index)
        RepDbDict['TYPEID'] = self.typeid
        RepDbDict['DATANAME'] = self.parentAttName
        #RepDbDict['VENDORRELEASE'] = self.VendorRelease
        RepDbDict['QUANTITY'] = Utils.strFloatToInt(self.Qty)
        
        return RepDbDict
    
    def difference(self,VecObject,deltaObj=None):
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
            deltaObj = Utils.Delta(self.Index,VecObject.Index)
        
        ############################################## Properties Difference #####################################################
        deltaObj.location.append('Properties') 

        Delta = Utils.DictDiffer(self.properties,VecObject.properties)
        for item in Delta.changed():
            deltaObj.addChange('<Changed>', item, self.properties[item], VecObject.properties[item])
    
        for item in Delta.added():
            deltaObj.addChange('<Added>', item, '', VecObject.properties[item])
                
        for item in Delta.removed():
            deltaObj.addChange('<Removed>', item, self.properties[item], '')
        
        deltaObj.location.pop()
        