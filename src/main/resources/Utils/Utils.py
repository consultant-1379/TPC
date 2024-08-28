'''
Created on May 30, 2016

@author: ebrifol
'''
import os
import zipfile
import shutil
import sys
import Utils
from com.ericsson.eniq.tpc.util import SFTPSession, SSHSession
from xml.etree import ElementTree
from ftplib import FTP
from java.util import Date
from java.text import SimpleDateFormat
from ftplib import FTP_TLS
from math import floor

def compareRStates(rstate1,rstate2):
    '''Compare two rstates 
        Returns 1 if rstate1 is later, 0 if they are equal and -1 if rstate2 is later.'''
    if rstate1[0] == 'R' and rstate2[0] == 'R':
        if rstate1[1:-1].isdigit and rstate2[1:-1].isdigit:
            digit1 = rstate1[1:-1]
            digit2 = rstate2[1:-1]
            if int(digit1) > int(digit2):
                return 1
            elif int(digit1) == int(digit2):
                if rstate1[-1].isalpha and rstate2[-1].isalpha:
                    alpha1 = rstate1[-1]
                    alpha2 = rstate2[-1]
                    if alpha1 > alpha2:
                        return 1
                    elif alpha1 == alpha2:
                        return 0
                    else:
                        return -1
            else:
                return -1

def strFloatToInt(value):
    '''Converts string float to string int'''
    try:
        float(value)    # checks that the value being converted is a number
        if (float(value) - floor(float(value))) == 0: # only converts to int if number actually is integer
            value = str(value).split(".")[0]
            if 'e+' in value:
                value = str(value.split('e+')[0])

        return value
    
    except ValueError:
        return value

def getBaseTPName(crsr):
    crsr.execute("SELECT VERSIONID from Versioning where TECHPACK_TYPE =?", ('BASE',))
    baseTPs = Utils.rowToList(crsr.fetchall()) 
    return sorted(baseTPs)[-1]

def checkNull(inputStr):
    '''Check if string is null'''
    if inputStr == 'null' or inputStr == 'None':
        return ''
    else:
        return inputStr

def safeNull(elementText):
    '''Converts a None type object to an empty string.Used by FromXML methods for handling element tags with empty
    values'''
    if elementText == None:
        elementText = ''
        return elementText
    else:
        return elementText.strip() 

def escape(text):
    '''return text that is safe to use in an XML string'''
    html_escape_table = {
        "&": "&amp;",
        '"': "&quot;",
        ">": "&gt;",
        "<": "&lt;",
    }   
    return "".join(html_escape_table.get(c,c) for c in str(text))

def unescape(s):
    '''change XML string to text'''
    s = s.replace("&lt;", "<")
    s = s.replace("&gt;", ">")
    s = s.replace("&apos;", "'")
    s = s.replace("&quot;", '"')
    s = s.replace("&amp;", "&")
    return s 

def rowToList(resultset):
    '''Convert single column resultset to a list'''
    mylist = []
    for i in resultset:
        mylist.append(i[0],)
    return mylist 

def fileToXMLObject(xmlfile):
    '''Convert File to XML Object'''
    xmlString = xmlfile.read()
    xmlObject = ElementTree.fromstring(xmlString)
    return xmlObject


def unzipTpi(tpiFile,outDir):
    '''Unzips a tpi (tpiFile) file to the specified output directory. Function
    
    tpiFile: tpiFile to be extracted
    outDir: Output directory destination
    
   Exceptions:
            Raised if the file does not end with .tpi
            Raised if its not a valid zipfFile'''
       
    extractDirName = tpiFile.split('.')[0]
    if os.path.splitext(tpiFile)[1] != '.tpi':
        strg = "TPAPI.unzipTpi() file " +tpiFile + " : is not a .tpi file.. exiting"
        raise Exception(strg)
        
    if not zipfile.is_zipfile(tpiFile):
        strg()
        raise Exception(strg)
    
    if os.path.exists(outDir):
        shutil.rmtree(outDir)
               
    os.makedirs(outDir)
    
    zfile = zipfile.ZipFile(tpiFile)
    for name in zfile.namelist():
        (dirName, fileName) = os.path.split(name)
        
        newDir = outDir + '/' + dirName
        if not os.path.exists(newDir):
            os.makedirs(newDir)
        
        if fileName != '':
            # file
            fd = open(outDir + '/' + name, 'wb')
            fd.write(zfile.read(name))
            fd.close()

    zfile.close()

