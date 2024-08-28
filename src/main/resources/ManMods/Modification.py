'''
Created on 30 Nov 2016

@author: ebrifol
'''

import Utils

class Modification(object):

    # initialize object
    def __init__(self):
        self.dataStorage = {}
        self.modtype = ''
        self.table = ''
        self.parentname = ''

    # set and get type value  
    def settype(self, modtype):
        self.modtype = modtype
        
    def gettype(self):
        return self.modtype
        
    # set and get table value      
    def settable(self, table):
        self.table = table
        
    def gettable(self):
        return self.table
    
        # set and get table value      
    def setparentname(self, parentname):
        self.parentname = parentname
        
    def getparentname(self):
        return self.parentname
    
    # adds data by storageKey and storageValue to dataStorage
    def addDataToStore(self, storageKey, storageValue):
        self.dataStorage[storageKey] = Utils.unescape(storageValue)
    
    # gets Data from dataStorage by storageKey value   
    def getDataStore(self):
        return self.dataStorage
    
    # removes data from dataStorage by storageKey value
    def removeDataFromStore(self, storageKey):
        self.dataStorage.pop(storageKey, None)
        
    # gets Data from dataStorage by storageKey value   
    def getDataFromStore(self, storageKey):
        return self.dataStorage.get(storageKey)

    def addIdentityTagToStore(self, storageKey, storageValue):
        if 'Identity' in self.dataStorage:
            identityDict = self.dataStorage['Identity']
        else:
            identityDict = {}
            
        identityDict[storageKey] = storageValue
        self.dataStorage['Identity'] = identityDict
        
    def addModifyTagToStore(self, storageKey, storageValue):
        if 'Modify' in self.dataStorage:
            modifyDict = self.dataStorage['Modify']
        else:
            modifyDict = {}
            
        modifyDict[storageKey] = storageValue
        self.dataStorage['Modify'] = modifyDict
        
        
        