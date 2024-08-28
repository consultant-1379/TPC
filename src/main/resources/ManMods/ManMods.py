'''
Created on 30 Nov 2016

@author: ebrifol
'''

import Modification
import Utils
import xml.etree.ElementTree as ET
import exceptions

class ManualMods(object):
    
    def __init__(self, dbConn, tp,logger):
        self.dbConn = dbConn
        self.tp = tp
        self.log = logger
        
    def applyModifications(self, inputFile):
        
        root = ET.parse(inputFile).getroot()
        tpName = self.tp.versionID
        # Initializing blank dictionary'
        modsDict = Utils.odict()
  
        self.coll_set_name = tpName.split(':')[0]
        self.buildNo = tpName.split(':')[1]
            
        for child in root:
            # To check for all attributes
            try:
                # load in order numbers as a string from the XML and convert them to an integer
                orderNoStr = child.attrib['OrderNo']
                orderNo = int (orderNoStr)
                table = child.attrib['Table']
                modtype = child.attrib['Type']
                if len(child.attrib) == 4:
                    self.parent = child.attrib['ParentName']
                elif len(child.attrib) == 3:
                    self.parent = None
                else:
                    self.log.error("Incorrect number of root properties in Modification " + orderNoStr)
                    raise
            
                # Calls Modification() class from Modification script
                # & sets table and type values
                datastorage = Modification.Modification()
                datastorage.settable(table)
                datastorage.settype(modtype)
                datastorage.setparentname(self.parent)
                datastorage.addDataToStore('VERSION_NUMBER', self.buildNo)
                self.coll_set_id = self._getCollectionSetId()   
                if self.coll_set_id != None: 
                    datastorage.addDataToStore('COLLECTION_SET_ID', str(self.coll_set_id))
            
                #collection_id = self._getCollectionId()
                #if collection_id != None:
                    #datastorage.addDataToStore('COLLECTION_ID', str(collection_id))

                # Adds data from the Xml file to the dataStorage
                self.searchTags = ['Identity', 'Modify']
                for data in child:
                    if data.tag in self.searchTags:
                        for column in data: 
                            column.text = column.text.replace("'", '"')
                            if data.tag == 'Identity':
                                datastorage.addIdentityTagToStore(column.tag, column.text)
                            elif data.tag == 'Modify':
                                datastorage.addModifyTagToStore(column.tag, column.text)
    
                # Fills modsDict dictionary with key of orderNo and value dataStorage
                modsDict[orderNo] = datastorage
            except Exception as e:
                self.log.error("Incorrect root property assigned to Modification " + str(e))
                raise
        
        # dictionary to show table names in order. To be deleted
        for key in sorted(modsDict.keys()):
            self.pushToDB(modsDict[key],key)


    def pushToDB(self, modobj,slno):
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
        from com.distocraft.dc5000.etl.rock import Meta_collection_sets
        from com.distocraft.dc5000.etl.rock import Meta_collections
        from com.distocraft.dc5000.etl.rock import Meta_transfer_actions
        from com.distocraft.dc5000.etl.rock import Meta_schedulings
        from com.distocraft.dc5000.repository.dwhrep import Datainterface
        from com.distocraft.dc5000.repository.dwhrep import Interfacetechpacks
        from com.distocraft.dc5000.repository.dwhrep import Interfacedependency
        from com.distocraft.dc5000.repository.dwhrep import InterfacedependencyFactory
        
        mappingDict = {'versioning': Versioning,            'techpackdependency': Techpackdependency ,  'supportedvendorrelease': Supportedvendorrelease,
        'referencetable' : Referencetable ,                 'measurementtype' : Measurementtype,        'measurementtypeclass' : Measurementtypeclass,
        'measurementcounter' : Measurementcounter ,         'measurementkey' : Measurementkey,          'measurementdeltacalcsupport' : Measurementdeltacalcsupport,
        'referencecolumn' : Referencecolumn,                'measurementvector' : Measurementvector,    'measurementobjbhsupport' : Measurementobjbhsupport,
        'busyhour' : Busyhour,                              'busyhourmapping' : Busyhourmapping,        'busyhourplaceholders' : Busyhourplaceholders,
        'busyhourrankkeys' : Busyhourrankkeys,              'busyhoursource' : Busyhoursource,          'transformer' : Transformer,
        'transformation' : Transformation,                  'defaulttags' : Defaulttags,                'universeobject' : Universeobject,
        'universename' : Universename,                      'universetable' : Universetable,            'universeclass' : Universeclass,
        'universecondition' : Universecondition,            'universejoin' : Universejoin,              'universecomputedobject' : Universecomputedobject,
        'universeformulas' : Universeformulas,              'universeparameters' : Universeparameters,  'externalstatement' : Externalstatement,
        'measurementtable' : Measurementtable,              'measurementcolumn' : Measurementcolumn,    'aggregation' : Aggregation,
        'aggregationrule' : Aggregationrule,                'dataformat' : Dataformat,                  'dataitem' : Dataitem,
        'meta_collection_sets' : Meta_collection_sets,      'meta_collections' : Meta_collections,      'meta_schedulings' : Meta_schedulings,
        'meta_transfer_actions' : Meta_transfer_actions,    'datainterface' : Datainterface,            'interfacetechpacks' : Interfacetechpacks,
        'interfacedependency' : Interfacedependency }
        
        #matches table from xml doc to database table name
        tablename = modobj.gettable().lower()
        modtype = modobj.gettype()
        collection_id = self._getCollectionId(modobj.getparentname())
        if collection_id != None:
            modobj.addDataToStore('COLLECTION_ID', str(collection_id))
        dataList = modobj.getDataStore()

        if tablename == "meta_transfer_actions":
            populatedObj = self._createTransferAction(dataList,modtype)
        elif tablename == "meta_schedulings":
            populatedObj = self._createScheduling(dataList,modtype)
        elif tablename == "meta_collections":
            populatedObj = self._createCollection(dataList,modtype)
        else:
            populatedObj = Utils.populateObjectFromDict(mappingDict[tablename], dataList, self.dbConn)
                           
        # either insert's, update or deletes sets from database depending on type from xml doc        
        self.log.info('Applying Modification ' + str(slno) + ' of type ' + modtype + ' to ' + tablename)    
        if 'New' in modtype:
            populatedObj.insertDB()
        elif 'Update' in modtype:
            populatedObj.updateDB()     
        elif 'Delete' in modtype:
            if modobj.gettable().upper() == "META_COLLECTIONS":
                self.deleteSets(modobj.getparentname())
            populatedObj.deleteDB()
        
        sql = 'SELECT COUNT(*) AS numberofrows FROM ' + tablename + ' WHERE '
        for key, value in dataList.iteritems():
            if key in self.searchTags:
                for key_dict, value_dict in value.iteritems():
                    try:
                        intvalue = int(value_dict)
                        sql = sql + key_dict + '=' + intvalue + ' and '
                    except:
                        stringvalue = str(value_dict)
                        sql = sql + key_dict + '=\'' + stringvalue.strip() + '\' and '
            else:
                try:
                    intvalue = int(value)
                    sql = sql + key + '=' + intvalue + ' and '
                except:
                    stringvalue = str(value)
                    sql = sql + key + '=\'' + stringvalue.strip() + '\' and '
            
        sql = sql[:-4]
        self.log.debug('sql statement: ' + sql)
        #'bool' object has no attribute 'next' line 139
        result = self.dbConn.getConnection().createStatement().executeQuery(sql)
        result.next()
        numberofrows = int(result.getInt('numberofrows'))
        
        if 'New' in modtype or 'Update' in modtype:
            if numberofrows == 1:
                self.log.info('Modification was made to the database')
            elif numberofrows == 0:
                self.log.warn('Modification was not made to the database')
            elif numberofrows > 1:
                self.log.warn('Duplicate set in the database after modification')     
        elif 'Delete' in modtype:
            if numberofrows == 1:
                self.log.warn('Modification was not made to the database')
            elif numberofrows == 0:
                self.log.info('Modification was made to the database')
            elif numberofrows > 1:
                self.log.warn('Duplicate set in the database after modification')
    
    def deleteSets(self, collectionName):
        from com.distocraft.dc5000.etl.rock import Meta_collections
        from com.distocraft.dc5000.etl.rock import Meta_collectionsFactory
        from com.distocraft.dc5000.etl.rock import Meta_schedulings
        from com.distocraft.dc5000.etl.rock import Meta_schedulingsFactory
        from com.distocraft.dc5000.etl.rock import Meta_transfer_actions
        from com.distocraft.dc5000.etl.rock import Meta_transfer_actionsFactory
        
        rmc = Meta_collections(self.dbConn);
        rmc.setCollection_set_id(self.coll_set_id)
        rmc.setCollection_name(collectionName)
        rmc.setVersion_number(self.buildNo)
        rmcF = Meta_collectionsFactory(self.dbConn, rmc)
        for m in rmcF.get():
            mta = Meta_transfer_actions(self.dbConn)
            mta.setCollection_id(m.getCollection_id())
            mta.setCollection_set_id(self.coll_set_id)
            mtaF = Meta_transfer_actionsFactory(self.dbConn, mta)
            for a in mtaF.get():
                a.deleteDB()
            
            ms = Meta_schedulings(self.dbConn)
            ms.setCollection_id(m.getCollection_id())
            ms.setCollection_set_id(self.coll_set_id)
            msF = Meta_schedulingsFactory(self.dbConn, ms)
            for s in msF.get():
                s.deleteDB()
            m.deleteDB() 
    
    def getHighestID(self, db, statement):
        id = 0
        try:
            r = db.getConnection().createStatement().executeQuery(statement)
            r.next()
            id = int(r.getLong("maxval"))
        except:
            id = 0
        finally:
            r.close()
            
        return id + 1

    def _createTransferAction(self, properties,modType):
        from com.distocraft.dc5000.etl.rock import Meta_transfer_actions
        from com.distocraft.dc5000.etl.rock import Meta_transfer_actionsFactory
        
        setMethodMap = {'VERSION_NUMBER': [str,'setVersion_number'],            'TRANSFER_ACTION_ID': [long,'setTransfer_action_id'] ,  'COLLECTION_ID': [long,'setCollection_id'],
        'COLLECTION_SET_ID' : [long,'setCollection_set_id'] ,                 'ACTION_TYPE' : [str,'setAction_type'],        'TRANSFER_ACTION_NAME' : [str,'setTransfer_action_name'],
        'ORDER_BY_NO' : [long,'setOrder_by_no'] ,         'DESCRIPTION' : [str,'setDescription'],          'WHERE_CLAUSE_01' : [str,'setWhere_clause_01'],
        'ACTION_CONTENTS_01' : [str,'setAction_contents_01'],                'ENABLED_FLAG' : [str,'setEnabled_flag'],    'CONNECTION_ID' : [long,'setConnection_id'],
        'WHERE_CLAUSE_02' : [str,'setWhere_clause_02'],                              'WHERE_CLAUSE_03' : [str,'setWhere_clause_03'],        'ACTION_CONTENTS_02' : [str,'setAction_contents_02'],
        'ACTION_CONTENTS_03' : [str,'setAction_contents_03'] }
        
        props = {}
        mta = Meta_transfer_actions(self.dbConn)
        mta.setVersion_number(self.buildNo)
        mta.setCollection_set_id(self.coll_set_id)
        if 'COLLECTION_ID' in properties:
            mta.setCollection_id(long(properties['COLLECTION_ID']))
            props['COLLECTION_ID'] = properties['COLLECTION_ID']
            
        if modType == 'Update' or modType == 'Delete':
            identDict = properties['Identity']
            for key, value in identDict.iteritems():
                value = setMethodMap[key][0](value)
                getattr(mta, setMethodMap[key][1])(value)
                
            msf = Meta_transfer_actionsFactory(self.dbConn,mta)
            if len(msf.get()) == 0:
                self.log.error("No existing row can be found with given Identity tags")
                raise
            elif len(msf.get()) > 1:
                self.log.error("Multiple rows found with given Identity tags. Please provide more information with Identity tags to narrow selection to 1")
                raise
            elif len(msf.get()) == 1:
                mta = msf.getElementAt(0)
                self.log.debug("Identifies a unique row")
                
        if modType == 'New':
            props = self._nullColumnCheck(props,properties['Modify'])
            props['TRANSFER_ACTION_ID'] = self.getHighestID(self.dbConn, "select max(TRANSFER_ACTION_ID) maxval from META_TRANSFER_ACTIONS")
            props['ORDER_BY_NO'] = self.getHighestID(self.dbConn, "select max(ORDER_BY_NO) maxval from META_TRANSFER_ACTIONS where collection_id = " + 
                                                          str(properties['COLLECTION_ID']))
            props['ENABLED_FLAG'] = 'Y'
        
        if modType == 'Update' or modType == 'New': 
            props.update(properties['Modify'])
        
        return Utils.populateObjectFromDict(Meta_transfer_actions, props, self.dbConn, mta)
    
    def _createScheduling(self, properties,modType):
        from com.distocraft.dc5000.etl.rock import Meta_schedulings
        from com.distocraft.dc5000.etl.rock import Meta_schedulingsFactory
        
        setMethodMap = {'VERSION_NUMBER': [str,'setVersion_number'], 'ID': [long,'setId'], 'EXECUTION_TYPE': [str,'setExecution_type'], 'OS_COMMAND' : [str,'setOs_command'],
        'SCHEDULING_MONTH' : [long,'setScheduling_month'], 'SCHEDULING_DAY' : [long,'setScheduling_day'],  'SCHEDULING_HOUR' : [long,'setScheduling_hour'], 'SCHEDULING_MIN' : [long,'setScheduling_min'],
        'COLLECTION_SET_ID' : [long,'setCollection_set_id'], 'COLLECTION_ID' : [long,'setCollection_id'], 'MON_FLAG' : [str,'setMon_flag'], 'TUE_FLAG' : [str,'setTue_flag'],
        'WED_FLAG' : [str,'setWed_flag'], 'THU_FLAG' : [str,'setThu_flag'], 'FRI_FLAG' : [str,'setFri_flag'], 'SAT_FLAG' : [str,'setSat_flag'], 'SUN_FLAG' : [str,'setSun_flag'], 
        'STATUS' : [str,'setStatus'] , 'LAST_EXECUTION_TIME' : [str,'setLast_execution_time'],'INTERVAL_HOUR' : [long,'setInterval_hour'], 'INTERVAL_MIN' : [long,'setInterval_min'],
        'NAME' : [str,'setName'],'HOLD_FLAG' : [str,'setHold_flag'], 'PRIORITY' : [long,'setPriority'],    'SCHEDULING_YEAR' : [long,'setScheduling_year'],
        'TRIGGER_COMMAND' : [str,'setTrigger_command'], 'LAST_EXEC_TIME_MS' : [long,'setLast_exec_time_ms'] }
        
        props = {}
        ms = Meta_schedulings(self.dbConn)
        ms.setVersion_number(self.buildNo)
        ms.setCollection_set_id(self.coll_set_id)
        if 'COLLECTION_ID' in properties:
            ms.setCollection_id(long(properties['COLLECTION_ID']))
            props['COLLECTION_ID'] = properties['COLLECTION_ID']
            
        if modType == 'Update' or modType == 'Delete':
            identDict = properties['Identity']
            for key, value in identDict.iteritems():
                value = setMethodMap[key][0](value)
                getattr(ms, setMethodMap[key][1])(value)
                
            msf = Meta_schedulingsFactory(self.dbConn,ms)
            if len(msf.get()) == 0:
                self.log.error("No existing row can be found with given Identity tags")
                raise
            elif len(msf.get()) > 1:
                self.log.error("Multiple rows found with given Identity tags. Please provide more information with Identity tags to narrow selection to 1")
                raise
            elif len(msf.get()) == 1:
                ms = msf.getElementAt(0)
                self.log.debug("Identifies a unique row")
                
        if modType == 'New':
            props = self._nullColumnCheck(props,properties['Modify'])
            props['ID'] = self.getHighestID(self.dbConn, "select max(ID) maxval from META_SCHEDULINGS")
            props['HOLD_FLAG'] = 'N'
        
        if modType == 'Update' or modType == 'New': 
            props.update(properties['Modify'])
        
        return Utils.populateObjectFromDict(Meta_schedulings, props, self.dbConn, ms)
    
    def _createCollection(self, properties, modType):
        from com.distocraft.dc5000.etl.rock import Meta_collections
        from com.distocraft.dc5000.etl.rock import Meta_collectionsFactory
        
        setMethodMap = {'VERSION_NUMBER': [str,'setVersion_number'], 'COLLECTION_ID': [long,'setCollection_id'], 'COLLECTION_NAME': [str,'setCollection_name'], 
        'COLLECTION' : [str,'setCollection'], 'MAIL_ERROR_ADDR' : [str,'setMail_error_addr'],'MAIL_FAIL_ADDR' : [str,'setMail_fail_addr'], 'MAIL_BUG_ADDR' : [str,'setMail_bug_addr'],  
        'MAX_ERRORS' : [long,'setMax_errors'], 'MAX_FK_ERRORS' : [long,'setMax_fk_errors'],'COLLECTION_SET_ID' : [long,'setCollection_set_id'],
        'MAX_COL_LIMIT_ERRORS' : [long,'setMax_col_limit_errors'], 'CHECK_FK_ERROR_FLAG' : [str,'setCheck_fk_error_flag'], 'CHECK_COL_LIMITS_FLAG' : [str,'setCheck_col_limits_flag'],
        'LAST_TRANSFER_DATE' : [str,'setLast_transfer_date'], 'USE_BATCH_ID' : [str,'setUse_batch_id'], 'PRIORITY' : [str,'setPriority'], 'QUEUE_TIME_LIMIT' : [str,'setQueue_time_limit'], 
        'ENABLED_FLAG' : [str,'setEnabled_flag'],'SETTYPE' : [str,'setSettype'] , 'FOLDABLE_FLAG' : [str,'setFoldable_flag'],
        'MEASTYPE' : [str,'setMeastype'], 'HOLD_FLAG' : [str,'setHold_flag'],'SCHEDULING_INFO' : [str,'setScheduling_info'] }
        
        props = {}
        ms = Meta_collections(self.dbConn)
        ms.setVersion_number(self.buildNo)
        ms.setCollection_set_id(self.coll_set_id)
        if 'COLLECTION_ID' in properties:
            ms.setCollection_id(long(properties['COLLECTION_ID']))
            props['COLLECTION_ID'] = properties['COLLECTION_ID']
            
        if modType == 'Update' or modType == 'Delete':
            identDict = properties['Identity']
            for key, value in identDict.iteritems():
                value = setMethodMap[key][0](value)
                getattr(ms, setMethodMap[key][1])(value)
                
            mcf = Meta_collectionsFactory(self.dbConn,ms)
            if len(mcf.get()) == 0:
                self.log.error("No existing row can be found with given Identity tags")
                raise
            elif len(mcf.get()) > 1:
                self.log.error("Multiple rows found with given Identity tags. Please provide more information with Identity tags to narrow selection to 1")
                raise
            elif len(mcf.get()) == 1:
                ms = mcf.getElementAt(0)
                self.log.debug("Identifies a unique row")
                
        if modType == 'New':
            props['COLLECTION_ID'] = self.getHighestID(self.dbConn, "select max(COLLECTION_ID) maxval from META_COLLECTIONS")
            props['MAX_ERRORS'] = 0
            props['MAX_FK_ERRORS'] = 0
            props['MAX_COL_LIMIT_ERRORS'] = 0
            props['CHECK_FK_ERROR_FLAG'] = 'N'
            props['CHECK_COL_LIMITS_FLAG'] = 'N'
            props['PRIORITY'] = 0
            props['QUEUE_TIME_LIMIT'] = 0
            props['ENABLED_FLAG'] = 'Y'
            props['HOLD_FLAG'] = 'N'
        
        if modType == 'Update' or modType == 'New': 
            props.update(properties['Modify'])
   
        return Utils.populateObjectFromDict(Meta_collections, props, self.dbConn, ms)
    
    def _getCollectionSetId(self):
        from com.distocraft.dc5000.etl.rock import Meta_collection_sets
        from com.distocraft.dc5000.etl.rock import Meta_collection_setsFactory
        
        mcs = Meta_collection_sets(self.dbConn)
        mcs.setCollection_set_name(self.coll_set_name)
        mcs.setVersion_number(self.buildNo)
        mcsF = Meta_collection_setsFactory(self.dbConn,mcs)
        coll_set_id = None
        if mcsF != None and mcsF.get() != None and len(mcsF.get()) > 0:
            coll_set_id = mcsF.getElementAt(0).getCollection_set_id()
               
        return coll_set_id
      
    def _getCollectionId(self,parent):
        from com.distocraft.dc5000.etl.rock import Meta_collections
        from com.distocraft.dc5000.etl.rock import Meta_collectionsFactory
        
        collection_id = None 
        mc = Meta_collections(self.dbConn)
        mc.setCollection_name(parent)
        mc.setVersion_number(self.buildNo)
        mc.setCollection_set_id(self.coll_set_id)
        mcF = Meta_collectionsFactory(self.dbConn,mc)
        if mcF != None and mcF.get() != None and len(mcF.get()) > 0:
            collection_id = mcF.getElementAt(0).getCollection_id()
        
        return collection_id
    
    def _nullColumnCheck(self, newProps, xmlProperties):
        '''
        Fix to check if any of the below columns are null and replace with empty string if that is the case
        '''
        if 'ACTION_CONTENTS_01' not in xmlProperties:
            newProps['ACTION_CONTENTS_01'] = ""
        if 'ACTION_CONTENTS_02' not in xmlProperties:
            newProps['ACTION_CONTENTS_02'] = ""
        if 'ACTION_CONTENTS_03' not in xmlProperties:
            newProps['ACTION_CONTENTS_03'] = ""
        if 'WHERE_CLAUSE_01' not in xmlProperties:
            newProps['WHERE_CLAUSE_01'] = ""
        if 'WHERE_CLAUSE_02' not in xmlProperties:
            newProps['WHERE_CLAUSE_02'] = ""
        if 'WHERE_CLAUSE_03' not in xmlProperties:
            newProps['WHERE_CLAUSE_03'] = ""
            
        return newProps
