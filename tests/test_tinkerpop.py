'''
Created on 2020-04-20

@author: wf
'''
import unittest
import os
import getpass
from tp.gremlin import RemoteGremlin
from pathlib import Path

class TestPyJanusGraph(unittest.TestCase):
    '''
    pyunit test cases for pyjanusgraph
    '''

    def setUp(self):
        '''
        setUp the environment for the test
        '''
        # uncomment if you'd like to debug parts of the tests
        RemoteGremlin.debug=True
        # default server for janusgraph instance
        self.gremlinserver="localhost"
        # default sharepoint 
        self.sharepoint=str(Path.home())+"/graphdata/"
        # developer's environment
        # adapt to your own username and needs
        if getpass.getuser()=="wf":
            self.gremlinserver="capri.bitplan.com"
            self.sharepoint="/Volumes/bitplan/user/wf/graphdata/"
        # open the remote gremlin connection and set up the share point    
        self.rg = RemoteGremlin(self.gremlinserver)
        self.rg.open()
        self.rg.setSharepoint(self.sharepoint, "/graphdata/")
        pass


    def tearDown(self):
        '''
        after finishing close the remote connection
        '''
        self.rg.close()
        pass

    
    def testJanusGraph(self):
        '''
        test communication to janus Graph
        '''
        self.rg.clean()
        # we have a traversal now
        # assert isinstance(gV,GraphTraversal)
        # convert it to a list to get the actual vertices
        vList = self.rg.g.V().toList()
        print (len(vList))
        assert len(vList) == 0
        pass
    
    def test_loadGraph(self):
        '''
        test loading a graph ml database
        '''
        self.rg.clean()
        g = self.rg.g
        graphmlFile = "air-routes-small.xml";
        for path in [".","tests"]:
            graphmlPath=path+"/"+graphmlFile
            if os.path.isfile(graphmlPath):
                shared = self.rg.share(graphmlPath)
        # read the content from the air routes example
        g.io(shared).read().iterate()
        vCount = g.V().count().next()
        print ("%s has %d vertices" % (shared, vCount))
        assert vCount == 47


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()