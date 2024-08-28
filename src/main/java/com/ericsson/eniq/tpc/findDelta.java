package com.ericsson.eniq.tpc;

import java.io.*;
import java.util.*;
//import java.util.logging.*;
//import java.util.regex.Pattern;

//import org.apache.poi.hssf.util.HSSFColor.AQUA;
import org.apache.poi.ss.usermodel.Cell;
//import org.apache.poi.ss.usermodel.CellValue;
import org.apache.poi.ss.usermodel.Row;
import org.apache.poi.xssf.usermodel.*;
//import org.python.modules._hashlib.Hash;
//import org.apache.poi.ss.usermodel.Row;
import org.apache.poi.ss.usermodel.Sheet;
//import org.apache.poi.ss.usermodel.Cell;


//import com.sybase.jdbc4.jdbc.SybConnectionPoolDataSource;

//import jxl.*;
import jxl.write.*;

import jxl.Workbook;
//import jxl.format.CellFormat;
import jxl.format.Colour;
//import jxl.format.UnderlineStyle;
import jxl.read.biff.BiffException;
import jxl.write.WritableWorkbook;
import jxl.write.WriteException;
import jxl.write.biff.RowsExceededException;

public class findDelta {
	
	XSSFWorkbook oldWorkbook = null, newWorkbook = null;
	String [] requiredSheetList = {"Coversheet","Interfaces","Transformations","Data Format","Fact Tables","Topology Tables"
			,"Keys","Topology Keys","Counters","Vectors","BH","BH Rank Keys","External Statement","Universe Extension"
			,"Universe Topology Tables","Universe Class","Universe Topology Objects","Universe Conditions"
			,"Universe Joins","Report objects","Report conditions"};
	
	LinkedHashMap<String, LinkedHashMap<String, String>> oldWorkbookData = new LinkedHashMap<String, LinkedHashMap<String, String>>();
	LinkedHashMap<String, LinkedHashMap<String, String>> newWorkbookData = new LinkedHashMap<String, LinkedHashMap<String, String>>();
	LinkedHashMap<String, LinkedHashMap<String, String>> deltaOldWorkbookData = new LinkedHashMap<String, LinkedHashMap<String, String>>();
	LinkedHashMap<String, LinkedHashMap<String, String>> deltaNewWorkbookData = new LinkedHashMap<String, LinkedHashMap<String, String>>();
	
	
	public void fileInput()  {
		FileInputStream oldInput = null, newInput = null;
        File oldFile = null, newFile = null;
        
        try {
        	Scanner sc = new Scanner(System.in);
        	System.out.print("Enter old File Path :- ");
        	String oldFilePath = sc.nextLine();
        	System.out.print("Enter new File Path :- ");
        	String newFilePath = sc.nextLine();
        	sc.close();
        	
        	System.out.println("Loading Input Files");
            oldFile = new File(oldFilePath);
            newFile = new File(newFilePath);
            oldInput = new FileInputStream(oldFile);
            newInput = new FileInputStream(newFile);
            
            oldWorkbook = new XSSFWorkbook(oldInput);
        	newWorkbook = new XSSFWorkbook(newInput);
        	System.out.println("Input Files Loading Complete \n");
            
        
        System.out.println("Extracting Sheets Data");
        XSSFSheet sheet = null;
        LinkedHashMap<String, String> sheetData= new LinkedHashMap<>();
        System.out.println("Reading Individual Sheets Data ");
        for(String sheetName : requiredSheetList) {
        	sheet = oldWorkbook.getSheet(sheetName);
        	sheetData = getData(sheet);
        	oldWorkbookData.put(sheetName, sheetData);
        	
        	sheet = newWorkbook.getSheet(sheetName);
        	sheetData = getData(sheet);
        	newWorkbookData.put(sheetName, sheetData);
        	
        	deltaOldWorkbookData = (LinkedHashMap) oldWorkbookData.clone();
        	deltaNewWorkbookData = (LinkedHashMap) newWorkbookData.clone();
        }
        System.out.println("Extraction Done \n");
        	
        
        //finding Delta
        System.out.println("Finding Delta");
    	for(String sheetName : requiredSheetList) {
    		for(String s : oldWorkbookData.get(sheetName).keySet().stream().toArray(String[] ::new)) {
    			if(newWorkbookData.get(sheetName).keySet().contains(s)) {
    				deltaNewWorkbookData.get(sheetName).keySet().remove(s);
    				deltaOldWorkbookData.get(sheetName).keySet().remove(s);
    			}
    				
    		}
    	}
    	System.out.println("Delta Complete");
        
        
        writeDelta();
        
        } catch (Exception e) {
        	System.out.println("\tException in accessing fd:" + e + "\n");
        	e.printStackTrace();
        	System.exit(0);
        }
	}
	
