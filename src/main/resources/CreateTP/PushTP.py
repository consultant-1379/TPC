'''
Created on Jun 20, 2016

@author: ebrifol
'''
import Utils
import CreateTPUtils
import java.lang.System
from datetime import datetime

class PushTPtoDB(object):
    
    def __init__(self, dbConn, PathtoDb, envPath, dbAccess, logger, createSets):
        self.pathToDB = PathtoDb
        self.envPath = envPath
        self.dbConn = dbConn
        self.dbAccess = dbAccess
        self.log = logger
        self.createSets = createSets
    
    def pushData(self, TPModel):
        self.dataStore = Utils.DataStorage()
        
        self.log.info('Pushing Versioning')
        self._pushVersioningDetails(TPModel)
        self.log.info('Pushing Fact Tables')
        self._pushFactTables(TPModel)
        self.log.info('Pushing Busy Hours')
        self._pushBusyHours(TPModel)
        self.log.info('Pushing Attributes and Parsers')
        self._pushAttributesAndParsers(TPModel)
        self.log.info('Pushing Reference Tables')
        self._pushReferenceTables(TPModel)
        self.log.info('Pushing External Statements')
        self._pushExternalStatements(TPModel)
        
        self.log.info('Pushing background Fact Table details')
        CreateTPUtils.factTableBackgroundGeneration(self.dataStore, self.dbConn)
        self.log.info('Pushing background Busy Hour details')
        CreateTPUtils.BusyHourBackground(self.dataStore, self.dbConn)
        self.log.info('Pushing background Reference Tables details')
        CreateTPUtils.RefTableBackground(self.dataStore, self.dbConn)
        
        self.log.info('Pushing Universe details')
        self._pushUniverse(TPModel)
        
        if self.createSets:
            self.log.info('Pushing Sets')
            CreateTPUtils.generateSets(self.dataStore, self.dbConn, self.envPath)
        
        
        
    def _pushVersioningDetails(self, TPModel):
        from com.distocraft.dc5000.repository.dwhrep import Versioning
        from com.distocraft.dc5000.repository.dwhrep import Supportedvendorrelease
        from com.distocraft.dc5000.repository.dwhrep import Techpackdependency
        ####### TP LEVEL #######
        #TP Versioning
        lockdate = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        Versioningdict, TpDependencies, SupportedVendorReleases = TPModel.populateRepDbDicts()
        Versioningdict['BASEDEFINITION'] = Utils.getBaseTPName(self.dbAccess.getCursor())
        Versioningdict['STATUS'] = 1
        Versioningdict['ENIQ_LEVEL'] = self.pathToDB.split('/')[-3].split('-')[1]
        Versioningdict['LOCKEDBY'] = 'TPC-' + java.lang.System.getProperty('TPCbuildNumber')
        Versioningdict['LOCKDATE'] = lockdate
        versioning = Utils.convertAndPush(Versioningdict, Versioning, self.dbConn)
        self.dataStore.addDataToStore('Versioning', versioning)
        
        #Tech Pack Dependency
        for dependency in TpDependencies:
            Utils.convertAndPush(dependency, Techpackdependency, self.dbConn)
        
        #Supported Vendor Releases
        for VendorRelease in SupportedVendorReleases:
            RepVendorRelease = Supportedvendorrelease(self.dbConn, True)
            RepVendorRelease.setVersionid(TPModel.versionID)
            RepVendorRelease.setVendorrelease(VendorRelease)
            RepVendorRelease.insertDB()
        self.dataStore.addDataToStore('SVR', SupportedVendorReleases)
    
    def _pushFactTables(self, TPModel):
        from com.distocraft.dc5000.repository.dwhrep import Measurementtypeclass
        from com.distocraft.dc5000.repository.dwhrep import Measurementtype
        from com.distocraft.dc5000.repository.dwhrep import Measurementdeltacalcsupport
        
        ####### Fact Tables #######
        for table in TPModel.measurementTables.itervalues():
            MeasTypeClass, deltacalcSupport, MeasType = table.populateRepDbDicts()
            measTypeClasses = self.dataStore.getDataFromStore('MeasTypeClass')
            if MeasTypeClass['TYPECLASSID'] not in measTypeClasses:
                Utils.convertAndPush(MeasTypeClass, Measurementtypeclass, self.dbConn)
                measTypeClasses.append(MeasTypeClass['TYPECLASSID'])
                self.dataStore.addDataToStore('MeasTypeClass', measTypeClasses)
                
            Utils.convertAndPush(MeasType, Measurementtype, self.dbConn)
        
            if MeasType['DELTACALCSUPPORT'] == 1:
                SVR = self.dataStore.getDataFromStore('SVR')
                if 'VENDORRELEASE' in deltacalcSupport:
                    deltaCalc = deltacalcSupport['VENDORRELEASE']
                    if deltaCalc.find(":") != -1:
                        deltaCalc = deltaCalc[0:deltaCalc.index(":")]
                        
                    supportedReleases = str(deltaCalc + ',').split(',')
                    for VendorRelease in SVR:
                        deltacalcSupport['VENDORRELEASE'] = VendorRelease
                        if VendorRelease in supportedReleases:
                            deltacalcSupport['DELTACALCSUPPORT'] = 1
                        else:
                            deltacalcSupport['DELTACALCSUPPORT'] = 0
                            Utils.convertAndPush(deltacalcSupport, Measurementdeltacalcsupport, self.dbConn)
    
    def _pushBusyHours(self, TPModel):
        from com.distocraft.dc5000.repository.dwhrep import Busyhourplaceholders
        from com.distocraft.dc5000.repository.dwhrep import Busyhourmapping
        from com.distocraft.dc5000.repository.dwhrep import Busyhourrankkeys
        from com.distocraft.dc5000.repository.dwhrep import Busyhoursource
        from com.distocraft.dc5000.repository.dwhrep import Busyhour
        from com.distocraft.dc5000.repository.dwhrep import Measurementobjbhsupport
        
        ####### Busy Hours #######
        for busyhour in TPModel.busyHours.itervalues():
            objbhsupport, bhplaceholdersDict, BHMapping = busyhour.populateRepDbDicts()
            Utils.convertAndPush(bhplaceholdersDict, Busyhourplaceholders, self.dbConn)
        
            ####### Busy Hours Placeholders #######
            for placeholder in busyhour.busyHourPlaceHolders.itervalues():
                busyhourDict, BhSources, BHRankKeys = placeholder.populateRepDbDicts()
                
                busyhourDict['BHLEVEL'] = busyhour.rankingTable
                Utils.convertAndPush(busyhourDict, Busyhour, self.dbConn)
                
                for BHSource in BhSources:
                    BHSource['BHLEVEL'] = busyhour.rankingTable
                    Utils.convertAndPush(BHSource, Busyhoursource, self.dbConn)
                    
                for BHRankKey in BHRankKeys:
                    BHRankKey['BHLEVEL'] = busyhour.rankingTable
                    Utils.convertAndPush(BHRankKey, Busyhourrankkeys, self.dbConn)
            
            for objbh in objbhsupport:
                Utils.convertAndPush(objbh, Measurementobjbhsupport, self.dbConn)
            
            for mapping in BHMapping: 
                Utils.convertAndPush(mapping, Busyhourmapping, self.dbConn)
    
    def _pushReferenceTables(self, TPModel):
        from com.distocraft.dc5000.repository.dwhrep import Referencetable
        from com.distocraft.dc5000.repository.dwhrep import Referencecolumn
        
        ####### Reference Tables #######
        for table in TPModel.referenceTables.itervalues():
            Utils.convertAndPush(table.populateRepDbDicts(), Referencetable, self.dbConn)
            
            ####### Attributes #######
            refKeyColNumber = 100
            for attribute in table.attributes.itervalues():
                attDict = attribute.populateRepDbDicts()
                attDict['TYPEID'] = table.typeid
                if attribute.attributeType == 'referenceKey':
                    attDict['COLNUMBER'] = refKeyColNumber
                    Utils.convertAndPush(attDict, Referencecolumn, self.dbConn)
                    refKeyColNumber = refKeyColNumber +1
            
            ####### Parsers #######
            self._pushParsers(table) 
                
    def _pushAttributesAndParsers(self, TPModel):
        from com.distocraft.dc5000.repository.dwhrep import Measurementcounter
        from com.distocraft.dc5000.repository.dwhrep import Measurementkey
        from com.distocraft.dc5000.repository.dwhrep import Measurementvector
        
        for table in TPModel.measurementTables.itervalues():
            MeasTypeClass, deltacalcSupport, MeasType = table.populateRepDbDicts()
            ####### Attributes #######
            measCounters = []
            measKeys = []
            measCounterColNumber = 1
            measKeyColNumber = 1
            for attribute in table.attributes.itervalues():
                attDict = attribute.populateRepDbDicts()
                attDict['TYPEID'] = table.typeid
                if attribute.attributeType == 'measurementCounter':
                    attDict['COLNUMBER'] = measCounterColNumber
                    attDict['COUNTAGGREGATION'] = CreateTPUtils.evaluteCountAggreation(MeasType, deltacalcSupport, self.dataStore)
                    meascounter = Utils.convertAndPush(attDict, Measurementcounter, self.dbConn)
                    measCounters.append(meascounter)
                    measCounterColNumber = measCounterColNumber +1
                    
                    for quant in attribute.vectors.itervalues():
                        for indices in quant.itervalues():
                            for vector in indices.itervalues():
                                for venRel in vector.VendorRelease.split(","):
                                    vectorRow = vector.populateRepDbDicts()
                                    vectorRow['VENDORRELEASE'] = venRel
                                    Utils.convertAndPush(vectorRow, Measurementvector, self.dbConn)
                                
                elif attribute.attributeType == 'measurementKey':
                    attDict['COLNUMBER'] = measKeyColNumber
                    measkey = Utils.convertAndPush(attDict, Measurementkey, self.dbConn)
                    measKeys.append(measkey)
                    measKeyColNumber = measKeyColNumber +1
            
            self.dataStore.addDataToStore('counters', measCounters)
            self.dataStore.addDataToStore('keys', measKeys)
            ####### Parsers #######
            self._pushParsers(table)
        
    def _pushParsers(self, table):
        from com.distocraft.dc5000.repository.dwhrep import Dataformat
        from com.distocraft.dc5000.repository.dwhrep import Defaulttags
        from com.distocraft.dc5000.repository.dwhrep import Transformer
        from com.distocraft.dc5000.repository.dwhrep import Transformation
        
        for parser in table.parsers.itervalues():
            datatags, transDict, attributeTags = parser.populateRepDbDicts()
            
            if table.properties['DATAFORMATSUPPORT'] == '1':
                df = Dataformat(self.dbConn)
                df.setDataformatid(parser.dataFormatID)
                df.setTypeid(table.typeid)
                df.setVersionid(table.versionID)
                df.setObjecttype(table.tableType)
                df.setFoldername(table.name)
                df.setDataformattype(parser.parserType)
                df.insertDB()
            
            attrDict = self.dataStore.getDataFromStore(table.typeid)
            if len(attrDict) == 0:
                attrDict = {}
            attrDict[parser.dataFormatID] = attributeTags
            self.dataStore.addDataToStore(table.typeid, attrDict)
                        
            for datatag in datatags:
                Utils.convertAndPush(datatag, Defaulttags, self.dbConn)
            
            ####### Transformations #######
            Utils.convertAndPush(transDict, Transformer, self.dbConn)
            
            for trans in parser.transformations:
                Utils.convertAndPush(trans.populateRepDbDicts(), Transformation, self.dbConn)

    def _pushExternalStatements(self, TPModel):
        from com.distocraft.dc5000.repository.dwhrep import Externalstatement
        ####### External Statements #######
        ExecOrder = CreateTPUtils.baseExternalStatements(self.dataStore, self.dbConn, 0)
        
        for ExtStatement in TPModel.externalStatements.itervalues():
            extDict = ExtStatement.populateRepDbDicts()
            EXECUTIONORDER = int(extDict['EXECUTIONORDER'])
            difference = 0
            if EXECUTIONORDER <= ExecOrder:
                difference = ExecOrder - EXECUTIONORDER
                ExecOrder = EXECUTIONORDER + difference + 1
            extDict['EXECUTIONORDER'] = str(ExecOrder)
            Utils.convertAndPush(extDict, Externalstatement, self.dbConn)
        
    def _pushUniverse(self, TPModel):
        from com.distocraft.dc5000.repository.dwhrep import Universename
        from com.distocraft.dc5000.repository.dwhrep import Universetable
        from com.distocraft.dc5000.repository.dwhrep import Universeclass
        from com.distocraft.dc5000.repository.dwhrep import Universeobject
        from com.distocraft.dc5000.repository.dwhrep import Universecondition
        from com.distocraft.dc5000.repository.dwhrep import Universejoin
        
        for UniverseModel in TPModel.universes.itervalues():

            if len(UniverseModel.universeExtensions) == 0:
                Utils.convertAndPush(UniverseModel.populateRepDbDicts(), Universename, self.dbConn)
            
            classOrderNumber = 1
            for universeClass in UniverseModel.universeClasses.itervalues():
                RepDbDict = universeClass.populateRepDbDicts()
                if 'ORDERNRO' not in RepDbDict:
                    RepDbDict['ORDERNRO']= classOrderNumber
                Utils.convertAndPush(RepDbDict, Universeclass, self.dbConn)
                classOrderNumber = classOrderNumber + 1
                    
                objOrderNumber = 0
                for universeObject in universeClass.universeObjObjects.itervalues():
                    RepDbDict = universeObject.populateRepDbDicts()
                    RepDbDict['ORDERNRO']= objOrderNumber
                    Utils.convertAndPush(RepDbDict, Universeobject, self.dbConn)
                    objOrderNumber = objOrderNumber + 1
                    
                condorderno = 0  
                for universeCon in universeClass.universeConditionObjects.itervalues():
                    RepDbDict = universeCon.populateRepDbDicts()
                    RepDbDict['ORDERNRO']= condorderno
                    Utils.convertAndPush(RepDbDict, Universecondition, self.dbConn)
                    condorderno = condorderno + 1
                
            tableorderno = 0 
            for universeTable in UniverseModel.universeTables.itervalues():
                RepDbDict = universeTable.populateRepDbDicts()
                RepDbDict['ORDERNRO'] = tableorderno
                Utils.convertAndPush(RepDbDict, Universetable, self.dbConn)
                tableorderno = tableorderno + 1
                
            for universeJoin in UniverseModel.universeJoins.itervalues():
                Utils.convertAndPush(universeJoin.populateRepDbDicts(), Universejoin, self.dbConn)
            
            ####### UNIVERSE EXTENSION #######
            for extension in UniverseModel.universeExtensions.itervalues():
                Utils.convertAndPush(extension.populateRepDbDicts(), Universename, self.dbConn)
                
                classOrderNumber = 1
                for universeClass in extension.universeClassObjects.itervalues():
                    RepDbDict = universeClass.populateRepDbDicts()
                    if 'ORDERNRO' not in RepDbDict:
                        RepDbDict['ORDERNRO']= classOrderNumber
                    Utils.convertAndPush(RepDbDict, Universeclass, self.dbConn)
                    classOrderNumber = classOrderNumber + 1
                    
                    objOrderNumber = 0
                    for universeObject in universeClass.universeObjObjects.itervalues():
                        RepDbDict = universeObject.populateRepDbDicts()
                        RepDbDict['ORDERNRO']= objOrderNumber
                        Utils.convertAndPush(RepDbDict, Universeobject, self.dbConn)
                        objOrderNumber = objOrderNumber + 1
                    
                    condorderno = 0  
                    for universeCon in universeClass.universeConditionObjects.itervalues():
                        RepDbDict = universeCon.populateRepDbDicts()
                        RepDbDict['ORDERNRO']= condorderno
                        Utils.convertAndPush(RepDbDict, Universecondition, self.dbConn)
                        condorderno = condorderno + 1
                
                tableorderno = 0 
                for universeTable in extension.universeTableObjects.itervalues():
                    RepDbDict = universeTable.populateRepDbDicts()
                    RepDbDict['ORDERNRO'] = tableorderno
                    Utils.convertAndPush(RepDbDict, Universetable, self.dbConn)
                    tableorderno = tableorderno + 1
                
                for universeJoin in extension.universeJoinObjects.itervalues():
                    Utils.convertAndPush(universeJoin.populateRepDbDicts(), Universejoin, self.dbConn)
        


            
    