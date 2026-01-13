"""Orchestrator for coordinating Structure Agent and Content Agent."""

import json
from typing import Dict, Any, Optional, Callable
from pathlib import Path
from agents.structure_agent import StructureAgent
from agents.content_agent import ContentAgent


class Orchestrator:
    """Orchestrator that coordinates the entire pipeline."""
    
    def __init__(
        self,
        language: str = "id",
        retriever: str = "bing",
        output_dir: str = "output"
    ):
        """
        Initialize Orchestrator.
        
        Args:
            language: Language code for content generation
            retriever: Retrieval method for STORM
            output_dir: Base output directory
        """
        self.language = language
        self.retriever = retriever
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize agents
        self.structure_agent = StructureAgent()
        self.content_agent = ContentAgent(
            language=language,
            retriever=retriever,
            output_dir=str(self.output_dir / "content")
        )
        
        self.outline: Optional[Dict[str, Any]] = None
        self.generated_content: Dict[str, str] = {}
    
    def run_pipeline(
        self,
        topic: str,
        audience: str,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Dict[str, Any]:
        """
        Run the complete pipeline: structure generation -> content generation.
        
        Args:
            topic: Main topic for learning material
            audience: Target audience level
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dictionary containing outline and generated content paths
        """
        if progress_callback:
            progress_callback("Starting pipeline...")
        
        # Step 1: Generate outline
        if progress_callback:
            progress_callback(f"Step 1/2: Generating outline for '{topic}'...")
        
        self.outline = self.structure_agent.generate_outline(
            topic=topic,
            language=self.language,
            audience=audience
        )
        
        # Save outline
        outline_file = self.output_dir / "outline.json"
        with open(outline_file, 'w', encoding='utf-8') as f:
            json.dump(self.outline, f, indent=2, ensure_ascii=False)
        
        if progress_callback:
            progress_callback(f"Outline generated: {len(self.outline.get('parts', []))} parts")
        
        # Step 2: Generate content
        if progress_callback:
            progress_callback("Step 2/2: Generating content for all chapters...")
        
        self.generated_content = self.content_agent.generate_all_content(
            outline=self.outline,
            progress_callback=progress_callback
        )
        
        if progress_callback:
            progress_callback("Pipeline completed successfully!")
        
        return {
            "outline": self.outline,
            "content": self.generated_content,
            "outline_file": str(outline_file),
            "content_dir": str(self.content_agent.output_dir)
        }
    
    def get_outline(self) -> Optional[Dict[str, Any]]:
        """Get the generated outline."""
        return self.outline
    
    def get_generated_content(self) -> Dict[str, str]:
        """Get dictionary of generated content paths."""
        return self.generated_content
    
    def save_summary(self, output_file: Optional[str] = None) -> Path:
        """
        Save a summary of the generated materials.
        
        Args:
            output_file: Optional output file path
            
        Returns:
            Path to saved summary file
        """
        if not output_file:
            output_file = str(self.output_dir / "summary.json")
        
        summary = {
            "topic": self.outline.get("topic", "") if self.outline else "",
            "language": self.language,
            "outline": self.outline,
            "content_files": list(self.generated_content.keys()),
            "total_parts": len(self.outline.get("parts", [])) if self.outline else 0,
            "total_chapters": sum(
                len(part.get("chapters", []))
                for part in self.outline.get("parts", [])
            ) if self.outline else 0
        }
        
        summary_path = Path(output_file)
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        return summary_path
    
    def cleanup(self) -> None:
        """Cleanup resources."""
        if self.content_agent:
            self.content_agent.cleanup()

