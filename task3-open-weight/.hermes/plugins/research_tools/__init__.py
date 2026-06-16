from . import schemas, tools


def register(ctx):
    ctx.register_tool(name="save_article", toolset="research_tools", schema=schemas.SAVE_ARTICLE, handler=tools.save_article)
