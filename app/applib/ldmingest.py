from applib import ldmbridge
from twisted.python import log
from twisted.internet import reactor
from applib import rtstats


class RTStatsIngestor(ldmbridge.LDMProductReceiver):
    def connectionLost(self, reason):
        ''' Called when the STDIN connection is lost '''
        log.msg('connectionLost')
        log.err(reason)
        reactor.callLater(15, reactor.callWhenRunning, reactor.stop)

    def process_data(self, raw):
        ''' Process a chunk of data '''
        df = self.dbpool.runInteraction(rtstats.parser, raw)
        df.addErrback(log.err)
