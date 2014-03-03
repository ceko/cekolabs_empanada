import collections
import tags


class Tokens:
    TAG_OPEN_START = 1
    TAG_OPEN_CONTENT = 2    
    TAG_OPEN_END = 4
    TAG_CLOSE_START = 5
    TAG_CLOSE_CONTENT = 6
    TAG_CLOSE_END = 7
    RAW_STRING = 8

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
        
    @property
    def in_quoted_content(self):
        return self._in_quoted_content
    
    @in_quoted_content.setter
    def in_quoted_content(self, value):    
        self._in_quoted_content = value
        
    def peekahead(self):
        if len(self.string) > self.pos:
            return self.string[self.pos]
    
    def next(self):                
        if len(self.string) > self.pos:
            self.pos += 1                 
            if self.in_quoted_content:
                if self.string[self.pos-1] == self.quote_char and self.string[self.pos-1] <> '\\':
                    self.in_quoted_content = False
            else:
                if self.string[self.pos-1] in ['"', "'"]:
                    print 'in quoted content'
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
                Tokens.RAW_STRING: self.process_raw_string,
                Tokens.TAG_OPEN_START: self.process_tag_open_start,
                Tokens.TAG_OPEN_CONTENT: self.process_tag_open_content,
                Tokens.TAG_OPEN_END: self.process_tag_open_end,
                Tokens.TAG_CLOSE_START: self.process_tag_close_start,
                Tokens.TAG_CLOSE_CONTENT: self.process_tag_close_content,
                Tokens.TAG_CLOSE_END: self.process_tag_close_end,
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
    
class Tokenizer(object):
        
    def yield_tokens(self, template):        
        template = template or ""
                
        cur_token = Tokens.RAW_STRING
        cur_token_content = ''   
        
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
                
            if cur_token == Tokens.RAW_STRING:                
                if tag_open_start_match():                    
                    yield Token(Tokens.RAW_STRING, cur_token_content[:-2])
                    yield Token(Tokens.TAG_OPEN_START, ReservedCharacters.TAG_OPEN)
                    
                    cur_token = Tokens.TAG_OPEN_CONTENT
                    cur_token_content = ''
                elif tag_close_start_match():
                    yield Token(cur_token, cur_token_content[:-3])
                    yield Token(Tokens.TAG_CLOSE_START, ReservedCharacters.TAG_OPEN + ReservedCharacters.TAG_MATCH_SYMBOL)
                    
                    cur_token = Tokens.TAG_CLOSE_CONTENT
                    cur_token_content = ''
                    
            elif cur_token in [Tokens.TAG_OPEN_CONTENT, Tokens.TAG_CLOSE_CONTENT]:
                if string_iterator.in_quoted_content:
                    continue                 
                
                if tag_end_match():
                    if cur_token == Tokens.TAG_OPEN_CONTENT:
                        yield Token(cur_token, cur_token_content[:-2])
                        yield Token(Tokens.TAG_OPEN_END, ReservedCharacters.TAG_CLOSE)
                    else:
                        yield Token(cur_token, cur_token_content[:-2])
                        yield Token(Tokens.TAG_CLOSE_END, ReservedCharacters.TAG_CLOSE)
                   
                    cur_token = Tokens.RAW_STRING
                    cur_token_content = ''
                    
                    