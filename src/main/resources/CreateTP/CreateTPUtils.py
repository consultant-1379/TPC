'''
Created on Jul 5, 2016

@author: ebrifol
'''
import Utils
from java.util import Properties
from java.util import Vector
from __builtin__ import type

def evaluteCountAggreation(MeasType, deltacalcSupport, dataStore):
    if MeasType['DELTACALCSUPPORT'] == 1:
        SVR = dataStore.getDataFromStore('SVR')
        CountAggSupportedList = []
        CountAggNotSupportedList = []
        flagTreatAs = None
        if 'VENDORRELEASE' in deltacalcSupport:
            deltaCalc = deltacalcSupport['VENDORRELEASE']
            if deltaCalc.find(":") != -1:
                flagTreatAs = deltaCalc[deltaCalc.index(":"):]
                deltaCalc = deltaCalc[0:deltaCalc.index(":")]
                
            supportedReleases = str(deltaCalc + ',').split(',')
            for VendorRelease in SVR:
                if VendorRelease in supportedReleases:
                    CountAggSupportedList.append(VendorRelease)
                else:
                    CountAggNotSupportedList.append(VendorRelease)
                    
        if len(CountAggSupportedList) == 0:
            return 'GAUGE'
        elif len(CountAggNotSupportedList) == 0:
            return 'PEG'
        else:
            countAggSupp = ','.join(CountAggSupportedList) + ';PEG/' + ','.join(CountAggNotSupportedList) + ';GAUGE'
            if flagTreatAs != None:
                countAggSupp = countAggSupp + flagTreatAs
                
            return countAggSupp
        
    return ''

