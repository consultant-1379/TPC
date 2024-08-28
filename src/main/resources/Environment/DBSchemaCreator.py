'''
Created on Jun 9, 2016

@author: ebrifol
'''

import Utils
import Environment

class SchemaCreator(object):

    def __init__(self, ServerName, dbPasswords,logger):
        self.ServerName = ServerName
        self.PasswordList = dbPasswords
        self.databases = ['dwhrep' , 'etlrep']
        self.log = logger
        
    def getSchema(self, destDir):
        self.destDir = destDir
        dbaccess = Utils.DbAccess(self.ServerName,'DBA',self.PasswordList)
                
        for DBname in self.databases:
            tmpTables = self._readSysColumns(dbaccess, DBname)
            Tables = self._sortTableInsertionOrder(dbaccess, tmpTables)
            
            tableSchema = open(destDir+'/db/'+DBname+'.sql','w')
            for table in Tables.itervalues():
                tableSchema.write(table.createSQL()+'\n')
            tableSchema.close()
        
    
    def _readSysColumns(self, dbaccess, DBname):
        tmpTablesDict = {}
        currentTableName = ''
        DBTableInstance = None
        
        DbCursor = dbaccess.getCursor()
        DbCursor.execute("SELECT tname, cname, coltype, length, nulls, default_value, in_primary_key FROM sys.syscolumns WHERE creator =? ORDER BY tname", (DBname,))
        resultset = DbCursor.fetchall()
        for row in resultset:
            tname = str(row[0]).strip()
            cname = str(row[1]).strip()
            coltype = str(row[2]).strip()
            length = str(row[3]).strip()
            nulls = str(row[4]).strip()
            in_primary_key = str(row[6]).strip()
            default_value = str(row[5]).strip()
            
            if default_value is None or default_value == 'None':
                default_value = 'NULL'
            
            if coltype == 'long varchar':
                length = '2147483647'
            
            if currentTableName != tname:
                if currentTableName != '':
                    tmpTablesDict[currentTableName] = DBTableInstance
                
                DBTableInstance = Environment.Table(tname)
                getForeignKeys = True
                currentTableName = tname
            
            DBTableInstance.createColumnSQL(cname, coltype, length, default_value, nulls)
            if in_primary_key.lower() == 'y':
                DBTableInstance.addPrimary_key(cname)
                
            if getForeignKeys:
                getForeignKeys = False
                DBTableInstance = self._getForeignKeys(dbaccess, DBTableInstance)
        
        dbaccess.closeCursor()
        tmpTablesDict[DBTableInstance.getTablename()] = DBTableInstance
        return tmpTablesDict
            
            
    def _getForeignKeys(self, dbaccess, DBTableInstance):
        DbCursor = dbaccess.getCursor()
        DbCursor.execute("select role, columns, primary_tname from sys.sysforeignkeys where foreign_tname='" + DBTableInstance.getTablename() + "'",)
        resultset = DbCursor.fetchall()
        for row in resultset:
            role = str(row[0]).strip()
            columns = str(row[1]).strip()
            primary_tname = str(row[2]).strip()
            
            foreign_keys = columns.split(',')
            keys = ''
            reference=''
            count = 0
            for foreignKey in foreign_keys:
                reference = reference + foreignKey.split(' IS ')[1]
                keys = keys + foreignKey.split(' IS ')[0]
                
                if count != len(foreignKey)-1:
                    keys = keys +', '
                    reference = reference +', '
                count+=1
            
            if keys.endswith(', '):
                keys = keys[:-2]
            if reference.endswith(', '):
                reference = reference[:-2]
            
            DBTableInstance.addForeign_key(role , primary_tname + ' (' + reference + '):(' + keys + ')')
            
        dbaccess.closeCursor()
        
        return DBTableInstance
    
    def _sortTableInsertionOrder(self, dbaccess, tmpTablesDict):
        Tables = Utils.odict()
        if 'Versioning' in tmpTablesDict.keys():
            Tables['Versioning'] = tmpTablesDict['Versioning']
        if 'META_COLLECTIONS_SETS' in tmpTablesDict.keys():
            Tables['META_COLLECTIONS_SETS'] = tmpTablesDict['META_COLLECTIONS_SETS'] 
            
        while len(Tables) < len(tmpTablesDict):
            for tablename, table in tmpTablesDict.iteritems():
                
                if tablename not in Tables:
                    addTable = True
                    DbCursor = dbaccess.getCursor()
                    DbCursor.execute("select distinct(primary_tname) from sys.sysforeignkeys where foreign_tname='"+ tablename +"'",)
                    resultset = DbCursor.fetchall()
                    for row in resultset:
                        primary_tname = str(row[0]).strip()
                        if primary_tname not in Tables.keys():
                            addTable = False
                    
                    if addTable:
                        Tables[tablename] = table
                    
                    dbaccess.closeCursor()
                    
        return Tables
            
            