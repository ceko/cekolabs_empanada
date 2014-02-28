import collections


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
                    
                    