def factTableBackgroundGeneration(dataStore, dbConn):
    from com.distocraft.dc5000.repository.dwhrep import Measurementtype
    from com.distocraft.dc5000.repository.dwhrep import MeasurementtypeFactory
    from com.distocraft.dc5000.repository.dwhrep import Measurementobjbhsupport
    from com.distocraft.dc5000.repository.dwhrep import MeasurementobjbhsupportFactory
    from com.distocraft.dc5000.repository.dwhrep import Aggregation
    from com.distocraft.dc5000.repository.dwhrep import Aggregationrule

    versioning = dataStore.getDataFromStore('Versioning')
    mt = Measurementtype(dbConn)
    mt.setVersionid(versioning.getVersionid())
    mtF = MeasurementtypeFactory(dbConn, mt)
    for MeasTyp in mtF.get():
        createCountTable = False
        if Utils.verifyNotNone(MeasTyp, 'getDeltacalcsupport') == 1:
            createCountTable = True
        
        if Utils.verifyNotNone(MeasTyp, 'getRankingtable') == 0:
            if Utils.verifyNotNone(MeasTyp, 'getPlaintable') == 1:
                createMeasurementInformation(versioning, MeasTyp, 'PLAIN', dbConn, dataStore)
            elif Utils.verifyNotNone(MeasTyp, 'getMixedpartitionstable') == 1:
                createMeasurementInformation(versioning, MeasTyp, 'BIG_RAW', dbConn, dataStore)
                createMeasurementInformation(versioning, MeasTyp, 'RAW', dbConn, dataStore)
            else:
                createMeasurementInformation(versioning, MeasTyp, 'RAW', dbConn, dataStore)
                
            if Utils.verifyNotNone(MeasTyp, 'getTotalagg') == 1:
                createMeasurementInformation(versioning, MeasTyp, 'DAY', dbConn, dataStore)
            
            
            MbhS = Measurementobjbhsupport(dbConn)
            MbhS.setTypeid(MeasTyp.getTypeid())
            MbhSF = MeasurementobjbhsupportFactory(dbConn, MbhS)
            if MbhSF.size() > 0:
                createMeasurementInformation(versioning, MeasTyp, 'DAYBH', dbConn, dataStore)
                
            if createCountTable:
                createMeasurementInformation(versioning, MeasTyp, 'COUNT', dbConn, dataStore)
                
        else:
            createMeasurementInformation(versioning, MeasTyp, 'RANKBH', dbConn, dataStore)
        
        aggdict = {}
        ruleID = 0
        #AGGREGATIONS
        if Utils.verifyNotNone(MeasTyp, 'getRankingtable') == 0:
            if Utils.verifyNotNone(MeasTyp, 'getTotalagg') == 1:
                if createCountTable:
                    aggdict['AGGREGATION'] = MeasTyp.getTypename()+'_COUNT'
                    aggdict['VERSIONID'] = MeasTyp.getVersionid()
                    aggdict['AGGREGATIONTYPE'] = 'TOTAL'
                    aggdict['AGGREGATIONSCOPE'] = 'COUNT'
                    Utils.convertAndPush(aggdict, Aggregation, dbConn)
                    
                aggdict = {}  
                aggdict['AGGREGATION'] = MeasTyp.getTypename()+'_DAY'
                aggdict['VERSIONID'] = MeasTyp.getVersionid()
                aggdict['AGGREGATIONTYPE'] = 'TOTAL'
                aggdict['AGGREGATIONSCOPE'] = 'DAY'
                Utils.convertAndPush(aggdict, Aggregation, dbConn)
                
                aggdict = {}
                aggdict['AGGREGATION'] = MeasTyp.getTypename() +'_DAY'
                aggdict['VERSIONID'] = MeasTyp.getVersionid()
                aggdict['RULEID'] = ruleID
                aggdict['TARGET_MTABLEID'] = MeasTyp.getTypeid()+':DAY'
                aggdict['TARGET_TYPE'] = MeasTyp.getTypename()
                aggdict['TARGET_LEVEL'] = 'DAY'
                aggdict['TARGET_TABLE'] = MeasTyp.getTypename() +'_DAY'
                aggdict['SOURCE_TYPE'] = MeasTyp.getTypename()
                aggdict['RULETYPE'] = 'TOTAL'
                aggdict['AGGREGATIONSCOPE'] = 'DAY'
                if createCountTable:
                    aggdict['SOURCE_MTABLEID'] = MeasTyp.getTypeid()+':COUNT'
                    aggdict['SOURCE_LEVEL'] = 'COUNT'
                    aggdict['SOURCE_TABLE'] = MeasTyp.getTypename() +'_COUNT'  
                else:
                    aggdict['SOURCE_MTABLEID'] = MeasTyp.getTypeid()+':RAW'
                    aggdict['SOURCE_LEVEL'] = 'RAW'
                    aggdict['SOURCE_TABLE'] = MeasTyp.getTypename() +'_RAW'
                Utils.convertAndPush(aggdict, Aggregationrule, dbConn)
                ruleID = ruleID + 1
                
                for measobjbhsupport in MbhSF.get():
                    bhtype = measobjbhsupport.getObjbhsupport()
                    
                    #Create DayBH aggregation
                    aggdict = {}  
                    aggdict['AGGREGATION'] = MeasTyp.getTypename()+'_DAYBH_'+bhtype
                    aggdict['VERSIONID'] = MeasTyp.getVersionid()
                    aggdict['AGGREGATIONTYPE'] = 'DAYBH'
                    aggdict['AGGREGATIONSCOPE'] = 'DAY'
                    Utils.convertAndPush(aggdict, Aggregation, dbConn)

                    aggdict = {}
                    aggdict['AGGREGATION'] = MeasTyp.getTypename() +'_DAYBH_'+bhtype
                    aggdict['VERSIONID'] = MeasTyp.getVersionid()
                    aggdict['RULEID'] = ruleID
                    aggdict['TARGET_MTABLEID'] = MeasTyp.getTypeid()+':DAYBH'
                    aggdict['TARGET_TYPE'] = MeasTyp.getTypename()
                    aggdict['TARGET_LEVEL'] = 'DAYBH'
                    aggdict['TARGET_TABLE'] = MeasTyp.getTypename() +'_DAYBH'
                    aggdict['SOURCE_TYPE'] = MeasTyp.getTypename()
                    aggdict['RULETYPE'] = 'BHSRC'
                    aggdict['AGGREGATIONSCOPE'] = 'DAY'
                    if createCountTable:
                        #Create DayBH-Count aggregations rule (BHSRC)
                        aggdict['SOURCE_MTABLEID'] = MeasTyp.getTypeid()+':COUNT'
                        aggdict['SOURCE_LEVEL'] = 'COUNT'
                        aggdict['SOURCE_TABLE'] = MeasTyp.getTypename() +'_COUNT'
                    else:
                        #DayBH-Raw aggregation rule (BHSRC)
                        aggdict['SOURCE_MTABLEID'] = MeasTyp.getTypeid()+':RAW'
                        aggdict['SOURCE_LEVEL'] = 'RAW'
                        aggdict['SOURCE_TABLE'] = MeasTyp.getTypename() +'_RAW'
                    Utils.convertAndPush(aggdict, Aggregationrule, dbConn)
                    ruleID = ruleID + 1
                    
                    #Create WeekBH aggregation
                    aggdict = {}  
                    aggdict['AGGREGATION'] = MeasTyp.getTypename()+'_WEEKBH_'+bhtype
                    aggdict['VERSIONID'] = MeasTyp.getVersionid()
                    aggdict['AGGREGATIONTYPE'] = 'DAYBH'
                    aggdict['AGGREGATIONSCOPE'] = 'WEEK'
                    Utils.convertAndPush(aggdict, Aggregation, dbConn)
            
                    #Create WeekBH-DayBH aggregation rules (DAYBHCLASS)
                    aggdict = {}
                    aggdict['AGGREGATION'] = MeasTyp.getTypename() +'_WEEKBH_'+bhtype
                    aggdict['VERSIONID'] = MeasTyp.getVersionid()
                    aggdict['RULEID'] = ruleID
                    aggdict['TARGET_MTABLEID'] = MeasTyp.getTypeid()+':DAYBH'
                    aggdict['TARGET_TYPE'] = MeasTyp.getTypename()
                    aggdict['TARGET_LEVEL'] = 'DAYBH'
                    aggdict['TARGET_TABLE'] = MeasTyp.getTypename() +'_DAYBH'
                    aggdict['SOURCE_MTABLEID'] = MeasTyp.getTypeid()+':DAYBH'
                    aggdict['SOURCE_TYPE'] = MeasTyp.getTypename()
                    aggdict['SOURCE_LEVEL'] = 'DAYBH'
                    aggdict['SOURCE_TABLE'] = MeasTyp.getTypename() +'_DAYBH'
                    aggdict['RULETYPE'] = 'DAYBHCLASS_DAYBH'
                    aggdict['AGGREGATIONSCOPE'] = 'WEEK'
                    Utils.convertAndPush(aggdict, Aggregationrule, dbConn)
                    ruleID = ruleID + 1
                    
                    #Create MonthBH aggregation
                    aggdict = {}  
                    aggdict['AGGREGATION'] = MeasTyp.getTypename()+'_MONTHBH_'+bhtype
                    aggdict['VERSIONID'] = MeasTyp.getVersionid()
                    aggdict['AGGREGATIONTYPE'] = 'DAYBH'
                    aggdict['AGGREGATIONSCOPE'] = 'MONTH'
                    Utils.convertAndPush(aggdict, Aggregation, dbConn)
            
                    #Create MonthBH-DayBH aggregation rule (DAYBHCLASS)
                    aggdict = {}
                    aggdict['AGGREGATION'] = MeasTyp.getTypename() +'_MONTHBH_'+bhtype
                    aggdict['VERSIONID'] = MeasTyp.getVersionid()
                    aggdict['RULEID'] = ruleID
                    aggdict['TARGET_MTABLEID'] = MeasTyp.getTypeid()+':DAYBH'
                    aggdict['TARGET_TYPE'] = MeasTyp.getTypename()
                    aggdict['TARGET_LEVEL'] = 'DAYBH'
                    aggdict['TARGET_TABLE'] = MeasTyp.getTypename() +'_DAYBH'
                    aggdict['SOURCE_MTABLEID'] = MeasTyp.getTypeid()+':DAYBH'
                    aggdict['SOURCE_TYPE'] = MeasTyp.getTypename()
                    aggdict['SOURCE_LEVEL'] = 'DAYBH'
                    aggdict['SOURCE_TABLE'] = MeasTyp.getTypename() +'_DAYBH'
                    aggdict['RULETYPE'] = 'DAYBHCLASS_DAYBH'
                    aggdict['AGGREGATIONSCOPE'] = 'MONTH'
                    Utils.convertAndPush(aggdict, Aggregationrule, dbConn)
                    ruleID = ruleID + 1
                    
                    #Create DayBH-RankBH aggregation : rule (RANKSRC)
                    aggdict = {}
                    aggdict['AGGREGATION'] = MeasTyp.getTypename() +'_DAYBH_'+bhtype
                    aggdict['VERSIONID'] = MeasTyp.getVersionid()
                    aggdict['RULEID'] = ruleID
                    aggdict['TARGET_MTABLEID'] = MeasTyp.getTypeid()+':DAYBH'
                    aggdict['TARGET_TYPE'] = MeasTyp.getTypename()
                    aggdict['TARGET_LEVEL'] = 'DAYBH'
                    aggdict['TARGET_TABLE'] = MeasTyp.getTypename() +'_DAYBH'
                    aggdict['SOURCE_MTABLEID'] = MeasTyp.getVersionid()+':'+MeasTyp.getVendorid()+'_'+bhtype+'BH:RANKBH'
                    aggdict['SOURCE_TYPE'] = MeasTyp.getVendorid()+'_'+bhtype+'BH' 
                    aggdict['SOURCE_LEVEL'] = 'RANKBH'
                    aggdict['SOURCE_TABLE'] = MeasTyp.getVendorid()+'_'+bhtype+'BH_RANKBH' 
                    aggdict['RULETYPE'] = 'RANKSRC'
                    aggdict['AGGREGATIONSCOPE'] = 'DAY'
                    Utils.convertAndPush(aggdict, Aggregationrule, dbConn)
                    ruleID = ruleID + 1
                    
                    #Create Week-RankBH aggregation : rule (DAYBHCLASS)
                    aggdict = {}
                    aggdict['AGGREGATION'] = MeasTyp.getTypename() +'_WEEKBH_'+bhtype
                    aggdict['VERSIONID'] = MeasTyp.getVersionid()
                    aggdict['RULEID'] = ruleID
                    aggdict['TARGET_MTABLEID'] = MeasTyp.getTypeid()+':DAYBH'
                    aggdict['TARGET_TYPE'] = MeasTyp.getTypename()
                    aggdict['TARGET_LEVEL'] = 'DAYBH'
                    aggdict['TARGET_TABLE'] = MeasTyp.getTypename() +'_DAYBH'
                    aggdict['SOURCE_MTABLEID'] = MeasTyp.getVersionid()+':'+MeasTyp.getVendorid()+'_'+bhtype+'BH:RANKBH'
                    aggdict['SOURCE_TYPE'] = MeasTyp.getVendorid()+'_'+bhtype+'BH' 
                    aggdict['SOURCE_LEVEL'] = 'RANKBH'
                    aggdict['SOURCE_TABLE'] = MeasTyp.getVendorid()+'_'+bhtype+'BH_RANKBH' 
                    aggdict['RULETYPE'] = 'DAYBHCLASS'
                    aggdict['AGGREGATIONSCOPE'] = 'WEEK'
                    Utils.convertAndPush(aggdict, Aggregationrule, dbConn)
                    ruleID = ruleID + 1
                    
                    #Create MonthBH-RankBH aggregation : rule (DAYBHCLASS)
                    aggdict = {}
                    aggdict['AGGREGATION'] = MeasTyp.getTypename() +'_MONTHBH_'+bhtype
                    aggdict['VERSIONID'] = MeasTyp.getVersionid()
                    aggdict['RULEID'] = ruleID
                    aggdict['TARGET_MTABLEID'] = MeasTyp.getTypeid()+':DAYBH'
                    aggdict['TARGET_TYPE'] = MeasTyp.getTypename()
                    aggdict['TARGET_LEVEL'] = 'DAYBH'
                    aggdict['TARGET_TABLE'] = MeasTyp.getTypename() +'_DAYBH'
                    aggdict['SOURCE_MTABLEID'] = MeasTyp.getVersionid()+':'+MeasTyp.getVendorid()+'_'+bhtype+'BH:RANKBH'
                    aggdict['SOURCE_TYPE'] = MeasTyp.getVendorid()+'_'+bhtype+'BH' 
                    aggdict['SOURCE_LEVEL'] = 'RANKBH'
                    aggdict['SOURCE_TABLE'] = MeasTyp.getVendorid()+'_'+bhtype+'BH_RANKBH' 
                    aggdict['RULETYPE'] = 'DAYBHCLASS'
                    aggdict['AGGREGATIONSCOPE'] = 'MONTH'
                    Utils.convertAndPush(aggdict, Aggregationrule, dbConn)
                    ruleID = ruleID + 1
                    
        if createCountTable:
            aggdict = {}
            aggdict['AGGREGATION'] = MeasTyp.getTypename() +'_COUNT'
            aggdict['VERSIONID'] = MeasTyp.getVersionid()
            aggdict['RULEID'] = ruleID
            aggdict['TARGET_MTABLEID'] = MeasTyp.getTypeid()+':COUNT'
            aggdict['TARGET_TYPE'] = MeasTyp.getTypename()
            aggdict['TARGET_LEVEL'] = 'COUNT'
            aggdict['TARGET_TABLE'] = MeasTyp.getTypename() +'_COUNT'
            aggdict['SOURCE_MTABLEID'] = MeasTyp.getTypename()+':RAW'
            aggdict['SOURCE_TYPE'] = MeasTyp.getTypename() 
            aggdict['SOURCE_LEVEL'] = 'RAW'
            aggdict['SOURCE_TABLE'] = MeasTyp.getTypename()+'_RAW'
            aggdict['RULETYPE'] = 'COUNT'
            aggdict['AGGREGATIONSCOPE'] = 'DAY'
            Utils.convertAndPush(aggdict, Aggregationrule, dbConn)
            ruleID = ruleID + 1

     
