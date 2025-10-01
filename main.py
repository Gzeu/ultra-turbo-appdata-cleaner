#!/usr/bin/env python3
"""
Ultra-Turbo AppData Cleaner - Main Entry Point
Aplicație avansată pentru curățarea sistemului Windows
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.settings import Settings
from config.logging_config import setup_logging
from gui.main_window import MainWindow
from cli.commands import CLICommands

def main():
    """Main application entry point"""
    parser = argparse.ArgumentParser(description='Ultra-Turbo AppData Cleaner')
    parser.add_argument('--cli', action='store_true', help='Run in CLI mode')
    parser.add_argument('--scan', action='store_true', help='Scan only mode')
    parser.add_argument('--clean', action='store_true', help='Auto clean mode')
    parser.add_argument('--config', type=str, help='Config file path')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    
    # Load settings
    settings = Settings(args.config)
    
    if args.cli:
        # Run CLI mode
        cli = CLICommands(settings)
        if args.scan:
            cli.scan_command()
        elif args.clean:
            cli.clean_command()
        else:
            cli.interactive_mode()
    else:
        # Run GUI mode
        app = MainWindow(settings)
        app.run()

if __name__ == "__main__":
    main()