	public boolean isEmptyCell(Cell cell) {
		if (cell == null || String.valueOf(cell).isEmpty())
			return true;
		else
			return false;
			
	}
	
	public String getCellValue(Cell cell) {
		String s = null;
		if (cell == null || String.valueOf(cell).isEmpty())
			return s;
		switch (cell.getCellType()) {
		case 0:
			Double d = cell.getNumericCellValue();
			Integer i = d.intValue();
		    s = i.toString();
		    break;
		case 1:
		    s = cell.getStringCellValue();
		    break;
		default:
		    break;
		}
		return s;
	}
	
	public LinkedHashMap<String, String> getData(XSSFSheet sheet) {
		
		LinkedHashMap<String, String> sheetData = new LinkedHashMap<>();
		try {
            for(Row row : sheet) {
            	String cellValue = null;
            	String s = null;
            	if(row!=null) {
            		for(Cell cell : row) {
            			if(isEmptyCell(cell))
            				s = "EMPTY CELL";
            			else if(cell.getCellType() == cell.CELL_TYPE_NUMERIC)
            				s = getCellValue(cell);
            			else
            				s = String.valueOf(cell).toString();
            			if(cellValue==null)
            				cellValue = s;
            			else
            				cellValue = cellValue +":-" + s;
            		}
            		sheetData.put(cellValue, row.getRowNum()+1+"");
            		
            	}
            }
        }
        catch (Exception e) {
            e.printStackTrace();
        }
		
		return sheetData;
	}
	