def createMeasurementInformation(Versioning, MeasTyp, tablelevel, dbConn, dataStore):
    from com.distocraft.dc5000.repository.dwhrep import Measurementtable
    from com.distocraft.dc5000.repository.dwhrep import Measurementcolumn
    from com.distocraft.dc5000.repository.dwhrep import MeasurementcolumnFactory
    from com.distocraft.dc5000.repository.dwhrep import Measurementkey
    from com.distocraft.dc5000.repository.dwhrep import MeasurementkeyFactory
    from com.distocraft.dc5000.repository.dwhrep import Measurementcounter
    from com.distocraft.dc5000.repository.dwhrep import MeasurementcounterFactory
    
    mtableid = MeasTyp.getTypeid() + ':' + tablelevel
    measurementtable = Measurementtable(dbConn, True)
    measurementtable.setMtableid(mtableid)
    measurementtable.setTypeid(MeasTyp.getTypeid())
    measurementtable.setTablelevel(tablelevel)
    measurementtable.setPartitionplan(MeasTyp.getSizing().lower() + '_' + tablelevel.lower())
    if tablelevel == 'PLAIN':
        measurementtable.setBasetablename(MeasTyp.getTypename())
    else:
        measurementtable.setBasetablename(MeasTyp.getTypename() + '_' + tablelevel)
    measurementtable.insertDB()
    
    col = 0
    measkey = Measurementkey(dbConn)
    measkey.setTypeid(MeasTyp.getTypeid())
    mkF = MeasurementkeyFactory(dbConn, measkey, "ORDER BY COLNUMBER")
    for measurementkey in mkF.get():
        col = col + 1
        measurementcolumn = Measurementcolumn(dbConn)
        measurementcolumn.setMtableid(mtableid)
        measurementcolumn.setDataname(Utils.replaceNone(measurementkey.getDataname))
        measurementcolumn.setColnumber(col)
        measurementcolumn.setDatatype(Utils.replaceNone(measurementkey.getDatatype))
        measurementcolumn.setDatasize(Utils.replaceNone(measurementkey.getDatasize))
        measurementcolumn.setDatascale(Utils.replaceNone(measurementkey.getDatascale))
        measurementcolumn.setUniquevalue(Utils.replaceNone(measurementkey.getUniquevalue))
        measurementcolumn.setNullable(Utils.replaceNone(measurementkey.getNullable))
        measurementcolumn.setIndexes(Utils.replaceNone(measurementkey.getIndexes))
        measurementcolumn.setDescription(Utils.replaceNone(measurementkey.getDescription))            
        if measurementkey.getDataid() == None or len(measurementkey.getDataid()) <1:
            measurementcolumn.setDataid(Utils.replaceNone(measurementkey.getDataname))
        else:
            measurementcolumn.setDataid(Utils.replaceNone(measurementkey.getDataid))
        measurementcolumn.setReleaseid(Utils.replaceNone(MeasTyp.getVersionid))
        measurementcolumn.setUniquekey(Utils.replaceNone(measurementkey.getUniquekey))
        measurementcolumn.setIncludesql(Utils.replaceNone(measurementkey.getIncludesql))
        measurementcolumn.setColtype("KEY")
        measurementcolumn.insertDB()
        if tablelevel == 'RAW': 
            process_instruction = 'key'
            if Utils.replaceNone(measurementkey.getDataname) == 'DCVECTOR_INDEX':
                process_instruction = ''
            createDataItem(dataStore, measurementcolumn, dbConn, process_instruction)

        
    basedef = Versioning.getBasedefinition()
    whereMeasurementcolumn = Measurementcolumn(dbConn)
    whereMeasurementcolumn.setMtableid(basedef + ':' + tablelevel)
    mcF = MeasurementcolumnFactory(dbConn, whereMeasurementcolumn, "ORDER BY COLNUMBER")
    for publicColumn in mcF.get():
        col = col + 1
        measurementcolumn = Measurementcolumn(dbConn)
        measurementcolumn.setMtableid(mtableid)
        measurementcolumn.setDataname(Utils.replaceNone(publicColumn.getDataname))
        measurementcolumn.setColnumber(col)
        measurementcolumn.setDatatype(Utils.replaceNone(publicColumn.getDatatype))
        measurementcolumn.setDatasize(Utils.replaceNone(publicColumn.getDatasize))
        measurementcolumn.setDatascale(Utils.replaceNone(publicColumn.getDatascale))
        measurementcolumn.setUniquevalue(Utils.replaceNone(publicColumn.getUniquevalue))
        measurementcolumn.setNullable(Utils.replaceNone(publicColumn.getNullable))
        measurementcolumn.setIndexes(Utils.replaceNone(publicColumn.getIndexes))
        measurementcolumn.setDescription(Utils.replaceNone(publicColumn.getDescription))
        measurementcolumn.setDataid(Utils.replaceNone(publicColumn.getDataid))
        measurementcolumn.setReleaseid(Utils.replaceNone(publicColumn.getReleaseid))
        measurementcolumn.setUniquekey(Utils.replaceNone(publicColumn.getUniquekey))
        measurementcolumn.setIncludesql(Utils.replaceNone(publicColumn.getIncludesql))
        measurementcolumn.setColtype("PUBLICKEY")
        measurementcolumn.insertDB()
        if tablelevel == 'RAW': 
            createDataItem(dataStore, measurementcolumn, dbConn, '')
            
    if tablelevel != 'RANKBH':
        meascount = Measurementcounter(dbConn)
        meascount.setTypeid(MeasTyp.getTypeid())
        mcF = MeasurementcounterFactory(dbConn, meascount, "ORDER BY COLNUMBER")
        for meascounter in mcF.get():
            col = col + 1
            meascolumn = Measurementcolumn(dbConn)
            meascolumn.setMtableid(mtableid)
            meascolumn.setDataname(Utils.replaceNone(meascounter.getDataname))
            meascolumn.setColnumber(col)
            meascolumn.setDatatype(Utils.replaceNone(meascounter.getDatatype))
            meascolumn.setDatasize(Utils.replaceNone(meascounter.getDatasize))
            meascolumn.setDatascale(Utils.replaceNone(meascounter.getDatascale))
            meascolumn.setUniquevalue(255)
            meascolumn.setNullable(1)
            meascolumn.setIndexes("")
            meascolumn.setDescription(Utils.replaceNone(meascounter.getDescription))
            if meascounter.getDataid() == None:# or len(meascounter.getDataid()) < 1:
                meascolumn.setDataid(Utils.replaceNone(meascounter.getDataname))
            else:
                meascolumn.setDataid(Utils.replaceNone(meascounter.getDataid))
            meascolumn.setReleaseid(Utils.replaceNone(MeasTyp.getVersionid))
            meascolumn.setUniquekey(0)
            meascolumn.setIncludesql(Utils.replaceNone(meascounter.getIncludesql))
            meascolumn.setColtype("COUNTER");
            meascolumn.insertDB()
            if tablelevel == 'RAW': 
                createDataItem(dataStore, meascolumn, dbConn, meascounter.getCountertype())


