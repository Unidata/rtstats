"""Simple templating"""
import os


class MyView(object):

    def __init__(self):
        self.vars = dict()

    def render(self, template):
        fn = "%s/%s" % (os.path.join(os.path.dirname(__file__),
                        "../templates"), template)
        if not os.path.isfile(fn):
            raise Exception("template %s not found!" % (fn,))
        tpl = open(fn).read()
        for key, val in self.vars.iteritems():
            tpl = tpl.replace("<!--%s-->" % (key,), val)
        return tpl
