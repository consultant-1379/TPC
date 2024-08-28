'''
Created on Jun 13, 2016

@author: ebrifol
'''

import Utils
from java.util import Date
from java.text import SimpleDateFormat

class BaseTPRetrieval(object):    

    def __init__(self, ServerName,dbPasswords,logger):
        self.ServerName = ServerName
        self.PasswordList = dbPasswords
        self.log = logger
    
    def getBaseTPInfo(self, destDir):
        from ssc.rockfactory import RockFactory
        from com.distocraft.dc5000.repository.dwhrep import Versioning
        from com.distocraft.dc5000.repository.dwhrep import Techpackdependency
        from com.distocraft.dc5000.repository.dwhrep import Supportedvendorrelease
        from com.distocraft.dc5000.repository.dwhrep import Referencetable
        from com.distocraft.dc5000.repository.dwhrep import Measurementtype
        from com.distocraft.dc5000.repository.dwhrep import Measurementtypeclass
        from com.distocraft.dc5000.repository.dwhrep import Measurementcounter
        from com.distocraft.dc5000.repository.dwhrep import Measurementkey
        from com.distocraft.dc5000.repository.dwhrep import Referencecolumn
        from com.distocraft.dc5000.repository.dwhrep import Measurementdeltacalcsupport
        from com.distocraft.dc5000.repository.dwhrep import Measurementobjbhsupport
        from com.distocraft.dc5000.repository.dwhrep import Measurementvector
        from com.distocraft.dc5000.repository.dwhrep import Busyhour
        from com.distocraft.dc5000.repository.dwhrep import Busyhourmapping
        from com.distocraft.dc5000.repository.dwhrep import Busyhourplaceholders
        from com.distocraft.dc5000.repository.dwhrep import Busyhourrankkeys
        from com.distocraft.dc5000.repository.dwhrep import Busyhoursource
        from com.distocraft.dc5000.repository.dwhrep import Transformer
        from com.distocraft.dc5000.repository.dwhrep import Transformation
        from com.distocraft.dc5000.repository.dwhrep import Defaulttags
        from com.distocraft.dc5000.repository.dwhrep import Universename
        from com.distocraft.dc5000.repository.dwhrep import Universetable
        from com.distocraft.dc5000.repository.dwhrep import Universeclass
        from com.distocraft.dc5000.repository.dwhrep import Universeobject
        from com.distocraft.dc5000.repository.dwhrep import Universecondition
        from com.distocraft.dc5000.repository.dwhrep import Universejoin
        from com.distocraft.dc5000.repository.dwhrep import Universecomputedobject
        from com.distocraft.dc5000.repository.dwhrep import Universeformulas
        from com.distocraft.dc5000.repository.dwhrep import Universeparameters
        from com.distocraft.dc5000.repository.dwhrep import Externalstatement
        from com.distocraft.dc5000.repository.dwhrep import Measurementtable
        from com.distocraft.dc5000.repository.dwhrep import Measurementcolumn
        from com.distocraft.dc5000.repository.dwhrep import Aggregation
        from com.distocraft.dc5000.repository.dwhrep import Aggregationrule
        from com.distocraft.dc5000.repository.dwhrep import Dataformat
        from com.distocraft.dc5000.repository.dwhrep import Dataitem
        from com.distocraft.dc5000.etl.rock import Meta_collections
        from com.distocraft.dc5000.etl.rock import Meta_schedulings
        from com.distocraft.dc5000.etl.rock import Meta_transfer_actions
        from com.distocraft.dc5000.etl.rock import Meta_collection_sets
        
        self.destDir = destDir
        self.etlrepTables = [Meta_collections , Meta_schedulings, Meta_transfer_actions]
        self.DBAccess = Utils.DbAccess(self.ServerName,'dwhrep',self.PasswordList)
        self.BaseTPFile = open(destDir+'/db/BaseTPs.sql','w')
        
        self.readRepInfo(Versioning, 'VERSIONID')
        self.readRepInfo(Supportedvendorrelease, 'VERSIONID')
        self.readRepInfo(Techpackdependency, 'VERSIONID')
        
        self.readRepInfo(Measurementtypeclass, 'VERSIONID')
        self.readRepInfo(Measurementtype, 'VERSIONID')
        self.readRepInfo(Measurementcounter, 'TYPEID')
        self.readRepInfo(Measurementvector, 'TYPEID')
        self.readRepInfo(Measurementkey, 'TYPEID')
        self.readRepInfo(Measurementdeltacalcsupport, 'TYPEID')
        self.readRepInfo(Measurementobjbhsupport, 'TYPEID')
        
        self.readRepInfo(Measurementtable, 'MTABLEID')
        self.readRepInfo(Measurementcolumn, 'MTABLEID')
        
        self.readRepInfo(Referencetable, 'VERSIONID')
        self.readRepInfo(Referencecolumn, 'TYPEID')
        
        self.readRepInfo(Aggregation, 'VERSIONID')
        self.readRepInfo(Aggregationrule, 'VERSIONID')
        self.readRepInfo(Externalstatement, 'VERSIONID')
        
        self.readRepInfo(Transformer, 'VERSIONID')
        self.readRepInfo(Transformation, 'TRANSFORMERID')
        
        self.readRepInfo(Busyhour, 'VERSIONID')
        self.readRepInfo(Busyhourmapping, 'VERSIONID')
        self.readRepInfo(Busyhourplaceholders, 'VERSIONID')
        self.readRepInfo(Busyhourrankkeys, 'VERSIONID')
        self.readRepInfo(Busyhoursource, 'VERSIONID')
        
        self.readRepInfo(Dataformat, 'DATAFORMATID')
        self.readRepInfo(Defaulttags, 'DATAFORMATID')
        self.readRepInfo(Dataitem, 'DATAFORMATID')
        
        self.readRepInfo(Universename, 'VERSIONID')
        self.readRepInfo(Universeclass, 'VERSIONID')
        self.readRepInfo(Universetable, 'VERSIONID')
        self.readRepInfo(Universeobject, 'VERSIONID')
        self.readRepInfo(Universeparameters, 'VERSIONID')
        self.readRepInfo(Universecomputedobject, 'VERSIONID')
        self.readRepInfo(Universecondition, 'VERSIONID')
        self.readRepInfo(Universeformulas, 'VERSIONID')
        self.readRepInfo(Universejoin, 'VERSIONID')
        
        self.DBAccess = Utils.DbAccess(self.ServerName,'etlrep',self.PasswordList)
        collectionIDList = self.getCollectionSetIDs(Meta_collection_sets, 'COLLECTION_SET_NAME')
        for DbTablename in self.etlrepTables:
            self.readEtlInfo(DbTablename, collectionIDList)
        
        self.BaseTPFile.close()
            
    
    def readRepInfo(self, tablename, keyname):
        DbCursor = self.DBAccess.getCursor()
        DbCursor.execute("SELECT * from " + str(tablename.__name__) +" where " + keyname +" LIKE '%TP_BASE%' OR " + keyname +" LIKE '%DWH_MONITOR%' OR " + keyname +" LIKE '%DWH_BASE%'")
        cols = DbCursor.description
        rows = DbCursor.fetchall()
        
        if rows is not None:
            for row in rows:
                properties = {}
                colcount=0
                for col in cols:
                    value = str(row[colcount])
                    if value != 'None':
                        value = Utils.strFloatToInt(value)
                        if col[0] == 'ORDERNRO':
                            value = float(value)
                        properties[col[0]] = value
                    elif value == 'None' and col[0] == 'GROUPING':
                        properties[col[0]] = value
                    colcount+=1
                obj = Utils.populateObjectFromDict(tablename, properties)
                self.BaseTPFile.write(obj.toSQLInsert())
        else:
            self.log.warning('No data')
        
        DbCursor.close()
            
    
    def readEtlInfo(self, tablename, collectionsetIDs):
        DbCursor = self.DBAccess.getCursor()
        collectionsetidcsv = ','.join(collectionsetIDs)
        DbCursor.execute("SELECT * from " + str(tablename.__name__) +" where COLLECTION_SET_ID  IN ( " + collectionsetidcsv + " )")
        cols = DbCursor.description
        rows = DbCursor.fetchall()
        
        if rows is not None:
            for row in rows:
                properties = {}
                colcount=0
                for col in cols:
                    value = str(row[colcount])
                    if value != 'None':
                        value = Utils.strFloatToInt(value)
                        if col[0] == 'LAST_EXEC_TIME_MS':
                            value = float(value)
                        properties[col[0]] = value
                    elif value == 'None' and col[0] == 'GROUPING':
                        properties[col[0]] = value
                    colcount+=1
                obj = Utils.populateObjectFromDict(tablename, properties)
                self.BaseTPFile.write(obj.toSQLInsert())
        else:
            self.log.warning('No data')
        
        DbCursor.close()
            
    def getCollectionSetIDs(self, tablename, keyname):
        collectionSetIDs = []
        DbCursor = self.DBAccess.getCursor()
        DbCursor.execute("SELECT * from " + str(tablename.__name__) +" where " + keyname +" LIKE '%TP_BASE%' OR " + keyname +" LIKE '%DWH_MONITOR%' OR " + keyname +" LIKE '%DWH_BASE%'")
        cols = DbCursor.description
        rows = DbCursor.fetchall()
        
        if rows is not None:
            for row in rows:
                properties = {}
                colcount=0
                for col in cols:
                    value = str(row[colcount])
                    if value != 'None':
                        properties[col[0]] = Utils.strFloatToInt(value)
                    colcount+=1
                    
                collectionSetIDs.append(properties['COLLECTION_SET_ID'])
                obj = Utils.populateObjectFromDict(tablename, properties)
                self.BaseTPFile.write(obj.toSQLInsert())
        else:
            self.log.warning('No data')
        
        DbCursor.close()
        return collectionSetIDs
        
            