def createDataItem(dataStore, measCol, dbConn, processInstruction):
    from com.distocraft.dc5000.repository.dwhrep import Dataitem
    
    typeid = measCol.getMtableid().rsplit(':',1)[0]
    attrTags = dataStore.getDataFromStore(typeid)
    for dataformatID, attrTagDict in attrTags.iteritems():
        if len(attrTagDict) > 0:
            di = Dataitem(dbConn)
            di.setDataformatid(dataformatID)
            di.setDataname(measCol.getDataname())
            di.setColnumber(measCol.getColnumber())
            di.setProcess_instruction(processInstruction)
            di.setDatatype(measCol.getDatatype())
            di.setDatasize(measCol.getDatasize())
            di.setDatascale(measCol.getDatascale())
            if measCol.getDataname() in attrTagDict and attrTagDict[measCol.getDataname()] != None:
                di.setDataid(attrTagDict[measCol.getDataname()])
            else:
                di.setDataid(measCol.getDataid())
                
            di.insertDB()


def RefTableBackground(dataStore, dbConn):
    from com.distocraft.dc5000.repository.dwhrep import Referencetable
    from com.distocraft.dc5000.repository.dwhrep import ReferencetableFactory
    from com.distocraft.dc5000.repository.dwhrep import Measurementtype
    from com.distocraft.dc5000.repository.dwhrep import MeasurementtypeFactory
    from com.distocraft.dc5000.repository.dwhrep import Referencecolumn
    from com.distocraft.dc5000.repository.dwhrep import ReferencecolumnFactory
    
    versioning = dataStore.getDataFromStore('Versioning')
    techpack_type = versioning.getTechpack_type()
    if techpack_type != 'BASE' and techpack_type != 'SYSTEM':
        rt = Referencetable(dbConn)
        rt.setVersionid(versioning.getBasedefinition())
        rtF = ReferencetableFactory(dbConn, rt)
        for tmpRT in rtF.get():
            if tmpRT.getObjectname() == '(DIM_RANKMT)_BHTYPE':
                mt = Measurementtype(dbConn)
                mt.setVersionid(versioning.getVersionid())
                mtF = MeasurementtypeFactory(dbConn, mt)
                for tmpMT in mtF.get():
                    if tmpMT.getRankingtable() == 1:
                        typeName = tmpRT.getTypename().replace("(DIM_RANKMT)","DIM_" + tmpMT.getObjectname().replace("DC_", "", 1))
                        typeId = versioning.getVersionid() + ":" + typeName
                        
                        newRT = Referencetable(dbConn)
                        newRT.setTypeid(typeId)
                        newRT.setVersionid(versioning.getVersionid())
                        newRT.setTypename(typeName)
                        newRT.setObjectid(typeId)
                        newRT.setObjectname(typeName)
                        newRT.setObjectversion(tmpRT.getObjectversion())
                        newRT.setObjecttype(tmpRT.getObjecttype())
                        newRT.setDescription(tmpRT.getDescription())
                        newRT.setStatus(tmpRT.getStatus())
                        newRT.setUpdate_policy(tmpRT.getUpdate_policy())
                        newRT.setTable_type(tmpRT.getTable_type())
                        newRT.setDataformatsupport(tmpRT.getDataformatsupport())
                        newRT.setBasedef(1)
                        newRT.insertDB()
                        
                        rc = Referencecolumn(dbConn)
                        rc.setTypeid(tmpRT.getTypeid())
                        rcF = ReferencecolumnFactory(dbConn, rc)
                        for tmpRC in rcF.get():
                            newRC = Referencecolumn(dbConn)
                            newRC.setTypeid(typeId)
                            newRC.setDataname(tmpRC.getDataname())
                            newRC.setColnumber(tmpRC.getColnumber())
                            newRC.setDatatype(tmpRC.getDatatype())
                            newRC.setDatasize(tmpRC.getDatasize())
                            newRC.setDatascale(tmpRC.getDatascale())
                            newRC.setUniquevalue(tmpRC.getUniquevalue())
                            newRC.setNullable(tmpRC.getNullable())
                            newRC.setIndexes(tmpRC.getIndexes())
                            newRC.setUniquekey(tmpRC.getUniquekey())
                            newRC.setIncludesql(tmpRC.getIncludesql())
                            newRC.setIncludeupd(tmpRC.getIncludeupd())
                            newRC.setColtype('PUBLICCOL')
                            newRC.setDescription(tmpRC.getDescription())
                            newRC.setUniverseclass(tmpRC.getUniverseclass())
                            newRC.setUniverseobject(tmpRC.getUniverseobject())
                            newRC.setUniversecondition(tmpRC.getUniversecondition())
                            newRC.setDataid(tmpRC.getDataid())
                            newRC.setBasedef(1)
                            newRC.insertDB()
                            
            elif tmpRT.getObjectname() == 'SELECT_(TPNAME)_AGGLEVEL':
                typeName = tmpRT.getTypename().replace("(TPNAME)",versioning.getTechpack_name().replace("DC_", "", 1))
                typeId = versioning.getVersionid() + ":" + typeName
                
                newRT = Referencetable(dbConn)
                newRT.setTypeid(typeId)
                newRT.setVersionid(versioning.getVersionid())
                newRT.setTypename(typeName)
                newRT.setObjectid(typeId)
                newRT.setObjectname(typeName)
                newRT.setObjectversion(tmpRT.getObjectversion())
                newRT.setObjecttype(tmpRT.getObjecttype())
                newRT.setDescription(tmpRT.getDescription())
                newRT.setStatus(tmpRT.getStatus())
                newRT.setUpdate_policy(tmpRT.getUpdate_policy())
                newRT.setTable_type(tmpRT.getTable_type())
                newRT.setDataformatsupport(tmpRT.getDataformatsupport())
                newRT.setBasedef(1)
                newRT.insertDB()
        
            elif tmpRT.getObjectname() == 'PUBLIC_REFTYPE':
                tmpRcList = []
                rc = Referencecolumn(dbConn)
                rc.setTypeid(tmpRT.getTypeid())
                rcF = ReferencecolumnFactory(dbConn, rc, "ORDER BY COLNUMBER")
                for tmpRC in rcF.get():
                    tmpRcList.append(tmpRC)
                
                rt = Referencetable(dbConn)
                rt.setVersionid(versioning.getVersionid())
                rtF = ReferencetableFactory(dbConn, rt)
                for tmpnewRT in rtF.get():
                    if tmpnewRT.getBasedef() == None or (tmpnewRT.getBasedef() != None and tmpnewRT.getBasedef() != 1):
                        if tmpnewRT.getUpdate_policy() == 2 or tmpnewRT.getUpdate_policy() == 3 or tmpnewRT.getUpdate_policy() == 4:
                            colNumber = 0
                            rc2 = Referencecolumn(dbConn)
                            rc2.setTypeid(tmpnewRT.getTypeid())
                            rcF2 = ReferencecolumnFactory(dbConn, rc2)
                            colNumber = len(rcF2.get()) + 100
                            
                            for tmpRC in tmpRcList:
                                colNumber = colNumber + 1
                                
                                newRC = Referencecolumn(dbConn)
                                newRC.setTypeid(tmpnewRT.getTypeid())
                                newRC.setDataname(tmpRC.getDataname())
                                newRC.setColnumber(colNumber)
                                newRC.setDatatype(tmpRC.getDatatype())
                                newRC.setDatasize(tmpRC.getDatasize())
                                newRC.setDatascale(tmpRC.getDatascale())
                                newRC.setUniquevalue(tmpRC.getUniquevalue())
                                newRC.setNullable(tmpRC.getNullable())
                                newRC.setIndexes(tmpRC.getIndexes())
                                newRC.setUniquekey(tmpRC.getUniquekey())
                                newRC.setIncludesql(tmpRC.getIncludesql())
                                newRC.setIncludeupd(tmpRC.getIncludeupd())
                                newRC.setColtype("PUBLICCOL")
                                newRC.setDescription(tmpRC.getDescription())
                                newRC.setUniverseclass(tmpRC.getUniverseclass())
                                newRC.setUniverseobject(tmpRC.getUniverseobject())
                                newRC.setUniversecondition(tmpRC.getUniversecondition())
                                newRC.setDataid(tmpRC.getDataid())
                                newRC.setBasedef(1)
                                newRC.insertDB()
        
        createTopologyDataItem(dataStore,dbConn)
                                
