"""Course Orchestrator for coordinating the complete course generation pipeline."""

import json
from typing import Dict, Any, Optional, Callable
from pathlib import Path
from agents.course_questionnaire import CourseQuestionnaire
from agents.roadmap_agent import RoadmapAgent
from agents.module_agent import ModuleAgent
from agents.content_agent import ContentAgent


class CourseOrchestrator:
    """Orchestrator that coordinates the complete course generation pipeline."""
    
    def __init__(
        self,
        language: str = "id",
        retriever: str = "bing",
        output_dir: str = "output"
    ):
        """
        Initialize Course Orchestrator.
        
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
        self.questionnaire = CourseQuestionnaire(language=language)
        self.roadmap_agent = RoadmapAgent()
        self.module_agent = ModuleAgent()
        self.content_agent = ContentAgent(
            language=language,
            retriever=retriever,
            output_dir=str(self.output_dir / "content")
        )
        
        # Store results
        self.course_requirements: Optional[Dict[str, Any]] = None
        self.roadmap: Optional[Dict[str, Any]] = None
        self.outline: Optional[Dict[str, Any]] = None
        self.generated_content: Dict[str, str] = {}
    
    def run_course_pipeline(
        self,
        topic: str,
        audience: str,
        progress_callback: Optional[Callable[[str], None]] = None,
        skip_questionnaire: bool = False
    ) -> Dict[str, Any]:
        """
        Run the complete course generation pipeline.
        
        Pipeline flow:
        1. Interactive Q&A (CourseQuestionnaire)
        2. Generate Course Roadmap (RoadmapAgent)
        3. Break down into Modules (ModuleAgent)
        4. Generate Content for all Chapters (ContentAgent)
        
        Args:
            topic: Main topic for the course
            audience: Target audience level
            progress_callback: Optional callback for progress updates
            skip_questionnaire: If True, skip Q&A and use default requirements
            
        Returns:
            Dictionary containing all results and paths
        """
        if progress_callback:
            progress_callback("Starting course generation pipeline...")
        
        # Step 1: Interactive Q&A
        if not skip_questionnaire:
            if progress_callback:
                progress_callback("Step 1/4: Conducting course requirements questionnaire...")
            
            self.course_requirements = self.questionnaire.conduct_interview(
                output_dir=self.output_dir
            )
        else:
            if progress_callback:
                progress_callback("Step 1/4: Skipping questionnaire, using default requirements...")
            
            # Use default requirements
            self.course_requirements = {
                "learning_goals": f"Comprehensive understanding of {topic}",
                "time_dedication": "5 hours per week",
                "prior_knowledge": "Basic knowledge",
                "learning_focus": "3",  # Combination
                "expected_outcomes": f"Master {topic} concepts and applications"
            }
            
            # Save default requirements
            requirements_file = self.output_dir / "course_requirements.json"
            with open(requirements_file, 'w', encoding='utf-8') as f:
                json.dump(self.course_requirements, f, indent=2, ensure_ascii=False)
        
        if progress_callback:
            progress_callback("✓ Questionnaire completed")
        
        # Step 2: Generate Roadmap
        if progress_callback:
            progress_callback(f"Step 2/4: Generating course roadmap for '{topic}'...")
        
        self.roadmap = self.roadmap_agent.generate_roadmap(
            topic=topic,
            course_requirements=self.course_requirements,
            language=self.language,
            audience=audience,
            output_dir=self.output_dir
        )
        
        if progress_callback:
            roadmap_phases = len(self.roadmap.get("learning_path", []))
            total_modules = sum(
                len(phase.get("modules", []))
                for phase in self.roadmap.get("learning_path", [])
            )
            progress_callback(f"✓ Roadmap generated: {roadmap_phases} phases, {total_modules} modules")
        
        # Step 3: Break down into Modules
        if progress_callback:
            progress_callback("Step 3/4: Breaking down roadmap into detailed modules and chapters...")
        
        self.outline = self.module_agent.generate_modules(
            roadmap=self.roadmap,
            language=self.language,
            output_dir=self.output_dir
        )
        
        if progress_callback:
            total_modules = len(self.outline.get("modules", []))
            total_chapters = sum(
                len(module.get("chapters", []))
                for module in self.outline.get("modules", [])
            )
            progress_callback(f"✓ Modules generated: {total_modules} modules, {total_chapters} chapters")
        
        # Step 4: Generate Content
        if progress_callback:
            progress_callback("Step 4/4: Generating content for all chapters...")
        
        self.generated_content = self.content_agent.generate_all_content(
            outline=self.outline,
            progress_callback=progress_callback
        )
        
        if progress_callback:
            progress_callback("✓ Content generation completed!")
        
        # Return comprehensive results
        return {
            "course_requirements": self.course_requirements,
            "roadmap": self.roadmap,
            "outline": self.outline,
            "content": self.generated_content,
            "requirements_file": str(self.output_dir / "course_requirements.json"),
            "roadmap_file": str(self.output_dir / "course_roadmap.json"),
            "outline_file": str(self.output_dir / "course_outline.json"),
            "content_dir": str(self.content_agent.output_dir)
        }
    
    def get_course_requirements(self) -> Optional[Dict[str, Any]]:
        """Get the course requirements from questionnaire."""
        return self.course_requirements
    
    def get_roadmap(self) -> Optional[Dict[str, Any]]:
        """Get the generated roadmap."""
        return self.roadmap
    
    def get_outline(self) -> Optional[Dict[str, Any]]:
        """Get the generated outline."""
        return self.outline
    
    def get_generated_content(self) -> Dict[str, str]:
        """Get dictionary of generated content paths."""
        return self.generated_content
    
    def save_summary(self, output_file: Optional[str] = None) -> Path:
        """
        Save a summary of the generated course.
        
        Args:
            output_file: Optional output file path
            
        Returns:
            Path to saved summary file
        """
        if not output_file:
            output_file = str(self.output_dir / "summary.json")
        
        # Count totals
        total_phases = len(self.roadmap.get("learning_path", [])) if self.roadmap else 0
        total_roadmap_modules = sum(
            len(phase.get("modules", []))
            for phase in self.roadmap.get("learning_path", [])
        ) if self.roadmap else 0
        
        total_outline_modules = len(self.outline.get("modules", [])) if self.outline else 0
        total_chapters = sum(
            len(module.get("chapters", []))
            for module in self.outline.get("modules", [])
        ) if self.outline else 0
        
        summary = {
            "topic": self.outline.get("topic", "") if self.outline else "",
            "course_title": self.roadmap.get("course_title", "") if self.roadmap else "",
            "language": self.language,
            "audience": self.outline.get("audience", "") if self.outline else "",
            "course_requirements": self.course_requirements,
            "roadmap": {
                "phases": total_phases,
                "modules": total_roadmap_modules
            },
            "outline": {
                "modules": total_outline_modules,
                "chapters": total_chapters
            },
            "content_files": list(self.generated_content.keys()),
            "files": {
                "requirements": str(self.output_dir / "course_requirements.json"),
                "roadmap": str(self.output_dir / "course_roadmap.json"),
                "outline": str(self.output_dir / "course_outline.json"),
                "content_dir": str(self.content_agent.output_dir)
            }
        }
        
        summary_path = Path(output_file)
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        return summary_path
    
    def cleanup(self) -> None:
        """Cleanup resources."""
        if self.content_agent:
            self.content_agent.cleanup()

