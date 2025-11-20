"""
Example of interactive document processing.
"""

from xtox.core import InteractiveProcessor

def main():
    # Example files
    files = [
        "test_data/test_doc.md",
        "test_data/test_image.png",
        # Add more files as needed
    ]
    
    # Initialize interactive processor
    processor = InteractiveProcessor(output_dir="output/interactive_example")
    
    print("🌐 Interactive Web Processing Example")
    print("This will show default conversions and let you modify them.")
    
    # Process with user interaction
    results = processor.process_with_user_input(files, use_case='web')
    
    if results.get('status') != 'cancelled':
        print(f"\n✨ Processing Results:")
        print(f"  Converted files: {len(results.get('converted', []))}")
        print(f"  Copied files: {len(results.get('copied', []))}")
        print(f"  Errors: {len(results.get('errors', []))}")

if __name__ == "__main__":
    main()