def createTopologyDataItem(dataStore,dbConn):
    '''
    Method that creates Dataitem entries for topology table columns
    '''    
    from com.distocraft.dc5000.repository.dwhrep import Dataitem
    from com.distocraft.dc5000.repository.dwhrep import Dataformat
    from com.distocraft.dc5000.repository.dwhrep import Referencetable
    from com.distocraft.dc5000.repository.dwhrep import ReferencetableFactory
    from com.distocraft.dc5000.repository.dwhrep import Referencecolumn
    from com.distocraft.dc5000.repository.dwhrep import ReferencecolumnFactory
    
    versioning = dataStore.getDataFromStore('Versioning')
    rt = Referencetable(dbConn)
    rt.setDataformatsupport(1)
    rt.setVersionid(versioning.getVersionid())
    rtF = ReferencetableFactory(dbConn, rt)
    
    for rtype in rtF.get():
        attrTags = dataStore.getDataFromStore(rtype.getTypeid())
        if type(attrTags).__name__ != 'list':
            for dataformatID, attrTag in attrTags.iteritems():
                items = dataformatID.rsplit(':',1)
                typeID = items[0]
                dataformattype = items[1]
                if rtype.getTypeid() == typeID:
                    rc = Referencecolumn(dbConn)
                    rc.setTypeid(rtype.getTypeid())
                    rcF = ReferencecolumnFactory(dbConn, rc)
                    for rcol in rcF.get():
                        rcolAttrTags = dataStore.getDataFromStore(rcol.getTypeid())
                        for rcdataformatID, attrTagDict in rcolAttrTags.iteritems():
                            if (rcdataformatID == dataformatID):
                                di = Dataitem(dbConn)
                                di.setDataformatid(dataformatID)
                                di.setDataname(rcol.getDataname())
                                di.setColnumber(rcol.getColnumber())
                                if (rcol.getDataname() in attrTagDict and attrTagDict[rcol.getDataname()] != None):
                                    di.setDataid(attrTagDict[rcol.getDataname()])
                                else:
                                    di.setDataid(rcol.getDataname())
                                di.setProcess_instruction('')
                                di.setDatatype(rcol.getDatatype())
                                di.setDatasize(rcol.getDatasize())
                                di.setDatascale(rcol.getDatascale())
                                di.insertDB()

