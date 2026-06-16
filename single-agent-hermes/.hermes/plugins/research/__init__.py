from . import schemas, tools


def register(ctx):
    ctx.register_tool(
        name="save_note",
        toolset="research",
        schema=schemas.SAVE_NOTE,
        handler=tools.save_note,
    )
