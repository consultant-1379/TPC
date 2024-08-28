/*------------------------------------------------------------------------------
 *******************************************************************************
 * COPYRIGHT Ericsson 2012
 *
 * The copyright to the computer program(s) herein is the property of
 * Ericsson Inc. The programs may be used and/or copied only with written
 * permission from Ericsson Inc. or in accordance with the terms and
 * conditions stipulated in the agreement/contract under which the
 * program(s) have been supplied.
 *******************************************************************************
 *----------------------------------------------------------------------------*/

package com.ericsson.eniq.tpc;

import java.io.IOException;
import java.net.URL;
import java.net.URLClassLoader;
import java.util.HashMap;
import java.util.logging.Handler;
import java.util.logging.Logger;

import com.maverick.ssh.LicenseManager;

import jxl.read.biff.BiffException;
import jxl.write.WriteException;
import jxl.write.biff.RowsExceededException;

/**
 * This class is used to invoke and run python using Jython Object Factory and load maverick license.
 */
public class TPC {
	
	private TPCMain getInstance(){
		loadMaverickLicense();
		getVersionDetails();
		configureLogging();
		JythonObjectFactory factory = new JythonObjectFactory(TPCMain.class,"TPC", "TPCMainClass");
		TPCMain main = (TPCMain) factory.createObject();
    	return main;
	}
	
	public void runTPC(HashMap<String, String> parameters){
		TPCMain tpc = getInstance();
		tpc.run(parameters);
	}
	
	public void configureLogging(){
		Logger globalLogger = Logger.getLogger("");
		Handler[] handlers = globalLogger.getHandlers();
		for(Handler handler : handlers) {
		    globalLogger.removeHandler(handler);
		}
	}
	
	public void getVersionDetails(){
		//Get the build number from the TPC jar file and use it when creating a TP.
		ClassLoader cl = ClassLoader.getSystemClassLoader();
        URL[] urls = ((URLClassLoader)cl).getURLs();
        for(URL url: urls){
        	String filename = url.getFile();
        	if(filename.contains("TPC-")){
        		String buildnumber = filename.split("TPC-")[1];
        		buildnumber = buildnumber.split(".jar")[0];
        		System.setProperty("TPCbuildNumber", buildnumber);
        	}
        	
        }
	}
	
	
    public static void main(String[] args){
        org.apache.log4j.PropertyConfigurator.configure("log4j.properties");
    	if(args.length > 0){
    		if(args[0].equals("findDelta")) {
    			findDelta ob = new findDelta();
    			ob.fileInput();
    			System.exit(0);
    		}
    		TPC app = new TPC();
    		TPCMain tpc = app.getInstance();
    		tpc.run(args[0]);
    	}else{
    		System.out.println("Please provide the path to a valid parameters file");
    	}

    }
    
    private void loadMaverickLicense(){
    	String license = "----BEGIN 3SP LICENSE----\n"+
			"Product : Maverick Legacy Client\n"+
			"Licensee: Ericsson AB (EAB) [6854]\n"+
			"Comments: Standard Support\n"+
			"Type    : Professional License (Standard Support)\n"+
			"Created : 22-Oct-2015\n"+
			
			"37872059C89153DBA600F3CF9CCEF4C88D00878CAA94197D\n"+
			"17495F5618C1BE1365669F6FA397C0D805005F4D3A25CD6C\n"+
			"B82619E6682A89E295F583C45121C00D93395D7977DD901C\n"+
			"C8DCFB25E544A75708A1087FE58E7AF26002148D6EE24DAB\n"+
			"E058FC36E4D84AC13D06731CB1DB07A900EBBEBA2AE47AB6\n"+
			"098487C2C292E2D30257C5720CCC9A9D217C29DCD32C63C7\n"+
			"----END 3SP LICENSE----";
    	LicenseManager.addLicense(license);
    }
}
