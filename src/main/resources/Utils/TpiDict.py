'''
Created on May 31, 2016

@author: ebrifol
'''

import sys
import os
import re
import Utils
import csv
import shutil

class TpiDict(object):
    '''Class for extraction and intermediate storage of metadata from inside a tpi file.'''
    
    _instance = None
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(TpiDict, cls).__new__(
                                cls, *args, **kwargs)
        return cls._instance    
    
    def __init__(self,logger,filename=None,directory=None):
        if filename == None and directory == None:
            logger.error('Arguments are not correct')
            return
        
        self.tpidict = {}
        tpis = [] 
        extractedDirs = [] 
        self.filename = filename
        self.directory = directory
        self.interfaceSql = False
        BaseDest = sys.getBaseProperties().getProperty("user.home")+'\\tpi_tmp'
        unzipDest = BaseDest + '\\unzip'
        
        if filename is not None:
            if os.path.exists(filename):
                fileName = os.path.basename(filename)
                directoryName = os.path.dirname(filename)
                if directoryName != '':
                    absInputDir = os.path.abspath(directoryName)
                else:
                    # No path found, use current directory
                    absInputDir = os.path.abspath(os.path.dirname(os.getcwd()))
                filePath = os.path.join(absInputDir,fileName)
                if fileName.find('INTF_') == 0:
                    self.interfaceSql = True
                #unzipDest = os.path.join(absInputDir,'tmp')                
                
                Utils.unzipTpi(filePath,unzipDest)
                extractedDirs.append(unzipDest)
               
        elif directory is not None:
            if os.path.isdir(directory):
                absInputDir = os.path.abspath(directory)
                for myfile in os.listdir(absInputDir):
                    if myfile.endswith(".tpi"):
                        if fileName.find('INTF_') == 0:
                            self.interfaceSql = True
                        tpiFile = os.path.join(absInputDir,myfile)
                        destDir = os.path.join(absInputDir,'/tmp')
                        Utils.unzipTpi(tpiFile,destDir)
                        tpis.append(myfile)
                        extractedDirs.append(myfile.split('.')[0])

        for dir in extractedDirs:
            if os.path.exists(os.path.join(absInputDir,dir)):
                # Dirs contained in  the tpi file
                for dir2 in os.listdir(os.path.join(absInputDir,dir)):
                    for fileName in os.listdir(os.path.join(absInputDir,dir,dir2)):
                        if fileName.find('Tech_Pack') == 0:    
                            if re.match('.*(\.sql)',fileName):
                                logger.info('Reading SQL File')
                                path = os.getcwd()
                                sqlFile = open(os.path.join(absInputDir,dir,dir2,fileName))
                                lines = sqlFile.readlines()
                                count=0
                                
                                testString = ''
                                string = ''
                                completelines=[]
                                while count <= len(lines)-1:
                                    if self.interfaceSql:
                                        testString = lines[count]
                                        if len(testString) > 2 and not testString.startswith('--'):
                                            string = string + lines[count]
                                            if re.match('.*\)(\r)?', string):
                                                completelines.append(string)
                                                string = ''
                                    else:
                                        string = string + lines[count]
                                        if string[:-1].endswith(');'):
                                            completelines.append(string)
                                            string = ''     
                                    count = count + 1
                                for line in completelines:
                                    matchObj = re.match('insert into\s(.+?)[\s|\(]\(?.+? ',line)
                                    if matchObj:
                                        tableName = matchObj.group(1)
                                        if tableName not in self.tpidict:
                                            self.tpidict[tableName] = {}                      
                                        columns = line[line.find('(')+1:line.find(')')].split(',')
                                        if self.interfaceSql :
                                            vals = line[line.find('(',line.index(')'))+1:-2]
                                        else:
                                            vals = line[line.find('(',line.index(')'))+1:-3]
                                        p=[]
                                        p.append(vals)
                                        testReader = csv.reader(p,quotechar="'", skipinitialspace=True)
                                        for row in testReader:   
                                            for col,val in zip(columns,row):
                                                col = col.strip().upper()
                                                val = val.strip().strip("'")
                                                val = val.rstrip('\\')                 
                                                if col not in self.tpidict[tableName]:
                                                    self.tpidict[tableName][col] = {}
                                                self.tpidict[tableName][col][len(self.tpidict[tableName][col])+1 ] =  val

                                sqlFile.close()
                                logger.info('SQL File completed')
                            elif re.match('.*(\.xml)',fileName):
                                if self.interfaceSql:
                                    logger.info('Reading Interface Sets XML File')
                                    xmlFile = open(os.path.join(absInputDir,dir,dir2,fileName),"rb")
                                    for line in xmlFile:
                                        # escape commas found in the description field
                                        line = re.sub("'.+\s,'.+(,).+'\s,.+'",' &comma ',line)
                                        matchObj = re.search('.+<(.+?)\s.+?',line)
                                        #index = 0
                                        if matchObj:
                                            tableName = matchObj.group(1)
                                            if tableName not in self.tpidict:
                                                self.tpidict[tableName] = {}
                                                index = 0
                                            matchObj1 = re.search('.+<.+?\s(.+?)/>',line)
                                            if matchObj1:
                                                kevals = matchObj1.group(1)
                                            mysplit = re.split('"\s', kevals)
                                            
                                            for entry in mysplit:
                                                # Where clause can have multiple equals signs which mess up the splitting of the string
                                                s = re.split('="',entry)
                                                if len(s) > 1:
                                                    column =  s[0]
                                                    value = s[1].strip('"')
                                                if column not in self.tpidict[tableName]:
                                                    self.tpidict[tableName][column] = {} 
                                                self.tpidict[tableName][column][str(index)] =  value
                                            index = index + 1
                                    xmlFile.close()
                                    logger.info('Interface Sets XML File completed')
        shutil.rmtree(BaseDest)
               
    def printDict(self):
        f = open('tpiDict.txt', 'w')
        for table in self.tpidict:
            f.write("table is " + table +"\n")
            for column in self.tpidict[table]:
                f.write("column is " + column+"\n")
                for row in self.tpidict[table][column]:
                    f.write("row is " + str(row)+"\n")
                    f.write("value is " +self.tpidict[table][column][row]+"\n")

    def returnTPIDict(self):
        return self.tpidict

        