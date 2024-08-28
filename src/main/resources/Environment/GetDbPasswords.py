'''
Created on 25 Jan 2018

@author: xarjsin
'''
import collections
import Utils

class PasswordCollect(object):
    '''
    classdocs
    '''

    def __init__(self, servername,username,password,port,logger):
        '''
        Constructor
        '''
        self.servername = servername
        self.username = username
        self.password = password
        self.port = port
        self.requiredDBs = collections.defaultdict(dict)
        self.requiredDBs['dwhdb'] = {'user':'dc','connection':'dwh'}
        self.requiredDBs['dwhrep'] = {'user':'dwhrep','connection':'dwhrep'}
        self.requiredDBs['etlrep'] = {'user':'etlrep','connection':'etlrep'}
        self.requiredDBs['DBA'] = {'user':'DBA','connection':'dwhrep'}
        self.log = logger
        
    
    def getDbPasswords(self):
        PassDict = dict()
        dbusers = "/eniq/sw/installer/dbusers"
        ssh = Utils.getSshConnection(self.servername,self.username,self.password,self.port)
        
        for dbName,eachDB in self.requiredDBs.iteritems():
            dbusersFullCommand = dbusers + " " + eachDB['user'] + " " + eachDB['connection']
            PassDict[dbName] = ssh.getCommandOutput(dbusersFullCommand)
            PassDict[dbName] = PassDict[dbName].encode("ascii")
            #print "Password in python - " + PassDict[dbName]
        
        ssh.close()
        return PassDict
        
