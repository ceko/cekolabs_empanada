import collections
import tags


class TemplateTokens:
    TAG_OPEN_START = 1
    TAG_OPEN_CONTENT = 2    
    TAG_OPEN_END = 4
    TAG_CLOSE_START = 5
    TAG_CLOSE_CONTENT = 6
    TAG_CLOSE_END = 7
    RAW_STRING = 100

class OperatorTokens:
    GREATER_THAN = 1
    LESS_THAN = 2
    EQUAL_TO = 3
    GREATER_THAN_OR_EQUAL_TO = 4
    LESS_THAN_OR_EQUAL_TO = 5
    AND = 5
    OR = 6    
    NOT_EQUALS = 7
    IN = 8
    NOT = 9
    NOT_IN = 10
    ADDITION = 11
    SUBTRACTION = 12
    MULTIPLICATION = 13
    DIVISION = 14
    NEGATION = 15
    NULL = 16
    #this is a string or numeric literal or
    #a dot-notation lookup
    #examples: 
    #  "orange"
    #  fruit.name
    #  142    
    LITERAL = 100

    @staticmethod
    def as_token(operator):
        ret_dict = {
            '>': OperatorTokens.GREATER_THAN,
            '<': OperatorTokens.LESS_THAN,
            '=': OperatorTokens.EQUAL_TO,
            '==': OperatorTokens.EQUAL_TO,
            '>=': OperatorTokens.GREATER_THAN_OR_EQUAL_TO,
            '<=': OperatorTokens.LESS_THAN_OR_EQUAL_TO,
            'and': OperatorTokens.AND,
            'or': OperatorTokens.OR,
            '!=': OperatorTokens.NOT_EQUALS,
            '<>': OperatorTokens.NOT_EQUALS,
            'in': OperatorTokens.IN,
            'not': OperatorTokens.NOT,
            'not in': OperatorTokens.NOT_IN,
            '+': OperatorTokens.ADDITION,
            '-': OperatorTokens.SUBTRACTION,
            'neg': OperatorTokens.NEGATION,
            'null': OperatorTokens.NULL,
            '*': OperatorTokens.MULTIPLICATION,
            '/': OperatorTokens.DIVISION
        }

        return ret_dict[operator.lower()]

class ReservedCharacters:    
    TAG_OPEN = '{{'
    TAG_CLOSE = '}}'
    TAG_MATCH_SYMBOL = '/'
    TAG_ARGUMENTS_DELIMITER = ' '
    
class StringIterator(collections.Iterator):    
    
    def __init__(self, string):
        self.string = string or ''
        self.pos = 0
        self.in_quoted_content = False
        self.quote_char = None
        self.tracking_quotes = False
        
    @property
    def in_quoted_content(self):
        return self._in_quoted_content
    
    @in_quoted_content.setter
    def in_quoted_content(self, value):    
        self._in_quoted_content = value
    
    @property
    def tracking_quotes(self):
        return self._tracking_quotes
    
    @tracking_quotes.setter
    def tracking_quotes(self, value):
        self._tracking_quotes = False
        
    def peekahead(self, extra=0, never_null = False):        
        if len(self.string) > self.pos+extra:
            return self.string[self.pos:self.pos+extra+1]
        elif never_null:
            return ''
    
    def advance(self, steps):
        for step in xrange(steps):
            self.next()
    
    def next(self):
        if len(self.string) > self.pos:
            self.pos += 1                 
            if self.in_quoted_content:
                #this doesn't handle escaped backslashes, but that's fine for this simple exercise.
                if self.string[self.pos-1] == self.quote_char and self.string[self.pos-1] <> '\\':
                    self.in_quoted_content = False
            else:
                if self.tracking_quotes and self.string[self.pos-1] in ['"', "'"]:                    
                    self.in_quoted_content = True
                    self.quote_char = self.string[self.pos-1]                   
                    
            return self.string[self.pos-1]
        else:
            raise StopIteration

