"""
Multi-document processing with dynamic format selection.
"""

import os
from pathlib import Path
from typing import List, Dict, Optional, Union, Tuple
import mimetypes

from .document_converter import DocumentConverter
from .image_converter import ImageConverter


class MultiDocumentProcessor:
    """Process multiple documents with intelligent format selection."""
    
    def __init__(self, output_dir: Optional[str] = None):
        self.converter = DocumentConverter(output_dir)
        self.image_converter = ImageConverter()
        self.output_dir = Path(output_dir) if output_dir else None
        
        # Format recommendations based on use case
        self.format_recommendations = {
            'web': {'documents': 'html', 'images': 'webp'},
            'print': {'documents': 'pdf', 'images': 'jpeg'},
            'archive': {'documents': 'pdf', 'images': 'png'},
            'editing': {'documents': 'docx', 'images': 'png'},
            'ai_processing': {'documents': 'markdown', 'images': 'jpeg'}
        }
    
    def process_documents(
        self,
        file_paths: List[Union[str, Path]],
        target_use_case: Optional[str] = None,
        user_preferences: Optional[Dict] = None,
        output_dir: Optional[str] = None
    ) -> Dict[str, List[str]]:
        """
        Process multiple documents with intelligent format selection.
        
        Args:
            file_paths: List of file paths to process
            target_use_case: Use case ('web', 'print', 'archive', 'editing', 'ai_processing')
            user_preferences: User format preferences {'documents': 'pdf', 'images': 'jpeg'}
            output_dir: Output directory
            
        Returns:
            Dictionary with processed file paths by category
        """
        if output_dir:
            self.output_dir = Path(output_dir)
            self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Categorize files
        categorized_files = self._categorize_files(file_paths)
        
        # Determine target formats
        target_formats = self._determine_formats(target_use_case, user_preferences)
        
        results = {
            'documents': [],
            'images': [],
            'errors': []
        }
        
        # Process documents
        for doc_path in categorized_files['documents']:
            try:
                converted_path = self._convert_document(doc_path, target_formats['documents'])
                results['documents'].append(converted_path)
            except Exception as e:
                results['errors'].append(f"Document {doc_path}: {str(e)}")
        
        # Process images
        for img_path in categorized_files['images']:
            try:
                converted_path = self._convert_image(img_path, target_formats['images'])
                results['images'].append(converted_path)
            except Exception as e:
                results['errors'].append(f"Image {img_path}: {str(e)}")
        
        return results
    
    def _categorize_files(self, file_paths: List[Union[str, Path]]) -> Dict[str, List[Path]]:
        """Categorize files by type."""
        categorized = {
            'documents': [],
            'images': [],
            'unsupported': []
        }
        
        document_extensions = {'.md', '.html', '.tex', '.docx', '.txt', '.rtf'}
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.gif', '.webp'}
        
        for file_path in file_paths:
            path = Path(file_path)
            if not path.exists():
                continue
                
            ext = path.suffix.lower()
            
            if ext in document_extensions:
                categorized['documents'].append(path)
            elif ext in image_extensions:
                categorized['images'].append(path)
            else:
                # Try to detect by MIME type
                mime_type, _ = mimetypes.guess_type(str(path))
                if mime_type:
                    if mime_type.startswith('text/') or 'document' in mime_type:
                        categorized['documents'].append(path)
                    elif mime_type.startswith('image/'):
                        categorized['images'].append(path)
                    else:
                        categorized['unsupported'].append(path)
                else:
                    categorized['unsupported'].append(path)
        
        return categorized
    
    def _determine_formats(
        self, 
        use_case: Optional[str], 
        user_preferences: Optional[Dict]
    ) -> Dict[str, str]:
        """Determine target formats based on use case and preferences."""
        # Start with defaults
        formats = {'documents': 'pdf', 'images': 'jpeg'}
        
        # Apply use case recommendations
        if use_case and use_case in self.format_recommendations:
            formats.update(self.format_recommendations[use_case])
        
        # Apply user preferences (highest priority)
        if user_preferences:
            formats.update(user_preferences)
        
        return formats
    
    def _convert_document(self, doc_path: Path, target_format: str) -> str:
        """Convert a single document."""
        if target_format == 'pdf':
            if doc_path.suffix.lower() == '.md':
                result = self.converter.markdown_to_pdf(doc_path, str(self.output_dir))
                return result['pdf_path']
            elif doc_path.suffix.lower() == '.tex':
                return self.converter.latex_to_pdf(doc_path)
        
        elif target_format == 'html':
            if doc_path.suffix.lower() == '.md':
                return self.converter.markdown_to_html(doc_path, str(self.output_dir))
        
        elif target_format == 'docx':
            if doc_path.suffix.lower() == '.md':
                return self.converter.markdown_to_docx(doc_path, str(self.output_dir))
        
        elif target_format == 'markdown':
            if doc_path.suffix.lower() == '.html':
                return self.converter.html_to_markdown(doc_path, str(self.output_dir))
        
        # If no conversion needed or supported, copy original
        if self.output_dir:
            output_path = self.output_dir / doc_path.name
            import shutil
            shutil.copy2(doc_path, output_path)
            return str(output_path)
        
        return str(doc_path)
    
    def _convert_image(self, img_path: Path, target_format: str) -> str:
        """Convert a single image."""
        if self.output_dir:
            output_path = self.output_dir / f"{img_path.stem}.{target_format}"
        else:
            output_path = img_path.with_suffix(f".{target_format}")
        
        return self.image_converter.convert_image(
            img_path, 
            output_path, 
            target_format=target_format,
            quality='high'
        )
    
    def get_recommendations(self, file_paths: List[Union[str, Path]]) -> Dict:
        """Get format recommendations for given files."""
        categorized = self._categorize_files(file_paths)
        
        recommendations = {
            'use_cases': {
                'web': 'Optimized for web delivery (HTML + WebP)',
                'print': 'High quality for printing (PDF + JPEG)',
                'archive': 'Long-term storage (PDF + PNG)',
                'editing': 'Further editing (DOCX + PNG)',
                'ai_processing': 'AI/ML processing (Markdown + JPEG)'
            },
            'file_analysis': {
                'documents': len(categorized['documents']),
                'images': len(categorized['images']),
                'unsupported': len(categorized['unsupported'])
            },
            'suggested_formats': self.format_recommendations
        }
        
        return recommendations