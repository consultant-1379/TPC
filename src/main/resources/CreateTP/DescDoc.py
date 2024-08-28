'''
Created on Nov 29, 2016

@author: ebrifol
'''

import Utils
import TPM
import os
from java.text import SimpleDateFormat
from java.util import Date
from java.util import Properties
from java.io import StringWriter

class DescriptionDoc(object):
    
    def __init__(self, dbConn):
        self.dbConn = dbConn
        
    def createTPdoc(self, versionID, envPath, outputpath, tpInterfaceList, params, logger):
        from com.distocraft.dc5000.repository.dwhrep import Versioning
        from com.distocraft.dc5000.repository.dwhrep import Supportedvendorrelease
        from com.distocraft.dc5000.repository.dwhrep import SupportedvendorreleaseFactory
        from com.distocraft.dc5000.repository.dwhrep import Measurementtype
        from com.distocraft.dc5000.repository.dwhrep import MeasurementtypeFactory
        from com.distocraft.dc5000.repository.dwhrep import Measurementobjbhsupport
        from com.distocraft.dc5000.repository.dwhrep import MeasurementobjbhsupportFactory
        from com.distocraft.dc5000.repository.dwhrep import Measurementkey
        from com.distocraft.dc5000.repository.dwhrep import MeasurementkeyFactory
        from com.distocraft.dc5000.repository.dwhrep import Measurementcounter
        from com.distocraft.dc5000.repository.dwhrep import MeasurementcounterFactory
        from com.distocraft.dc5000.repository.dwhrep import Busyhour
        from com.distocraft.dc5000.repository.dwhrep import BusyhourFactory
        from com.distocraft.dc5000.repository.dwhrep import BusyhoursourceFactory
        from com.distocraft.dc5000.repository.dwhrep import Busyhoursource
        from com.distocraft.dc5000.repository.dwhrep import BusyhourrankkeysFactory
        from com.distocraft.dc5000.repository.dwhrep import Busyhourrankkeys
        from com.distocraft.dc5000.repository.dwhrep import BusyhourmappingFactory
        from com.distocraft.dc5000.repository.dwhrep import Busyhourmapping
        from com.distocraft.dc5000.repository.dwhrep import ReferencetableFactory
        from com.distocraft.dc5000.repository.dwhrep import Referencetable
        from com.distocraft.dc5000.repository.dwhrep import MeasurementcolumnFactory
        from com.distocraft.dc5000.repository.dwhrep import Measurementcolumn
        from com.distocraft.dc5000.repository.dwhrep import MeasurementtableFactory
        from com.distocraft.dc5000.repository.dwhrep import Measurementtable
        from com.distocraft.dc5000.repository.dwhrep import DatainterfaceFactory
        from com.distocraft.dc5000.repository.dwhrep import Datainterface
        from com.distocraft.dc5000.repository.dwhrep import InterfacemeasurementFactory
        from com.distocraft.dc5000.repository.dwhrep import Interfacemeasurement
        from com.distocraft.dc5000.repository.dwhrep import DataformatFactory
        from com.distocraft.dc5000.repository.dwhrep import Dataformat
        from com.distocraft.dc5000.repository.dwhrep import ReferencecolumnFactory
        from com.distocraft.dc5000.repository.dwhrep import Referencecolumn
        from com.distocraft.dc5000.repository.dwhrep import Universename
        from com.distocraft.dc5000.repository.dwhrep import UniversenameFactory
        from org.apache.velocity import VelocityContext
        from org.apache.velocity.app import Velocity
        
        addDescriptionFlag = False
        if ('UNIVERSE_DELIVERED' in params):
            addDescriptionFlag = True if params['UNIVERSE_DELIVERED'] == 'NO' else False
        
        if not os.path.exists(outputpath):
            os.makedirs(outputpath)
        
        p = Properties();
        p.setProperty("file.resource.loader.path", envPath);
        Velocity.init(p);
        
        context = VelocityContext()
        
        self.Versioning = Versioning(self.dbConn, versionID)
        
        versID = self.Versioning.getVersionid()
        version = versID.split(':')[1]
        version = version.replace('((', '')
        version = version.replace('))', '')
        tpName = versID.split(':')[0]
        dte = Date()
        dateFormats = {'year': 'yyyy', 'day': 'dd', 'month': 'MM'}
        for key, formattype in dateFormats.iteritems():
            formatter = SimpleDateFormat(formattype)
            context.put(key, formatter.format(dte))
        
        description = self.Versioning.getDescription().strip()
        if description.endswith(version):
            description = description.rsplit(version, 1)[0]
        
        sdifFile = open(outputpath+'\\TP Description ' + description + '.sdif','w') 
        
        if ('SUPPORTED_NODE_TYPES' in params):
            supportedNodeTypes = params['SUPPORTED_NODE_TYPES']
            description = supportedNodeTypes
        
        tpVers = self.Versioning.getTechpack_version()
        if tpVers.endswith(version):
            tpVers = tpVers.replace('_'+version, 1)

        context.put("revision", Utils.escape(tpVers))
        context.put("productNumber", Utils.escape(self.Versioning.getProduct_number()))
        context.put("versioning", Utils.escape(self.Versioning))
        context.put("version", Utils.escape(tpName))
        context.put("description", Utils.escape(description.strip()))
        context.put("Interfaces", Utils.escape(tpInterfaceList))
        context.put("productNumberAndRelease", Utils.escape(self.Versioning.getProduct_number() 
                                                            + ' ' + tpVers))
        
        releases = ''
        where = Supportedvendorrelease(self.dbConn)
        where.setVersionid(versID)
        svrF = SupportedvendorreleaseFactory(self.dbConn, where)
        for svr in svrF.get():
            releases = releases + svr.getVendorrelease()+','
            
        releases = releases.rsplit(',', 1)[0]
        context.put("releases", Utils.escape(releases))
        
        f=open('TagId.txt','r')
        lines=f.readlines()
        tag={}
        k=[]
        s=''
        for line in lines:
        	l=line.strip().split(":")
        	if l[0]=="Fact Table":
        		tag[s]=k
        		if l[1] not in tag:
        			tag[l[1]]=''
        			k=[]
        			s=l[1]
        	else:
        		if l[1]!='':
        			k.append(l[1])
        f.close()
        tag.pop('',None)
        os.remove('TagId.txt')
        factTableList = {}
        where = Measurementtype(self.dbConn)
        where.setVersionid(versID)
        mtf = MeasurementtypeFactory(self.dbConn, where)
        for mt in mtf.get():
            mtCalls = {'OneMinuteAggregation' : 'getOneminagg',
                    'FifteenMinuteAggregation' : 'getFifteenminagg',
                    'totalAggregation' : 'getTotalagg',
                    'SonAggregation' : 'getSonagg',
                    'elementBusyHourSupport' : 'getElementbhsupport',
                    'deltaCalculation' : 'getDeltacalcsupport',
                    'Load File Duplicate Check' : 'getLoadfile_dup_check',
                    }
            flag=1
            if mt.getFollowjohn()!=1 and len(tag[mt.getTypename()])==0:
            	flag=0
            if mt.getRankingtable() == 0 and flag==1:
                factTableData = {}
                factTableData["factTable"] = Utils.escape(mt.getTypename())
                factTableData["typeID"] = Utils.escape(mt.getTypeid())
                factTableData["size"] = Utils.escape(mt.getSizing())
                
                #EQEV-45021 - update with fact table description and universe extension 
                if(mt.getDescription() != None and mt.getDescription() != ""):
                    factTableData["factDesc"] = Utils.escape(mt.getDescription())
                else:
                    factTableData["factDesc"] = 'No Description present'
                
                unvExt = mt.getUniverseextension()
                #print(factTableData["factTable"])
                unvExtName = 'No Universe present'
                if (unvExt != None and unvExt != ""):
                    if(unvExt == 'ALL'):
                        unvExtName = unvExt
                    else:
                        #EQEV-108746 (Bug TR): 
                        #Universe Name is not present in BULK_CM Technology Package Description Document for Few Tables.
                        l=unvExt.split(",")
                        Extname=""
                        for i in range(len(l)):
                            unvwhere = Universename(self.dbConn)
                            unvwhere.setVersionid(versID)
                            unvwhere.setUniverseextension(l[i])
                            unvf = UniversenameFactory(self.dbConn, unvwhere)
                            if(unvf.getElementAt(0) != None):
                                unv = unvf.getElementAt(0)
                                if(unv.getUniverseextensionname() != None and unv.getUniverseextensionname() != ""):
                                    unvExtName = unv.getUniverseextensionname()
                                    if i>0:
                                        Extname+=",  "
                                    Extname+=unvExtName
                                else:
                                    unvExtName = unvExt
                
                        unvExtName=Extname              
                
                factTableData["universeName"] = Utils.escape(unvExtName)
                
                methods = dir(mt)
                for key, call in mtCalls.iteritems():
                    if call in methods:
                        value = getattr(mt,call)()
                        if value == 1:
                            factTableData[key] ='Yes'
                        else:
                            factTableData[key] ='No'
                        
                factTableList[mt.getTypename()] = factTableData

                
        for table, data in factTableList.iteritems():
            where = Measurementobjbhsupport(self.dbConn)
            where.setTypeid(data['typeID'])
            mobhsF = MeasurementobjbhsupportFactory(self.dbConn, where)
            mobhs = ''
            for mbhs in mobhsF.get():
                mobhs = mobhs + mbhs.getObjbhsupport()+','
            mobhs = mobhs.rsplit(',', 1)[0]
            if len(mobhs) > 0:
                data['objectBusyHourSupport'] = mobhs
            else:
                data['objectBusyHourSupport'] = 'None'
        
            where = Measurementkey(self.dbConn)
            where.setTypeid(data['typeID'])
            mkF = MeasurementkeyFactory(self.dbConn, where)
            rows = []
            for mk in mkF.get():
                row = {}
                row['name'] = mk.getDataname()
                if addDescriptionFlag:
                    row['description'] =  mk.getDescription()
                row['dataType'] = str(mk.getDatatype()) + '(' + str(mk.getDatasize()) + ')'
                if mk.getUniquekey() == 1:
                    row['duplicateConstraint'] = 'Yes'
                else:
                    row['duplicateConstraint'] = 'No'
                if mk.getIselement() == 1:
                    row['isElement'] = 'Yes'
                else:
                    row['isElement'] = 'No'
                rows.append(row)
            data[data['factTable']+'_keys'] = rows
        
        
            where = Measurementcounter(self.dbConn)
            where.setTypeid(data['typeID'])
            mcF = MeasurementcounterFactory(self.dbConn, where)
            rows = []
            for mc in mcF.get():
                row = {}
                row['name'] = mc.getDataname()
                if addDescriptionFlag:
                    row['description'] = mc.getDescription()
                row['Aggregation'] = mc.getTimeaggregation() + '/ ' + mc.getGroupaggregation()
                row['type'] = mc.getCountertype()
                if mc.getDatascale() != None:
                    if int(mc.getDatascale()) >= 0:
                        row['dataType'] = str(mc.getDatatype()) + '(' + str(mc.getDatasize()) + ',' + str(mc.getDatascale())+ ')'
                    else:
                        row['dataType'] = str(mc.getDatatype()) + '(' + str(mc.getDatasize()) + ')'
                rows.append(row)
            data[data['factTable']+'_counters'] = rows
        context.put("factTableData", factTableList)
        
        bhWhere = Busyhour(self.dbConn)
        bhWhere.setVersionid(versID)
        bhf = BusyhourFactory(self.dbConn, bhWhere, 'ORDER BY BHLEVEL, BHTYPE')
        phTypes = ['PP', 'CP']
        bhTypeToString = {'RANKBH_TIMELIMITED' : 'Timelimited',
                    'RANKBH_SLIDINGWINDOW' : 'Slidingwindow',
                    'RANKBH_TIMECONSISTENT' : 'Timelimited + Timeconsistent',
                    'RANKBH_TIMECONSISTENT_SLIDINGWINDOW' : 'Slidingwindow + Timeconsistent',
                    'RANKBH_PEAKROP' : 'Peakrop',
                    }
        if bhf.getElementAt(0) != None:
            if bhf.getElementAt(0).getPlaceholdertype() in phTypes:
                bhLevelList = {}
                bhActive = {}
                bhInactive = {}
                bhRankTables = {}
                bhDescription = {}
                bhList = {}
                bhObject=[]
                for bh in bhf.get():
                	bhObject.append(bh.getBhobject())
                bhObjectset=set(bhObject)
                for Object in bhObjectset:
                	bhActive[Object]=''
                	bhInactive[Object]=''
                for bh in bhf.get():
                    if bh.getBhobject() not in bhRankTables.keys():
                        bhRankTables[bh.getBhobject()] = Utils.escape(bh.getBhlevel())
                        
                        ameastype = Measurementtype(self.dbConn)
                        ameastype.setVersionid(bh.getVersionid())
                        ameastype.setTypename(bh.getBhlevel())
                        mtf = MeasurementtypeFactory(self.dbConn, ameastype)
                        if mtf.getElementAt(0) != None:
                            bhDescription[bh.getBhobject()] = Utils.escape(mtf.getElementAt(0).getDescription())
                    if bh.getEnable() == 0:
                        inactiveList = ''
                        if bh.getBhobject() in bhInactive.keys():
                            inactiveList = bhInactive[bh.getBhobject()]
                        inactiveList = inactiveList +',' + str(bh.getBhtype())
                        if inactiveList.startswith(','):
                            inactiveList = inactiveList[1:]
                        bhInactive[bh.getBhobject()] = Utils.escape(inactiveList)
                    else:
                        
                        activeList = ''
                        if bh.getBhobject() in bhActive.keys():
                            activeList = bhActive[bh.getBhobject()]
                        activeList = activeList +',' + str(bh.getBhtype())
                        if activeList.startswith(','):
                            activeList = activeList[1:]
                        bhActive[bh.getBhobject()] = Utils.escape(activeList)
                        
                    splitList = {}
                    orderPlaceholderList = []
                    if bh.getBhobject() in bhLevelList.keys():
                        splitList = bhLevelList[bh.getBhobject()]
                    if bh.getPlaceholdertype() in splitList.keys():
                        orderPlaceholderList = splitList[bh.getPlaceholdertype()]
                    datamap = {}
                    datamap["description"] = bh.getDescription()
                    datamap["criteria"] = bh.getBhcriteria()
                    datamap["whereCondition"] = bh.getWhereclause()
                    datamap["targetVersionId"] = bh.getTargetversionid()
                    datamap["versionId"] = bh.getVersionid()
                    datamap["bhType"] = bh.getBhtype()
                    datamap["bhLevel"] = bh.getBhlevel()
                    datamap["aggregationType"] = bhTypeToString[bh.getAggregationtype()]
                    datamap["bhVersion"] = "1"
                    datamap["grouping"] = '' #Left empty because CR in IDE code. Added to tidy up output Doc.
                        
                    sWhere = Busyhoursource(self.dbConn)
                    sWhere.setVersionid(bh.getVersionid())
                    sWhere.setTargetversionid(bh.getTargetversionid())
                    sWhere.setBhtype(bh.getBhtype())
                    sWhere.setBhlevel(bh.getBhlevel())
                    bhsF = BusyhoursourceFactory(self.dbConn, sWhere)
                    source = ''
                    for bhs in bhsF.get():
                        source = source + bhs.getTypename() + ','
                    source = source.rsplit(',', 1)[0]
                    datamap["source"] = source
                        
                    kWhere = Busyhourrankkeys(self.dbConn)
                    kWhere.setBhtype(bh.getBhtype())
                    kWhere.setBhlevel(bh.getBhlevel())
                    kWhere.setVersionid(bh.getVersionid())
                    kFac = BusyhourrankkeysFactory(self.dbConn, kWhere)
                    sb = ''
                    for rkey in kFac.get():
                        if sb == '':
                            sb = sb + rkey.getKeyname()
                        else:
                            sb = sb + ',' + rkey.getKeyname()
                    datamap["rankKeys"] = sb
                        
                    mWhere = Busyhourmapping(self.dbConn)
                    mWhere.setBhtype(bh.getBhtype())
                    mWhere.setBhlevel(bh.getBhlevel())
                    mWhere.setVersionid(bh.getVersionid())
                    mFac = BusyhourmappingFactory(self.dbConn, mWhere)
                    msb = ''
                    for mapping in mFac.get():
                        msb = msb + mapping.getBhtargettype()+','
                    msb = msb.rsplit(',', 1)[0]
                    datamap["bhMappings"] = msb
                    datamap["bhType"] = bh.getBhtype()
                    if bh.getBhcriteria() == None or len(bh.getBhcriteria()) == 0:
                        datamap["defined"] = False
                    else:
                        datamap["defined"] = True
                    orderPlaceholderList.append(datamap)
                    splitList[bh.getPlaceholdertype()] = orderPlaceholderList
                    bhLevelList[bh.getBhobject()] = splitList
                
                    bhList = {}
                    for bhLevel in sorted(bhLevelList):
                        lList = []
                        if bhLevel in bhList.keys():
                            lList = bhList[bhLevel]
                        for pType in phTypes:
                            if pType in bhLevelList[bhLevel]:
                                lList = lList + bhLevelList[bhLevel][pType]
                        bhList[bhLevel] = Utils.escape(lList)                
                
                context.put("RankTables", bhRankTables)
                context.put("busyHourDescription", bhDescription)
                context.put("EnabledBusyHour", bhActive)
                context.put("DisabledBusyHour", bhInactive)
                context.put("busyHourData", bhList)
        
        dimensionTableList = {}
        dataTypes = ['tinyint','smallint','int','integer','date','datetime','insigned int']
        UPDATE_METHODS_TEXT = [ "Static", "Predefined", "Dynamic", "Timed Dynamic", "History Dynamic" ]
        where = Referencetable(self.dbConn)
        where.setVersionid(versID)
        rtF = ReferencetableFactory(self.dbConn, where)
        for rt in rtF.get():
