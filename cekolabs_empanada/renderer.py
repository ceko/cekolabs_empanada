from tokenizer import Tokens, StringIterator
import tags

class TagRenderer(object):
    
    def __init__(self):
        self.char_buffer = ''
        self.last_token = None
        self.last_tag= None
    
    def render(self, tags):
        
        for tag in tags:
            #better way to do this?
            self.char_buffer += tag.render()
                        
        return self.char_buffer
    