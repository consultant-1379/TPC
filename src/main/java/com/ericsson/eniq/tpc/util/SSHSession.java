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

import java.io.*;

import com.maverick.sftp.SftpStatusException;
import com.maverick.ssh.*;
import com.sshtools.net.SocketTransport;

public class SSHSession {
    
    private SshClient ssh = null;
    
    public void getConnection(String hostname, String username, String password, int port) 
            throws SshException, IOException, SftpStatusException, ChannelOpenException, Exception {
        SshConnector con = SshConnector.createInstance();
        ssh = con.connect(new SocketTransport(hostname, port), username, true);
        
        PasswordAuthentication pwd = new PasswordAuthentication();
        pwd.setPassword(password);
        
        if(!(ssh.authenticate(pwd)==SshAuthentication.COMPLETE)){
            throw new Exception("Unable to open SFTP conection to the server");
        }
    }
    
    public String getCommandOutput(String Command) throws SshException, SshIOException, ChannelOpenException, IOException, ShellTimeoutException {
        Shell shell = new Shell(ssh);
        //System.out.println("Command - " + Command);
        ShellProcess process = shell.executeCommand(Command);
        BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()));
        String line = reader.readLine();
        //System.out.println("Password in Java - " + line);
        return line;
        /*System.out.println("Password1 - " + reader.readLine());
        String line;
        while((line = reader.readLine())!=null) {
            line += line;
            System.out.println("Password2 - " + line);
        }
        System.out.println("Password - " + line);
        return line;*/
    }
    
    public void close() {
        ssh.disconnect();
    }
}
