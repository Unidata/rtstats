# twisted imports
from twisted.internet import stdio
from twisted.protocols import basic


class LDMProductReceiver(basic.LineReceiver):
    product_end = '\n'

    def __init__(self):
        self.productBuffer = ""
        self.setRawMode()
        self.cbFunc = self.process_data

    def rawDataReceived(self, data):
        """ callback for when raw data is received on the stdin buffer, this
        could be a partial product or lots of products """
        # See if we have anything left over from previous iteration
        if self.productBuffer != "":
            data = self.productBuffer + data

        tokens = data.split(self.product_end)
        # If length tokens is 1, then we did not find the splitter
        if len(tokens) == 1:
            # log.msg("Token not found, len data %s" % (len(data),))
            self.productBuffer = data
            return

        # Everything up until the last one can always go...
        for token in tokens[:-1]:
            # log.msg("ldmbridge cb product size: %s" % (len(token),))
            self.cbFunc(token)
        # We have some cruft left over!
        if tokens[-1] != "":
            self.productBuffer = tokens[-1]
        else:
            self.productBuffer = ""

    def connectionLost(self, reason):
        raise NotImplementedError

    def process_data(self, data):
        raise NotImplementedError

    def lineReceived(self, line):
        ''' needless override to make pylint happy '''
        pass


class LDMProductFactory(stdio.StandardIO):

    def __init__(self, protocol, **kwargs):
        """ constructor with a protocol instance """
        stdio.StandardIO.__init__(self, protocol, **kwargs)
