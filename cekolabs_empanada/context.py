import tokenizer
import parsers
import filters
import ast


class ContextLookupFail(object):
    pass

ContextLookupFail = ContextLookupFail()

class ContextWrap(object):
    
    def __init__(self, context, local_context=None):
        self.context = context
        self.local_context = local_context or {}
        
    def eval(self, expression):
        #supports string literals, numbers and object lookups
        retval = None
        print expression
        #Pipes are reserved characters that imply filters.  Filters are function lookups that do not
        #accept parameters.
        vt = tokenizer.TemplateVariableTokenizer()
        expr_parser = parsers.TemplateVarParser(vt.yield_tokens(expression))
        parsed_expression, expression_filters = expr_parser.parse()
        
        if not parsed_expression is None:
            if type(parsed_expression) == unicode or type(parsed_expression) == str:
                parsed_expression = parsed_expression.strip()
                #if it starts with a quote it's a string literal
                if parsed_expression.startswith('"') or parsed_expression.startswith("'"):                
                    retval = ast.literal_eval('u' + parsed_expression) #wooo this looks so dangerous
                else:
                    try:
                        # Code borrowed from Django                        
                        retval = float(parsed_expression)
            
                        # So it's a float... is it an int? If the original value contained a
                        # dot or an "e" then it was a float, not an int.
                        if '.' not in parsed_expression and 'e' not in parsed_expression.lower():
                            retval = int(parsed_expression)
            
                        # "2." is invalid
                        if parsed_expression.endswith('.'):
                            raise ValueError

                    except ValueError:
                        #do a dot-lookup against the dictionary
                        retval = self.lookup(parsed_expression)                        
            else:                
                retval = parsed_expression
        
        for filter in expression_filters:
            filter_func = filters.FilterMap.get(filter)
            if not filter_func:
                raise Exception('No filter with name ' + filter + ' found')
            retval = filter_func(retval)
                        
        return retval
            
    def lookup(self, path):
        retval = ContextLookupFail        
        if len(self.local_context):
            retval = self._lookup(path, self.local_context)
        
        if retval == ContextLookupFail:
            retval = self._lookup(path, self.context)
    
        if retval == ContextLookupFail:
            return None
        else:
            return retval
    
    def _lookup(self, path, context):        
        cur_context = context        
        for segment in path.split('.'):
            if segment.endswith('()'):
                segment = segment[:-2]                
            try:
                cur_context = cur_context[segment]
            except (TypeError, KeyError):
                try:                
                    cur_context = getattr(cur_context, segment)
                except Exception:
                    return ContextLookupFail
            
            if hasattr(cur_context, '__call__'):
                cur_context = cur_context()
            
        return cur_context
    
    
    
    