from prototypeclient.openstack.common.apiclient import base

class Sample(base.Resource):
    pass

class SampleManager(base.BaseManager):
    resource_class = Sample

    def debug_obj(self):
        body = self._get('debug')
        return body

    def debug(self):
        body = self.client.get('debug')
        # raw
        content = body.content
        # text
        text = body.text
        # json
        json = body.json()
        return content
    
    def list(self, **kwargs):
        pass