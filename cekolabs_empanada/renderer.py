from tokenizer import Tokens, StringIterator
import tags

class TokenRenderer(object):
    
    def __init__(self):
        self.char_buffer = ''
        self.last_token = None
        self.last_tag= None
    
    def render(self, tokens):                
        token_processors = {
            Tokens.RAW_STRING: self.process_raw_string,
            Tokens.TAG_OPEN_START: self.process_tag_open_start,
            Tokens.TAG_OPEN_CONTENT: self.process_tag_open_content,
            Tokens.TAG_OPEN_END: self.process_tag_open_end,
            Tokens.TAG_CLOSE_START: self.process_tag_close_start,
            Tokens.TAG_CLOSE_CONTENT: self.process_tag_close_content,
            Tokens.TAG_CLOSE_END: self.process_tag_close_end,
        }
        
        for token in tokens:
            processor = token_processors.get(token.type, None)
            if processor:
                processor(token)
                
            self.last_token = token
    
        return self.char_buffer
    
    def process_raw_string(self, token):
        self.char_buffer += token.value
        
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
                
        tag = tag_class()
        self.char_buffer += tag.render(arguments) 
        
    def process_tag_open_end(self, token):
        pass
    
    def process_tag_close_start(self, token):
        pass
    
    def process_tag_close_content(self, token):
        #clear last tag
        self.char_buffer += '[close:<b>tag content: ' + token.value + '</b>]'
        
    def process_tag_close_end(self, token):
        pass
    
    
    