def BusyHourBackground(dataStore, dbConn):
    from com.distocraft.dc5000.repository.dwhrep import Busyhour
    from com.distocraft.dc5000.repository.dwhrep import BusyhourFactory
    from com.distocraft.dc5000.repository.dwhrep import Busyhoursource
    from com.distocraft.dc5000.repository.dwhrep import BusyhoursourceFactory
    from com.distocraft.dc5000.repository.dwhrep import Aggregation
    from com.distocraft.dc5000.repository.dwhrep import Aggregationrule
    
    versioning = dataStore.getDataFromStore('Versioning')
    
    bh = Busyhour(dbConn)
    bh.setVersionid(versioning.getVersionid())
    bhF = BusyhourFactory(dbConn, bh)
    for busyhour in bhF.get():
        aggdict = {}
        aggdict['AGGREGATION'] = busyhour.getBhlevel()+'_RANKBH_'+busyhour.getBhobject()+"_"+busyhour.getBhtype()
        aggdict['VERSIONID'] = versioning.getVersionid()
        aggdict['AGGREGATIONTYPE'] = 'RANKBH'
        aggdict['AGGREGATIONSCOPE'] = 'DAY'
        Utils.convertAndPush(aggdict, Aggregation, dbConn)
        
        aggdict = {}
        aggdict['AGGREGATION'] = busyhour.getBhlevel()+'_RANKBH_'+busyhour.getBhobject()+"_"+busyhour.getBhtype()
        aggdict['VERSIONID'] = versioning.getVersionid()
        aggdict['RULEID'] = 0            
        aggdict['RULETYPE'] = 'RANKBH'
        aggdict['TARGET_TYPE'] = busyhour.getBhlevel()
        aggdict['TARGET_LEVEL'] = 'RANKBH'
        aggdict['TARGET_TABLE'] = busyhour.getBhlevel() +'_RANKBH'
        aggdict['TARGET_MTABLEID'] = versioning.getVersionid()+':'+busyhour.getBhlevel()+':RANKBH'
        aggdict['SOURCE_TABLE'] = busyhour.getBhlevel()+'_RANKBH_'+busyhour.getBhobject()+"_"+busyhour.getBhtype()
        aggdict['SOURCE_TYPE'] = ''
        aggdict['SOURCE_LEVEL'] = ''
        aggdict['SOURCE_MTABLEID'] = ''
        aggdict['AGGREGATIONSCOPE'] = 'DAY'
        aggdict['BHTYPE'] = busyhour.getBhobject()+"_"+busyhour.getBhtype()
        aggdict['ENABLE'] = busyhour.getEnable()
        
        bhs = Busyhoursource(dbConn)
        bhs.setVersionid(versioning.getVersionid())
        bhs.setBhobject(busyhour.getBhobject())
        bhs.setBhtype(busyhour.getBhtype())
        bhsF = BusyhoursourceFactory(dbConn, bhs)
        bhSourceFlag = 0
        for BHSource in bhsF.get():
            if bhSourceFlag != 1:
                Source_table = BHSource.getTypename().rsplit('_',1)
                aggdict['SOURCE_TYPE'] = Source_table[0]
                aggdict['SOURCE_LEVEL'] = Source_table[1]
                aggdict['SOURCE_MTABLEID']= versioning.getVersionid()+':'+Source_table[0]+':'+Source_table[1]
                bhSourceFlag = 1
        
        if bhSourceFlag == 0:
            aggdict['SOURCE_TYPE'] = ''
            aggdict['SOURCE_LEVEL'] = ''
            aggdict['SOURCE_MTABLEID']= ''
        Utils.convertAndPush(aggdict, Aggregationrule, dbConn)
        
        aggdict = {}
        aggdict['AGGREGATION'] = busyhour.getBhlevel()+'_WEEKRANKBH_'+busyhour.getBhobject()+"_"+busyhour.getBhtype()
        aggdict['VERSIONID'] = versioning.getVersionid()
        aggdict['AGGREGATIONTYPE'] = 'RANKBH'
        aggdict['AGGREGATIONSCOPE'] = 'WEEK'
        Utils.convertAndPush(aggdict, Aggregation, dbConn)
        
        aggdict = {}
        aggdict['AGGREGATION'] = busyhour.getBhlevel()+'_WEEKRANKBH_'+busyhour.getBhobject()+"_"+busyhour.getBhtype()
        aggdict['VERSIONID'] = versioning.getVersionid()
        aggdict['RULEID'] = 1
        aggdict['RULETYPE'] = 'RANKBHCLASS'
        aggdict['TARGET_TYPE'] = busyhour.getBhlevel()
        aggdict['TARGET_LEVEL'] = 'RANKBH'
        aggdict['TARGET_TABLE'] = busyhour.getBhlevel() +'_RANKBH'
        aggdict['TARGET_MTABLEID'] = versioning.getVersionid()+':'+busyhour.getBhlevel()+':RANKBH'
        aggdict['SOURCE_TYPE'] = busyhour.getBhlevel()
        aggdict['SOURCE_LEVEL'] = 'RANKBH'
        aggdict['SOURCE_MTABLEID']= versioning.getVersionid()+':'+busyhour.getBhlevel()+':RANKBH'
        aggdict['SOURCE_TABLE'] = busyhour.getBhlevel() +'_RANKBH'
        aggdict['AGGREGATIONSCOPE'] = 'WEEK'
        aggdict['BHTYPE'] = busyhour.getBhobject()+"_"+busyhour.getBhtype()
        aggdict['ENABLE'] = busyhour.getEnable()
        Utils.convertAndPush(aggdict, Aggregationrule, dbConn)
    
        aggdict = {}
        aggdict['AGGREGATION'] = busyhour.getBhlevel()+'_MONTHRANKBH_'+busyhour.getBhobject()+"_"+busyhour.getBhtype()
        aggdict['VERSIONID'] = versioning.getVersionid()
        aggdict['AGGREGATIONTYPE'] = 'RANKBH'
        aggdict['AGGREGATIONSCOPE'] = 'MONTH'
        Utils.convertAndPush(aggdict, Aggregation, dbConn)
        
        aggdict = {}
        aggdict['AGGREGATION'] = busyhour.getBhlevel()+'_MONTHRANKBH_'+busyhour.getBhobject()+"_"+busyhour.getBhtype()
        aggdict['VERSIONID'] = versioning.getVersionid()
        aggdict['RULEID'] = 2
        aggdict['RULETYPE'] = 'RANKBHCLASS'
        aggdict['TARGET_TYPE'] = busyhour.getBhlevel()
        aggdict['TARGET_LEVEL'] = 'RANKBH'
        aggdict['TARGET_TABLE'] = busyhour.getBhlevel() +'_RANKBH'
        aggdict['TARGET_MTABLEID'] = versioning.getVersionid()+':'+busyhour.getBhlevel()+':RANKBH'
        aggdict['SOURCE_TYPE'] = busyhour.getBhlevel()
        aggdict['SOURCE_LEVEL'] = 'RANKBH'
        aggdict['SOURCE_MTABLEID']= versioning.getVersionid()+':'+busyhour.getBhlevel()+':RANKBH'
        aggdict['SOURCE_TABLE'] = busyhour.getBhlevel() +'_RANKBH'
        aggdict['AGGREGATIONSCOPE'] = 'MONTH'
        aggdict['BHTYPE'] = busyhour.getBhobject()+"_"+busyhour.getBhtype()
        aggdict['ENABLE'] = busyhour.getEnable()
        Utils.convertAndPush(aggdict, Aggregationrule, dbConn)

