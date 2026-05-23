def generate(filename, content):
    return {
        "summary": f"Mock summary for {filename}",
        "functions": [{"name": "mock_func", "description": "Does mock things."}]
    }