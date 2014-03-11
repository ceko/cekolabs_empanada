import context, parsers, renderer, tags, tokenizer, codecs


def render(template_path, context):    
    template = codecs.open(template_path, encoding='utf-8').read()
    
    t = tokenizer.TemplateTokenizer()
    tag_graph = tokenizer.TagGraph(t.yield_tokens(template))
    tags = tag_graph.get_tags()
    r = renderer.TagRenderer(context)
    
    return r.render(tags)