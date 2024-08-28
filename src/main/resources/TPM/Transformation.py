'''
Created on May 30, 2016

@author: ebrifol
'''

import Utils
import hashlib

class Transformation(object):
    '''Class to represent a transformation. Child object of Parser class.'''
    
    def __init__(self,rowID,transformerID):
        self.rowID = str(rowID)
        self.transformerID = transformerID
        self.properties = Utils.odict() 
        self._hash = None
        
    def _getPropertiesFromServer(self,DbCursor):
        '''Populates the properties dictionary of the transformation from the server
        
        SQL Statement: 
                    SELECT TYPE,SOURCE,TARGET,CONFIG FROM Transformation where TRANSFORMERID=? AND ORDERNO=?
        '''

        DbCursor.execute("SELECT TYPE,SOURCE,TARGET,CONFIG FROM Transformation where TRANSFORMERID=? AND ORDERNO=?",(self.transformerID,self.rowID,))
        desc = DbCursor.description   
        row = DbCursor.fetchone()
        if row is not None:
            i = 0
            for x in desc:    
                val = str(row[i]).strip()
                self.properties[str(x[0])] = val
                i+=1
    
    def _getPropertiesFromTPI(self,tpiDict=None,filename=None):
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
            for row in tpiDict['Transformation']['TRANSFORMERID']:
                if tpiDict['Transformation']['TRANSFORMERID'][row].lower() == self.transformerID.lower() and tpiDict['Transformation']['ORDERNO'][row] == self.rowID:
                    
                    self.properties['TYPE'] = Utils.checkNull(tpiDict['Transformation']['TYPE'][row])
                    self.properties['SOURCE'] = Utils.checkNull(tpiDict['Transformation']['SOURCE'][row])
                    self.properties['TARGET'] = Utils.checkNull(tpiDict['Transformation']['TARGET'][row])
                    self.properties['CONFIG'] = Utils.checkNull(tpiDict['Transformation']['CONFIG'][row])
    
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
            if Name != 'TABLENAME' and Name != 'PARSERNAME':
                self.properties[Name] = Value
                
    
    def _toXLSX(self, xlsxFile, workbook):
        ''' Converts the object to an excel document
            
            Parent toXLSX() method is responsible for triggering child object toXLSX() methods
        '''
        
        tableName = self.transformerID.split(':')[2]
        parserName = self.transformerID.split(':')[3]
        
        sheet = workbook.getSheet('Transformations')
        rowNumber = sheet.getLastRowNum() + 1
        
        xlsxFile.writeToWorkbook(sheet, rowNumber, xlsxFile.findValue(sheet, 'PARSERNAME').getColumnIndex(), parserName)
        xlsxFile.writeToWorkbook(sheet, rowNumber, xlsxFile.findValue(sheet, 'TABLENAME').getColumnIndex(), tableName)
        
        for FDColumn in xlsxFile.TransList:
            if FDColumn in self.properties.keys():
                value = self.properties[FDColumn]
                xlsxFile.writeToWorkbook(sheet, rowNumber, xlsxFile.findValue(sheet, FDColumn).getColumnIndex(), str(value))
    
    def _getPropertiesFromXML(self,xmlElement):
            '''Populates the objects content from an xmlElement.'''
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
            
            outputXML = os + '<OrderNo index="'+str(self.rowID)+'">' 
            outputXML += os2+'<'"TYPE"'>'+Utils.escape(self.properties['TYPE'])+'<'"/TYPE"'>'
            outputXML += os2+'<'"SOURCE"'>'+Utils.escape(self.properties['SOURCE'])+'<'"/SOURCE"'>'
            outputXML += os2+'<'"TARGET"'>'+Utils.escape(self.properties['TARGET'])+'<'"/TARGET"'>'
            outputXML += os2+'<'"CONFIG"'>'+Utils.escape(self.properties['CONFIG'])+'<'"/CONFIG"'>'
            outputXML += os+'<'"/OrderNo"'>'
            return outputXML
    
    def _getHash(self):
        '''Calculates a hash value for the transformation, used for diffing at the parser object level'''
        if self._hash == None:
            m = hashlib.md5()
            for prop in sorted(self.properties.iterkeys()):
                if self.properties[prop] is None:
                    m.update("")
                else: 
                    m.update(self.properties[prop])
            self._hash = m.digest()
        return self._hash
    
    def populateRepDbDicts(self):
        RepDbDict = {}
        RepDbDict['TRANSFORMERID'] = self.transformerID
        RepDbDict['ORDERNO'] = self.rowID
        RepDbDict['TYPE'] = self.properties['TYPE']
        RepDbDict['SOURCE'] = self.properties['SOURCE']
        RepDbDict['TARGET'] = self.properties['TARGET']
        RepDbDict['CONFIG'] = self.properties['CONFIG']
        RepDbDict['DESCRIPTION'] = ''
        return RepDbDict
        