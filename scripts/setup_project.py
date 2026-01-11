"""
Project Setup Script

Initializes project structure and generates mock data.

Run this first: python scripts/setup_project.py
"""

from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from generate_mock_data import generate_warehouse_csv


def create_directory_structure():
    """Create all required directories"""
    dirs = [
        "data/raw",
        "data/processed",
        "diagrams/screenshots",
        "tests"
    ]
    
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {dir_path}")


def setup_environment():
    """Create .env file from template"""
    env_template = Path(".env.example")
    env_file = Path(".env")
    
    if not env_file.exists() and env_template.exists():
        env_file.write_text(env_template.read_text())
        print("✅ Created .env file")


def main():
    print("🚀 Setting up Aura Knowledge Pipeline project...\n")
    
    # Create directories
    create_directory_structure()
    
    # Setup environment
    setup_environment()
    
    # Generate mock data
    print("\n📊 Generating mock data...")
    generate_warehouse_csv()
    
    print("\n" + "=" * 60)
    print("✅ Project setup complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Start the mock APIs:")
    print("   uvicorn mock_apis.main:app --reload --port 8000")
    print("\n2. Run the pipeline:")
    print("   python scripts/run_pipeline.py")
    print("\n3. Run the demo:")
    print("   python scripts/demo_aura_queries.py")


if __name__ == "__main__":
    main()