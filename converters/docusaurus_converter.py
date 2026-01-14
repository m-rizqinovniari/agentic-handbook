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
        roadmap: Optional[Dict[str, Any]] = None,
        course_requirements: Optional[Dict[str, Any]] = None,
        language: str = "id"
    ) -> Dict[str, Any]:
        """
        Convert generated content to Docusaurus structure.
        
        Args:
            outline: Outline structure from Structure Agent or Module Agent
            roadmap: Optional course roadmap from RoadmapAgent
            course_requirements: Optional questionnaire results
            language: Language code
            
        Returns:
            Dictionary with conversion results
        """
        # Create course index page with roadmap and outline
        if roadmap:
            self.create_course_index_page(
                roadmap=roadmap,
                outline=outline,
                course_requirements=course_requirements,
                language=language
            )
        
        # Check if outline uses "modules" or "parts" structure
        modules = outline.get("modules", [])
        parts = outline.get("parts", [])
        use_modules = len(modules) > 0
        
        converted_files = []
        
        if use_modules:
            # Process modules structure
            for module in modules:
                module_num = module.get("module_number", 1)
                module_name = module.get("module_name", f"Module {module_num}")
                module_slug = module.get("module_slug", f"module-{module_num}")
                chapters = module.get("chapters", [])
                
                # Create module directory
                module_dir = self.docs_dir / module_slug
                module_dir.mkdir(parents=True, exist_ok=True)
                
                # Create category file for module
                self._create_category_file(module_dir, module_name, language)
                
                # Process each chapter
                for chapter in chapters:
                    chapter_num = chapter.get("chapter_number", 1)
                    chapter_title = chapter.get("title", f"Chapter {chapter_num}")
                    
                    # Copy chapter file
                    source_file = self.content_dir / module_slug / f"chapter-{chapter_num}.md"
                    if source_file.exists():
                        dest_file = module_dir / f"chapter-{chapter_num}.md"
                        shutil.copy2(source_file, dest_file)
                        
                        # Add frontmatter
                        self._add_frontmatter(
                            dest_file,
                            chapter_title,
                            module_name,
                            module_num,
                            chapter_num,
                            language,
                            is_module=True
                        )
                        
                        converted_files.append(str(dest_file.relative_to(self.docs_dir)))
        else:
            # Process parts structure (legacy)
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
                            language,
                            is_module=False
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
        language: str,
        is_module: bool = False
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
        Supports both modules and parts structure.
        
        Args:
            outline: Outline structure
            language: Language code
            
        Returns:
            Sidebar configuration dictionary
        """
        sidebar_items = []
        
        # Check if outline uses modules or parts
        modules = outline.get("modules", [])
        parts = outline.get("parts", [])
        use_modules = len(modules) > 0
        
        if use_modules:
            # Process modules structure
            for module in modules:
                module_num = module.get("module_number", 1)
                module_name = module.get("module_name", f"Module {module_num}")
                module_slug = module.get("module_slug", f"module-{module_num}")
                chapters = module.get("chapters", [])
                
                module_item = {
                    "type": "category",
                    "label": module_name,
                    "items": []
                }
                
                for chapter in chapters:
                    chapter_num = chapter.get("chapter_number", 1)
                    
                    module_item["items"].append(
                        f"{module_slug}/chapter-{chapter_num}"
                    )
                
                sidebar_items.append(module_item)
        else:
            # Process parts structure (legacy)
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
    
    def create_course_index_page(
        self,
        roadmap: Dict[str, Any],
        outline: Dict[str, Any],
        course_requirements: Optional[Dict[str, Any]] = None,
        language: str = "id"
    ) -> Path:
        """
        Create comprehensive course index page with roadmap and outline.
        
        Args:
            roadmap: Course roadmap from RoadmapAgent
            outline: Course outline (modules/chapters structure)
            course_requirements: Optional questionnaire results
            language: Language code
            
        Returns:
            Path to created index.md file
        """
        index_file = self.docs_dir / "index.md"
        
        # Generate markdown content
        content = self._build_index_content(
            roadmap=roadmap,
            outline=outline,
            course_requirements=course_requirements,
            language=language
        )
        
        # Write to file
        with open(index_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return index_file
    
    def _build_index_content(
        self,
        roadmap: Dict[str, Any],
        outline: Dict[str, Any],
        course_requirements: Optional[Dict[str, Any]],
        language: str
    ) -> str:
        """Build markdown content for index page."""
        
        course_title = roadmap.get("course_title", outline.get("topic", "Course"))
        course_description = roadmap.get("course_description", "")
        estimated_duration = roadmap.get("estimated_duration", "")
        
        # Frontmatter - use YAML safe_dump to properly quote title
        frontmatter_data = {
            "title": course_title,
            "sidebar_position": 0
        }
        frontmatter_yaml = yaml.safe_dump(
            frontmatter_data,
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=False
        )
        # Remove trailing newline and ensure proper format
        frontmatter_yaml = frontmatter_yaml.rstrip()
        frontmatter = f"---\n{frontmatter_yaml}\n---"
        
        # Header section
        header = f"""
