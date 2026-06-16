SAVE_ARTICLE = {
    "name": "save_article",
    "description": (
        "Save the final written article to the output folder. "
        "Call this as the last step after the Writer agent has produced the article."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "The article title (used as filename)",
            },
            "content": {
                "type": "string",
                "description": "The full article text in markdown",
            },
        },
        "required": ["title", "content"],
    },
}
