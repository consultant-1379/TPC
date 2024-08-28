'''
Created on May 28, 2019

@author: XARJSIN
'''

from ODict import odict
import Utils
import os
import sys
import traceback
from java.io import File, FileOutputStream
from org.apache.poi.xssf.usermodel import XSSFWorkbook
from os import path


class convVect(object):
    '''Class for extraction and intermediate storage of metadata from inside a xls file.'''
    VectorsList = ['Fact Table Name', 'Counter Name', 'Vendor Release', 'Index', 'From', 'To', 'Quantity', 'Vector Description']
    
    def __init__(self,logger):
        self.log = logger
        self.xlsxdict = odict()
        self.headerStyle = {}

    def readOldVectors(self,filename=None):
        if filename == None:
            self.log.error("Input MODEL-T not provided")
            return

        workbook = XSSFWorkbook(File(filename))
        # Vectors
        self.log.info('Opening Vectors sheet')
        sheet = workbook.getSheet('Vectors')
        self.getHeaderStyle(sheet)
        for rowNum in xrange(1, sheet.getLastRowNum() + 1):
            index = self.getCellValue(sheet, rowNum, 3)
            if index != '':
                vendDict = {}
                quantVec = self.getCellValue(sheet, rowNum, 6)
                vendRelVec = self.getCellValue(sheet, rowNum, 2)
                counterVec = self.getCellValue(sheet, rowNum, 1)
                tableVec = self.getCellValue(sheet, rowNum, 0)
                fromVec = self.getCellValue(sheet, rowNum, 4)
                toVec = self.getCellValue(sheet, rowNum, 5)
                descVec = self.getCellValue(sheet, rowNum, 7)
                
                vendDict['From'] = fromVec
                vendDict['To'] = toVec
                vendDict['Vector Description'] = descVec
                vendRelKey = vendRelVec
                
                if tableVec not in self.xlsxdict:
                    self.xlsxdict[tableVec] = odict()
                
                if counterVec not in self.xlsxdict[tableVec]:
                    self.xlsxdict[tableVec][counterVec] = odict()
                    
                if index not in self.xlsxdict[tableVec][counterVec]:
                    self.xlsxdict[tableVec][counterVec][index] = odict()
                    
                if quantVec not in self.xlsxdict[tableVec][counterVec][index]:
                    self.xlsxdict[tableVec][counterVec][index][quantVec] = odict()
                    
                for vendRel, resultDict in self.xlsxdict[tableVec][counterVec][index][quantVec].iteritems():
                    if resultDict == vendDict:
                        vendRelKey = vendRel + "," + vendRelVec
                        del self.xlsxdict[tableVec][counterVec][index][quantVec][vendRel]
                
                self.xlsxdict[tableVec][counterVec][index][quantVec][vendRelKey] = vendDict
        
        return sheet.getLastRowNum() + 1
    

    def createNewVectors(self,OutputPath):
        workbookPath = OutputPath + '\\' + 'Vectors.xlsx'
        workbook = XSSFWorkbook()
        
        spreadsheet = self.makeVectorSheet(workbook)
        for table, tableDict in self.xlsxdict.iteritems():
            for counter, counterDict in tableDict.iteritems():
                for index, indexDict in counterDict.iteritems():
                    for quant, quantDict in indexDict.iteritems():
                        for vendorRelist, vendRelDict in quantDict.iteritems():
                            rowNumber = spreadsheet.getLastRowNum() + 1
                            self.writeToWorkbook(spreadsheet, rowNumber, 0, table)
                            self.writeToWorkbook(spreadsheet, rowNumber, 1, counter)
                            self.writeToWorkbook(spreadsheet, rowNumber, 2, vendorRelist)
                            self.writeToWorkbook(spreadsheet, rowNumber, 3, index)
                            self.writeToWorkbook(spreadsheet, rowNumber, 4, vendRelDict['From'])
                            self.writeToWorkbook(spreadsheet, rowNumber, 5, vendRelDict['To'])
                            self.writeToWorkbook(spreadsheet, rowNumber, 6, quant)
                            self.writeToWorkbook(spreadsheet, rowNumber, 7, vendRelDict['Vector Description'])
        
        self.log.info('Writing new vector sheet to file')
        workbook.write(FileOutputStream(workbookPath))
        return spreadsheet.getLastRowNum() + 1
    
    
    def getCellValue(self, sheet, rowNum, cellNum):
        CellValue = ''
        try:
            CellValue = sheet.getRow(rowNum).getCell(cellNum).toString().strip()
        except:
            pass
        
        return CellValue
    
    
    def getHeaderStyle(self,sheet):
        for cell in sheet.getRow(0):
            metaData = []
            header = cell.toString().strip()
            style = cell.getCellStyle()
            fgColor = style.getFillForegroundColor()
            fillPattern = style.getFillPattern()
            wrapText = style.getWrapText()
            width = sheet.getColumnWidth(cell.getColumnIndex())
            metaData.append(fgColor)
            metaData.append(fillPattern)
            metaData.append(wrapText)
            metaData.append(width)
            self.headerStyle[header] = metaData
    
    
    def makeVectorSheet(self,workbook):
        font = workbook.createFont();
        font.setFontHeightInPoints(10);
        font.setFontName("Arial");
        font.setColor(9);
        
        spreadsheet = workbook.createSheet('Vectors')
        row = spreadsheet.createRow(0)
        row.setHeightInPoints(30)
        count = 0
        for key in self.VectorsList:
            style = workbook.createCellStyle();
            style.setFillForegroundColor(self.headerStyle[key][0])
            style.setFillPattern(self.headerStyle[key][1])
            style.setWrapText(self.headerStyle[key][2])
            style.setFont(font)
            cell = row.createCell(count)
            cell.setCellValue(key)
            cell.setCellStyle(style)
            spreadsheet.setColumnWidth(count, self.headerStyle[key][3])
            count = count+1
            
        return spreadsheet
    
    
    def writeToWorkbook(self, sheet, rowNumber, cellNumber, value):
        try:
            sheet.getRow(rowNumber).createCell(cellNumber).setCellValue(value)
        except:
            sheet.createRow(rowNumber).createCell(cellNumber).setCellValue(value)
  