# {course_title}

{course_description}

"""
        
        # Course Overview Section
        overview = self._build_course_overview(
            roadmap, course_requirements, language
        )
        
        # Learning Path Visualization
        path_viz = self._build_learning_path_viz(roadmap, outline, language)
        
        # Roadmap Section
        roadmap_section = self._build_roadmap_section(roadmap, language)
        
        # Outline Section (Modules & Chapters)
        outline_section = self._build_outline_section(outline, language)
        
        # Combine all sections
        content = f"""{frontmatter}
{header}
{overview}
{path_viz}
{roadmap_section}
{outline_section}
"""
        
        return content
    
    def _build_course_overview(
        self,
        roadmap: Dict[str, Any],
        course_requirements: Optional[Dict[str, Any]],
        language: str
    ) -> str:
        """Build course overview section."""
        
        if language == "id":
            section_title = "## 📋 Ringkasan Course"
            duration_label = "**Durasi Estimasi:**"
            level_label = "**Level:**"
            focus_label = "**Fokus Pembelajaran:**"
        else:
            section_title = "## 📋 Course Overview"
            duration_label = "**Estimated Duration:**"
            level_label = "**Level:**"
            focus_label = "**Learning Focus:**"
        
        overview = f"""{section_title}

"""
        
        # Course metadata
        if roadmap.get("estimated_duration"):
            overview += f"{duration_label} {roadmap.get('estimated_duration')}\n\n"
        
        if roadmap.get("level"):
            overview += f"{level_label} {roadmap.get('level')}\n\n"
        
        if course_requirements and course_requirements.get("learning_focus"):
            focus_map = {
                "1": "Teori mendalam" if language == "id" else "In-depth theory",
                "2": "Praktik dan implementasi" if language == "id" else "Practice and implementation",
                "3": "Kombinasi teori dan praktik" if language == "id" else "Combination of theory and practice",
                "4": "Studi kasus dan aplikasi real-world" if language == "id" else "Case studies and real-world applications"
            }
            focus_text = focus_map.get(course_requirements.get("learning_focus"), "")
            if focus_text:
                overview += f"{focus_label} {focus_text}\n\n"
        
        # Course objectives
        if roadmap.get("course_objectives"):
            if language == "id":
                overview += "**Tujuan Pembelajaran:**\n\n"
            else:
                overview += "**Learning Objectives:**\n\n"
            
            for obj in roadmap.get("course_objectives", []):
                overview += f"- {obj}\n"
            overview += "\n"
        
        return overview
    
    def _build_roadmap_section(
        self,
        roadmap: Dict[str, Any],
        language: str
    ) -> str:
        """Build roadmap visualization section."""
        
        if language == "id":
            section_title = "## 🗺️ Roadmap Pembelajaran"
            phase_label = "Fase"
            module_label = "Modul"
            time_label = "Waktu"
        else:
            section_title = "## 🗺️ Learning Roadmap"
            phase_label = "Phase"
            module_label = "Module"
            time_label = "Time"
        
        roadmap_content = f"""{section_title}

"""
        
        if language == "id":
            roadmap_content += "Roadmap ini menunjukkan alur pembelajaran dari dasar hingga tingkat lanjut.\n\n"
        else:
            roadmap_content += "This roadmap shows the learning path from basics to advanced level.\n\n"
        
        learning_path = roadmap.get("learning_path", [])
        
        for phase_idx, phase in enumerate(learning_path, 1):
            phase_name = phase.get("phase", f"Phase {phase_idx}")
            phase_desc = phase.get("description", "")
            modules = phase.get("modules", [])
            
            roadmap_content += f"""### {phase_name}

{phase_desc}

"""
            
            # Create table for modules in this phase
            roadmap_content += f"| {module_label} | Deskripsi | {time_label} |\n"
            roadmap_content += "|------|------------|-------|\n"
            
            for module in modules:
                module_name = module.get("module_name", "")
                module_desc = module.get("description", "")
                module_time = module.get("estimated_time", "")
                
                # Truncate description if too long
                if len(module_desc) > 100:
                    module_desc = module_desc[:97] + "..."
                
                roadmap_content += f"| {module_name} | {module_desc} | {module_time} |\n"
            
            roadmap_content += "\n"
        
        return roadmap_content
    
    def _build_outline_section(
        self,
        outline: Dict[str, Any],
        language: str
    ) -> str:
        """Build detailed outline section with modules and chapters."""
        
        if language == "id":
            section_title = "## 📚 Struktur Course Lengkap"
            part_label = "Bagian"
            chapter_label = "Bab"
            description_label = "Deskripsi"
        else:
            section_title = "## 📚 Complete Course Structure"
            part_label = "Part"
            chapter_label = "Chapter"
            description_label = "Description"
        
        outline_content = f"""{section_title}

