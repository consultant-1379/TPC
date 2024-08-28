'''
Created on Oct 5, 2016

@author: ebrifol
'''

import Utils
import shutil
import os
import zipfile
from java.util import Properties, Vector
from java.io import StringWriter

class IntfInstallerFile(object):

    def __init__(self, versionID, dbConn, outputPath, envPath):
        self.versionID = versionID
        self.outputPath = outputPath
        self.envPath = envPath
        self.dbConn = dbConn
    
    def createFile(self):
        from com.distocraft.dc5000.repository.dwhrep import Datainterface
        
        elements = self.versionID.split(':')
        dataIntf = Datainterface(self.dbConn, elements[0], elements[1])
        interface_name = elements[0]
        build_number = elements[1].replace('((', '').replace('))', '')
        outputFileName = interface_name + '_' + dataIntf.getRstate() + '_b' + build_number + '.tpi'
        
        self._createSetsXmlFile(build_number, interface_name)
        self._createInstallDirFiles(dataIntf, build_number, interface_name)
        self._createSQLFile(dataIntf, interface_name)
        
        Z = zipfile.ZipFile(self.outputPath+'\\'+outputFileName, 'w')
        directories = ['install','interface']
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
                
    
    def _createSetsXmlFile(self, build_number, interface_name):
        from com.distocraft.dc5000.etl.importexport import ETLCExport
        
        #Create .xml file in set directory
        setDir = self.outputPath+'/interface'
        if not os.path.exists(setDir):
            os.makedirs(setDir)
        setFile = open(setDir+'\\Tech_Pack_' + interface_name + '.xml','w')
        
        des = ETLCExport(None, self.dbConn.getConnection())
        filecontents = des.exportXml('#version#=((' + build_number + ')),#techpack#=' + interface_name)
        filecontents = filecontents.getBuffer().toString()
        setFile.write(filecontents)
        setFile.close()
    
    def _createInstallDirFiles(self, dataIntf, build_number, interface_name):
        from com.distocraft.dc5000.repository.dwhrep import Interfacedependency
        from com.distocraft.dc5000.repository.dwhrep import InterfacedependencyFactory
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
        installXmlContent = None
        try:
            installXmlContent = dataIntf.getInstalldescription()
        except:
            pass
        
        if installXmlContent != None and len(installXmlContent) > 0:
            installXml.write(installXmlContent)
        else:
            context = None
            vmFile = 'install.vm'
            strw = StringWriter()
            isMergeOk = Velocity.mergeTemplate(vmFile, Velocity.ENCODING_DEFAULT, context, strw)
            if isMergeOk:
                installXml.write(strw.toString().encode('ascii', 'ignore'))
        installXml.close()
        
        versionProps = open(installDir+'\\version.properties','w')
        versionProps.write('tech_pack.metadata_version=3\n')
        itd = Interfacedependency(self.dbConn)
        itd.setInterfacename(dataIntf.getInterfacename())
        itd.setInterfaceversion(dataIntf.getInterfaceversion())
        itdF = InterfacedependencyFactory(self.dbConn, itd)
        for i in itdF.get():
            versionProps.write('required_tech_packs.'+i.getTechpackname()+'='+i.getTechpackversion()+'\n')
        versionProps.write('tech_pack.name=' + dataIntf.getInterfacename()+'\n')
        versionProps.write('author=' + dataIntf.getLockedby()+'\n')
        versionProps.write('tech_pack.version=' + dataIntf.getRstate()+'\n')
        versionProps.write('build.number=' + build_number+'\n')
        versionProps.write('build.tag=\n')
        versionProps.write('licenseName=\n')
        versionProps.close()
    
    def _createSQLFile(self, dataIntf, interface_name):
        from com.distocraft.dc5000.repository.dwhrep import Datainterface
        from com.distocraft.dc5000.repository.dwhrep import DatainterfaceFactory
        from com.distocraft.dc5000.repository.dwhrep import Interfacetechpacks
        from com.distocraft.dc5000.repository.dwhrep import InterfacetechpacksFactory
        from com.distocraft.dc5000.repository.dwhrep import Interfacedependency
        from com.distocraft.dc5000.repository.dwhrep import InterfacedependencyFactory
        
        #Create .sql file in sql directory
        sqlDir = self.outputPath+'\\interface'
        if not os.path.exists(sqlDir):
            os.makedirs(sqlDir)
        sqlFile = open(sqlDir+'\\Tech_Pack_' + interface_name + '.sql','w')
        
        aimf = DatainterfaceFactory(self.dbConn, dataIntf)
        for im in aimf.get():
            sqlFile.write(im.toSQLInsert())
            
        aimt = Interfacetechpacks(self.dbConn)
        aimt.setInterfacename(dataIntf.getInterfacename())
        aimt.setInterfaceversion(dataIntf.getInterfaceversion())
        aimtf = InterfacetechpacksFactory(self.dbConn, aimt)
        for imt in aimtf.get():
            sqlFile.write(imt.toSQLInsert())
            
        infd = Interfacedependency(self.dbConn)
        infd.setInterfacename(dataIntf.getInterfacename())
        infd.setInterfaceversion(dataIntf.getInterfaceversion())
        infdf = InterfacedependencyFactory(self.dbConn, infd)
        for id in infdf.get():
            sqlFile.write(id.toSQLInsert())
        
        sqlFile.close()
        
    def getIntfFileName(self):
        from com.distocraft.dc5000.repository.dwhrep import Datainterface
        
        elements = self.versionID.split(':')
        dataIntf = Datainterface(self.dbConn, elements[0], elements[1])
        interface_name = elements[0]
        build_number = elements[1].replace('((', '').replace('))', '')
        outputFileName = interface_name + '_' + dataIntf.getRstate() + '_b' + build_number + '.tpi'
        return outputFileName  