def getENIQversion(Servername, Username, Passsword):
    filePath = sys.getBaseProperties().getProperty("user.home")+'\\eniq_status.txt'

    f=open(filePath, 'r')
    version = f.readline().split(' ')[1].split('_')[3]
    #version = "16.2.8"
    f.close()
    os.remove(filePath)

    return version 

class DictDiffer(object):
    """
    Class for calculating the difference between two dictionaries.
    
    """
    def __init__(self, current_dict, past_dict):
        '''Initialised with the two dictionary objects to be compared'''
        self.current_dict, self.past_dict = current_dict, past_dict
        self.set_current, self.set_past = set(current_dict.keys()), set(past_dict.keys())
        self.intersect = self.set_current.intersection(self.set_past)
    def added(self):
        '''Returns:
                Dictionary of added items'''
        return self.set_past - self.intersect 
    def removed(self):
        '''Returns:
                Dictionary of removed items'''
        return self.set_current - self.intersect 
    def changed(self):
        '''Returns:
                Dictionary of changed items'''
        return set(o for o in self.intersect if self.past_dict[o] != self.current_dict[o])
    def unchanged(self):
        '''Returns:
                Dictionary of unchanged items'''
        return set(o for o in self.intersect if self.past_dict[o] == self.current_dict[o])
    def common(self):
        '''Returns:
                Dictionary of common items'''
        return self.intersect

def verifyNotNone(obj, method):
    try:
        return int(getattr(obj,method)())
    except:
        return 0

def replaceNone(statement):
    if statement() == None:
        return ''
    else:
        return statement()

def getFTPConnection(host, user, password, port=22):
    try:
        ftp = SFTPSession()
        ftp.getConnection(host, user, password, int(port))
    except Exception as e:
        print "Exception occurred while connecting through sftp " , e
         
    return ftp


def getSshConnection(host, user, password, port=22):
    try:
        ssh = SSHSession()
        ssh.getConnection(host, user, password, int(port))
    except Exception as e:
        print "Exception occurred while connecting through sftp " , e
         
    return ssh


def convertAndPush(properties, ObjectTocreate, dbconn):
    populatedObj = populateObjectFromDict(ObjectTocreate, properties, dbconn)
    populatedObj.insertDB()
    return populatedObj

def populateObjectFromDict(Object, Dict, DBConnection=None, obj=None):
    if obj == None:
        obj = Object(DBConnection, True)       
    items = dir(Object)
    for i in items:
        if i.startswith('set'):
            propertyName = i.split('set', 1)[1].upper()
            if propertyName in Dict:
                propertyType = str(vars(Object)[i.split('set', 1)[1].lower()]).split(' ')[3].split('.')[2]
                value = Dict[propertyName]
                if value != None:
                    if propertyType == 'String':
                        value = value.strip()
                    elif propertyType == 'Integer':
                        if value == '' or value == '0' or value == 'None':
                            value = 0
                        else:
                            value = int(value)
                    elif propertyType == 'Long':
                        if value != 'None':
                            value = long(value)
                        else:
                            value = long(0)
                    elif propertyType == 'Timestamp':
                        from java.sql import Timestamp
                        if value != 'None':
                            value = Timestamp.valueOf(value)
                        else:
                            dateFormat = SimpleDateFormat("yyyy-MM-dd HH:mm:ss")
                            date = Date()
                            value = Timestamp.valueOf(dateFormat.format(date))
                    getattr(obj,i)(value)
    return obj

#Common method to read external statements from text file
def loadEStxtFile(filename):
    ESCollection = None
    if os.path.isfile(filename):
        ESCollection = {}
        filecontents = open(filename, 'r').read()
        filecontents = filecontents.split('@@')
        for ES in filecontents:
            if ES != '':
                info = ES.split('==')
                ESCollection[info[0]] = info[1]
    else:
        pass
    return ESCollection


def createCleanUnvDir(unvDirectory):
    '''Method to initialise universe details directory'''
    if os.path.exists(unvDirectory):
        shutil.rmtree(unvDirectory)
    
    os.makedirs(unvDirectory)
        
def writeUnvDetails(data, filename):
    '''Method to write to Universe create/update files'''
    unvFile = open(filename, 'a')
    print >>unvFile, data
    #unvFile.write(data + '\n')
    unvFile.close()
    