#             if not rt.getTypename().endswith('_BHTYPE') and not rt.getTypename().endswith('_AGGLEVEL'):
            dimensionTableData = {}
            dimensionTableData['dimensionTable'] = Utils.escape(rt.getTypename())
            dimensionTableData['typeID'] = Utils.escape(rt.getTypeid())
            dimensionTableData['description'] = Utils.escape(rt.getDescription())
            #print(rt.getDescription())
            dimensionTableData['updateMethod'] = UPDATE_METHODS_TEXT[int(rt.getUpdate_policy())]
            if 'SELECT_' in rt.getTypename() and '_AGGLEVEL' in rt.getTypename():
                dimensionTableData['type'] = 'View'
            else:
                dimensionTableData['type'] = 'Table'
                
            rows = []
            where = Referencecolumn(self.dbConn)
            where.setTypeid(rt.getTypeid())
            rcF = ReferencecolumnFactory(self.dbConn, where)
            for rc in rcF.get():
                row = {}
                row["name"] = Utils.escape(rc.getDataname())
                sb = rc.getDatatype()
                if rc.getDatatype() not in dataTypes and rc.getDatatype() == 'numeric':
                    sb = sb + '('+ str(rc.getDatasize()) +','+ str(rc.getDatascale()) +')'
                elif rc.getDatatype() not in dataTypes:
                    sb = sb + '(' + str(rc.getDatasize()) + ')'
                row["dataType"] = Utils.escape(sb)
                if rc.getUniquekey() == 1:
                    row["UniqueKey"] = 'Yes'
                else:
                    row["UniqueKey"] = 'No' 
                if rc.getIncludeupd() == 1:
                    row["includedInUpdates"] = 'Yes'
                else:
                    row["includedInUpdates"] = 'No'
                rows.append(row)
                dimensionTableData[rt.getTypename()+'_columns'] = rows

                dimensionTableList[rt.getTypename()] = dimensionTableData
                context.put("dimensionTableData", dimensionTableList)
        
        interfaceList = {}
        where = Dataformat(self.dbConn)
        where.setVersionid(versID)
        dfF = DataformatFactory(self.dbConn, where)
        for df in dfF.get():
            where = Interfacemeasurement(self.dbConn)
            where.setDataformatid(df.getDataformatid())
            ifmF = InterfacemeasurementFactory(self.dbConn, where)
            for ifm in ifmF.get():
                where = Datainterface(self.dbConn)
                where.setInterfacename(ifm.getInterfacename())
                diF = DatainterfaceFactory(self.dbConn, where)
                di = diF.getElementAt(0)
                interfaceData = {}
                interfaceData["name"] = Utils.escape(di.getInterfacename() + "_" + di.getInterfacetype())
                interfaceData["type"] = Utils.escape(di.getInterfacetype())
                interfaceList[ifm.getInterfacename()] = interfaceData
        context.put("interfaceData", interfaceList)
        
        sqlInterfaceList = {}
        where = Measurementtype(self.dbConn)
        where.setVersionid(versID)
        mtf = MeasurementtypeFactory(self.dbConn, where)
        for mt in mtf.get():
            where = Measurementtable(self.dbConn)
            where.setTypeid(mt.getTypeid())
            mtbf = MeasurementtableFactory(self.dbConn, where)
            for mtb in mtbf.get():
                where = Measurementcolumn(self.dbConn)
                where.setMtableid(mtb.getMtableid())
                where.setIncludesql(1)
                mcF = MeasurementcolumnFactory(self.dbConn, where)
                columns = []
                for mc in mcF.get():
                    if mc.getColtype().upper() == 'PUBLICKEY':
                        row = {}
                        row['name'] = Utils.escape(mc.getDataname())
                        sb = mc.getDatatype()
                        if mc.getDatatype() not in dataTypes and mc.getDatatype() == 'numeric':
                            sb = sb + '('+ str(mc.getDatasize()) +','+ str(mc.getDatascale()) +')'
                        elif mc.getDatatype() not in dataTypes:
                            sb = sb + '('+ str(mc.getDatasize()) +')'
                        row['type'] = Utils.escape(sb)
                        columns.append(row)
                tablename = mtb.getTypeid()
                tablename = tablename.replace(versID+':' , '')
                tempDict = {}
                if tablename in sqlInterfaceList.keys():
                    tempDict = sqlInterfaceList[tablename]
                
                tempDict[mtb.getBasetablename()] = columns
                sqlInterfaceList[tablename] = tempDict
                
        where = Referencetable(self.dbConn)
        where.setVersionid(versID)
        rtF = ReferencetableFactory(self.dbConn, where)
        for rt in rtF.get():
            columns = []
            where = Referencecolumn(self.dbConn)
            where.setTypeid(rt.getTypeid())
            where.setIncludesql(1)
            rcF = ReferencecolumnFactory(self.dbConn, where)
            for rc in rcF.get():
