import sys

if "--mcp" in sys.argv[1:]:
    from todo.mcp_server import main as run
else:
    from todo.gui import main as run

run()