def baseExternalStatements(dataStore, dbConn, ExecOrder):
    from com.distocraft.dc5000.repository.dwhrep import Externalstatement
    from com.distocraft.dc5000.repository.dwhrep import ExternalstatementFactory
    
    versioning = dataStore.getDataFromStore('Versioning')
    
    es = Externalstatement(dbConn)
    es.setVersionid(versioning.getBasedefinition())
    esF = ExternalstatementFactory(dbConn, es, 'ORDER BY EXECUTIONORDER')
    for tmpEs in esF.get():
        if tmpEs.getExecutionorder() > 0:
            statementName = tmpEs.getStatementname()
            statement = tmpEs.getStatement()
            ExecOrder = ExecOrder + 1
            
            if tmpEs.getStatementname() == 'create view SELECT_(((TPName)))_AGGLEVEL':
                tpName = versioning.getTechpack_name().replace('DC_', '')
                statementName = statementName.replace('(((TPName)))', tpName);
                statement = statement.replace('(((TPName)))', tpName)
            
            tmpDict = {}
            tmpDict['VERSIONID'] = versioning.getVersionid()
            tmpDict['STATEMENTNAME'] = statementName
            tmpDict['EXECUTIONORDER'] = ExecOrder
            tmpDict['DBCONNECTION'] = tmpEs.getDbconnection()
            tmpDict['STATEMENT'] = statement
            tmpDict['BASEDEF'] = 1
            Utils.convertAndPush(tmpDict, Externalstatement, dbConn)
    
    return ExecOrder