class TagGraph(object):
    
    def __init__(self, tokens):
        self.tokens = tokens
            
    class TagGraphBuilder(object):
        
        def __init__(self, tokens):
            self.tokens = tokens
            self.current_tag = tags.TemplateContentTag([])        
            self.graph = [self.current_tag]    
            self.tag_stack = [self.current_tag]
            self.token_processors = {
                TemplateTokens.RAW_STRING: self.process_raw_string,
                TemplateTokens.TAG_OPEN_START: self.process_tag_open_start,
                TemplateTokens.TAG_OPEN_CONTENT: self.process_tag_open_content,
                TemplateTokens.TAG_OPEN_END: self.process_tag_open_end,
                TemplateTokens.TAG_CLOSE_START: self.process_tag_close_start,
                TemplateTokens.TAG_CLOSE_CONTENT: self.process_tag_close_content,
                TemplateTokens.TAG_CLOSE_END: self.process_tag_close_end,
            }
        
        def graph_tags(self):
            for token in self.tokens:
                processor = self.token_processors.get(token.type, None)
                if processor:
                    processor(token)
            
            return self.graph
            
        def process_raw_string(self, token):
            self.current_tag.children.append(tags.LiteralContent(token.value))
        
        def process_tag_open_start(self, token):
            pass
        
        def process_tag_open_content(self, token):
            #Tags have two parts, a method and optional arguments.  The method is either 
            #separated by arguments by a string (like to_lower) or it's a shortcut 
            #non-alpha string of characters, like : or > 
                                            
            method_buffer = ''
            method = None        
            argument_buffer = ''
            arguments = []
            string_iterator = StringIterator(token.value.strip())
            string_iterator.tracking_quotes = True
            for character in string_iterator:
                if not method:
                    method_buffer += character
                    
                    if not character.isalpha() and not character in ['_', '-']:
                        method = method_buffer.strip()
                else:                
                    if character == ' ' and not string_iterator.in_quoted_content:
                        if len(argument_buffer.strip()):
                            arguments.append(argument_buffer.strip())
                        argument_buffer = ''
                    else:
                        argument_buffer += character
    
            if not method:
                method = method_buffer
    
            if len(argument_buffer.strip()):
                arguments.append(argument_buffer.strip())                    
            
            tag_class = tags.TagMap.get(method, None)                        
            if not tag_class:    
                raise Exception("Tag not found: " + method)
                                    
            tag = tag_class(arguments)
            self.current_tag.children.append(tag)
            
            if issubclass(tag_class, tags.PairedTag):                
                self.current_tag = tag
                self.tag_stack.append(tag)
            
            string_iterator.tracking_quotes = False
                    
        def process_tag_open_end(self, token):
            pass
        
        def process_tag_close_start(self, token):
            pass
        
        def process_tag_close_content(self, token):
            tag_method = token.value.strip()
            if type(self.current_tag).closing_literal == tag_method:
                self.tag_stack.pop()
                self.current_tag = self.tag_stack[-1]
            else:                
                raise Exception("Closing " + tag_method + " found for " + str(self.current_tag))
        
        def process_tag_close_end(self, token):
            pass
            
    def get_tags(self):
        return TagGraph.TagGraphBuilder(self.tokens).graph_tags()
    
class Token(object):
    
    def __init__(self, type, value):
        self.type = type
        self.value = value

class ExpressionTokenizer(object):
    
    NO_MATCH = 0
    PARTIAL_OPERATOR_MATCH = 1
    FULL_OPERATOR_MATCH = 2
    OPERATORS = ['<', '<=', '>', '>=', '=', '==', '!', '!=', '<>', '-', '+', '*', '/']
    
    def __init__(self):
        self.operator_match_buffer = ''
    
    def yield_tokens(self, expression):
        expression = expression or ""
                
        string_iterator = StringIterator(expression)        
        cur_literal = ''
        last_token = None
        
        for character in string_iterator:            
            if string_iterator.in_quoted_content:
                cur_literal += character
            else:
                match_state, operator = self.operator_match_state(string_iterator, character)
                if operator and match_state == ExpressionTokenizer.FULL_OPERATOR_MATCH:
                    if len(cur_literal.strip()):                        
                        last_token = Token(OperatorTokens.LITERAL, cur_literal)
                        yield last_token
                                                            
                    retval = Token(OperatorTokens.as_token(operator), operator)
                    #if the last token wasn't a literal, then this is negating a literal or it's just incorrect                    
                    if retval.type == OperatorTokens.SUBTRACTION and (not last_token or last_token.type <> OperatorTokens.LITERAL):                        
                        retval = Token(OperatorTokens.NEGATION, 'neg')
                    elif retval.type == OperatorTokens.ADDITION and (not last_token or last_token.type <> OperatorTokens.LITERAL):                        
                        retval = Token(OperatorTokens.NEGATION, 'null') 
                    last_token = retval
                    
                    yield last_token                    
                    cur_literal = ''
                elif match_state <> ExpressionTokenizer.PARTIAL_OPERATOR_MATCH:
                    cur_literal += character
        
        if len(cur_literal):  
            yield Token(OperatorTokens.LITERAL, cur_literal)
          
    def operator_match_state(self, string_iterator, character):
        evaluating_string = character
        if len(self.operator_match_buffer):
            evaluating_string = self.operator_match_buffer + character
        
        if evaluating_string in ExpressionTokenizer.OPERATORS:
            self.operator_match_buffer += character
        elif character == ' ' or string_iterator.pos == 1:
            reset_iterator = string_iterator.pos == 1
            if reset_iterator:
                string_iterator.pos = 0
                                            
            #special case for operators that need to be separated by whitespace, like 'and' and 'or'
            retval = None            
            if string_iterator.peekahead(extra=3, never_null=True).lower() == 'and ':
                retval = 'and'                
            elif string_iterator.peekahead(extra=2, never_null=True).lower() == 'or ':
                retval = 'or'
            elif string_iterator.peekahead(extra=2, never_null=True).lower() == 'in ':
                retval = 'in'
            elif string_iterator.peekahead(extra=6, never_null=True).lower() == 'not in ':
                retval = 'not in'
            elif string_iterator.peekahead(extra=3, never_null=True).lower() == 'not ':
                retval = 'not'
        
            if retval:
                string_iterator.advance(len(retval))
                self.operator_match_buffer = ''
                return (ExpressionTokenizer.FULL_OPERATOR_MATCH, retval)
            elif reset_iterator:
                string_iterator.pos = 1            
        
        if len(self.operator_match_buffer):
            #look ahead to see if this operator is done matching
            if self.operator_match_buffer + string_iterator.peekahead() in ExpressionTokenizer.OPERATORS:
                return (ExpressionTokenizer.PARTIAL_OPERATOR_MATCH, self.operator_match_buffer)
            else:
                retval = self.operator_match_buffer
                self.operator_match_buffer = ''
                return (ExpressionTokenizer.FULL_OPERATOR_MATCH, retval)
        
        return (ExpressionTokenizer.NO_MATCH, None)
        
