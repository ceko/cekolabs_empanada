import parsers
import tokenizer
import cgi


html_escape_table = {
    "&": "&amp;",
    '"': "&quot;",
    "'": "&apos;",
    ">": "&gt;",
    "<": "&lt;",
    }

def html_escape(text):
    """Produce entities within text."""
    return "".join(html_escape_table.get(c,c) for c in str(text))

class Tag(object):
    def __init__(self, args):
        self.args = args
            
    def render(self, context):
        return ''

class PairedTag(Tag):
    
    def __init__(self, args):        
        self.children = []
        super(PairedTag, self).__init__(args)

    def render(self, context):        
        char_buffer = ''
        for child in self.children:
            char_buffer += unicode(child.render(context))
            
        return char_buffer

class SingleLineTag(Tag):
    pass

class TemplateContentTag(PairedTag):
    pass

class LiteralContent(Tag):
    def __init__(self, content):
        self.content = content
    
    def render(self, context):
        return self.content

class EscapedContentTag(Tag):
    def render(self, context):
        return html_escape(context.eval(' '.join(self.args)))
    
class UnescapedContentTag(Tag):
    def render(self, context):
        return context.eval(' '.join(self.args))

class IfTag(PairedTag):
    closing_literal = 'if'
    
    def render(self, context):
        #if tag can have an else tag too, so we need to first check for that.
        #this is a stack of groups to evaluate in order
        expression_groups = []
        current_group = []
        current_group_conditional = self
        
        for child in self.children:
            if type(child) == ElseTag:
                expression_groups.append((current_group_conditional, current_group))
                current_group_conditional = child
                current_group = []
            else:
                current_group.append(child)
                
        expression_groups.append((current_group_conditional, current_group))
        
        retval = ''                
        for conditional, tag_group in expression_groups:            
            ct = tokenizer.ExpressionTokenizer()
            parser = parsers.TopDownParser(ct.yield_tokens(' '.join(conditional.args)))
            if len(parser.tokens):
                if parser.parse().eval(context):
                    for tag in tag_group:
                        retval += unicode(tag.render(context))
                    break
            else:
                for tag in tag_group:
                    retval += unicode(tag.render(context))
                break
                                    
        return retval

class ElseTag(Tag):
    
    def render(self, context):
        raise Exception("Cannot call render directly on else tag")

TagMap = {
    'render' : EscapedContentTag,
    ':' : EscapedContentTag,
    '>' : UnescapedContentTag,
    'if' : IfTag,
    'else' : ElseTag,
    'elif' : ElseTag,
}
