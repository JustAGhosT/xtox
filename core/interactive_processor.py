"""
Interactive document processor with user format selection.
"""

from pathlib import Path
from typing import List, Dict, Union, Optional
import os

from .multi_document_processor import MultiDocumentProcessor


class InteractiveProcessor:
    """Interactive processor allowing user to review and modify conversion settings."""
    
    def __init__(self, output_dir: Optional[str] = None):
        self.processor = MultiDocumentProcessor(output_dir)
        self.format_map = {
            'documents': {
                '.md': {'web': 'html', 'print': 'pdf', 'archive': 'pdf', 'editing': 'docx'},
                '.html': {'web': 'html', 'print': 'pdf', 'archive': 'pdf', 'editing': 'docx'},
                '.tex': {'web': 'pdf', 'print': 'pdf', 'archive': 'pdf', 'editing': 'pdf'},
                '.docx': {'web': 'html', 'print': 'pdf', 'archive': 'pdf', 'editing': 'docx'},
                '.txt': {'web': 'html', 'print': 'pdf', 'archive': 'pdf', 'editing': 'docx'}
            },
            'images': {
                '.png': {'web': 'webp', 'print': 'jpeg', 'archive': 'png', 'editing': 'png'},
                '.jpg': {'web': 'webp', 'print': 'jpeg', 'archive': 'jpeg', 'editing': 'png'},
                '.jpeg': {'web': 'webp', 'print': 'jpeg', 'archive': 'jpeg', 'editing': 'png'},
                '.bmp': {'web': 'webp', 'print': 'jpeg', 'archive': 'png', 'editing': 'png'},
                '.tiff': {'web': 'webp', 'print': 'jpeg', 'archive': 'png', 'editing': 'png'},
                '.gif': {'web': 'webp', 'print': 'jpeg', 'archive': 'gif', 'editing': 'png'},
                '.webp': {'web': 'webp', 'print': 'jpeg', 'archive': 'png', 'editing': 'png'}
            }
        }
    
    def process_with_user_input(
        self, 
        file_paths: List[Union[str, Path]], 
        use_case: str = 'web'
    ) -> Dict:
        """Process files with interactive user format selection."""
        
        # Analyze files and get default conversions
        file_plan = self._create_conversion_plan(file_paths, use_case)
        
        # Show plan to user and get modifications
        modified_plan = self._get_user_modifications(file_plan, use_case)
        
        # Execute conversions
        return self._execute_plan(modified_plan)
    
    def _create_conversion_plan(self, file_paths: List[Union[str, Path]], use_case: str) -> List[Dict]:
        """Create initial conversion plan with defaults."""
        plan = []
        
        for file_path in file_paths:
            path = Path(file_path)
            if not path.exists():
                continue
            
            ext = path.suffix.lower()
            file_type = self._get_file_type(ext)
            default_format = self._get_default_format(ext, file_type, use_case)
            
            plan.append({
                'path': path,
                'name': path.name,
                'type': file_type,
                'extension': ext,
                'default_format': default_format,
                'selected_format': default_format,
                'size_kb': path.stat().st_size / 1024 if path.exists() else 0
            })
        
        return plan
    
    def _get_file_type(self, ext: str) -> str:
        """Determine file type category."""
        doc_exts = {'.md', '.html', '.tex', '.docx', '.txt', '.rtf'}
        img_exts = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.gif', '.webp'}
        
        if ext in doc_exts:
            return 'document'
        elif ext in img_exts:
            return 'image'
        else:
            return 'unknown'
    
    def _get_default_format(self, ext: str, file_type: str, use_case: str) -> str:
        """Get default format for file type and use case."""
        if file_type == 'document' and ext in self.format_map['documents']:
            return self.format_map['documents'][ext].get(use_case, 'pdf')
        elif file_type == 'image' and ext in self.format_map['images']:
            return self.format_map['images'][ext].get(use_case, 'jpeg')
        else:
            return 'copy'  # Just copy unknown files
    
    def _get_user_modifications(self, plan: List[Dict], use_case: str) -> List[Dict]:
        """Get user modifications to the conversion plan."""
        print(f"\n📋 Conversion Plan for '{use_case}' use case:")
        print("=" * 80)
        print(f"{'#':<3} {'File':<30} {'Type':<8} {'Size':<8} {'Default':<10} {'Selected':<10}")
        print("-" * 80)
        
        for i, item in enumerate(plan, 1):
            size_str = f"{item['size_kb']:.1f}KB"
            print(f"{i:<3} {item['name']:<30} {item['type']:<8} {size_str:<8} {item['default_format']:<10} {item['selected_format']:<10}")
        
        print("\n🔧 Modification Options:")
        print("- Enter file number to change format")
        print("- Type 'done' to proceed with conversions")
        print("- Type 'quit' to cancel")
        
        while True:
            choice = input("\nEnter choice: ").strip().lower()
            
            if choice == 'done':
                break
            elif choice == 'quit':
                return []
            elif choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(plan):
                    plan[idx] = self._modify_file_format(plan[idx])
                else:
                    print("Invalid file number")
            else:
                print("Invalid input. Enter file number, 'done', or 'quit'")
        
        return plan
    
    def _modify_file_format(self, item: Dict) -> Dict:
        """Allow user to modify format for a specific file."""
        print(f"\n📄 Modifying: {item['name']}")
        
        if item['type'] == 'document':
            formats = ['html', 'pdf', 'docx', 'markdown', 'copy']
        elif item['type'] == 'image':
            formats = ['webp', 'jpeg', 'png', 'copy']
        else:
            formats = ['copy']
        
        print("Available formats:")
        for i, fmt in enumerate(formats, 1):
            marker = "👉" if fmt == item['selected_format'] else "  "
            print(f"{marker} {i}. {fmt}")
        
        while True:
            choice = input(f"Select format (1-{len(formats)}) or press Enter to keep current: ").strip()
            
            if not choice:  # Keep current
                break
            elif choice.isdigit() and 1 <= int(choice) <= len(formats):
                item['selected_format'] = formats[int(choice) - 1]
                print(f"✅ Changed to: {item['selected_format']}")
                break
            else:
                print("Invalid choice")
        
        return item
    
    def _execute_plan(self, plan: List[Dict]) -> Dict:
        """Execute the conversion plan."""
        if not plan:
            return {'status': 'cancelled'}
        
        print(f"\n🚀 Starting conversions...")
        
        results = {
            'converted': [],
            'copied': [],
            'errors': []
        }
        
        for item in plan:
            try:
                if item['selected_format'] == 'copy':
                    # Just copy the file
                    if self.processor.output_dir:
                        import shutil
                        dest = self.processor.output_dir / item['name']
                        shutil.copy2(item['path'], dest)
                        results['copied'].append(str(dest))
                    else:
                        results['copied'].append(str(item['path']))
                else:
                    # Convert the file
                    converted_path = self._convert_single_file(item)
                    results['converted'].append(converted_path)
                
                print(f"✅ {item['name']} → {item['selected_format']}")
                
            except Exception as e:
                error_msg = f"{item['name']}: {str(e)}"
                results['errors'].append(error_msg)
                print(f"❌ {error_msg}")
        
        print(f"\n📊 Summary:")
        print(f"  Converted: {len(results['converted'])}")
        print(f"  Copied: {len(results['copied'])}")
        print(f"  Errors: {len(results['errors'])}")
        
        return results
    
    def _convert_single_file(self, item: Dict) -> str:
        """Convert a single file based on its plan."""
        if item['type'] == 'document':
            return self.processor._convert_document(item['path'], item['selected_format'])
        elif item['type'] == 'image':
            return self.processor._convert_image(item['path'], item['selected_format'])
        else:
            raise ValueError(f"Unknown file type: {item['type']}")


def interactive_cli():
    """Command-line interface for interactive processing."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python -m xtox.core.interactive_processor <files...> [--use-case web|print|archive|editing]")
        return
    
    files = []
    use_case = 'web'
    
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == '--use-case' and i + 1 < len(sys.argv):
            use_case = sys.argv[i + 1]
            i += 2
        else:
            files.append(arg)
            i += 1
    
    processor = InteractiveProcessor(output_dir='output/interactive')
    results = processor.process_with_user_input(files, use_case)
    
    if results.get('status') != 'cancelled':
        print(f"\n🎉 Processing complete! Check 'output/interactive' folder.")


if __name__ == "__main__":
    interactive_cli()