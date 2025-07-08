import os
import re
import shutil
from pathlib import Path

def copy_images_to_output_dir(markdown_content, source_dir, target_dir):
    """
    Copy all images referenced in markdown to the target directory.
    """
    images_dir = os.path.join(target_dir, "images")
    os.makedirs(images_dir, exist_ok=True)
    
    image_matches = re.findall(r'!\[.*?\]\((.*?)\)', markdown_content)
    path_mapping = {}
    
    for image_path in image_matches:
        full_source_path = os.path.join(source_dir, image_path)
        
        if not os.path.exists(full_source_path):
            if os.path.exists(image_path):
                full_source_path = image_path
            else:
                print(f"Warning: Image not found: {image_path}")
                continue
        
        image_filename = os.path.basename(image_path)
        target_path = os.path.join(images_dir, image_filename)
        
        shutil.copy2(full_source_path, target_path)
        print(f"Copied image: {image_path} → {target_path}")
        
        path_mapping[image_path] = os.path.join("images", image_filename)
    
    return path_mapping

def update_image_paths(markdown_content, path_mapping):
    """
    Update image paths in markdown content based on the mapping.
    """
    updated_content = markdown_content
    for old_path, new_path in path_mapping.items():
        updated_content = updated_content.replace(f'![]({old_path})', f'![]({new_path})')
        updated_content = updated_content.replace(f']({old_path})', f']({new_path})')
    
    return updated_content