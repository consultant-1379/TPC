'''
Created on Jul 25, 2016

@author: ebrifol
'''

import Utils
import shutil
import os
import zipfile
from java.util import Properties, Vector
from java.io import StringWriter

class TPInstallerFile(object):

    def __init__(self, tp, dbConn, outputPath, envPath, dbAccess):
        self.TPModel = tp
        self.versionID = tp.versionID
        self.outputPath = outputPath
        self.envPath = envPath
        self.dbConn = dbConn
        self.dbAccess = dbAccess
        
        self.isVector = tp.isVector
    
    def createFile(self):
        from com.distocraft.dc5000.repository.dwhrep import Versioning
        
        versioning = Versioning(self.dbConn, self.versionID) 
        
        elements = versioning.getVersionid().split(':')
        techpack_name = elements[0]
        build_number = elements[1].replace('((', '').replace('))', '')
        outputFileName = techpack_name + '_' + versioning.getTechpack_version() + '_b' + build_number + '.tpi'
        
        self._createSetsXmlFile(build_number, techpack_name)
        self._createInstallDirFiles(versioning, build_number, techpack_name)
        self._createSQLFile(versioning, techpack_name)
        if self.isVector:
            self._createVectorFile(techpack_name)
        
        Z = zipfile.ZipFile(self.outputPath+'\\'+outputFileName, 'w')
        directories = ['install','set','sql']
        if self.isVector:
            directories.append('vector')
            
        for directory in directories:
            for dirpath,dirs,files in os.walk(self.outputPath+'\\'+directory):
                for f in files:
                    if not f.endswith('.tpi'):
                        fn = os.path.join(dirpath, f)
                        Z.write(str(fn), str(directory+'\\'+f), zipfile.ZIP_DEFLATED)
        Z.close()
            
        dirs = os.listdir(self.outputPath)
        for dir in dirs:
            if dir in directories:
                shutil.rmtree(self.outputPath+'\\'+dir)
        
    
    def _createSetsXmlFile(self, build_number, techpack_name):
        from com.distocraft.dc5000.etl.importexport import ETLCExport
        
        #Create .xml file in set directory
        setDir = self.outputPath+'/set'
        if not os.path.exists(setDir):
            os.makedirs(setDir)
        setFile = open(setDir+'\\Tech_Pack_' + techpack_name + '.xml','w')
        
        des = ETLCExport(None, self.dbConn.getConnection())
        filecontents = des.exportXml('#version#=((' + build_number + ')),#techpack#=' + techpack_name)
        filecontents = filecontents.getBuffer().toString()
        setFile.write(filecontents)
        setFile.close()
    
    def _createInstallDirFiles(self, versioning, build_number, techpack_name):
        from com.distocraft.dc5000.repository.dwhrep import Techpackdependency
        from com.distocraft.dc5000.repository.dwhrep import TechpackdependencyFactory
        from org.apache.velocity.app import Velocity
        from org.apache.velocity import VelocityContext
        
        p = Properties();
        p.setProperty("file.resource.loader.path", self.envPath);
        Velocity.init(p);
        
        #Create install directory for version.properties and install.xml
        installDir = self.outputPath+'\\install'
        if not os.path.exists(installDir):
            os.makedirs(installDir)
        
        installXml = open(installDir+'\\install.xml','w')   
        installXmlContent = versioning.getInstalldescription()
        if installXmlContent != None and len(installXmlContent) > 0:
            installXml.write(installXmlContent)
        else:
            context = None
            vmFile = 'install.vm'
            if techpack_name == 'AlarmInterfaces' or techpack_name == 'DC_Z_ALARM':
                context = VelocityContext()
                context.put("configurationDirectory", "${configurationDirectory}")
                context.put("binDirectory", "${binDirectory}")
            if techpack_name == 'AlarmInterfaces':
                vmFile = 'install_AlarmInterfaces.vm'
            elif techpack_name == 'DC_Z_ALARM':
                vmFile = 'install_DC_Z_ALARM.vm'
                
            if self.isVector:
                vmFile = 'install_Vector.vm'
            
            strw = StringWriter()
            isMergeOk = Velocity.mergeTemplate(vmFile, Velocity.ENCODING_DEFAULT, context, strw)
            if isMergeOk:
                installXml.write(strw.toString().encode('ascii', 'ignore'))
        installXml.close()
        
        
        versionProps = open(installDir+'\\version.properties','w')
        versionProps.write('tech_pack.metadata_version=3\n')
        tpd = Techpackdependency(self.dbConn)
        tpd.setVersionid(versioning.getVersionid());
        tpdF = TechpackdependencyFactory(self.dbConn, tpd)
        for t in tpdF.get():
            versionProps.write('required_tech_packs.'+t.getTechpackname()+'='+t.getVersion()+'\n')
        versionProps.write('tech_pack.name=' + techpack_name+'\n')
        versionProps.write('author=' + versioning.getLockedby()+'\n')
        versionProps.write('tech_pack.version=' + versioning.getTechpack_version()+'\n')
        versionProps.write('build.number=' + build_number+'\n')
        versionProps.write('build.tag=\n')
        licenseName = ''
        if versioning.getLicensename() != None:
            licenseName = versioning.getLicensename()
        versionProps.write('license.name='+licenseName+'\n')
        versionProps.close()
    
    def _createSQLFile(self, versioning, techpack_name):
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
        
        #Create .sql file in sql directory
        sqlDir = self.outputPath+'\\sql'
        if not os.path.exists(sqlDir):
            os.makedirs(sqlDir)
        sqlFile = open(sqlDir+'\\Tech_Pack_' + techpack_name + '.sql','w')
        
        versionid = versioning.getVersionid()
        
        sqlFile.write(versioning.toSQLInsert())
        self._readRepInfo( Supportedvendorrelease, 'VERSIONID', versionid, sqlFile)
        
        self._readRepInfo( Measurementtypeclass, 'VERSIONID', versionid, sqlFile)
        self._readRepInfo( Measurementtype, 'VERSIONID', versionid, sqlFile)
        self._readRepInfo( Measurementcounter, 'TYPEID', versionid, sqlFile)
        self._readRepInfo( Measurementvector, 'TYPEID', versionid, sqlFile)
        self._readRepInfo( Measurementkey, 'TYPEID', versionid, sqlFile)
        self._readRepInfo( Measurementdeltacalcsupport, 'TYPEID', versionid, sqlFile)
        self._readRepInfo( Measurementobjbhsupport, 'TYPEID', versionid, sqlFile)
        self._readRepInfo( Measurementtable, 'MTABLEID', versionid, sqlFile)
        self._readRepInfo( Measurementcolumn, 'MTABLEID', versionid, sqlFile)
        
        self._readRepInfo( Busyhour, 'VERSIONID', versionid, sqlFile)
        self._readRepInfo( Busyhourrankkeys, 'VERSIONID', versionid, sqlFile)
        self._readRepInfo( Busyhourmapping, 'VERSIONID', versionid, sqlFile)
        self._readRepInfo( Busyhoursource, 'VERSIONID', versionid, sqlFile)
        self._readRepInfo( Busyhourplaceholders, 'VERSIONID', versionid, sqlFile)
        
        self._readRepInfo( Techpackdependency, 'VERSIONID', versionid, sqlFile)
        
        self._readRepInfo( Referencetable, 'VERSIONID', versionid, sqlFile)
        self._readRepInfo( Referencecolumn, 'TYPEID', versionid, sqlFile)
        
        self._readRepInfo( Transformer, 'VERSIONID', versionid, sqlFile)
        self._readRepInfo( Transformation, 'TRANSFORMERID', versionid, sqlFile)
        self._readRepInfo( Dataformat, 'VERSIONID', versionid, sqlFile)
        self._readRepInfo( Defaulttags, 'DATAFORMATID', versionid, sqlFile)
        self._readRepInfo( Dataitem, 'DATAFORMATID', versionid, sqlFile)
        
        self._readRepInfo( Aggregation, 'VERSIONID', versionid, sqlFile)
        self._readRepInfo( Aggregationrule, 'VERSIONID', versionid, sqlFile)
        
        self._readRepInfo( Externalstatement, 'VERSIONID', versionid, sqlFile)
        
        self._readRepInfo( Universename, 'VERSIONID', versionid, sqlFile)
        self._readRepInfo( Universeclass, 'VERSIONID', versionid, sqlFile)
        self._readRepInfo( Universetable, 'VERSIONID', versionid, sqlFile)
        self._readRepInfo( Universejoin, 'VERSIONID', versionid, sqlFile)
        self._readRepInfo( Universeobject, 'VERSIONID', versionid, sqlFile)
        self._readRepInfo( Universecomputedobject, 'VERSIONID', versionid, sqlFile)
        self._readRepInfo( Universeparameters, 'VERSIONID', versionid, sqlFile)
        self._readRepInfo( Universeformulas, 'VERSIONID', versionid, sqlFile)
        self._readRepInfo( Universecondition, 'VERSIONID', versionid, sqlFile)
        
        sqlFile.close()
        
    
    def _readRepInfo(self, tablename, keyname, versionid, filehandle):
        DbCursor = self.dbAccess.getCursor()
        DbCursor.execute("SELECT * from " + str(tablename.__name__) +" where " + keyname +" LIKE '%" + versionid + "%'")
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
                filehandle.write(obj.toSQLInsert())
        else:
            pass
        
    def getTpiFileName(self):
        from com.distocraft.dc5000.repository.dwhrep import Versioning
        
        versioning = Versioning(self.dbConn, self.versionID) 
        
        elements = versioning.getVersionid().split(':')
        techpack_name = elements[0]
        build_number = elements[1].replace('((', '').replace('))', '')
        outputFileName = techpack_name + '_' + versioning.getTechpack_version() + '_b' + build_number + '.tpi' 
        return outputFileName
    
    
    def _createVectorFile(self, techpack_name):
        #Create .sql file in sql directory
        vectorDir = self.outputPath+'\\vector'
        if not os.path.exists(vectorDir):
            os.makedirs(vectorDir)
        vecLoader = open(vectorDir+'\\Tech_Pack_' + techpack_name + '.txt','wb')
        
        vecDict = {}
        for table in self.TPModel.measurementTables.itervalues():
            for attribute in table.attributes.itervalues():
                if attribute.attributeType == 'measurementCounter':
                    for quant in attribute.vectors.itervalues():
                        for indices in quant.itervalues():
                            for vector in indices.itervalues():
                                vecDict = vector.populateRepDbDicts()
                                table_name_dim = table.name.replace("DC","DIM",1)
                                table_counter = table_name_dim + '_' + attribute.name
                                value = vecDict['VFROM'] + ' - ' + vecDict['VTO'] + ' ' + vecDict['MEASURE']
                                relList = vector.VendorRelease.split(',')
                                for release in relList:
                                    vecRow = table_counter + '\t' + vecDict['VINDEX'] + '\t' + release + '\t' + vecDict['QUANTITY'] + '\t' + value + '\t\n'
                                    vecLoader.write(vecRow)
                                
        vecLoader.close()
        