class TemplateTokenizer(object):
        
    def yield_tokens(self, template):
        template = template or ""
                
        cur_token = TemplateTokens.RAW_STRING
        cur_token_content = ''
        tag_in_quoted_content = False
        
        string_iterator = StringIterator(template)
        
        #tag open may look like {{
        def tag_open_start_match():                                       
            return len(cur_token_content) > 1 \
                and cur_token_content[-2:] == ReservedCharacters.TAG_OPEN \
                and string_iterator.peekahead() <> ReservedCharacters.TAG_MATCH_SYMBOL                            
        
        #tag open close may look like }}
        def tag_end_match():
            return len(cur_token_content) > 1 and cur_token_content[-2:] == ReservedCharacters.TAG_CLOSE
                    
        #tag close start may look like {{/         
        def tag_close_start_match():
            return len(cur_token_content) > 2 \
                and cur_token_content[-3:-1] == ReservedCharacters.TAG_OPEN \
                and cur_token_content[-1] == ReservedCharacters.TAG_MATCH_SYMBOL                
                    
        for character in string_iterator:                                         
            cur_token_content += character
                
            if cur_token == TemplateTokens.RAW_STRING:                
                if tag_open_start_match():                    
                    yield Token(TemplateTokens.RAW_STRING, cur_token_content[:-2])
                    yield Token(TemplateTokens.TAG_OPEN_START, ReservedCharacters.TAG_OPEN)
                    
                    cur_token = TemplateTokens.TAG_OPEN_CONTENT
                    cur_token_content = ''
                elif tag_close_start_match():
                    yield Token(cur_token, cur_token_content[:-3])
                    yield Token(TemplateTokens.TAG_CLOSE_START, ReservedCharacters.TAG_OPEN + ReservedCharacters.TAG_MATCH_SYMBOL)
                    
                    cur_token = TemplateTokens.TAG_CLOSE_CONTENT
                    cur_token_content = ''
                    
            elif cur_token in [TemplateTokens.TAG_OPEN_CONTENT, TemplateTokens.TAG_CLOSE_CONTENT]:
                if string_iterator.in_quoted_content:
                    continue                 
                
                if tag_end_match():
                    if cur_token == TemplateTokens.TAG_OPEN_CONTENT:
                        yield Token(cur_token, cur_token_content[:-2])
                        yield Token(TemplateTokens.TAG_OPEN_END, ReservedCharacters.TAG_CLOSE)
                    else:
                        yield Token(cur_token, cur_token_content[:-2])
                        yield Token(TemplateTokens.TAG_CLOSE_END, ReservedCharacters.TAG_CLOSE)
                   
                    cur_token = TemplateTokens.RAW_STRING
                    cur_token_content = ''
        
        yield Token(TemplateTokens.RAW_STRING, cur_token_content)            
                    