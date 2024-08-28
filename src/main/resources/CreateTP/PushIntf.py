'''
Created on Oct 5, 2016

@author: ebrifol
'''

import Utils
import java.lang.System

class PushIntftoDB(object):
    
    def __init__(self, dbConn, PathtoDb, envPath,logger):
        self.pathToDB = PathtoDb
        self.envPath = envPath
        self.dbConn = dbConn
        self.log = logger
    
    def pushData(self, IntModel):
        from com.distocraft.dc5000.repository.dwhrep import Datainterface
        from com.distocraft.dc5000.repository.dwhrep import Interfacetechpacks
        from com.distocraft.dc5000.repository.dwhrep import Interfacedependency 
        
        intfTechpacks, Dependencies, DatainterfaceDict, setsDict = IntModel.populateRepDbDicts()
        
        DatainterfaceDict['ENIQ_LEVEL'] = self.pathToDB.split('/')[-3].split('-')[1]
        DatainterfaceDict['LOCKEDBY'] = 'TPC'
        Utils.convertAndPush(DatainterfaceDict, Datainterface, self.dbConn)
        
        for intfTechpack in intfTechpacks:
            Utils.convertAndPush(intfTechpack, Interfacetechpacks, self.dbConn)
        
        for dependency in Dependencies:
            Utils.convertAndPush(dependency, Interfacedependency, self.dbConn)
        
        self.generateSets(setsDict)
    
    def generateSets(self, setsDict):
        from com.distocraft.dc5000.repository.dwhrep import Versioning
        from com.distocraft.dc5000.repository.dwhrep import VersioningFactory
        from com.distocraft.dc5000.etl.rock import Meta_collection_sets
        from com.distocraft.dc5000.etl.rock import Meta_collection_setsFactory
        from com.distocraft.dc5000.etl.rock import Meta_transfer_actions
        from com.distocraft.dc5000.etl.rock import Meta_transfer_actionsFactory
        from com.distocraft.dc5000.etl.rock import Meta_schedulings
        from com.distocraft.dc5000.etl.rock import Meta_schedulingsFactory
        from com.ericsson.eniq.common.setWizards import CreateIDiskmanagerSet
        from java.util import Properties
        from org.apache.velocity.app import Velocity
        
        p = Properties();
        p.setProperty("file.resource.loader.path", self.envPath);
        Velocity.init(p);
        
        setName = setsDict['INTERFACENAME']
        version = setsDict['INTERFACEVERSION']
        type = setsDict['INTERFACETYPE']
        elementTypeF = setsDict['ELEMTYPE']
        formatType = setsDict['DATAFORMATTYPE']
        
        mwhere = Meta_collection_sets(self.dbConn)
        mwhere.setCollection_set_name(setName)
        mwhere.setVersion_number(version)
        mcsf = Meta_collection_setsFactory(self.dbConn,mwhere)
        etl_tp = None
        if len(mcsf.get()) <= 0:
            csw = Meta_collection_sets(self.dbConn)
            csf = Meta_collection_setsFactory(self.dbConn, csw)
            largest = -1
            for mc in csf.get():
                if largest < mc.getCollection_set_id():
                    largest = mc.getCollection_set_id()
            largest = largest + 1
                
            etl_tp = Meta_collection_sets(self.dbConn)
            etl_tp.setCollection_set_id(largest)
            #print largest
            etl_tp.setCollection_set_name(setName)
            etl_tp.setVersion_number(version)
            etl_tp.setDescription("Interface " + setName + " by TPC-" + java.lang.System.getProperty('TPCbuildNumber'))
            etl_tp.setEnabled_flag("N")
            etl_tp.setType("Interface")
            etl_tp.insertDB(False, False)
        else:
            etl_tp = mcsf.getElementAt(0)
        
        cdc = None
        from com.ericsson.eniq.common.setWizards import CreateIDirCheckerSetFactory
        try:
            cdc = CreateIDirCheckerSetFactory.createIDirCheckerSet(type, etl_tp.getVersion_number(), self.dbConn, long(float(etl_tp.getCollection_set_id())), setName, elementTypeF)
        except:
            cdc = CreateIDirCheckerSetFactory.createIDirCheckerSet(type, etl_tp.getVersion_number(), self.dbConn, long(float(etl_tp.getCollection_set_id())), setName, elementTypeF, formatType)
            
        cdc.removeSets()
        cdc.create(False)
        
        cdm = CreateIDiskmanagerSet(type, etl_tp.getVersion_number(), self.dbConn, long(float(etl_tp.getCollection_set_id())), setName, elementTypeF)
        cdm.removeSets(True)
        cdm.create(False, True)
        
        TechPacks = []
        ver = Versioning(self.dbConn)
        verF = VersioningFactory(self.dbConn, ver, True)
        for v in verF.get():
            versionNumber = v.getVersionid().split(':')[1]
            TechPacks.append(v.getTechpack_name() + ':' + v.getTechpack_version()+ ':' + versionNumber)
            
        cis = None
        from com.ericsson.eniq.common.setWizards import CreateInterfaceSetFactory
        from tpapi.eniqInterface.rescource import DummyResourceMap
        
        application = DummyResourceMap()
        cis = CreateInterfaceSetFactory.createInterfaceSet(type, '5.2', version, '', self.dbConn, self.dbConn, long(float(etl_tp.getCollection_set_id())), setName, version, formatType, formatType, elementTypeF, '2', application.getResourceMap())
    
        cis.removeTechpacks(TechPacks, formatType, True)
        cis.createTechpacks(False, TechPacks, formatType, True)
        
        
        config = setsDict['intfConfig']
        
        inDir = config['inDir']
        inDirParts = inDir.split('/')
        inDir = inDirParts[0] + '/' + inDirParts[1] + '/'
        mta = Meta_transfer_actions(self.dbConn)
        mta.setCollection_set_id(etl_tp.getCollection_set_id())
        mta.setAction_type('CreateDir')
        mta.setTransfer_action_name('CreateDir_in')
        mtaF = Meta_transfer_actionsFactory(self.dbConn, mta)
        for a in mtaF.get():
            a.setWhere_clause_01(inDir)
            a.saveDB()
        
        
        newConfig = ''
        existingParams = []
        mta = Meta_transfer_actions(self.dbConn)
        mta.setCollection_set_id(etl_tp.getCollection_set_id())
        mta.setAction_type('Parse')
        mtaF = Meta_transfer_actionsFactory(self.dbConn, mta)
        for a in mtaF.get():          
            config_list = a.getAction_contents().replace('\r', '\n')
            config_list = config_list.rsplit('\n')[2:]
            
            for item in config_list:
                if item != '':
                    kvp = item.split("=",1)
                    param = kvp[0]
                    action = ''
                    try:
                        action = kvp[1]
                    except:
                        pass
                    
                    if param in config.keys():
                        existingParams.append(param)
                        if action != '':
                            action = action.replace(action,config[param])
                        else:
                            action = config[param]+action
                    newConfig = newConfig + param + '=' + action + '\n'
                    
            for param, action in config.iteritems():
                if param not in existingParams and param != 'AS_Interval' and param != 'AS_SchBaseTime':
                    newConfig = newConfig + param + '=' + action + '\n'

            a.setAction_contents(newConfig)
            a.saveDB()
        
        
        sch = Meta_schedulings(self.dbConn)
        sch.setCollection_set_id(etl_tp.getCollection_set_id())
        sch.setName('TriggerAdapter_'+setName+'_'+formatType)
        schF = Meta_schedulingsFactory(self.dbConn, sch)

        for s in schF.get():
            if 'AS_Interval' in config.keys():
                items = config['AS_Interval'].split(',')
                s.setInterval_hour(long(float(items[0])))
                s.setInterval_min(long(float(items[1])))
            if 'AS_SchBaseTime' in config.keys():
                items = config['AS_SchBaseTime'].split(',')
                s.setScheduling_hour(long(float(items[0])))
                s.setScheduling_min(long(float(items[1])))
            s.saveDB()
    
        self.deactivateIntf(setName + ":" + version)
                    
        
    def deactivateIntf(self, versionID):
        from com.distocraft.dc5000.repository.dwhrep import Datainterface
        from com.distocraft.dc5000.repository.dwhrep import Interfacemeasurement
        from com.distocraft.dc5000.repository.dwhrep import InterfacemeasurementFactory
        from com.distocraft.dc5000.etl.rock import Meta_collection_sets
        from com.distocraft.dc5000.etl.rock import Meta_collection_setsFactory
        from com.distocraft.dc5000.etl.rock import Meta_collections
        from com.distocraft.dc5000.etl.rock import Meta_collectionsFactory
        from com.distocraft.dc5000.etl.rock import Meta_transfer_actions
        from com.distocraft.dc5000.etl.rock import Meta_transfer_actionsFactory
        
        items = versionID.split(':')
        dataIntf = Datainterface(self.dbConn, items[0], items[1])
