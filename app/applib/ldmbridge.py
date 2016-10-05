# twisted imports
from twisted.internet import stdio
from twisted.python import log
from twisted.internet import reactor
from applib import rtstats
from twisted.protocols import basic


class RTStatsIngestor(basic.LineReceiver):
    # default delimiter is \r\n
    delimiter = b'\n'

    def connectionLost(self, reason):
        ''' Called when the STDIN connection is lost '''
        log.msg('connectionLost')
        log.err(reason)
        reactor.callLater(15, reactor.callWhenRunning, reactor.stop)

    def lineReceived(self, line):
        ''' Process a chunk of data '''
        df = self.dbpool.runInteraction(rtstats.parser, line)
        df.addErrback(log.err)


class LDMProductFactory(stdio.StandardIO):

    def __init__(self, protocol, **kwargs):
        """ constructor with a protocol instance """
        stdio.StandardIO.__init__(self, protocol, **kwargs)