def generateSets(dataStore, dbconn, envPath):
    from com.distocraft.dc5000.repository.dwhrep import Versioning
    from com.distocraft.dc5000.etl.rock import Meta_collection_sets
    from com.distocraft.dc5000.etl.rock import Meta_collection_setsFactory
    from java.util import Properties
    from org.apache.velocity.app import Velocity
    from java.util import Vector
    
    versioning = dataStore.getDataFromStore('Versioning')
    skiplist = Vector() 

    p = Properties();
    p.setProperty("file.resource.loader.path", envPath);
    Velocity.init(p);
    
    versionID = versioning.getVersionid()
    setName = versioning.getTechpack_name()
    setVersion = versionID.split(":")[1]
    
    mwhere = Meta_collection_sets(dbconn)
    mwhere.setCollection_set_name(setName)
    mwhere.setVersion_number(setVersion)
    mcsf = Meta_collection_setsFactory(dbconn,mwhere)
    
    metaCollectionSet = Meta_collection_sets(dbconn)
    metaCollectionSet.setCollection_set_name(setName)
    metaCollectionSet.setVersion_number(setVersion)
    
    tpType = versioning.getTechpack_type().upper()
    if tpType == 'CUSTOM':
        metaCollectionSet.setType('Custompack')
    elif tpType == 'SYSTEM':
        metaCollectionSet.setType('Maintenance')
    else:
        metaCollectionSet.setType('Techpack')
    metaCollectionSet.setDescription("TechPack " + setName + ":" + setVersion + " by " + versioning.getLockedby())
        
    if len(mcsf.get()) <= 0:
        csw = Meta_collection_sets(dbconn);
        csf = Meta_collection_setsFactory(dbconn, csw)
        largest = -1
        for mc in csf.get():
            if largest < mc.getCollection_set_id():
                largest = mc.getCollection_set_id()
        
        metaCollectionSet.setCollection_set_id(long(float(largest+1)))
    else:
        metaCollectionSet = mcsf.get().get(0)
    
    metaCollectionSet.setEnabled_flag("Y")
    metaCollectionSet.insertDB(False, False)
    
    Cs_id = metaCollectionSet.getCollection_set_id()
    Cs_name = metaCollectionSet.getCollection_set_name()
    
    try:
        from com.ericsson.eniq.common.setWizards import CreateDWHMSet
        cls = CreateDWHMSet(setName, setVersion, dbconn, long(float(Cs_id)), Cs_name, True)
        cls.removeSets()
        cls.create(False)
    except:
        pass
    
    cls = None
    try:
        from com.ericsson.eniq.common.setWizards import CreateLoaderSetFactory
        cls = CreateLoaderSetFactory.createLoaderSet("5.2", setName, setVersion, versionID, dbconn, dbconn, int(Cs_id), Cs_name, True)
    except:
        from com.ericsson.eniq.common.setWizards import CreateLoaderSet
        cls = CreateLoaderSet("5.2", setName, setVersion, versionID, dbconn, dbconn, int(Cs_id), Cs_name, True)
    
    cls.removeSets()
    cls.create(False)
    
    
    try:
        from com.ericsson.eniq.common.setWizards import CreateAggregatorSet
        cas = CreateAggregatorSet("5.2",setName, setVersion, versionID, dbconn, dbconn, int(Cs_id), True)
        cas.removeSets()
        cas.create(False)
    except:
        pass
    
    
    cdc = None
    try:
        from com.ericsson.eniq.common.setWizards import CreateTPDirCheckerSetFactory
        cdc = CreateTPDirCheckerSetFactory.createTPDirCheckerSet(setName, setVersion, versionID, "Techpack", dbconn, dbconn, long(float(Cs_id)), Cs_name)
    except:
        from com.ericsson.eniq.common.setWizards import CreateTPDirCheckerSet
        cdc = CreateTPDirCheckerSet(setName, setVersion, versionID, dbconn, dbconn, long(float(Cs_id)), Cs_name)
    
    cdc.removeSets(True)
    cdc.create(True, False)
    
    
    try:
        from com.ericsson.eniq.common.setWizards import CreateTPDiskmanagerSet
        cdm = CreateTPDiskmanagerSet(setName, setVersion, dbconn, long(float(Cs_id)), Cs_name)
        cdm.removeSets()
        cdm.create(False, True)
    except:
        pass
    
    
    tls = None
    try:
        from com.ericsson.eniq.common.setWizards import CreateTopologyLoaderSetFactory
        tls = CreateTopologyLoaderSetFactory.createTopologyLoaderSet("5.2", setName, setVersion, versionID, dbconn, dbconn, int(Cs_id), Cs_name, True)
    except:
        from com.ericsson.eniq.common.setWizards import CreateTopologyLoaderSet
        tls = CreateTopologyLoaderSet("5.2", setName, setVersion, versionID, dbconn, dbconn, int(Cs_id), Cs_name, True)
    
    tls.removeSets(skiplist)
    tls.create(False)


def _countOccuranceInList(objList, refid):
    for obj in objList:
        if refid == obj.getTypeid():
            return True
    return False
    
