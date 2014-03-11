import parsers
import tokenizer
import context


html_escape_table = {
    "&": "&amp;",
    '"': "&quot;",
    "'": "&apos;",
    ">": "&gt;",
    "<": "&lt;",
    }

def html_escape(text):
    """Produce entities within text."""
    return "".join(html_escape_table.get(c,c) for c in unicode(text))

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
        return unicode(self.content)

#tags should support expressions, like #index+1
class EscapedContentTag(Tag):
    def render(self, context):
        ct = tokenizer.ExpressionTokenizer()
        parser = parsers.TopDownParser(ct.yield_tokens(' '.join(self.args)))
        return html_escape(parser.parse().eval(context))
    
#tags should support expressions, like index+1
class UnescapedContentTag(Tag):
    def render(self, context):     
        ct = tokenizer.ExpressionTokenizer()
        parser = parsers.TopDownParser(ct.yield_tokens(' '.join(self.args)))   
        return unicode(parser.parse().eval(context))

class CommentTag(Tag):
    def render(self, context):
        return ''

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

class ForTag(PairedTag):
    closing_literal = 'for'
    
    def render(self, var_context):
        if len(self.args) <> 3:
            raise Exception('The for tag takes exactly three arguments following the pattern instance_var in iterable')
        
        for_child_tags = []
        else_child_tags = []
        
        in_else_tag = False        
        for child in self.children:
            if in_else_tag:
                else_child_tags.append(child)
            else:
                for_child_tags.append(child)
            
            if type(child) == ElseTag:
                in_else_tag = True
                
        
        class_var = self.args[0]
        iterable = var_context.eval(self.args[2])
        
        retval = ''
        cnt = 0
        if iterable and len(iterable):
            for item in iterable:
                #add the current class var in the context dictionary for all children.  it could
                #overlay something already existing, but that's fine.
                local_context = context.ContextWrap(var_context.context, { class_var: item, '#index' : cnt })
                cnt+=1
                for child in for_child_tags:
                    retval += child.render(local_context)
        else:           
            for child in else_child_tags:
                retval += child.render(var_context)
                    
        return retval

class VerbatimTag(PairedTag):
    closing_literal = 'verbatim'    

TagMap = {
    'render' : EscapedContentTag,
    ':' : EscapedContentTag,
    '>' : UnescapedContentTag,
    '#' : CommentTag,
    'if' : IfTag,
    'else' : ElseTag,
    'elif' : ElseTag,
    'verbatim' : VerbatimTag,
    'for' : ForTag,
}
