'''
Created on May 30, 2016

@author: ebrifol
'''

import TPM
import Utils
import copy

class Parser(object):
    '''Class to represent a parser object. Identified by VersionID, parentTableName and parserType. Child object of TechPackVersion'''

    def __init__(self,versionID,parentTableName,parserType):
        self.versionID = versionID
        self.parserType = parserType 
        self.parentTableName = parentTableName
        self.transformations = []
        self.attributeTags = Utils.odict()
        self.dataTags = [] # stores the mappings between table names and their data tags
        self.dataFormatID = self.versionID + ":" + self.parentTableName + ":" + self.parserType
        self.transformerID = self.versionID + ":" + self.parentTableName + ":" + self.parserType
        self.parentAttributeNames = [] # This is used to only get TP specific information. Should not load data from base TP
    
    def _getPropertiesFromServer(self,DbCursor):
        ''''Gets all properties (and child objects) from the server
    
        In this particular case Parser objects dont have a properties dictionary.
        They have transformation objects,tagids and dataids associated with them'''
        
        self._getTransformations(DbCursor)
        if not self.parentTableName.endswith('BH'):
            
            DbCursor.execute("SELECT TAGID FROM DefaultTags where DATAFORMATID=?",(self.dataFormatID,))
            resultset = DbCursor.fetchall()
            for row in resultset:
                self.dataTags.append(str(row[0]))


            DbCursor.execute("SELECT DATANAME,DATAID FROM DataItem where DATAFORMATID=?",(self.dataFormatID,))
            rows = DbCursor.fetchall()        
            for row in rows:
                if row is not None:
                    if row[0] in self.parentAttributeNames:
                        self.attributeTags[row[0]] = str(row[1])
        
    def _getTransformations(self,crsr):
        '''Gets transformation information for the server for the parser object,creates the transformation object and appends it
        to the list of transformationObjects'''
        
        crsr.execute("SELECT ORDERNO FROM Transformation where TRANSFORMERID=? ORDER BY ORDERNO",(self.transformerID,))
        row = crsr.fetchall()          
        for rowid in row:
            rowid = Utils.strFloatToInt(rowid[0])
            transformation = TPM.Transformation(rowid, self.transformerID)
            transformation._getPropertiesFromServer(crsr)
            self.transformations.append(transformation)     
    
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

        rowIDs = []
        for row in tpiDict['Transformation']['TRANSFORMERID']:
            if tpiDict['Transformation']['TRANSFORMERID'][row].lower() == self.transformerID.lower():
                if row in tpiDict['Transformation']['ORDERNO']:
                    rowIDs.append(int(tpiDict['Transformation']['ORDERNO'][row]))
        
        rowIDs.sort()           
        for rowid in rowIDs:
            transformation = TPM.Transformation(rowid ,self.transformerID)
            transformation._getPropertiesFromTPI(tpiDict)
            self.transformations.append(transformation)
        
        if not self.parentTableName.endswith('BH'):
            for row in tpiDict['Dataitem']['DATAFORMATID']:
                if tpiDict['Dataitem']['DATAFORMATID'][row].lower() == self.dataFormatID.lower():
                    if tpiDict['Dataitem']['DATANAME'][row] in self.parentAttributeNames:
                        self.attributeTags[tpiDict['Dataitem']['DATANAME'][row]] = tpiDict['Dataitem']['DATAID'][row]
            
            for row in tpiDict['Defaulttags']['DATAFORMATID']:
                if tpiDict['Defaulttags']['DATAFORMATID'][row].lower() == self.dataFormatID.lower():
                    self.dataTags.append(tpiDict['Defaulttags']['TAGID'][row])
    
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
                    
                rowIDs = xlsDict.keys()    
                rowIDs.sort()
                
                for rowid in rowIDs:
                    if rowid != 'DATATAGS' and rowid != 'ATTRTAGS':
                        transformation = TPM.Transformation(rowid ,self.transformerID)
                        transformation._getPropertiesFromXls(xlsDict[rowid])
                        self.transformations.append(transformation)
                        
                if 'DATATAGS' in xlsDict:
                    if ';' in xlsDict['DATATAGS']:
                        tableTags = xlsDict['DATATAGS'].split(';')
                        for tag in tableTags:
                            if tag != '':
                                self.dataTags.append(tag.strip())
                    else:
                        self.dataTags.append(xlsDict['DATATAGS'].strip())
                
                if 'ATTRTAGS' in xlsDict.keys():
                    for key, value in xlsDict['ATTRTAGS'].iteritems():
                        self.attributeTags[key] = value
    
    def _getPropertiesFromXlsx(self,xlsxDict):
        '''Populate the objects contents from a XlsxDict object.
        
        Exceptions: 
                   Raised if XlsDict and filename are both None (ie nothing to process)
        '''
        
        dataTags = xlsxDict['Tables'][self.parentTableName]['Parsers'][self.parserType] + ';'
        for tag in dataTags.split(';'):
            if tag != '':
                self.dataTags.append(tag.strip())
                
        if self.parentTableName in xlsxDict['DataFormat']:
            if self.parserType in xlsxDict['DataFormat'][self.parentTableName]:
                for Name, Value in xlsxDict['DataFormat'][self.parentTableName][self.parserType].iteritems():
                    if(Value!=None and Value.strip() != ''):
                        self.attributeTags[Name] = Value
        
        if self.parentTableName in xlsxDict['Trans']:
            if self.parserType in xlsxDict['Trans'][self.parentTableName]:
                rowIDs = xlsxDict['Trans'][self.parentTableName][self.parserType].keys()
                rowIDs.sort()
                
                for rowid in rowIDs:
                    transformation = TPM.Transformation(rowid ,self.transformerID)
                    transformation._getPropertiesFromXlsx(xlsxDict['Trans'][self.parentTableName][self.parserType][rowid])
                    self.transformations.append(transformation)
    
    def _toXLSX(self, xlsxFile, workbook, TransformationCollection):
        ''' Converts the object to an excel document
            
            Parent toXLSX() method is responsible for triggering child object toXLSX() methods
        '''
        
        sheet = workbook.getSheet('Data Format')
        rowNumber = sheet.getLastRowNum() + 1
        
        parserCell = xlsxFile.findHeaderValue(sheet, self.parserType)
        if parserCell == None:
            parserColumn = sheet.getRow(0).getLastCellNum()
            xlsxFile.writeToWorkbook(sheet, 0, parserColumn, self.parserType)
        else:
            parserColumn = parserCell.getColumnIndex()
        
        tableCell = xlsxFile.findValue(sheet, self.parentTableName)
        if tableCell != None:
            rowNumber = tableCell.getRowIndex()
        
        for AttName, format in sorted(self.attributeTags.iteritems()):            
            cellNumber = xlsxFile.findValue(sheet, 'TABLENAME').getColumnIndex()
            xlsxFile.writeToWorkbook(sheet, rowNumber, cellNumber, self.parentTableName)
            cellNumber = xlsxFile.findValue(sheet, 'ATTRIBUTENAME').getColumnIndex()
            xlsxFile.writeToWorkbook(sheet, rowNumber, cellNumber, AttName)
            xlsxFile.writeToWorkbook(sheet, rowNumber, parserColumn, format)
            rowNumber = rowNumber + 1
        
        
        if self.parentTableName.startswith('DIM'):
            sheet = workbook.getSheet('Top Tables')
            parserCell = xlsxFile.findHeaderValue(sheet, self.parserType)
            if parserCell == None:
                parserColumn = sheet.getRow(0).getLastCellNum()
                xlsxFile.writeToWorkbook(sheet, 0, parserColumn, self.parserType)
            else:
                parserColumn = parserCell.getColumnIndex()
            
            xlsxFile.writeToWorkbook(sheet, 0, parserColumn, self.parserType)
            
            topTableCell = xlsxFile.findValue(sheet, self.parentTableName)
                                                                                             
            if topTableCell is not None:
                rowNumber = topTableCell.getRowIndex()
                xlsxFile.writeToWorkbook(sheet, rowNumber, parserColumn, ";".join(self.dataTags))
                
        else:
            sheet = workbook.getSheet('Fact Tables')                                       
            parserCell = xlsxFile.findHeaderValue(sheet, self.parserType)
            if parserCell == None:
                parserColumn = sheet.getRow(0).getLastCellNum()
                xlsxFile.writeToWorkbook(sheet, 0, parserColumn, self.parserType)
            else:
                parserColumn = parserCell.getColumnIndex()
            
            xlsxFile.writeToWorkbook(sheet, 0, parserColumn, self.parserType)
            
            factTableCell = xlsxFile.findValue(sheet, self.parentTableName)
            
            if factTableCell is not None:
                rowNumber = factTableCell.getRowIndex()
                xlsxFile.writeToWorkbook(sheet, rowNumber, parserColumn, ";".join(self.dataTags))
                
        if self.parserType not in TransformationCollection:
            TransformationCollection[self.parserType] = {}
        
        for trans in self.transformations:
            TransformationCollection[self.parserType][int(trans.rowID)] = trans
        
        return TransformationCollection
    
    def _getPropertiesFromXML(self,xmlElement):
        '''Populates the objects content from an xmlElement.
        
        The method is also responsible for triggering its child objects getPropertiesFromXML() method'''
        index = 0 
        for elem in xmlElement:
            if elem.tag=='Transformations':
                for elem1 in elem:
                    if elem1.tag == "OrderNo":
                        transformation = TPM.Transformation(elem1.attrib['index'], self.transformerID)
                        transformation._getPropertiesFromXML(elem1)
                        self.transformations.append(transformation)
                        index = index + 1         
            
            if elem.tag == 'Dataformat':
                for elem1 in elem:
                    for elem2 in elem1:
                        if elem1.tag == "TableTags":
                            self.dataTags.append(elem2.text)
                        if elem1.tag == 'attributeTags':
                            self.attributeTags[elem2.tag]= elem2.text
    
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
        os4 = os3 + offset

        outputXML  = os+ '<Parser type="'+self.parserType+'">'

        outputXML +=os2+ '<Dataformat DataFormatID="'+self.transformerID+'">'
        tags = []
        for tag in self.dataTags:
            tags.append(tag)
        outputXML +=os3+'<TableTags>'
        for tag in tags:
            outputXML +=os4+ '<TableTag>'+str(tag)+'</TableTag>'
        outputXML +=os3+'</TableTags>'
        outputXML +=os3+'<attributeTags>'
        
        for col,row in self.attributeTags.iteritems():
            outputXML += os4+'<'+str(col)+'>'+str(row)+'</'+str(col)+'>'
        outputXML +=os3+'</attributeTags>'
        outputXML +=os2+ '</Dataformat>'
        
        if len(self.transformations) > 0:
            outputXML +=os2+ '<Transformations transformerID="'+self.transformerID+'">'
            for transformer in self.transformations:
                outputXML += transformer._toXML(indent+2)
            outputXML +=os2+'</Transformations>'
        
        outputXML +=os+'</Parser>'
        return outputXML
    
    def populateRepDbDicts(self):
        datatags = []
        for tag in self.dataTags:
            tmpDict = {}
            tmpDict['TAGID'] = tag
            tmpDict['DATAFORMATID'] = self.dataFormatID
            tmpDict['DESCRIPTION'] = 'tag'
            datatags.append(tmpDict)
        
        #Transformer
        transDict = {}
        transDict['TRANSFORMERID'] = self.transformerID
        transDict['VERSIONID'] = self.versionID
        transDict['DESCRIPTION'] = ''
        if self.transformerID.endswith('ALL'):
            transDict['TYPE'] = 'ALL'
        else:
            transDict['TYPE'] = 'SPECIFIC'
        
        
        return datatags, transDict, self.attributeTags
    
    def setAttributeNames(self, listOfNames):
        self.parentAttributeNames = listOfNames
    
    def difference(self,prsrObj,deltaObj=None):
        '''Calculates the difference between two parser objects
        
            Method takes prsrObj,deltaObj and deltaTPV as inputs.
            prsrObj: The parser to be compared against
            DeltaObj: The single object that gets passed through the entire diff recording the changes.
            DeltaTPV: A TechPackVersion Object that gets passed through the entire diff recording only new content.
            
            The Difference method will trigger the difference method of its child objects, passing
            in the object to compare, deltaObj and deltaTPV. After calculating the diff the child object passes these objects
            back in conjunction with a flag to say whether a (only new or changed content.. not deleted) was found or not. This flag is used to decide
            whether a child object should be added to the parent object in the DeltaTPV.
            
            
            Parser Difference method deviates from other diff methods in that it explicity calculates the diff for transformations.
            Transformation objects do not have a diff method.
            Transformation Hash value is used to find index changes in transformationObjects. If a transformation has moved sequence it index will be reported as
            having being moved, if the other transformationObjects have not changed sequence (but their index has moved) they are ignored . Transformations 
            are either new, deleted or have has their index changed. Diff does not happen at the transformation object level
            because its possible to have two transformationObjects under the same parser object with exactly the same properties/config
            
            Returns:
                    diffFlag (Boolean indicating where a change was found or not)
                    deltaObj
                    deltaTPV 
        '''
        
        if deltaObj is None:
            deltaObj = Utils.Delta(self.parserType,prsrObj.parserType)
            
        ############################################## Attribute Tags Difference #####################################################
        deltaObj.location.append('AttributeTags') 

        Delta = Utils.DictDiffer(self.attributeTags,prsrObj.attributeTags)
        for item in Delta.changed():
            deltaObj.addChange('<Changed>', item, self.attributeTags[item], prsrObj.attributeTags[item])
    
        for item in Delta.added():
            deltaObj.addChange('<Added>', item, '', prsrObj.attributeTags[item])
                
        for item in Delta.removed():
            deltaObj.addChange('<Removed>', item, self.attributeTags[item], '')
        
        deltaObj.location.pop()
        
        ############################################## Data Tags Difference #####################################################
        deltaObj.location.append('DataTags') 
        
        Delta = list(set(prsrObj.dataTags) - set(self.dataTags))    
        for item in Delta:
            deltaObj.addChange('<Added>', item, '', item)
                
        Delta = list(set(self.dataTags) - set(prsrObj.dataTags))    
        for item in Delta:
            deltaObj.addChange('<Removed>', item, item, '')
        
        deltaObj.location.pop()
        
        ############################################## Transformation Difference #####################################################  
        origHashDict = {}
        upgradeHashDict = {}
         
        for transformation in self.transformations:
            hashval = transformation._getHash()
            origHashDict[hashval] = transformation
         
        for transformation in prsrObj.transformations:
            hashval = transformation._getHash()
            upgradeHashDict[hashval] = transformation
        
        upgradeHashListCopy = copy.deepcopy(upgradeHashDict.keys()) 
        origHashListCopy = copy.deepcopy(origHashDict.keys()) 
        deltaTransforms = set(upgradeHashDict.keys()).difference(set(origHashDict.keys()))
        removedTransforms = set(origHashDict.keys()).difference(set(upgradeHashDict.keys())) 
        
        deltaObj.location.append('Transformation')
        for x in removedTransforms:
            origHashListCopy.remove(x)
            deltaObj.addChange('<Removed>', origHashDict[x].transformerID, origHashDict[x].rowID, '')          
             
        for x in deltaTransforms:
            upgradeHashListCopy.remove(x)
            deltaObj.addChange('<Added>', upgradeHashDict[x].transformerID, '', upgradeHashDict[x].rowID)
          
        for trans in list(origHashListCopy):
            if upgradeHashListCopy.index(trans) != origHashListCopy.index(trans):
                deltaObj.addChange('<Changed>', upgradeHashDict[trans].transformerID, origHashDict[trans].rowID, upgradeHashDict[trans].rowID)
        
        deltaObj.location.pop()
        
        return deltaObj