from twisted.web import resource


class GetJSON(resource.Resource):

    def __init__(self):
        resource.Resource.__init__(self)

    def render(self, request):
        return 'hi'


class RootResource(resource.Resource):

    def __init__(self):
        resource.Resource.__init__(self)
        self.putChild('get-json', GetJSON())
