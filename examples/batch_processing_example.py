"""
Example of batch processing multiple documents and images.
"""

from pathlib import Path
from xtox.core import MultiDocumentProcessor, ImageConverter

def main():
    # Example files (create some test files first)
    files = [
        "test_data/test_doc.md",
        "test_data/test_image.png",
        # Add more files as needed
    ]
    
    # Initialize processor
    processor = MultiDocumentProcessor(output_dir="output/batch_example")
    
    # Get recommendations
    recommendations = processor.get_recommendations(files)
    print("Format Recommendations:")
    for use_case, description in recommendations['use_cases'].items():
        print(f"  {use_case}: {description}")
    
    print(f"\nFile Analysis:")
    print(f"  Documents: {recommendations['file_analysis']['documents']}")
    print(f"  Images: {recommendations['file_analysis']['images']}")
    
    # Process for web use case
    print("\nProcessing for web use case...")
    results = processor.process_documents(
        files,
        target_use_case='web',
        output_dir="output/web_optimized"
    )
    
    print(f"Web processing complete:")
    print(f"  Documents: {len(results['documents'])}")
    print(f"  Images: {len(results['images'])}")
    
    # Process for print use case
    print("\nProcessing for print use case...")
    results = processor.process_documents(
        files,
        target_use_case='print',
        output_dir="output/print_ready"
    )
    
    print(f"Print processing complete:")
    print(f"  Documents: {len(results['documents'])}")
    print(f"  Images: {len(results['images'])}")
    
    # Image-specific processing
    print("\nImage compression example...")
    img_converter = ImageConverter()
    
    # Compress to specific size
    if Path("test_data/test_image.png").exists():
        compressed = img_converter.compress_image(
            "test_data/test_image.png",
            "output/compressed_image.jpg",
            target_size_kb=100
        )
        print(f"Compressed image: {compressed}")
        
        # Get image info
        info = img_converter.get_image_info(compressed)
        print(f"Compressed size: {info['file_size_kb']:.1f} KB")

if __name__ == "__main__":
    main()