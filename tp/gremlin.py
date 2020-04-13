'''
Created on 2020-03-30

@author: wf
'''
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.structure.graph import Graph
from shutil import copyfile
import os
import csv

class RemoteGremlin(object):
    '''
    helper for remote gremlin connections
    '''
    debug=False

    def __init__(self, server, port=8182):
        '''
        construct me with the given server and port
        '''
        self.server=server
        self.port=port    
        
    def sharepoint(self,sharepoint,sharepath):
        '''
        set up the sharepoint
        '''
        self.sharepoint=sharepoint
        self.sharepath=sharepath
        
        
    def share(self,file):
        '''
        share the given file  and return the path as seen by the server
        '''
        fbase=os.path.basename(file)
        target=self.sharepoint+fbase
        if RemoteGremlin.debug:
            print("copying %s to %s" % (file,target))
        copyfile(file,target)
        return self.sharepath+fbase
            
    def open(self):
        '''
        open the remote connection
        '''
        self.graph = Graph()
        self.url='ws://%s:%s/gremlin' % (self.server,self.port)
        self.connection = DriverRemoteConnection(self.url, 'g')    
        # The connection should be closed on shut down to close open connections with connection.close()
        self.g = self.graph.traversal().withRemote(self.connection)

    def close(self):
        '''
        close the remote connection
        '''
        self.connection.close()    
        
        
    def clean(self):    
        '''
        clean the graph database by removing all  vertices
        '''
        # drop the existing content of the graph
        self.g.V().drop().iterate()    
        
class TinkerPopAble(object):
    '''
    mixin for classes to store and retrieve from tinkerpop graph database
    '''
    debug=False
    
    def storeFields(self,fieldList):
        '''
        define the fields to be stored as tinkerpop vertice properties
        '''
        if not hasattr(self,'tpfields'):
            self.tpfields={}
        fields=vars(self)
        for field in fieldList:
            self.tpfields[field]=fields[field]
    
    def toVertex(self,g):
        '''
        create a vertex from me
        '''
        label=type(self).__name__;
        t=g.addV(label)
        if TinkerPopAble.debug:
            print(label)
        tpfields=TinkerPopAble.fields(self)
        for name,value in tpfields.items():
            if TinkerPopAble.debug:
                print("\t%s=%s" % (name,value))
            if value is not None:    
                t=t.property(name,value)
        t.iterate()    
        
    def fromMap(self,pMap):
        '''
        fill my attributes from the given pMap dict
        '''
        for name,value in pMap.items():
            self.__setattr__(name, value[0])    #
            
    @staticmethod
    def fields(instance):     
        # if there is a pre selection of fields store only these
        if hasattr(instance,'tpfields'):
            tpfields=instance.tpfields    
        else:
            # else use all fields
            tpfields=vars(instance)
        return tpfields       
            
    @staticmethod
    def writeCSV(csvfileName,objectList,fieldnames=None):
        if fieldnames is None:
            if len(objectList)<1:
                raise("writCSV needs at least one object in ObjectList when fieldnames are not specified")
            headerInstance=objectList[0]
            fieldnames=TinkerPopAble.fields(headerInstance).keys()
        with open(csvfileName, 'w', newline='') as csvfile: 
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for instance in objectList:
                rowdict={}
                for fieldname in fieldnames:
                    fields=TinkerPopAble.fields(instance)
                    rowdict[fieldname]=fields[fieldname]
                writer.writerow(rowdict)    
            
    @staticmethod        
    def cache(rg,gfile,clazz,objectList,initFunction):
        '''
        generic save
        '''
        g=rg.g
        cachefile=rg.sharepoint+gfile
        clazzname=clazz.__name__
        if os.path.isfile(cachefile):
            g.io(rg.sharepath+gfile).read().iterate()
            for pMap in g.V().hasLabel(clazzname).valueMap().toList():
                if TinkerPopAble.debug:
                    print (pMap)
                instance=clazz.ofMap(pMap)
                objectList.append(instance)
                if TinkerPopAble.debug:
                    print (instance)
        else:
            initFunction()
            for instance in objectList:
                if TinkerPopAble.debug:
                    print(instance)
                instance.toVertex(g)
            g.io(rg.sharepath+gfile).write().iterate()
        return cachefile
    