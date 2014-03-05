

class ContextWrap(object):
    
    def __init__(self, context):
        self.context = context
        
    def eval(self, expression):
        #supports string literals, numbers and object lookups
        retval = None
        
        if not expression is None:
            if type(expression) == unicode or type(expression) == str:
                expression = expression.strip()
                #if it starts with a quote it's a string literal
                if expression.startswith('"') or expression.startswith("'"):                
                    retval = unicode(expression[1:-1])
                else:
                    try:
                        # Code borrowed from Django                        
                        retval = float(expression)
            
                        # So it's a float... is it an int? If the original value contained a
                        # dot or an "e" then it was a float, not an int.
                        if '.' not in expression and 'e' not in expression.lower():
                            retval = int(expression)
            
                        # "2." is invalid
                        if expression.endswith('.'):
                            raise ValueError

                    except ValueError:
                        #do a dot-lookup against the dictionary
                        retval = self.lookup(expression)                        
            else:
                import pdb;pdb.set_trace()
                retval = expression
                        
        return retval
            
    def lookup(self, path):
        cur_context = self.context
        for segment in path.split('.'):
            if segment.endswith('()'):
                segment = segment[:-2]
                
            try:
                cur_context = cur_context[segment]
            except (TypeError, KeyError):                
                cur_context = getattr(cur_context, segment)
            
            if hasattr(cur_context, '__call__'):
                cur_context = cur_context()
            
        return cur_context