"""Content Agent for generating learning material content using STORM."""

import json
from typing import Dict, Any, List, Optional, Callable
from pathlib import Path
from storm_integration.storm_wrapper import StormWrapper


class ContentAgent:
    """Agent that generates content for each chapter using STORM."""
    
    def __init__(
        self,
        language: str = "id",
        retriever: str = "bing",
        output_dir: str = "output/content"
    ):
        """
        Initialize Content Agent.
        
        Args:
            language: Language code for content generation
            retriever: Retrieval method for STORM ('bing', 'wiki', or 'duckduckgo')
            output_dir: Directory for output files
        """
        self.language = language
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize STORM wrapper
        self.storm_wrapper = StormWrapper(
            language=language,
            retriever=retriever,
            output_dir=str(self.output_dir / "storm")
        )
        self.storm_wrapper.initialize()
        
        self.generated_content: Dict[str, str] = {}
    
    def generate_all_content(
        self,
        outline: Dict[str, Any],
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Dict[str, str]:
        """
        Generate content for all chapters in the outline.
        
        Args:
            outline: Outline structure from Structure Agent
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dictionary mapping chapter paths to generated content
        """
        self.generated_content = {}
        
        parts = outline.get("parts", [])
        total_chapters = sum(len(part.get("chapters", [])) for part in parts)
        current_chapter = 0
        
        for part in parts:
            part_num = part.get("part_number", 1)
            part_title = part.get("title", f"Part {part_num}")
            chapters = part.get("chapters", [])
            
            if progress_callback:
                progress_callback(f"Processing {part_title}...")
            
            for chapter in chapters:
                current_chapter += 1
                chapter_num = chapter.get("chapter_number", 1)
                chapter_title = chapter.get("title", f"Chapter {chapter_num}")
                
                if progress_callback:
                    progress_callback(
                        f"Generating content for {chapter_title} "
                        f"({current_chapter}/{total_chapters})..."
                    )
                
                # Generate content for this chapter
                content = self._generate_chapter_content(
                    chapter,
                    part_title,
                    progress_callback
                )
                
                # Store content with path
                chapter_path = f"part-{part_num}/chapter-{chapter_num}"
                self.generated_content[chapter_path] = content
                
                # Save to file
                self._save_chapter_content(
                    part_num,
                    chapter_num,
                    chapter_title,
                    content
                )
        
        if progress_callback:
            progress_callback("All content generation completed!")
        
        return self.generated_content
    
    def _generate_chapter_content(
        self,
        chapter: Dict[str, Any],
        part_title: str,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> str:
        """
        Generate content for a single chapter.
        
        Args:
            chapter: Chapter dictionary with title, description, sections, etc.
            part_title: Title of the parent part
            progress_callback: Optional progress callback
            
        Returns:
            Generated markdown content
        """
        chapter_title = chapter.get("title", "Untitled Chapter")
        
        # Build topic string with context
        topic = f"{part_title}: {chapter_title}"
        
        # Prepare chapter context
        chapter_context = {
            "title": chapter_title,
            "description": chapter.get("description", ""),
            "sections": chapter.get("sections", []),
            "learning_objectives": chapter.get("learning_objectives", [])
        }
        
        try:
            # Use STORM to generate content
            content = self.storm_wrapper.generate_content(
                topic=topic,
                chapter_context=chapter_context,
                progress_callback=progress_callback
            )
            
            return content
            
        except Exception as e:
            error_msg = f"Error generating content for {chapter_title}: {e}"
            if progress_callback:
                progress_callback(f"Error: {error_msg}")
            
            # Return error message as content (can be handled later)
            return f"# {chapter_title}\n\n*Error generating content: {error_msg}*"
    
    def _save_chapter_content(
        self,
        part_num: int,
        chapter_num: int,
        chapter_title: str,
        content: str
    ) -> None:
        """
        Save chapter content to file.
        
        Args:
            part_num: Part number
            chapter_num: Chapter number
            chapter_title: Chapter title
            content: Generated content
        """
        # Create part directory
        part_dir = self.output_dir / f"part-{part_num}"
        part_dir.mkdir(parents=True, exist_ok=True)
        
        # Save chapter file
        chapter_file = part_dir / f"chapter-{chapter_num}.md"
        with open(chapter_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Also save metadata
        metadata_file = part_dir / f"chapter-{chapter_num}.meta.json"
        metadata = {
            "part_number": part_num,
            "chapter_number": chapter_num,
            "title": chapter_title,
            "file": f"chapter-{chapter_num}.md"
        }
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    def get_content_path(self, part_num: int, chapter_num: int) -> Optional[Path]:
        """
        Get file path for a specific chapter's content.
        
        Args:
            part_num: Part number
            chapter_num: Chapter number
            
        Returns:
            Path to chapter file, or None if not found
        """
        chapter_file = self.output_dir / f"part-{part_num}" / f"chapter-{chapter_num}.md"
        if chapter_file.exists():
            return chapter_file
        return None
    
    def cleanup(self) -> None:
        """Cleanup resources."""
        if self.storm_wrapper:
            self.storm_wrapper.cleanup()

