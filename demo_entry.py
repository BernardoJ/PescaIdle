"""Separate packaged demonstration entry. Never opens an ordinary profile."""
if __name__ == '__main__':
    import sys
    from tools.demo_tamanhos import run
    sys.exit(run())
