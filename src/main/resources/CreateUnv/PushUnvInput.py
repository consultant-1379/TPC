'''
Created on May 25, 2018

@author: xarjsin
'''
import Utils
from CreateTP import CreateTPUtils
import java.lang.System
from datetime import datetime
import os

class PushUnvInput(object):
    
    def __init__(self, params, logger):
        self.TPModel = params['tpModel']
        self.log = logger
        self.unvDirectory = params['UniInputPath'] + "/"
        
        dbPath = params['dbpath']
        envPath = params['envPath']
        from ssc.rockfactory import RockFactory
        self.dbAccess = Utils.DbAccess(dbPath, 'HSQL')
        self.dbDetails = self.dbAccess.getConnectionProperties('HSQL')
        self.dbConn = RockFactory(self.dbDetails['url'].replace('DBpath', dbPath), 
                                  self.dbDetails['uid'], self.dbDetails['pid'],
                                  self.dbDetails['driver'], "TPC", True)
        self.baseTP = Utils.getBaseTPName(self.dbAccess.getCursor())
        self.versionId = ""
    
    def pushUnv(self):
        
        Utils.createCleanUnvDir(self.unvDirectory)
        self.dataStore = Utils.DataStorage()
        
        self.log.info('Export General Universe Details')
        self._pushGenUnvDetails()
        self.log.info('Export Busy Hour Functionality Details')
        self._pushBHDetails()
        self.log.info('Export Universe Details From Techpack')
        self._pushUniverseDetails()
        self.log.info('Export Counters, Keys and Vector Ranges')
        self._pushCounterKeys()
        self.log.info('Export Measurement Types')
        self._pushMeasTypes()
        self.log.info('Export Public Keys')
        self._pushPublicKeys()
        self.log.info('Export Base TP Joins')
        self._pushBaseTPJoins()
        self.log.info('Export Reference Table Details')
        self._pushRefTable()
        self.log.info('Export Reference Column Details')
        self._pushRefCol()
        self.log.info('Export Common Topology')
        self._pushCommonTop()
        self.log.info('Export Base Classes')
        self._pushBaseClasses()
        self.log.info('Export Base Tables')
        self._pushBaseTables()
        self.log.info('Export Base Objects')
        self._pushBaseObjects()
        self.log.info('Export Base Conditions')
        self._pushBaseConditions()
        
        
    def _pushGenUnvDetails(self):
        '''To export general details queried during Universe Task'''
        
        versioningDetails = ['TECHPACK_NAME','DESCRIPTION','TECHPACK_VERSION','VERSIONID',
                             'PRODUCT_NUMBER','TECHPACK_TYPE']
        universeNameDetails = ['UNIVERSENAME']
        suppVendorRelDetails = ['VENDORRELEASE']
        baseTPName = "BASE_TECHPACK_NAME=TP_BASE"
        
        Versioningdict, TpDependencies, SupportedVendorReleases = self.TPModel.populateRepDbDicts()
        Utils.writeUnvDetails(baseTPName, self.unvDirectory + 'generalDetails')
        self.versionId = Versioningdict['VERSIONID']
        for keyCol in versioningDetails:
            data = keyCol + '=' + Versioningdict[keyCol]
            Utils.writeUnvDetails(data, self.unvDirectory + 'generalDetails')
            
        for keyCol in universeNameDetails:
            data1 = ""
            for UnvName in self.TPModel.universes.itervalues():
                UnvNameDict = UnvName.populateRepDbDicts()
                data1 = data1 + UnvNameDict[keyCol] + ","
            
            data = keyCol + '=' + data1[:-1]#.rstrip(",")
            Utils.writeUnvDetails(data, self.unvDirectory + 'generalDetails')
        
        for keyCol in suppVendorRelDetails:
            data1 = ""
            for vendorRel in SupportedVendorReleases:
                data1 = data1 + vendorRel + ","
                
            data = keyCol + '=' + data1[:-1]
            Utils.writeUnvDetails(data, self.unvDirectory + 'generalDetails')


    def _pushBHDetails(self):
        '''Exporting Busy Hour functionality related details'''
        
        rankBHenable = "False"
        objSuppDict = {}
        bhTargetTypeDict = {}
        bhLevelSet = set()
        for busyhour in self.TPModel.busyHours.itervalues():
            objbhsupport, bhplaceholdersDict, BHMapping = busyhour.populateRepDbDicts()
            for objBH in objbhsupport:
                typeId = objBH['TYPEID']
                objSupp = objBH['OBJBHSUPPORT']
                if typeId in objSuppDict:
                    sup_tmp_set = objSuppDict[typeId]
                    sup_tmp_set.add(objSupp)
                    objSuppDict[typeId] = sup_tmp_set
                else:
                    sup_tmp_set = set()
                    sup_tmp_set.add(objSupp)
                    objSuppDict[typeId] = sup_tmp_set
                
                #objBHEntry = objBH['TYPEID'] + '=' + objBH['OBJBHSUPPORT']
                #Utils.writeUnvDetails(objBHEntry, self.unvDirectory + 'objBHDetails')
                
            for mapDict in BHMapping:
                bhLevel = mapDict['BHLEVEL']
                targetType = mapDict['BHTARGETTYPE']
                bhLevelSet.add(bhLevel)
                if bhLevel in bhTargetTypeDict:
                    tmp_set = bhTargetTypeDict[bhLevel]
                    tmp_set.add(targetType)
                    bhTargetTypeDict[bhLevel] = tmp_set
                else:
                    tmp_set = set()
                    tmp_set.add(targetType)
                    bhTargetTypeDict[bhLevel] = tmp_set
                
            if len(bhLevelSet) > 0:
                rankBHenable = "True"
                
        data = 'rankBusyHourFunctionality' + '=' + rankBHenable
        Utils.writeUnvDetails(data, self.unvDirectory + 'generalDetails')
        for type in objSuppDict:
            data2 = type + "="
            for bhtype in objSuppDict[type]:
                data2 = data2 + bhtype + ","
                
            data2 = data2[:-1]
            Utils.writeUnvDetails(data2, self.unvDirectory + 'objBHDetails')
            
        for keyCol in bhTargetTypeDict:
            data1 = keyCol + "="
            for target in bhTargetTypeDict[keyCol]:
                data1 = data1 + target + ","
            
            data1 = data1[:-1]
            Utils.writeUnvDetails(data1, self.unvDirectory + 'bhTargetType')
    
    
    def _pushUniverseDetails(self):
        '''Exporting all universe related details in TP model - Classes, Objects, Conditions, Joins, etc'''
        
        UnvClsDetails = ['CLASSNAME','UNIVERSEEXTENSION','DESCRIPTION','PARENT','OBJ_BH_REL','ELEM_BH_REL']
        UnvObjDetails = ['CLASSNAME','UNIVERSEEXTENSION','OBJECTNAME','DESCRIPTION','OBJECTTYPE',
                         'QUALIFICATION','AGGREGATION','OBJSELECT','OBJWHERE','OBJ_BH_REL','ELEM_BH_REL']
        UnvCondDetails = ['CLASSNAME','UNIVERSEEXTENSION','UNIVERSECONDITION','DESCRIPTION','CONDWHERE',
                         'AUTOGENERATE','CONDOBJCLASS','CONDOBJECT','PROMPTTEXT','MULTISELECTION','FREETEXT',
                         'OBJ_BH_REL','ELEM_BH_REL']
        UnvTabDetails = ['OWNER','TABLENAME','UNIVERSEEXTENSION','ALIAS','OBJ_BH_REL','ELEM_BH_REL']
        UnvJoinsDet = ['SOURCETABLE','SOURCELEVEL','SOURCECOLUMN','TARGETTABLE','TARGETLEVEL','TARGETCOLUMN', #'EXPRESSION',
                       'CARDINALITY','CONTEXT','EXCLUDEDCONTEXTS','UNIVERSEEXTENSION']
        
        for UnvMod in self.TPModel.universes.itervalues():
            unvExt = ""
            if len(UnvMod.universeExtensions) == 0:
                unvExt = "None,"
            for unvCls in UnvMod.universeClasses.itervalues():
                unvClsDict = unvCls.populateRepDbDicts()
                if not unvClsDict['NAME'].endswith("_Keys"):
                    clsUni = ""
                    for col in UnvClsDetails:
                        clsUni = clsUni + self._formatData(str(unvClsDict[col])) + ","
                        
                    Utils.writeUnvDetails(clsUni[:-1], self.unvDirectory + 'unvClasses')
                
                for unvObj in unvCls.universeObjObjects.itervalues():
                    unvObjDict = unvObj.populateRepDbDicts()
                    objUni = ""
                    for col in UnvObjDetails:
                        objUni = objUni + self._formatData(str(unvObjDict[col])) + ","
                        
                    Utils.writeUnvDetails(objUni[:-1], self.unvDirectory + 'tpObjects')
                    
                for universeCon in unvCls.universeConditionObjects.itervalues():
                    unvConDict = universeCon.populateRepDbDicts()
                    condUni = ""
                    for col in UnvCondDetails:
                        condUni = condUni + self._formatData(str(unvConDict[col])) + ","
                        
                    Utils.writeUnvDetails(condUni[:-1], self.unvDirectory + 'tpConditions')
                    
            for universeTable in UnvMod.universeTables.itervalues():
                unvTabDict = universeTable.populateRepDbDicts()
                tabUni = ""
                for col in UnvTabDetails:
                    tabUni = tabUni + self._formatData(str(unvTabDict[col])) + ","
                        
                Utils.writeUnvDetails(tabUni[:-1], self.unvDirectory + 'unvTables')
                
            for unvJns in UnvMod.universeJoins.itervalues():
                unvJnsDict = unvJns.populateRepDbDicts()
                jnsUni = ""
                for col in UnvJoinsDet:
                    jnsUni = jnsUni + self._formatData(str(unvJnsDict[col])) + ","
                    
                Utils.writeUnvDetails(jnsUni[:-1], self.unvDirectory + 'unvJoins')
            
            for extension in UnvMod.universeExtensions.itervalues():
                extDict = extension.populateRepDbDicts()
                unvExt = unvExt + extDict['UNIVERSEEXTENSION'] + "=" + extDict['UNIVERSEEXTENSIONNAME'] + ","
                for unvCls in extension.universeClassObjects.itervalues():
                    unvClsDict = unvCls.populateRepDbDicts()
                    if not unvClsDict['NAME'].endswith("_Keys"):
                        clsUni = ""
                        for col in UnvClsDetails:
                            clsUni = clsUni + self._formatData(str(unvClsDict[col])) + ","
                        
                        Utils.writeUnvDetails(clsUni[:-1], self.unvDirectory + 'unvClasses')
                        
                    for unvObj in unvCls.universeObjObjects.itervalues():
                        unvObjDict = unvObj.populateRepDbDicts()
                        objUni = ""
                        for col in UnvObjDetails:
                            objUni = objUni + self._formatData(str(unvObjDict[col])) + ","
                        
                        Utils.writeUnvDetails(objUni[:-1], self.unvDirectory + 'tpObjects')
                            
                    for universeCon in unvCls.universeConditionObjects.itervalues():
                        unvConDict = universeCon.populateRepDbDicts()
                        condUni = ""
                        for col in UnvCondDetails:
                            condUni = condUni + self._formatData(str(unvConDict[col])) + ","
                        
                        Utils.writeUnvDetails(condUni[:-1], self.unvDirectory + 'tpConditions')

                for unvTab in extension.universeTableObjects.itervalues():
                    unvTabDict = unvTab.populateRepDbDicts()
                    tabUni = ""
                    for col in UnvTabDetails:
                        tabUni = tabUni + self._formatData(str(unvTabDict[col])) + ","
                        
                    Utils.writeUnvDetails(tabUni[:-1], self.unvDirectory + 'unvTables')
                    
                for unvJns in extension.universeJoinObjects.itervalues():
                    unvJnsDict = unvJns.populateRepDbDicts()
                    jnsUni = ""
                    for col in UnvJoinsDet:
                        jnsUni = jnsUni + self._formatData(str(unvJnsDict[col])) + ","
                    
                    Utils.writeUnvDetails(jnsUni[:-1], self.unvDirectory + 'unvJoins')
                        
            unvExt = unvExt[:-1]
            Utils.writeUnvDetails(unvExt, self.unvDirectory + 'unvExtensions')
                
            
    def _pushCounterKeys(self):
        '''Exporting measurement information like counter details, keys details and vector range details'''
        
        measCountDetails = ['DATANAME','DESCRIPTION','TIMEAGGREGATION','GROUPAGGREGATION',
                            'DATATYPE','DATASIZE','DATASCALE','INCLUDESQL','UNIVOBJECT',
                            'UNIVCLASS','COUNTERPROCESS']
        measKeyDetails = ['DATANAME','DESCRIPTION','DATATYPE','DATASIZE','DATASCALE','UNIQUEKEY',
                          'NULLABLE','INDEXES','UNIVOBJECT','ISELEMENT','INCLUDESQL']
        
        vecRangeSet = set()
        
        for table in self.TPModel.measurementTables.itervalues():
            for attribute in table.attributes.itervalues():
                attDict = attribute.populateRepDbDicts()
                data = table.typeid + ","
                if attribute.attributeType == 'measurementCounter':
                    for col in measCountDetails:
                        data = data + self._formatData(attDict[col]) + ","
                        
                    data = data[:-1]
                    Utils.writeUnvDetails(data, self.unvDirectory + 'counters')
                    for quant in attribute.vectors.itervalues():
                        for indices in quant.itervalues():
                            for vector in indices.itervalues():
                                vecDict = vector.populateRepDbDicts()
                                vecRange = vecDict['TYPEID'] + "+" + vecDict['DATANAME']
                                vecRangeSet.add(vecRange)
                    
                elif attribute.attributeType == 'measurementKey':
                    for col in measKeyDetails:
                        data = data + self._formatData(attDict[col]) + ","
                        
                    data = data[:-1]
                    Utils.writeUnvDetails(data, self.unvDirectory + 'keys')
        
        for keyCol in vecRangeSet:
            data1 = keyCol + "=1"
            Utils.writeUnvDetails(data1, self.unvDirectory + 'vecRange')
    
    
    def _pushMeasTypes(self):
        '''Exporting all required details for all measurement types in TP'''
        
        measTypeDetails = ['TYPEID','TYPECLASSID','TYPENAME','VENDORID','DESCRIPTION','JOINABLE','SIZING',
                           'TOTALAGG','ELEMENTBHSUPPORT','RANKINGTABLE','PLAINTABLE','DELTACALCSUPPORT',
                           'UNIVERSEEXTENSION','VECTORSUPPORT']
        
        for table in self.TPModel.measurementTables.itervalues():
            MeasTypeClass, deltacalcSupport, MeasType = table.populateRepDbDicts()
            data = ""
            delCal = self._formatData(str(MeasType['TYPEID'])) + '=' + self._formatData(str(MeasType['DELTACALCSUPPORT']))
            for col in measTypeDetails:
                data = data + self._formatData(str(MeasType[col])) + ","
            
            data = data + MeasTypeClass['DESCRIPTION']
            Utils.writeUnvDetails(data, self.unvDirectory + 'measType')
            Utils.writeUnvDetails(delCal, self.unvDirectory + 'deltaCalc')
                            
    
    def _pushPublicKeys(self):
        '''Export base TP keys'''
        
        pubKeySql = """SELECT t.MTABLEID,t.TABLELEVEL,c.DATANAME,c.DESCRIPTION,c.DATATYPE,c.DATASIZE, 
                    c.DATASCALE,c.UNIQUEKEY,c.INDEXES,c.NULLABLE,c.UNIQUEVALUE,c.INCLUDESQL 
                    FROM MeasurementColumn c, MeasurementTable t WHERE c.MTABLEID=t.MTABLEID 
                    and t.MTABLEID LIKE '""" + self.baseTP + "%'"
        
        self._writeSqlDetailsToFile(pubKeySql, 'publicKeys')
        
        
    def _pushBaseTPJoins(self):
        '''Export base TP joins'''
        
        baseJoinsSql = """SELECT SOURCETABLE,SOURCELEVEL,SOURCECOLUMN,TARGETTABLE,TARGETLEVEL,
        TARGETCOLUMN,CARDINALITY,CONTEXT,EXCLUDEDCONTEXTS,UNIVERSEEXTENSION 
        FROM Universejoin where versionid ='""" + self.baseTP + "'"
        
        self._writeSqlDetailsToFile(baseJoinsSql, 'baseJoins')
    
    
    def _pushRefTable(self):
        '''Export TP Topology table details
        Exporting from DB because some data is not part of TP Model'''
        
        refTabSql = """SELECT TYPEID,DESCRIPTION,TYPENAME,TABLE_TYPE,UPDATE_POLICY 
        FROM ReferenceTable where VERSIONID ='""" + self.versionId + "'"
        
        self._writeSqlDetailsToFile(refTabSql, 'refTable')
        
    
    def _pushRefCol(self):
        '''Export TP Topology column details
        Exporting from DB because some data is not part of TP Model'''
        
        refColSql = """SELECT c.TYPEID,TYPENAME,DATANAME,c.DESCRIPTION,DATATYPE,DATASIZE,DATASCALE,
        UNIQUEVALUE,NULLABLE,INDEXES,UNIQUEKEY,INCLUDESQL,INCLUDEUPD,UNIVERSECLASS,UNIVERSEOBJECT,
        UNIVERSECONDITION FROM ReferenceColumn c,ReferenceTable t 
        WHERE t.TYPEID=c.TYPEID AND c.TYPEID LIKE '""" + self.versionId + "%'"
        
        self._writeSqlDetailsToFile(refColSql, 'refCol')
            
            
    def _pushCommonTop(self):
        '''Export Topology table details
        Exporting from DB because some data is not part of TP Model'''
        
        comTopSql = """SELECT c.TYPEID,TYPENAME,DATANAME,c.DESCRIPTION,DATATYPE,DATASIZE,DATASCALE,
        UNIQUEVALUE,NULLABLE,INDEXES,UNIQUEKEY,INCLUDESQL,INCLUDEUPD,UNIVERSECLASS,UNIVERSEOBJECT,
        UNIVERSECONDITION,UPDATE_POLICY FROM ReferenceColumn c,ReferenceTable t 
        WHERE t.TYPEID=c.TYPEID AND (t.TYPENAME = '' OR t.TYPENAME IS NULL) 
        AND c.TYPEID LIKE '""" + self.versionId + "%'"
        
        self._writeSqlDetailsToFile(comTopSql, 'commonTop')
        
    
    def _pushBaseClasses(self):
        '''Export base TP Universe Classes'''
        
        baseClsSql = """SELECT CLASSNAME,UNIVERSEEXTENSION,DESCRIPTION,PARENT,OBJ_BH_REL,ELEM_BH_REL 
        FROM Universeclass where versionid ='""" + self.baseTP + "'and classname not like ('%_Keys') ORDER BY ORDERNRO"
        
        self._writeSqlDetailsToFile(baseClsSql, 'baseClasses')

    
    def _pushBaseTables(self):
        '''Export base TP Universe Tables'''
        
        baseTabSql = """SELECT OWNER,TABLENAME,UNIVERSEEXTENSION,ALIAS,OBJ_BH_REL,ELEM_BH_REL 
        FROM Universetable WHERE VERSIONID='""" + self.baseTP + "'"
        
        self._writeSqlDetailsToFile(baseTabSql, 'baseTables')

    
    def _pushBaseObjects(self):
        '''Export base TP Universe Objects'''
        
        baseObjSql = """SELECT CLASSNAME,UNIVERSEEXTENSION,OBJECTNAME,DESCRIPTION,OBJECTTYPE,
        QUALIFICATION,AGGREGATION,OBJSELECT,OBJWHERE,OBJ_BH_REL,ELEM_BH_REL FROM Universeobject 
        WHERE VERSIONID='""" + self.baseTP + "'"
        
        self._writeSqlDetailsToFile(baseObjSql, 'baseObjects')
        
    
    def _pushBaseConditions(self):
        '''Export base TP Universe Conditions'''
        
        baseCondSql = """SELECT CLASSNAME,UNIVERSEEXTENSION,UNIVERSECONDITION,DESCRIPTION,CONDWHERE,
        AUTOGENERATE,CONDOBJCLASS,CONDOBJECT,PROMPTTEXT,MULTISELECTION,FREETEXT,OBJ_BH_REL,ELEM_BH_REL 
        FROM Universecondition WHERE VERSIONID='""" + self.baseTP + "'"
        
        self._writeSqlDetailsToFile(baseCondSql, 'baseConditions')
    
    
    def _formatData(self,columnVal):
        '''Changing values to be consistent with how it is being read by VB Code'''
        
        columnVal = columnVal.replace(",","*comma*")
        columnVal = columnVal.replace("\r","\n")
        columnVal = columnVal.replace("\n","*newline*")
        if columnVal == "None":
            columnVal = ""
        return columnVal
    
    
    def _writeSqlDetailsToFile(self, sql, file):
        '''Util Method - get data from DB and write to file'''
        
        DbCursor = self.dbAccess.getCursor()
        DbCursor.execute(sql)
        cols = DbCursor.description
        rows = DbCursor.fetchall()
        if rows is not None:
            for row in rows:
                data = ""
                colcount=0
                for col in cols:
                    data = data + self._formatData(str(row[colcount])) + ","
                    colcount+=1
                
                data = data[:-1]
                Utils.writeUnvDetails(data, self.unvDirectory + file)
        else:
            pass
    