"""
        
        if language == "id":
            outline_content += "Struktur lengkap course dengan semua modul dan chapter.\n\n"
        else:
            outline_content += "Complete course structure with all modules and chapters.\n\n"
        
        # Check if outline uses modules or parts
        if "modules" in outline:
            # New structure: modules -> chapters
            modules = outline.get("modules", [])
            
            for module in modules:
                module_name = module.get("module_name", module.get("title", ""))
                module_desc = module.get("description", "")
                chapters = module.get("chapters", [])
                module_slug = module.get("module_slug", f"module-{module.get('module_number', 1)}")
                
                outline_content += f"""### {module_name}

{module_desc}

"""
                
                for chapter in chapters:
                    chapter_num = chapter.get("chapter_number", "")
                    chapter_title = chapter.get("title", "")
                    chapter_desc = chapter.get("description", "")
                    
                    # Create link to chapter
                    chapter_link = f"{module_slug}/chapter-{chapter_num}"
                    
                    outline_content += f"""#### [{chapter_num}. {chapter_title}]({chapter_link})

{chapter_desc}

"""
                    
                    if language == "id":
                        outline_content += "**Tujuan Pembelajaran:**\n"
                    else:
                        outline_content += "**Learning Objectives:**\n"
                    
                    # Learning objectives
                    for obj in chapter.get("learning_objectives", []):
                        outline_content += f"- {obj}\n"
                    
                    outline_content += "\n"
        
        else:
            # Legacy structure: parts -> chapters
            parts = outline.get("parts", [])
            
            for part in parts:
                part_num = part.get("part_number", "")
                part_title = part.get("title", "")
                part_desc = part.get("description", "")
                chapters = part.get("chapters", [])
                
                outline_content += f"""### {part_label} {part_num}: {part_title}

{part_desc}

"""
                
                for chapter in chapters:
                    chapter_num = chapter.get("chapter_number", "")
                    chapter_title = chapter.get("title", "")
                    chapter_desc = chapter.get("description", "")
                    
                    # Create link to chapter
                    chapter_link = f"part-{part_num}/chapter-{chapter_num}"
                    
                    outline_content += f"""#### [{chapter_num}. {chapter_title}]({chapter_link})

{chapter_desc}

"""
                    
                    if language == "id":
                        outline_content += "**Tujuan Pembelajaran:**\n"
                    else:
                        outline_content += "**Learning Objectives:**\n"
                    
                    # Learning objectives
                    for obj in chapter.get("learning_objectives", []):
                        outline_content += f"- {obj}\n"
                    
                    outline_content += "\n"
        
        return outline_content
    
    def _build_learning_path_viz(
        self,
        roadmap: Dict[str, Any],
        outline: Dict[str, Any],
        language: str
    ) -> str:
        """Build Mermaid diagram for learning path visualization."""
        
        if language == "id":
            section_title = "## 🎯 Alur Pembelajaran"
        else:
            section_title = "## 🎯 Learning Path"
        
        # Create Mermaid flowchart showing learning progression
        mermaid_diagram = """```mermaid
graph TD
"""
        
        learning_path = roadmap.get("learning_path", [])
        
        # Build nodes and connections
        prev_node = None
        for phase_idx, phase in enumerate(learning_path, 1):
            phase_name = phase.get("phase", f"Phase {phase_idx}")
            phase_node = f"P{phase_idx}"
            
            # Escape special characters for Mermaid
            phase_name_clean = phase_name.replace('"', "'")
            
            mermaid_diagram += f'    {phase_node}["{phase_name_clean}"]\n'
            
            if prev_node:
                mermaid_diagram += f"    {prev_node} --> {phase_node}\n"
            
            prev_node = phase_node
            
            # Add modules as sub-nodes
            modules = phase.get("modules", [])
            for mod_idx, module in enumerate(modules, 1):
                mod_node = f"M{phase_idx}_{mod_idx}"
                mod_name = module.get("module_name", f"Module {mod_idx}")
                mod_name_clean = mod_name.replace('"', "'")
                
                # Truncate if too long
                if len(mod_name_clean) > 30:
                    mod_name_clean = mod_name_clean[:27] + "..."
                
                mermaid_diagram += f'    {mod_node}["{mod_name_clean}"]\n'
                mermaid_diagram += f"    {phase_node} --> {mod_node}\n"
        
        mermaid_diagram += """```
"""
        
        if language == "id":
            viz_content = f"""{section_title}

Diagram berikut menunjukkan alur pembelajaran course ini:

{mermaid_diagram}

"""
        else:
            viz_content = f"""{section_title}

The following diagram shows the learning path of this course:

{mermaid_diagram}

"""
        
        return viz_content

