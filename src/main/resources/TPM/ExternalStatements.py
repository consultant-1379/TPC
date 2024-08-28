'''
Created on May 30, 2016

@author: ebrifol
'''

import TPM
import Utils
import os
from copy import deepcopy

class ExternalStatement(object):
    '''Class to represent ExternalStatement object. A child object of TechPack Version'''


    def __init__(self,versionID, name):
        self.versionID = versionID
        self.name = name
        self.properties = Utils.odict()
    
    def _getPropertiesFromServer(self, DbCursor, NoOfBaseES=None):
        '''Get all the properties associated with the External statement object
        
        SQL Executed:
                    SELECT EXECUTIONORDER,DBCONNECTION,STATEMENT,\BASEDEF FROM ExternalStatement WHERE VERSIONID =? AND STATEMENTNAME =?
        '''
        
        if NoOfBaseES == None:
            NoOfBaseES = 0
        
        DbCursor.execute("SELECT EXECUTIONORDER,DBCONNECTION,STATEMENT FROM ExternalStatement WHERE VERSIONID =? AND STATEMENTNAME =? and BASEDEF=?", (self.versionID, self.name,'0',))
        resultset = DbCursor.fetchall()
        for row in resultset:
            self.properties['DBCONNECTION'] = str(row[1])
            self.properties['STATEMENT'] = str(row[2]).strip()
            ExecOrder = Utils.strFloatToInt(str(row[0]))
            self.properties['EXECUTIONORDER'] = str(int(ExecOrder) - NoOfBaseES)
    
    def _getPropertiesFromTPI(self,tpiDict=None,filename=None, ExecOrder=None):
        '''Populate the objects contents from a tpiDict object or tpi file.
        
        If a tpi file is passed it is converted to a tpiDict object before processing.

        Exceptions: 
                   Raised if tpiDict and filename are both None (ie nothing to process)'''
        
        if tpiDict==None and filename==None:
            strg = 'getPropertiesFromTPI() Nothing to Process'
            raise Exception(strg)
        else:
            if filename is not None:
                tpiDict = Utils.TpiDict(filename).returnTPIDict()
        for row in tpiDict['Externalstatement']['STATEMENTNAME']:
            if tpiDict['Externalstatement']['STATEMENTNAME'][row] == self.name:
                self.properties['DBCONNECTION'] = tpiDict['Externalstatement']['DBCONNECTION'][row]
                self.properties['STATEMENT'] = tpiDict['Externalstatement']['STATEMENT'][row]
                if ExecOrder != None:
                    self.properties['EXECUTIONORDER'] = str(ExecOrder)
                else:
                    self.properties['EXECUTIONORDER'] = tpiDict['Externalstatement']['EXECUTIONORDER'][row]
    
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
            
            for Name, Value in xlsDict['ExternalStatements'][self.name].iteritems():
                self.properties[Name] = Value
    
    def _getPropertiesFromXlsx(self,xlsxDict):
        '''Populate the objects contents from a XlsxDict object.
        
        Exceptions: 
                   Raised if XlsDict and filename are both None (ie nothing to process)
        '''
        
        for Name, Value in xlsxDict['ES'][self.name].iteritems():
            self.properties[Name] = Value
        
    
    def _toXLSX(self, xlsxFile,  workbook, xlsxPath):
        ''' Converts the object to an excel document
        
        Parent toXLSX() method is responsible for triggering child object toXLSX() methods
        '''
        
        sheet = workbook.getSheet('External Statements')
        xlsxFile.writeToWorkbook(sheet, int(self.properties['EXECUTIONORDER']), xlsxFile.findValue(sheet, 'NAME').getColumnIndex(), self.name)
        
        for FDColumn in xlsxFile.ESList:
            if FDColumn in self.properties.keys():
                value = self.properties[FDColumn]
                if FDColumn == 'STATEMENT' and len(value) > 32000:
                    EFfilename = xlsxPath.replace('.xlsx' , '.txt')
                    ESFile = open(EFfilename, 'a')
                    ESFile.write('@@'+self.name+'=='+self.properties['STATEMENT'])
                    ESFile.close()
                    xlsxFile.writeToWorkbook(sheet, int(self.properties['EXECUTIONORDER']), xlsxFile.findValue(sheet, FDColumn).getColumnIndex(), os.path.basename(ESFile.name))
                else:                
                    xlsxFile.writeToWorkbook(sheet, int(self.properties['EXECUTIONORDER']), xlsxFile.findValue(sheet, FDColumn).getColumnIndex(), value)
                
                
    
    def _getPropertiesFromXML(self,xmlElement):
        '''Populates the objects content from an xmlElement
        
        The method is also responsible for triggering its child objects getPropertiesFromXML() method'''
        for elem in xmlElement:
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
        
        outputXML = os+'<ExternalStatement name="' + self.name + '">'
        for prop in self.properties:
            outputXML += os2+'<'+prop+'>'+ Utils.escape(self.properties[prop]) +'</'+prop+'>'
        outputXML += os+'</ExternalStatement>'   
        return outputXML
    
    def populateRepDbDicts(self):
        RepDbDict = deepcopy(self.properties)
        RepDbDict['VERSIONID'] = self.versionID
        RepDbDict['STATEMENTNAME'] = self.name
        RepDbDict['BASEDEF'] = 0
        return RepDbDict

    def difference(self,extStateObject,deltaObj=None):
        '''Calculates the difference between two external statement objects
            
            Method takes extStateObject,deltaObj and deltaTPV as inputs.
            extStateObject: The External Statement to be compared against
            DeltaObj: The single object that gets passed through the entire diff recording the changes.
            DeltaTPV: A TechPackVersion Object that gets passed through the entire diff recording only new content.
            
            The Difference method will trigger the difference method of its child objects, passing
            in the object to compare, deltaObj and deltaTPV. After calculating the diff the child object passes these objects
            back in conjunction with a flag to say whether a (only new or changed content.. not deleted) was found or not. This flag is used to decide
            whether a child object should be added to the parent object in the DeltaTPV.
            
            Note: External statement does not have any child objects
            
            Returns:
                    diffFlag (Boolean indicating where a change was found or not)
                    deltaObj
                    deltaTPV 
            
        '''
        if deltaObj is None:
            deltaObj = Utils.Delta(self.name,extStateObject.name)
        
        deltaObj.location.append('Properties') 

        Delta = Utils.DictDiffer(self.properties,extStateObject.properties)
        for item in Delta.changed():
            deltaObj.addChange('<Changed>', item, self.properties[item], extStateObject.properties[item])
    
        for item in Delta.added():
            deltaObj.addChange('<Added>', item, '', extStateObject.properties[item])
                
        for item in Delta.removed():
            deltaObj.addChange('<Removed>', item, self.properties[item], '')
        
        deltaObj.location.pop()

        return deltaObj
        