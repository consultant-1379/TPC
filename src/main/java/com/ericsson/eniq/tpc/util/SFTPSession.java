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

package com.ericsson.eniq.tpc.util;

import java.io.FileNotFoundException;
import java.io.IOException;
import java.util.ArrayList;

import com.maverick.sftp.SftpFile;
import com.maverick.sftp.SftpStatusException;
import com.maverick.sftp.TransferCancelledException;
import com.maverick.ssh.ChannelOpenException;
import com.maverick.ssh.PasswordAuthentication;
import com.maverick.ssh.SshAuthentication;
import com.maverick.ssh.SshClient;
import com.maverick.ssh.SshConnector;
import com.maverick.ssh.SshException;
import com.sshtools.net.SocketTransport;
import com.sshtools.sftp.SftpClient;

/**
 * This class is used for SFTP connection with the server to get the environment and db details.
 */
public class SFTPSession {
	
        private SshClient ssh = null;
	private SftpClient sftp = null;

	public void getConnection(String hostname, String username, String password, int port) 
			throws SshException, IOException, SftpStatusException, ChannelOpenException, Exception {
		SshConnector con = SshConnector.createInstance();
		ssh = con.connect(new SocketTransport(hostname, port), username, true);
		
		PasswordAuthentication pwd = new PasswordAuthentication();
		pwd.setPassword(password);
		
		if(ssh.authenticate(pwd)==SshAuthentication.COMPLETE) {
			sftp = new SftpClient(ssh);
			sftp.setTransferMode(SftpClient.MODE_BINARY);
			sftp.setRegularExpressionSyntax(SftpClient.GlobSyntax);
		}else{
			throw new Exception("Unable to open SFTP conection to the server");
		}
	}
	
	public String pwd(){
		return sftp.pwd();
	}
	
	public void cwd(String dir) throws SftpStatusException, SshException{
		sftp.cd(dir);
	}
	
	public void get(String remoteFileName, String localFileName) throws FileNotFoundException, 
		SftpStatusException, SshException, TransferCancelledException{
		sftp.get(remoteFileName, localFileName, false);
	}
	
	public void lcd(String dir) throws SftpStatusException{
		sftp.lcd(dir);
	}
	
	public ArrayList<String> ls(String path) throws SftpStatusException, SshException{
		ArrayList<String> list = new ArrayList<String>();
		for(SftpFile file : sftp.ls(path)){
			list.add(file.getFilename());
		}
		return list;
	}
	
	public ArrayList<String> ls() throws SftpStatusException, SshException{
		ArrayList<String> list = new ArrayList<String>();
		for(SftpFile file : sftp.ls()){
			list.add(file.getFilename());
		}
		return list;
	}
	
	public ArrayList<String> nlst() throws SftpStatusException, SshException{
		ArrayList<String> list = new ArrayList<String>();
		for(SftpFile file : sftp.ls()){
			list.add(file.getFilename());
		}
		return list;
	}
	
	public void close() throws SshException {
	        ssh.disconnect();
		sftp.exit();
	}
}