#         dataIntf.setStatus(long(float(0)))
#         dataIntf.saveDB()
        
        im_cond = Interfacemeasurement(self.dbConn)
        im_cond.setInterfacename(dataIntf.getInterfacename())
        im_cond.setInterfaceversion(dataIntf.getInterfaceversion())
        imf = InterfacemeasurementFactory(self.dbConn, im_cond)
        for im in imf.get():
            im.deleteDB()
            
        mcs = Meta_collection_sets(self.dbConn)
        mcsF = Meta_collection_setsFactory(self.dbConn, mcs)
        if mcsF != None and len(mcsF.get()) > 0:
            for metacs in mcsF.get():
                if metacs.getCollection_set_name() == dataIntf.getInterfacename() or dataIntf.getInterfacename() + "-" in metacs.getCollection_set_name():
                    metaCollectionSetName = metacs.getCollection_set_name()
                    interfaceVersion = metacs.getVersion_number()
                    
                    mcs = Meta_collection_sets(self.dbConn)
                    mcs.setCollection_set_name(metaCollectionSetName)
                    mcs.setVersion_number(interfaceVersion)
                    mcsFF = Meta_collection_setsFactory(self.dbConn, mcs)
                    if mcsFF != None and len(mcsFF.get()) > 0:
                        metacss = mcsFF.getElementAt(0)
                        mc = Meta_collections(self.dbConn)
                        mc.setCollection_set_id(metacss.getCollection_set_id())
                        mc.setVersion_number(interfaceVersion)
                        mcF = Meta_collectionsFactory(self.dbConn, mc)
                        for metac in mcF.get():
                            metac.setEnabled_flag('N')
                            metac.saveDB()
                            
                            mta = Meta_transfer_actions(self.dbConn)
                            mta.setCollection_set_id(metacs.getCollection_set_id())
                            mta.setVersion_number(interfaceVersion)
                            mtaF = Meta_transfer_actionsFactory(self.dbConn ,mta)
                            for action in mtaF.get():
                                action.setEnabled_flag('N')
                                action.saveDB()
                                    
                        metacss.setEnabled_flag('N')
                        metacss.saveDB()

        
        