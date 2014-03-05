from context import ContextWrap


class TagRenderer(object):
    
    def __init__(self, context):
        self.context = ContextWrap(context)
        self.char_buffer = ''
        self.last_token = None
        self.last_tag= None
    
    def render(self, tags):
        
        for tag in tags:
            #better way to do this?
            self.char_buffer += tag.render(self.context)
                        
        return self.char_buffer
    