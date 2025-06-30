"""
Smalltalk Validator MCP Server

A Model Context Protocol (MCP) server for validating Tonel formatted Smalltalk source code.
"""

__version__ = "0.1.0"
__author__ = "Smalltalk Validator MCP Server"

from .server import app

__all__ = ["app"]
