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

package com.ericsson.eniq.tpc.encryption;

import java.io.*;
import java.util.Enumeration;
import java.util.zip.ZipEntry;
import java.util.zip.ZipFile;

/**
 * Referenced classes of package com.distocraft.dc5000.install.ant: ZipCrypter
 */
public class ZipCrypterExtractor extends ZipCrypter {

	public ZipCrypterExtractor() {
		outputDir = null;
	}

	public void execute() throws Exception {
		initKey();
		if (fileTarget == null)
			throw new Exception("The target file has not been specified.");
		File inputFiles[] = { new File("") };
		if (fileTarget.isFile())
			inputFiles[0] = fileTarget;
		else
			inputFiles = fileTarget.listFiles();
		label0: for (int i = 0; i < inputFiles.length; i++) {
			File destDir = getDestinationDir(inputFiles[i]);
			if (destDir == null)
				continue;
			try {
				ZipFile zf = new ZipFile(inputFiles[i]);
				Enumeration entries = zf.entries();
				do {
					if (!entries.hasMoreElements())
						continue label0;
					ZipEntry ze = (ZipEntry) entries.nextElement();
					if (ze.isDirectory()) {
						File dir = new File(outputDir, ze.getName());
						dir.mkdir();
					} else {
						long startTime = System.currentTimeMillis();
						File outFile = new File(destDir, ze.getName());
						outFile.getParentFile().mkdirs();
						FileOutputStream fos = new FileOutputStream(outFile);
						fos.close();
						double totalTime = (double) (System.currentTimeMillis() - startTime) / 1000D;
					}
				} while (true);
			} catch (Exception e) {
				throw new Exception(e.getMessage(), e);
			}
		}
	}

	private File getDestinationDir(File file) {
		String fileName = file.getName();
		if (!file.isFile() || !fileName.endsWith(".tpi")
				&& !fileName.endsWith(".zip"))
			return null;
		String createDir = fileName.substring(0, fileName.length() - 4);
		File destDir = new File(outputDir, createDir);
		if (destDir.exists()) {
			return null;
		} else {
			return destDir;
		}
	}

	public void setFile(String file) throws Exception {
		super.setFile(file);
	}

	public void setCryptType(String type) {
		cryptMode = 2;
	}

	public void setOutputFile(String file) throws Exception {
		outputDir = new File(file);
		if (!outputDir.isDirectory() || !outputDir.canWrite())
			throw new Exception((new StringBuilder()).append("Directory ")
					.append(outputDir.getAbsolutePath())
					.append(" does not exist!").toString());
		if (!outputDir.canWrite())
			throw new Exception((new StringBuilder()).append("Directory ")
					.append(outputDir.getAbsolutePath())
					.append(" is not writable!").toString());
		else
			return;
	}

	public File getOutputFile() {
		return outputDir;
	}

	private File outputDir;
}
