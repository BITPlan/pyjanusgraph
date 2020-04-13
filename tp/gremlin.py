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
    
    :ivar server: the server to connect to
    :ivar port: the port to connect to
    :ivar sharepoint: the directory that is the shared with the janusgraph instance e.g. via a docker bind/mount or volume
    :ivar sharepath: the path o the sharepoint as seens by the janusgraph server
    '''
    debug=False

    def __init__(self, server='localhost', port=8182):
        '''
        construct me with the given server and port
        Args:
           server(str): the server to use
           port(int): the port to use
        '''
        self.server=server
        self.port=port    
        
    def setSharepoint(self,sharepoint,sharepath):
        '''
        set up a sharepoint
        Args:
           sharepoint(str): the directory that is the shared with the janusgraph instance e.g. via a docker bind/mount or volume
           sharepath(str): the path o the sharepoint as seens by the janusgraph server
        '''
        self.sharepoint=sharepoint
        self.sharepath=sharepath
        
    def share(self,file):
        '''
        share the given file  and return the path as seen by the server
        
        Args:
           file(str): path to the file to share
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
        
        Returns:
           GraphTraversalSource: the remote graph traversal source
        '''
        self.graph = Graph()
        self.url='ws://%s:%s/gremlin' % (self.server,self.port)
        self.connection = DriverRemoteConnection(self.url, 'g')    
        # The connection should be closed on shut down to close open connections with connection.close()
        self.g = self.graph.traversal().withRemote(self.connection)
        return self.g

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
        
        Args:
           fieldList(list): list of fields to be stored
        '''
        if not hasattr(self,'tpfields'):
            self.tpfields={}
        fields=vars(self)
        for field in fieldList:
            self.tpfields[field]=fields[field]
    
    def toVertex(self,g):
        '''
        create a vertex from me
        
        Args:
           g(GraphTraversalSource): where to add me as a vertex
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
        
        Args:
           pmap(dict): the dict to fill my attributes from
        '''
        for name,value in pMap.items():
            self.__setattr__(name, value[0])    #
            
    @staticmethod
    def fields(instance):     
        '''
        Returns:
           dict: either the vars of the instance or the fields specified by the tpfields attribute
        '''
        # if there is a pre selection of fields store only these
        if hasattr(instance,'tpfields'):
            tpfields=instance.tpfields    
        else:
            # else use all fields
            tpfields=vars(instance)
        return tpfields       
            
    @staticmethod
    def writeCSV(csvfileName,objectList,fieldnames=None):
        '''
        write the given objectList to a CSV file
         
        Args:
           csvfileName(str): the path for the CSV File to write to
           objectList(list): a list of instances for which CSV lines should be created
           fieldnames(list): an optional list of fieldnames - if set to None the fields will be derived from the first instance in the objectList
        '''
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
        generic caching
        
        Args:
           gfile(str): the graph storage file 
           clazz(class): the class of the objects in the objectList
           objectList(list): a list of instances to fill or read
           initFunction(function): a function to call to fill the cache
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
    