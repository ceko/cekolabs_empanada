

class EscapedContentTag(object):    
    def render(self, *args):
        return '<b>escaped</b> (' + ''.join(*args) + ')'
    
class UnescapedContentTag(object):
    def render(self, *args):
        return '<b>unescaped</b> (' + ''.join(*args) + ')'

class IfTag(object):
    def render(self, *args):
        return 'if tag'

TagMap = {
    'render' : EscapedContentTag,
    ':' : EscapedContentTag,
    '>' : UnescapedContentTag,
    'if' : IfTag
}