#                 if rc.getColtype().upper() == 'PUBLICCOL':
                row = {}
                row['name'] = rc.getDataname()
                sb = rc.getDatatype()
                if rc.getDatatype() not in dataTypes and rc.getDatatype() == 'numeric':
                    sb = sb + '('+ str(rc.getDatasize()) +','+ str(rc.getDatascale()) +')'
                elif rc.getDatatype() not in dataTypes:
                    sb = sb + '('+ str(rc.getDatasize() )+')'
                row['type'] = sb
                columns.append(row)
            tempDict = {}
            tempDict[rt.getTableName()] = columns
            sqlInterfaceList[rt.getTableName()] = columns
        context.put("sqlInterfaceData", sqlInterfaceList)
        
        try:
            from com.distocraft.dc5000.repository.dwhrep import Grouptypes
            from com.distocraft.dc5000.repository.dwhrep import GrouptypesFactory
            data = {}
            where = Grouptypes(self.dbConn)
            where.setVersionid(versID)
            fac = GrouptypesFactory(self.dbConn, where)
            for group in fac.get():
                gdata = []
                if group.getGrouptype() in data.keys():
                    gdata = data[group.getGrouptype()]
                gdata.append(group)
                data[group.getGrouptype()] = gdata
            context.put("groupDefData", data)
        except:
            pass
        
        strw = StringWriter()
        if addDescriptionFlag:
            logger.info('** Adding counter and key Description in Techpack Document **')
            isMergeOk = Velocity.mergeTemplate('/SDIFDescTemplate_CounterDescription.vm', Velocity.ENCODING_DEFAULT, context, strw)
        else:
            logger.info('** Proceeding without adding counter and key Description in Techpack Document **')
            isMergeOk = Velocity.mergeTemplate('/SDIFDescTemplate.vm', Velocity.ENCODING_DEFAULT, context, strw)

        if isMergeOk:
            sdifFile.write(strw.toString())
        sdifFile.close()
   
