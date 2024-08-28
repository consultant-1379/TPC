'''
Created on Jun 1, 2016

@author: ebrifol
'''

import Utils
import UM
from copy import deepcopy

class UniverseJoin(object):
    
    def __init__(self,versionID,unvextension,sourceColumn,sourceTable,targetColumn,targetTable,tmpCounter):
        self.versionID = versionID
        self.universeExtension=unvextension
        self.sourceColumn = sourceColumn
        self.sourceTable = sourceTable # refactor to list
        self.sourceTableList = sourceTable.split(',')
        self.targetColumn = targetColumn
        self.targetTable = targetTable
        self.tmpCounter = tmpCounter # is this needed?
        self.properties = Utils.odict() 
        self.contextList = []
        self.joinID = sourceColumn + ":" + sourceTable + ":" + targetColumn + ":" + targetTable
    
    def _getPropertiesFromServer(self,DbCursor): 
        DbCursor.execute("SELECT SOURCELEVEL,TARGETLEVEL,CARDINALITY,CONTEXT,EXCLUDEDCONTEXTS FROM dwhrep.UniverseJoin where versionid =? and sourceColumn=? and sourceTable=? and targetColumn=? and targettable=?",(self.versionID,self.sourceColumn,self.sourceTable,self.targetColumn,self.targetTable))
        row = DbCursor.fetchone()
        desc = DbCursor.description
        if row is not None:
            i = 0
            for x in desc:
                self.properties[x[0]] = str(row[i])
                i+=1
        self._contextSplit()
    
    def _getPropertiesFromTPI(self,tpiDict):
        for row in tpiDict['Universejoin']['CONTEXT']:
            srcc = tpiDict['Universejoin']['SOURCECOLUMN'][row]
            srct = tpiDict['Universejoin']['SOURCETABLE'][row]
            tgtc = tpiDict['Universejoin']['TARGETCOLUMN'][row]
            tgtt = tpiDict['Universejoin']['TARGETTABLE'][row]
            uniext = 'ALL'
            try:
                uniext = tpiDict['Universejoin']['UNIVERSEEXTENSION'][row]
            except:
                pass
            if uniext == '':
                uniext = 'ALL'
            if self.sourceColumn == srcc and self.sourceTable == srct and self.targetTable == tgtt and self.targetColumn == tgtc and self.universeExtension.upper() in uniext.upper():    
                cols = ('SOURCELEVEL','TARGETLEVEL','CARDINALITY','CONTEXT','EXCLUDEDCONTEXTS')
                for col in cols:
                    self.properties[col] = tpiDict['Universejoin'][col][row]
    
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
                if Name != 'SOURCETABLE' and Name != 'SOURCECOLUMN' and Name != 'TARGETTABLE' and Name != 'TARGETCOLUMN' and Name != 'UNIVERSEEXTENSION':
                    self.properties[Name] = Value
    
    def _getPropertiesFromXlsx(self,xlsxDict):
        '''Populate the objects contents from a XlsxDict object.
        
        Exceptions: 
                   Raised if XlsDict and filename are both None (ie nothing to process)
        '''
        
        for Name, Value in xlsxDict.iteritems():
            if Name != 'SOURCETABLE' and Name != 'SOURCECOLUMN' and Name != 'TARGETTABLE' and Name != 'TARGETCOLUMN' and Name != 'UNIVERSEEXTENSION':
                self.properties[Name] = Value
        
                    
    def _toXLSX(self, xlsxFile, workbook):
        ''' Converts the object to an excel document
        
        Parent toXLSX() method is responsible for triggering child object toXLSX() methods
        '''
        
        sheet = workbook.getSheet('Unv Joins')
        rowNumber = sheet.getLastRowNum() + 1
        
        addRow = True
        for row in sheet:
            sourceTable = row.getCell(xlsxFile.findValue(sheet, 'SOURCETABLE').getColumnIndex()).toString()
            sourceColumn = row.getCell(xlsxFile.findValue(sheet, 'SOURCECOLUMN').getColumnIndex()) # sourceColumn = sheet.getColumn(sheet.findCell('Source Columns').getColumn())[SourceTableCell.getRow()]
            targetTable = row.getCell(xlsxFile.findValue(sheet, 'TARGETTABLE').getColumnIndex())
            targetColumn = row.getCell(xlsxFile.findValue(sheet, 'TARGETCOLUMN').getColumnIndex())                
            if sourceTable == self.sourceTable and sourceColumn == self.sourceColumn and targetTable == self.targetTable and targetColumn == self.targetColumn:
                addRow = False
        
        if addRow:
            xlsxFile.writeToWorkbook(sheet, rowNumber, xlsxFile.findValue(sheet, 'SOURCETABLE').getColumnIndex(), self.sourceTable)
            xlsxFile.writeToWorkbook(sheet, rowNumber, xlsxFile.findValue(sheet, 'SOURCECOLUMN').getColumnIndex(), self.sourceColumn)
            xlsxFile.writeToWorkbook(sheet, rowNumber, xlsxFile.findValue(sheet, 'TARGETTABLE').getColumnIndex(), self.targetTable)
            xlsxFile.writeToWorkbook(sheet, rowNumber, xlsxFile.findValue(sheet, 'TARGETCOLUMN').getColumnIndex(), self.targetColumn)
            xlsxFile.writeToWorkbook(sheet, rowNumber, xlsxFile.findValue(sheet, 'UNIVERSEEXTENSION').getColumnIndex(), self.universeExtension)
            
            for FDColumn in xlsxFile.UniJoinsList:
                if FDColumn in self.properties.keys():
                    value = self.properties[FDColumn]
                    xlsxFile.writeToWorkbook(sheet, rowNumber, xlsxFile.findValue(sheet, FDColumn).getColumnIndex(), str(value))
    
    def _getPropertiesFromXML(self,xmlElement):
        for elem in xmlElement:
            if elem.text is None:
                self.properties[elem.tag] = ''
            else:
                self.properties[elem.tag] = Utils.safeNull(elem.text)
        self._contextSplit()
    
    def _toXML(self,indent=0):
        offset = '    '
        os = "\n" + offset*indent
        os2 = os + offset
        
        outputXML = os+ '<UniverseJoin sourceColumn="'+self.sourceColumn+'" sourceTable="'+self.sourceTable+'" targetColumn="'+self.targetColumn+'" targetTable="'+self.targetTable+'">'
        for prop in self.properties:
            outputXML += os2 +'<'+str(prop)+'>'+ Utils.escape(self.properties[prop]) +'</'+str(prop)+'>'
        outputXML +=os+ '</UniverseJoin>'
        return outputXML
    
    def populateRepDbDicts(self):
        RepDbDict = {}        
        RepDbDict = deepcopy(self.properties)
        RepDbDict['VERSIONID'] = self.versionID
        RepDbDict['SOURCECOLUMN'] = self.sourceColumn
        RepDbDict['SOURCETABLE'] = self.sourceTable      
        RepDbDict['TARGETCOLUMN'] = self.targetColumn
        RepDbDict['TARGETTABLE'] = self.targetTable
        RepDbDict['TMPCOUNTER'] = self.tmpCounter
        RepDbDict['UNIVERSEEXTENSION']=self.universeExtension

        return RepDbDict
    
    def difference(self,UniObj,deltaObj=None):
        
        if deltaObj is None:
            deltaObj = Utils.Delta(self.joinID,UniObj.joinID)
         
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
        
        return deltaObj
    
    def _contextSplit(self):
        if 'CONTEXT' in self.properties.iterkeys():
            self.contextList = self.properties['CONTEXT'].split(',')
    
    def getJoinId(self):
        return self.joinID
        