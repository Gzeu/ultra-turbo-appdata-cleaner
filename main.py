"""
Ultra-Turbo AppData Cleaner - Main Entry Point
Supports CLI, GUI, and Web Interface modes
"""

import argparse
import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

def run_cli():
    """Run in CLI mode"""
    print("💻 Ultra-Turbo AppData Cleaner - CLI Mode")
    print("\n⚡ Available commands:")
    print("  1. Quick scan")
    print("  2. Full system scan")
    print("  3. Clean temp files")
    print("  4. Clean AppData")
    print("  5. View settings")
    print("  6. Exit")
    
    while True:
        try:
            choice = input("\n🚀 Select option (1-6): ").strip()
            
            if choice == '1':
                print("🔍 Starting quick scan...")
                # TODO: Implement actual scan when modules are ready
                print("✅ Quick scan completed (mock)")
                
            elif choice == '2':
                print("🔍 Starting full system scan...")
                print("✅ Full scan completed (mock)")
                
            elif choice == '3':
                print("🧹 Cleaning temporary files...")
                print("✅ Temp files cleaned (mock)")
                
            elif choice == '4':
                print("🧹 Cleaning AppData...")
                print("✅ AppData cleaned (mock)")
                
            elif choice == '5':
                print("⚙️ Current Settings:")
                print("  - Safe Mode: ON")
                print("  - Backup: Enabled")
                print("  - Max Age: 30 days")
                
            elif choice == '6':
                print("👋 Goodbye!")
                break
                
            else:
                print("❌ Invalid option. Please select 1-6.")
                
        except KeyboardInterrupt:
            print("\n\n👋 Exiting CLI mode...")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
    
    return 0

def run_gui():
    """Run in GUI mode"""
    try:
        # Import GUI only when needed
        from gui.main_window import MainWindow
        print("🖼️ Starting GUI mode...")
        window = MainWindow()
        window.run()
    except ImportError:
        print("❌ GUI module not available. Install tkinter or run with --web")
        return 1
    except Exception as e:
        print(f"❌ GUI Error: {e}")
        return 1
    
    return 0

def run_web():
    """Run web interface"""
    print("🌐 Starting Web Interface...")
    
    # Set DRY_RUN mode for safety
    os.environ.setdefault('DRY_RUN', '1')
    
    try:
        # Import and run web app
        from web.app import app, socketio
        print(f"📱 Access at: http://localhost:5000")
        print(f"🔒 DRY_RUN Mode: {'ON' if os.environ.get('DRY_RUN') == '1' else 'OFF'}")
        
        socketio.run(app, debug=False, host='0.0.0.0', port=5000)
        
    except ImportError as e:
        print(f"❌ Web modules not available: {e}")
        print("📊 Install requirements: pip install flask flask-socketio")
        return 1
    except Exception as e:
        print(f"❌ Web Error: {e}")
        return 1
    
    return 0

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Ultra-Turbo AppData Cleaner - Advanced Windows System Cleaner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                # Start web interface (default)
  python main.py --cli          # Command line interface
  python main.py --gui          # Desktop GUI interface
  python main.py --web          # Web interface (explicit)

For web interface, access: http://localhost:5000
DRY_RUN mode is enabled by default for safety.
        """
    )
    
    # Add arguments
    parser.add_argument('--cli', action='store_true', 
                       help='Run in command line interface mode')
    parser.add_argument('--gui', action='store_true', 
                       help='Run in desktop GUI mode')
    parser.add_argument('--web', action='store_true', 
                       help='Run web interface (default if no mode specified)')
    parser.add_argument('--dry-run', action='store_true', default=True,
                       help='Enable dry run mode (no actual file deletion)')
    parser.add_argument('--no-dry-run', action='store_true', 
                       help='Disable dry run mode (DANGER: will actually delete files)')
    
    args = parser.parse_args()
    
    # Handle dry run settings
    if args.no_dry_run:
        os.environ['DRY_RUN'] = '0'
        print("⚠️  DRY_RUN disabled - files WILL be deleted!")
    else:
        os.environ['DRY_RUN'] = '1'
        print("🔒 DRY_RUN enabled - no files will be deleted")
    
    # Show banner
    print("🚀 Ultra-Turbo AppData Cleaner v1.0.0")
    print("👨‍💻 Created by: Pricop George")
    print("📍 Location: București, România")
    print()
    
    # Determine which mode to run
    if args.cli:
        return run_cli()
    elif args.gui:
        return run_gui()
    else:
        # Default to web interface
        return run_web()

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n👋 Operation cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)