

class Tag(object):
    def __init__(self, args):
        self.args = args
            
    def render(self):
        return ''

class PairedTag(Tag):
    
    def __init__(self, args):        
        self.children = []
        super(PairedTag, self).__init__(args)

    def render(self):        
        char_buffer = ''
        for child in self.children:
            char_buffer += child.render()
            
        return char_buffer

class SingleLineTag(Tag):
    pass

class TemplateContentTag(PairedTag):
    pass

class LiteralContent(Tag):
    def __init__(self, content):
        self.content = content
    
    def render(self):
        return self.content

class EscapedContentTag(Tag):    
    def render(self):
        return '<b>escaped</b> (' + ''.join(self.args) + ')'
    
class UnescapedContentTag(Tag):
    def render(self):
        return '<b>unescaped</b> (' + ''.join(self.args) + ')'

class IfTag(PairedTag):
    closing_literal = 'if'
    
    def render(self):
        print ' '.join(self.args)
                
        char_buffer = ''
        for child in self.children:
            char_buffer += child.render()
            
        return char_buffer

TagMap = {
    'render' : EscapedContentTag,
    ':' : EscapedContentTag,
    '>' : UnescapedContentTag,
    'if' : IfTag
}
