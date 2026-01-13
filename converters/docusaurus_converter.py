"""Converter for organizing markdown files into Docusaurus structure."""

import json
import shutil
import yaml
import re
from typing import Dict, Any, List, Optional
from pathlib import Path


def quoted_presenter(dumper, data):
    """Custom YAML representer to always quote strings."""
    return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='"')

# Register the custom representer
yaml.add_representer(str, quoted_presenter)


class DocusaurusConverter:
    """Converter that organizes generated content into Docusaurus structure."""
    
    def __init__(
        self,
        content_dir: str,
        docusaurus_dir: str = "docusaurus"
    ):
        """
        Initialize Docusaurus converter.
        
        Args:
            content_dir: Directory containing generated content
            docusaurus_dir: Docusaurus project directory
        """
        self.content_dir = Path(content_dir)
        self.docusaurus_dir = Path(docusaurus_dir)
        self.docs_dir = self.docusaurus_dir / "docs"
        
        # Create docs directory
        self.docs_dir.mkdir(parents=True, exist_ok=True)
    
    def convert(
        self,
        outline: Dict[str, Any],
        language: str = "id"
    ) -> Dict[str, Any]:
        """
        Convert generated content to Docusaurus structure.
        
        Args:
            outline: Outline structure from Structure Agent
            language: Language code
            
        Returns:
            Dictionary with conversion results
        """
        parts = outline.get("parts", [])
        converted_files = []
        
        # Process each part
        for part in parts:
            part_num = part.get("part_number", 1)
            part_title = part.get("title", f"Part {part_num}")
            chapters = part.get("chapters", [])
            
            # Create part directory
            part_dir = self.docs_dir / f"part-{part_num}"
            part_dir.mkdir(parents=True, exist_ok=True)
            
            # Create category file for part
            self._create_category_file(part_dir, part_title, language)
            
            # Process each chapter
            for chapter in chapters:
                chapter_num = chapter.get("chapter_number", 1)
                chapter_title = chapter.get("title", f"Chapter {chapter_num}")
                
                # Copy chapter file
                source_file = self.content_dir / f"part-{part_num}" / f"chapter-{chapter_num}.md"
                if source_file.exists():
                    dest_file = part_dir / f"chapter-{chapter_num}.md"
                    shutil.copy2(source_file, dest_file)
                    
                    # Add frontmatter
                    self._add_frontmatter(
                        dest_file,
                        chapter_title,
                        part_title,
                        part_num,
                        chapter_num,
                        language
                    )
                    
                    converted_files.append(str(dest_file.relative_to(self.docs_dir)))
        
        # Create sidebar configuration
        sidebar_config = self._create_sidebar_config(outline, language)
        
        return {
            "converted_files": converted_files,
            "docs_dir": str(self.docs_dir),
            "sidebar_config": sidebar_config
        }
    
    def _create_category_file(
        self,
        part_dir: Path,
        part_title: str,
        language: str
    ) -> None:
        """Create _category_.json file for part."""
        category_file = part_dir / "_category_.json"
        
        label_key = "label_id" if language == "id" else "label"
        category_data = {
            label_key: part_title,
            "position": 1
        }
        
        with open(category_file, 'w', encoding='utf-8') as f:
            json.dump(category_data, f, indent=2, ensure_ascii=False)
    
    def _add_frontmatter(
        self,
        file_path: Path,
        title: str,
        part_title: str,
        part_num: int,
        chapter_num: int,
        language: str
    ) -> None:
        """Add Docusaurus frontmatter to markdown file."""
        # Read existing content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if frontmatter already exists
        if content.startswith('---'):
            # Extract existing frontmatter and content
            parts = content.split('---', 2)
            if len(parts) >= 3:
                existing_frontmatter = parts[1]
                body_content = parts[2]
            else:
                existing_frontmatter = ""
                body_content = content
        else:
            existing_frontmatter = ""
            body_content = content
        
        # Create or update frontmatter
        # Ensure titles are properly quoted if they contain special characters
        frontmatter = {
            "title": str(title),  # Ensure it's a string
            "sidebar_position": chapter_num,
            "part": part_num,
            "part_title": str(part_title)  # Ensure it's a string
        }
        
        # Parse existing frontmatter if present
        if existing_frontmatter.strip():
            try:
                existing_data = yaml.safe_load(existing_frontmatter)
                if existing_data:
                    frontmatter.update(existing_data)
            except:
                pass
        
        # Write new content with frontmatter
        # Use safe_dump to ensure proper YAML formatting
        # Quote strings that contain special characters like colons
        frontmatter_yaml = yaml.safe_dump(
            frontmatter, 
            allow_unicode=True, 
            default_flow_style=False, 
            sort_keys=False
        )
        
        # Clean up frontmatter - remove empty lines
        frontmatter_lines = [line for line in frontmatter_yaml.split('\n') if line.strip() or line == '']
        # Remove leading empty lines
        while frontmatter_lines and not frontmatter_lines[0].strip():
            frontmatter_lines.pop(0)
        # Remove trailing empty lines
        while frontmatter_lines and not frontmatter_lines[-1].strip():
            frontmatter_lines.pop()
        
        frontmatter_clean = '\n'.join(frontmatter_lines)
        if not frontmatter_clean.endswith('\n'):
            frontmatter_clean += '\n'
        
        # Strip leading whitespace from body content to avoid issues
        body_content = body_content.lstrip('\n')
        
        # Ensure body content starts with a newline if it doesn't already
        if body_content and not body_content.startswith('\n'):
            body_content = '\n' + body_content
        
        # Escape curly braces in markdown content to prevent MDX parsing errors
        # This is especially important for LaTeX expressions and other content with {}
        body_content = self._escape_curly_braces_for_mdx(body_content)
        
        new_content = f"---\n{frontmatter_clean}---{body_content}"
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
    
    def _create_sidebar_config(
        self,
        outline: Dict[str, Any],
        language: str
    ) -> Dict[str, Any]:
        """
        Create sidebar configuration for Docusaurus.
        
        Args:
            outline: Outline structure
            language: Language code
            
        Returns:
            Sidebar configuration dictionary
        """
        sidebar_items = []
        parts = outline.get("parts", [])
        
        for part in parts:
            part_num = part.get("part_number", 1)
            part_title = part.get("title", f"Part {part_num}")
            chapters = part.get("chapters", [])
            
            part_item = {
                "type": "category",
                "label": part_title,
                "items": []
            }
            
            for chapter in chapters:
                chapter_num = chapter.get("chapter_number", 1)
                chapter_title = chapter.get("title", f"Chapter {chapter_num}")
                
                part_item["items"].append(
                    f"part-{part_num}/chapter-{chapter_num}"
                )
            
            sidebar_items.append(part_item)
        
        return {
            "docs": sidebar_items
        }
    
    def save_sidebar_config(self, config: Dict[str, Any], filename: str = "sidebars.json") -> Path:
        """
        Save sidebar configuration to file.
        
        Args:
            config: Sidebar configuration dictionary
            filename: Output filename
            
        Returns:
            Path to saved file
        """
        config_file = self.docusaurus_dir / filename
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        return config_file
    
    def _escape_curly_braces_for_mdx(self, content: str) -> str:
        """
        Escape curly braces in markdown content to prevent MDX parsing errors.
        MDX interprets { and } as JSX expressions, so we need to escape them.
        We preserve braces inside code blocks and inline code.
        
        Args:
            content: Markdown content
            
        Returns:
            Content with escaped curly braces
        """
        lines = content.split('\n')
        result = []
        in_code_block = False
        in_inline_code = False
        
        for line in lines:
            # Check for code block markers
            if line.strip().startswith('```'):
                in_code_block = not in_code_block
                result.append(line)
                continue
            
            # Don't escape inside code blocks
            if in_code_block:
                result.append(line)
                continue
            
            # Handle inline code (backticks)
            # Simple approach: escape all { and } outside code blocks
            # Replace { with {'{'} and } with {'}'} for MDX
            escaped_line = line.replace('{', "{'{'}").replace('}', "{'}'}")
            result.append(escaped_line)
        
        return '\n'.join(result)

