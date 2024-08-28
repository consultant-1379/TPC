'''
Created on May 31, 2016

@author: ebrifol
'''

class Delta(object):
    '''Class for recording and reporting techpack delta information'''
    
    def __init__(self,originalVersionID,newVersionID):
          
        self.originalVersionID = originalVersionID # base version of the tp
        self.newVersionID = newVersionID # upgraded versionid of the tp
        self.changes = []
        self.location = []

    def getNumOfDifferences(self):
        '''Returns the number of changes recorded in the delta 
        
        Returns:
                self.numchanges
        
        '''
        return len(self.changes)

    def addChange(self, changeType, changedItem, oldVal=None, newVal=None):
        '''Adds a change to the change dictionary, using a stack, delta & original values.'''
        changeString = changeType+';'+','.join(self.location)+';'
        changeString = changeString + str(changedItem)
        changeString = changeString + ';'+str(oldVal) + ';' + str(newVal)
        
        if changeString not in self.changes:
            self.changes.append(changeString)

    def toString(self):
        '''Converts the delta found to string output
        
        Returns:
                string of the delta recorded
        
        '''
        deltaString = ''
        
        for change in self.changes:
            deltaString = deltaString + change + '\n'
        
        return deltaString