import context, parsers, renderer, tags, tokenizer


def render(template_path, context):
    template = open(template_path).read()
            
    t = tokenizer.TemplateTokenizer()
    tag_graph = tokenizer.TagGraph(t.yield_tokens(template))
    tags = tag_graph.get_tags()
    r = renderer.TagRenderer(context)
    
    return r.render(tags)