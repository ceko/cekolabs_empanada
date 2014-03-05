

class TokenBase(object):
    id = None
    value = None
    first = second = None
    
    def nud(self, parser):
        pass
    
    def led(self, left, parser):
        pass
    
    def display(self):
        return self.id
    
    def __repr__(self):
        out = [str(x) for x in [self.id, self.first, self.second] if x is not None]
        return "(" + " ".join(out) + ")"

class EndToken(TokenBase):
    lbp = 0
    
    def nud(self, parser):
        raise Exception('Unexpected end of expression in if tag.')

EndToken = EndToken()

def infix(bp, func):
    """
    Creates an infix operator, given a binding power and a function that
    evaluates the node
    """
    class Operator(TokenBase):
        lbp = bp

        def led(self, left, parser):
            self.first = left
            self.second = parser.expression(bp)
            return self

        def eval(self, context):
            #try:                
                return func(context, self.first, self.second)
            #except Exception:
                # Templates shouldn't throw exceptions when rendering.  We are
                # most likely to get exceptions for things like {% if foo in bar
                # %} where 'bar' does not support 'in', so default to False
                #return False

    return Operator


def prefix(bp, func):
    """
    Creates a prefix operator, given a binding power and a function that
    evaluates the node.
    """
    class Operator(TokenBase):
        lbp = bp

        def nud(self, parser):
            self.first = parser.expression(bp)
            self.second = None
            return self

        def eval(self, context):
            #try:
                return func(context, self.first)
            #except Exception:
                return False

    return Operator


# Operator precedence follows Python.
OPERATORS = {
    'or': infix(6, lambda context, x, y: x.eval(context) or y.eval(context)),
    'and': infix(7, lambda context, x, y: x.eval(context) and y.eval(context)),
    'not': prefix(8, lambda context, x: not x.eval(context)),
    '!': prefix(8, lambda context, x: not x.eval(context)),
    'in': infix(9, lambda context, x, y: x.eval(context) in y.eval(context)),
    'not in': infix(9, lambda context, x, y: x.eval(context) not in y.eval(context)),
    '=': infix(10, lambda context, x, y: x.eval(context) == y.eval(context)),
    '==': infix(10, lambda context, x, y: x.eval(context) == y.eval(context)),
    '!=': infix(10, lambda context, x, y: x.eval(context) != y.eval(context)),
    '<>': infix(10, lambda context, x, y: x.eval(context) != y.eval(context)),
    '>': infix(10, lambda context, x, y: x.eval(context) > y.eval(context)),
    '>=': infix(10, lambda context, x, y: x.eval(context) >= y.eval(context)),
    '<': infix(10, lambda context, x, y: x.eval(context) < y.eval(context)),
    '<=': infix(10, lambda context, x, y: x.eval(context) <= y.eval(context)),
    '-': infix(20, lambda context, x, y: x.eval(context) - y.eval(context)),
    '+': infix(20, lambda context, x, y: x.eval(context) + y.eval(context)),
    '*': infix(21, lambda context, x, y: x.eval(context) * y.eval(context)),
    '/': infix(21, lambda context, x, y: x.eval(context) / y.eval(context)),
    'neg': prefix(30, lambda context, x: x.eval(context) * -1),
    #used for things that don't modify anything or are assumed, like +1
    'null': prefix(30, lambda context, x: x.eval(context)), 
}

# Assign 'id' to each:
for key, op in OPERATORS.items():
    op.id = key


class Literal(TokenBase):
    id = "literal"
    lbp = 0

    def __init__(self, value):
        self.value = value

    def display(self):
        return repr(self.value)

    def nud(self, parser):
        return self

    def eval(self, context):        
        return context.eval(self.value)        

    def __repr__(self):
        return "(%s %r)" % (self.id, self.value)
    

class TopDownParser(object):
    
    def __init__(self, tokens):
        mapped_tokens = []
        for token in tokens:
            mapped_tokens.append(self.translate_token(token.value))
        self.tokens = mapped_tokens
        self.pos= 0
        self.current_token = self.next_token()
            
    def translate_token(self, token):
        try:
            op = OPERATORS[token]
        except (KeyError, TypeError):
            return self.create_var(token)
        else:
            return op()
    
    def create_var(self, token):
        return Literal(token)
    
    def next_token(self):
        if self.pos >= len(self.tokens):
            return EndToken
        else:
            retval = self.tokens[self.pos]
            self.pos += 1
            return retval
    
    def parse(self):
        retval = self.expression()
        # Check that we have exhausted all the tokens
        if self.current_token is not EndToken:
            raise self.error_class("Unused '%s' at end of if expression." %
                                   self.current_token.display())
        return retval

    def expression(self, rbp=0):        
        t = self.current_token
        self.current_token = self.next_token()
        left = t.nud(self)
        while rbp < self.current_token.lbp:
            t = self.current_token
            self.current_token = self.next_token()
            left = t.led(left, self)
        return left
    