	public void writeDelta() throws IOException, WriteException, RowsExceededException, BiffException {
		
		WritableCellFormat cellFormats = new WritableCellFormat();
		try {
		final File exlFile = new File("DeltaOutput.xls");
		WritableWorkbook writableWorkbook = null;

		if (!exlFile.exists() && !exlFile.isFile()) {
			writableWorkbook = Workbook.createWorkbook(exlFile);
		} else {
			final Workbook workbook = Workbook.getWorkbook(exlFile);
			writableWorkbook = Workbook.createWorkbook(exlFile, workbook);
		}
		System.out.println("Writing starts");

		final WritableSheet writableSheet = writableWorkbook.createSheet("DeltaSheet", 0);
		String [] headers = {"Input Type","Sheet Name ", "COMMENT", "Row Number", "Row value"}; 
		cellFormats.setBackground(Colour.PINK);
		int col1 = 0;
		for(String s : headers) {
			Label label = new Label(col1++, 0, s, cellFormats);
			writableSheet.addCell(label);
		}
		
		//Writing Data
		String inputType = null, sheetName = null, comment = null, rowNum = null, rowValue = null;
		int row = 0;
		cellFormats = new WritableCellFormat();
		cellFormats.setBackground(Colour.YELLOW);
		for(String sheetNames : deltaOldWorkbookData.keySet()) {
			sheetName = sheetNames;
			inputType = "oldInputFile";
			comment = "MODIFIED/REMOVED";
			for(String s : deltaOldWorkbookData.get(sheetName).keySet()) {
				rowValue = s;
				rowNum = deltaOldWorkbookData.get(sheetNames).get(s);
				++row;
				Label label1 = new Label(0, row, inputType, cellFormats);
				Label label2 = new Label(1, row, sheetName, cellFormats);
				Label label3 = new Label(2, row, comment, cellFormats);
				Label label4 = new Label(3, row, rowNum, cellFormats);
				Label label5 = new Label(4, row, rowValue, cellFormats);
				writableSheet.addCell(label1);
				writableSheet.addCell(label2);
				writableSheet.addCell(label3);
				writableSheet.addCell(label4);
				writableSheet.addCell(label5);
				
			}
		}
		
		cellFormats = new WritableCellFormat();
		cellFormats.setBackground(Colour.LIGHT_GREEN);
		for(String sheetNames : deltaNewWorkbookData.keySet()) {
			sheetName = sheetNames;
			inputType = "NewInputFile";
			comment = "NEW/MODIFIED";
			for(String s : deltaNewWorkbookData.get(sheetName).keySet()) {
				rowValue = s;
				rowNum = deltaNewWorkbookData.get(sheetNames).get(s);
				++row;
				Label label1 = new Label(0, row, inputType, cellFormats);
				Label label2 = new Label(1, row, sheetName, cellFormats);
				Label label3 = new Label(2, row, comment, cellFormats);
				Label label4 = new Label(3, row, rowNum, cellFormats);
				Label label5 = new Label(4, row, rowValue, cellFormats);
				writableSheet.addCell(label1);
				writableSheet.addCell(label2);
				writableSheet.addCell(label3);
				writableSheet.addCell(label4);
				writableSheet.addCell(label5);
				
			}
		}
		
		//////**************Intechanging Rows***************************************************************	
		
		LinkedHashMap<String, LinkedHashMap<String, String>> oldinterworkbook = new LinkedHashMap<String, LinkedHashMap<String, String>>();
		LinkedHashMap<String, LinkedHashMap<String, String>> newinterworkbook = new LinkedHashMap<String, LinkedHashMap<String, String>>();

		LinkedHashMap<String, String> sheetData = new LinkedHashMap<>();
		XSSFSheet sheetInWrite = null;
		for (String sheetNameWrite : requiredSheetList) {
			sheetInWrite = oldWorkbook.getSheet(sheetNameWrite);
			sheetData = getData(sheetInWrite);

			oldinterworkbook.put(sheetNameWrite, sheetData);

			sheetInWrite = newWorkbook.getSheet(sheetNameWrite);
			sheetData = getData(sheetInWrite);

			newinterworkbook.put(sheetNameWrite, sheetData);
		}

		int sheetCounts = oldWorkbook.getNumberOfSheets();

		// So we will iterate through sheet by sheet
		for (int i = 0; i < sheetCounts; i++) {
			// Get sheet at same index of both work books
			Sheet s1 = oldWorkbook.getSheetAt(i);
			Sheet s2 = newWorkbook.getSheetAt(i);

			if ((newWorkbook.getSheetName(i).equals("Counters"))) {

				// Iterating through each row
				int rowCounts = s1.getPhysicalNumberOfRows();
				for (int j = 1; j < rowCounts; j++) {
					// Iterating through each cell
					int cellCounts = s2.getRow(j).getPhysicalNumberOfCells();
					// for (int k = 0; k < cellCounts; k++) {
					// Getting individual cell
					Cell oldCellOne = s1.getRow(j).getCell(0);
					Cell oldCellTwo = s1.getRow(j).getCell(1);
					Cell newCellOne = s2.getRow(j).getCell(0);
					Cell newCellTwo = s2.getRow(j).getCell(1);
					// comparing the both sheets cell data
					String cell_Old_1 = String.valueOf(oldCellOne).toString().trim();
					String cell_Old_2 = String.valueOf(oldCellTwo).toString().trim();
					String cell_New_1 = String.valueOf(newCellOne).toString().trim();
					String cell_New_2 = String.valueOf(newCellTwo).toString().trim();

					if (cell_Old_1.equals(cell_New_1) && cell_Old_2.equals(cell_New_2)) {

					} else {

						cellFormats = new WritableCellFormat();
						cellFormats.setBackground(Colour.LIGHT_ORANGE);
						sheetName = "Counters";
						inputType = "NewInputFile";
						comment = "INTERCHANGED";
						for (String s11 : newinterworkbook.get(sheetName).keySet().stream().toArray(String[]::new)) {
							String[] sp = s11.split(":-");
							String sp1 = sp[0];
							String sp2 = sp[1];
							String sp3=sp1+":-"+sp2;
							String cell_New_3=cell_New_1+":-"+cell_New_2;
							if (sp3.equals(cell_New_3)){
								rowValue = s11;
								rowNum = newinterworkbook.get(sheetName).get(s11);
								row++;
								Label label1 = new Label(0, row, inputType, cellFormats);
								Label label2 = new Label(1, row, sheetName, cellFormats);
								Label label3 = new Label(2, row, comment, cellFormats);
								Label label4 = new Label(3, row, rowNum, cellFormats);
								Label label5 = new Label(4, row, rowValue, cellFormats);
								writableSheet.addCell(label1);
								writableSheet.addCell(label2);
								writableSheet.addCell(label3);
								writableSheet.addCell(label4);
								writableSheet.addCell(label5);
							}

						}

					}

				}

			}
				//EQEV-128370 starts
			//rows interchange for transformation sheet n delta
			else if ((newWorkbook.getSheetName(i).equals("Transformations"))) {
				// Iterating through each row adding the old cell values in array list
				String temp = null;
				ArrayList<String> newsheetAr = new ArrayList<String>();
				ArrayList<String> oldsheetAr = new ArrayList<String>();
				int rowCounts = s1.getPhysicalNumberOfRows();
				for (int j = 1; j < rowCounts; j++) {
					temp = "";

					for (int k = 0; k < 6; k++) {

						Cell oldCellOne = s1.getRow(j).getCell(k);
						temp += oldCellOne + ":-";
					}
					oldsheetAr.add(temp);

				}
				// Iterating through each row adding the new cell values in array list
				rowCounts = s2.getPhysicalNumberOfRows();
				for (int j = 1; j < rowCounts; j++) {
					temp = "";

					for (int k = 0; k < 6; k++) {

						Cell newCellOne = s2.getRow(j).getCell(k);
						temp += newCellOne + ":-";
					}
					newsheetAr.add(temp);
				}
				for (int j = 0; j < oldsheetAr.size(); j++) {

					if (newsheetAr.contains(oldsheetAr.get(j))) {
						// System.out.println(newsheetAr.indexOf(oldsheetAr.get(j))+ " "+j);
						if (newsheetAr.indexOf(oldsheetAr.get(j)) < j) {
							cellFormats = new WritableCellFormat();
							cellFormats.setBackground(Colour.LIGHT_ORANGE);
							sheetName = "Transformations";
							inputType = "NewInputFile";
							comment = "INTERCHANGED  " + Integer.toString(j + 2) + "-->"
									+ Integer.toString(newsheetAr.indexOf(oldsheetAr.get(j)) + 2);
							String cellValue = newsheetAr.get(newsheetAr.indexOf(oldsheetAr.get(j)));
							rowNum =Integer.toString(newsheetAr.indexOf(oldsheetAr.get(j)) + 2);
							row++;
							Label label1 = new Label(0, row, inputType, cellFormats);
							Label label2 = new Label(1, row, sheetName, cellFormats);
							Label label3 = new Label(2, row, comment, cellFormats);
							Label label4 = new Label(3, row,rowNum, cellFormats);
							Label label5 = new Label(4, row, cellValue,cellFormats);
							writableSheet.addCell(label1);
							writableSheet.addCell(label2);
							writableSheet.addCell(label3);
							writableSheet.addCell(label4);
							writableSheet.addCell(label5);

						}
					}
				}
			}
			//EQEV-128370 Ends

			

		}			

		
		
		writableWorkbook.write();
		writableWorkbook.close();
		
		System.out.println("Writing Completed");
		}
		catch (Exception e) {
			e.printStackTrace();
		}
	}
	
}
