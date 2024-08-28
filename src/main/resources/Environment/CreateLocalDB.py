'''
Created on Jun 20, 2016

@author: ebrifol
'''

import os
import traceback
import sys
from java.sql import DriverManager

class CreateDB(object):

    def __init__(self, envDir,logger):
        self.envDir = envDir
        self.dbSchemaFiles = [ 'dwhrep.sql' , 'etlrep.sql' ]
        self.TPfiles = ['BaseTPs.sql']
        self.log = logger
        
    
    def createDB(self):
        dbDataSource = self.envDir + '/db'
        
        dblocation = self.envDir + '/db-Impl'
        os.makedirs(dblocation)
        
        db_file = open(dblocation + '/db_Impl', "wb")
        
        DB_URL = 'jdbc:hsqldb:file:' + db_file.name+';hsqldb.lock_file=false'
        self.connection = DriverManager.getConnection(DB_URL, 'sa', '')
        
        completeLine = ''
        for filename in self.dbSchemaFiles:
            with open(dbDataSource + '/' + filename, 'r') as ins:
                for line in ins:
                    completeLine += line
                    if ');' in line:
                        self._executeStatement(completeLine)
                        completeLine = ''
        self.connection.commit()
        
        for filename in self.TPfiles:
            sql_file = open(dbDataSource + '/' + filename, 'r')
            SQL = sql_file.read()
            self._executeStatement(SQL)
                        
        self.connection.commit()
        self.connection.close()
        db_file.close()
        
        return db_file.name
        
    def _executeStatement(self, statement):
        try:
            stmt = self.connection.createStatement()
            
            #Fix for ENIQ_EVENTS_ADMIN_PROPERTIES table
            if 'getdate' in statement:
                statement = statement.replace('"getdate"()' , 'NULL')
            
            stmt.execute(self.connection.nativeSQL(statement))
        except:
            self.log.error('Unable to execute statement: ' + statement)
            traceback.print_exc(file=sys.stdout)
        finally:
            stmt.close()