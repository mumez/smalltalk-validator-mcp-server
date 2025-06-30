"""
Entry point for running the Smalltalk Validator MCP Server.
"""

from .server import app

if __name__ == "__main__":
    app.run()
