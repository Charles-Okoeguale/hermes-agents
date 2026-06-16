SAVE_NOTE = {
    "name": "save_note",
    "description": (
        "Save a research note to a local markdown file in the notes/ folder. "
        "Use this to record findings, summaries, and source URLs so they persist "
        "after the conversation ends. Always call this as the final step."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "A short filename-safe title for the note.",
            },
            "body": {
                "type": "string",
                "description": "The note content in markdown, including source URLs.",
            },
        },
        "required": ["title", "body"],
    },
}
