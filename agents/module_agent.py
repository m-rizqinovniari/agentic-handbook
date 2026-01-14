"""Module Agent for breaking down roadmap into detailed modules with chapters."""

import json
from typing import Dict, Any, Optional
from pathlib import Path
from utils.azure_openai import get_azure_openai_client, get_deployment_name


class ModuleAgent:
    """Agent that breaks down roadmap into detailed module structure with chapters."""
    
    def __init__(self):
        """Initialize Module Agent."""
        self.client = get_azure_openai_client()
        self.deployment_name = get_deployment_name()
    
    def generate_modules(
        self,
        roadmap: Dict[str, Any],
        language: str = "id",
        output_dir: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        Break down roadmap into detailed module structure with chapters.
        
        Args:
            roadmap: Roadmap structure from RoadmapAgent
            language: Language code (e.g., 'id', 'en')
            output_dir: Optional directory to save outline JSON
            
        Returns:
            Dictionary containing module structure with chapters
        """
        language_name = self._get_language_name(language)
        
        prompt = self._build_prompt(
            roadmap=roadmap,
            language_name=language_name,
            language=language
        )
        
        response = self.client.chat.completions.create(
            model=self.deployment_name,
            messages=[
                {
                    "role": "system",
                    "content": self._get_system_prompt(language)
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            response_format={"type": "json_object"}
        )
        
        outline_json = json.loads(response.choices[0].message.content)
        
        # Validate and structure the outline
        validated_outline = self._validate_outline(outline_json, roadmap, language)
        
        # Also generate legacy "parts" structure for backward compatibility
        validated_outline = self._add_parts_structure(validated_outline)
        
        # Save to file if output_dir provided
        if output_dir:
            output_path = Path(output_dir) / "course_outline.json"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(validated_outline, f, indent=2, ensure_ascii=False)
            
            # Also save as legacy outline.json for backward compatibility
            legacy_path = Path(output_dir) / "outline.json"
            legacy_outline = {
                "topic": validated_outline.get("topic", ""),
                "language": validated_outline.get("language", ""),
                "audience": validated_outline.get("audience", ""),
                "parts": validated_outline.get("parts", [])
            }
            with open(legacy_path, 'w', encoding='utf-8') as f:
                json.dump(legacy_outline, f, indent=2, ensure_ascii=False)
        
        return validated_outline
    
    def _get_language_name(self, language_code: str) -> str:
        """Get language name from code."""
        language_map = {
            "id": "Bahasa Indonesia",
            "en": "English",
            "es": "Spanish",
            "fr": "French",
            "de": "German",
            "pt": "Portuguese",
            "zh": "Chinese",
            "ja": "Japanese",
            "ko": "Korean"
        }
        return language_map.get(language_code, "English")
    
    def _get_system_prompt(self, language: str) -> str:
        """Get system prompt based on language."""
        if language == "id":
            return """Anda adalah ahli dalam memecah roadmap course menjadi modul-modul pembelajaran yang detail dan terstruktur.

Tugas Anda adalah:
1. MENGURAIKAN roadmap menjadi modul-modul yang jelas dengan chapters yang detail
2. SETIAP MODUL harus memiliki chapters yang mencakup semua topik yang disebutkan di roadmap
3. SETIAP CHAPTER harus memiliki:
   - Sections (sub-bab) yang DETAIL dan SPESIFIK - minimal 4-6 sections per chapter
   - Learning objectives yang SPESIFIK dan DAPAT DIUKUR - minimal 3-5 objectives
   - Deskripsi yang JELAS tentang apa yang akan dipelajari
4. Struktur harus LOGIS dan PROGRESIF - setiap chapter membangun dari chapter sebelumnya
5. Pastikan semua topik dari roadmap tercakup dalam chapters

Output harus dalam format JSON yang valid dengan struktur modules dan chapters."""
        else:
            return """You are an expert in breaking down course roadmaps into detailed and well-structured learning modules.

Your task is to:
1. BREAK DOWN the roadmap into clear modules with detailed chapters
2. EACH MODULE must have chapters that cover all topics mentioned in the roadmap
3. EACH CHAPTER must have:
   - Sections (sub-sections) that are DETAILED and SPECIFIC - minimum 4-6 sections per chapter
   - Learning objectives that are SPECIFIC and MEASURABLE - minimum 3-5 objectives
   - Clear description of what will be learned
4. Structure must be LOGICAL and PROGRESSIVE - each chapter builds on previous chapters
5. Ensure all topics from roadmap are covered in chapters

Output must be in valid JSON format with modules and chapters structure."""
    
    def _build_prompt(
        self,
        roadmap: Dict[str, Any],
        language_name: str,
        language: str
    ) -> str:
        """Build the prompt for module breakdown."""
        
        course_title = roadmap.get("course_title", "")
        course_description = roadmap.get("course_description", "")
        learning_path = roadmap.get("learning_path", [])
        
        # Build roadmap summary
        roadmap_summary = ""
        for phase in learning_path:
            phase_name = phase.get("phase", "")
            phase_desc = phase.get("description", "")
            modules = phase.get("modules", [])
            
            roadmap_summary += f"\n\nFase: {phase_name}\n"
            roadmap_summary += f"Deskripsi: {phase_desc}\n"
            roadmap_summary += f"Modul-modul:\n"
            
            for module in modules:
                module_name = module.get("module_name", "")
                module_desc = module.get("description", "")
                module_time = module.get("estimated_time", "")
                topics = module.get("topics", [])
                
                roadmap_summary += f"  - {module_name}\n"
                roadmap_summary += f"    Deskripsi: {module_desc}\n"
                roadmap_summary += f"    Waktu: {module_time}\n"
                roadmap_summary += f"    Topik: {', '.join(topics)}\n"
        
        if language == "id":
            return f"""Berdasarkan roadmap course berikut, buatkan struktur modul dan chapter yang DETAIL dan KOMPREHENSIF.

INFORMASI COURSE:
- Judul: {course_title}
- Deskripsi: {course_description}
- Bahasa: {language_name}

ROADMAP YANG PERLU DIURAIKAN:
{roadmap_summary}

PERSYARATAN BREAKDOWN:
1. Setiap MODUL dari roadmap harus diuraikan menjadi CHAPTERS yang detail
2. Setiap CHAPTER harus memiliki:
   - Sections (sub-bab) yang DETAIL dan SPESIFIK - minimal 4-6 sections per chapter
   - Learning objectives yang SPESIFIK dan DAPAT DIUKUR - minimal 3-5 objectives per chapter
   - Deskripsi yang JELAS dan LENGKAP tentang apa yang akan dipelajari dalam chapter ini
   - Pastikan semua topik dari modul roadmap tercakup dalam chapters

3. Sections harus dirancang untuk pembelajaran bertahap:
   - Section awal: Pengenalan dan konsep dasar
   - Section tengah: Penjelasan mendalam dan detail
   - Section akhir: Contoh praktis, studi kasus, atau aplikasi

4. Struktur harus LOGIS dan PROGRESIF:
   - Chapters dalam modul harus saling berhubungan
   - Setiap chapter membangun dari chapter sebelumnya
   - Alur pembelajaran harus jelas dan mudah diikuti

5. Pastikan:
   - Semua topik dari roadmap tercakup
   - Setiap modul memiliki cukup chapters untuk pembelajaran mendalam
   - Learning objectives spesifik dan dapat diukur
   - Sections cukup detail untuk penjelasan mendalam

FORMAT OUTPUT JSON:
{{
  "topic": "{course_title}",
  "language": "{roadmap.get('language', 'id')}",
  "audience": "{roadmap.get('audience', 'intermediate')}",
  "modules": [
    {{
      "module_number": 1,
      "module_name": "Nama Modul dari Roadmap",
      "module_slug": "module-1",
      "description": "Deskripsi lengkap modul",
      "chapters": [
        {{
          "chapter_number": 1,
          "title": "Judul Chapter",
          "description": "Deskripsi lengkap chapter yang menjelaskan apa yang akan dipelajari, mengapa penting, dan bagaimana kaitannya dengan chapter sebelumnya",
          "sections": [
            "Section 1: [Judul spesifik yang jelas]",
            "Section 2: [Judul spesifik yang jelas]",
            "Section 3: [Judul spesifik yang jelas]",
            "Section 4: [Judul spesifik yang jelas]",
            "Section 5: [Judul spesifik yang jelas]",
            "Section 6: [Judul spesifik yang jelas]"
          ],
          "learning_objectives": [
            "Objective 1: [Spesifik dan dapat diukur]",
            "Objective 2: [Spesifik dan dapat diukur]",
            "Objective 3: [Spesifik dan dapat diukur]",
            "Objective 4: [Spesifik dan dapat diukur]",
            "Objective 5: [Spesifik dan dapat diukur]"
          ]
        }},
        {{
          "chapter_number": 2,
          "title": "Judul Chapter Berikutnya",
          "description": "...",
          "sections": [...],
          "learning_objectives": [...]
        }}
      ]
    }},
    {{
      "module_number": 2,
      "module_name": "Modul Berikutnya",
      "module_slug": "module-2",
      "description": "...",
      "chapters": [...]
    }}
  ]
}}

PENTING:
- Pastikan semua modul dari roadmap diuraikan menjadi chapters
- Setiap chapter harus memiliki minimal 4-6 sections
- Setiap chapter harus memiliki minimal 3-5 learning objectives
- Struktur harus progresif dan logis
- Gunakan format JSON yang valid"""
        else:
            return f"""Based on the following course roadmap, create a DETAILED and COMPREHENSIVE module and chapter structure.

COURSE INFORMATION:
- Title: {course_title}
- Description: {course_description}
- Language: {language_name}

ROADMAP TO BREAK DOWN:
{roadmap_summary}

BREAKDOWN REQUIREMENTS:
1. Each MODULE from the roadmap must be broken down into detailed CHAPTERS
2. Each CHAPTER must have:
   - Sections (sub-sections) that are DETAILED and SPECIFIC - minimum 4-6 sections per chapter
   - Learning objectives that are SPECIFIC and MEASURABLE - minimum 3-5 objectives per chapter
   - Clear and COMPLETE description of what will be learned in this chapter
   - Ensure all topics from the roadmap module are covered in chapters

3. Sections must be designed for progressive learning:
   - Early sections: Introduction and basic concepts
   - Middle sections: In-depth explanations and details
   - Final sections: Practical examples, case studies, or applications

4. Structure must be LOGICAL and PROGRESSIVE:
   - Chapters within module must be interconnected
   - Each chapter builds on previous chapters
   - Learning flow must be clear and easy to follow

5. Ensure:
   - All topics from roadmap are covered
   - Each module has enough chapters for in-depth learning
   - Learning objectives are specific and measurable
   - Sections are detailed enough for in-depth explanations

JSON OUTPUT FORMAT:
{{
  "topic": "{course_title}",
  "language": "{roadmap.get('language', 'en')}",
  "audience": "{roadmap.get('audience', 'intermediate')}",
  "modules": [
    {{
      "module_number": 1,
      "module_name": "Module Name from Roadmap",
      "module_slug": "module-1",
      "description": "Complete module description",
      "chapters": [
        {{
          "chapter_number": 1,
          "title": "Chapter Title",
          "description": "Complete chapter description explaining what will be learned, why it's important, and how it relates to previous chapters",
          "sections": [
            "Section 1: [Specific and clear title]",
            "Section 2: [Specific and clear title]",
            "Section 3: [Specific and clear title]",
            "Section 4: [Specific and clear title]",
            "Section 5: [Specific and clear title]",
            "Section 6: [Specific and clear title]"
          ],
          "learning_objectives": [
            "Objective 1: [Specific and measurable]",
            "Objective 2: [Specific and measurable]",
            "Objective 3: [Specific and measurable]",
            "Objective 4: [Specific and measurable]",
            "Objective 5: [Specific and measurable]"
          ]
        }},
        {{
          "chapter_number": 2,
          "title": "Next Chapter Title",
          "description": "...",
          "sections": [...],
          "learning_objectives": [...]
        }}
      ]
    }},
    {{
      "module_number": 2,
      "module_name": "Next Module",
      "module_slug": "module-2",
      "description": "...",
      "chapters": [...]
    }}
  ]
}}

IMPORTANT:
- Ensure all modules from roadmap are broken down into chapters
- Each chapter must have minimum 4-6 sections
- Each chapter must have minimum 3-5 learning objectives
- Structure must be progressive and logical
- Use valid JSON format"""
    
    def _validate_outline(
        self,
        outline: Dict[str, Any],
        roadmap: Dict[str, Any],
        language: str
    ) -> Dict[str, Any]:
        """
        Validate and ensure outline structure is correct.
        
        Args:
            outline: Generated outline dictionary
            roadmap: Original roadmap
            language: Language code
            
        Returns:
            Validated outline dictionary
        """
        # Ensure required fields exist
        if "modules" not in outline:
            raise ValueError("Outline must contain 'modules' field")
        
        if not isinstance(outline["modules"], list) or len(outline["modules"]) == 0:
            raise ValueError("Outline must have at least one module")
        
        # Validate and fix module structure
        chapter_counter = 1
        for i, module in enumerate(outline["modules"]):
            if "module_number" not in module:
                module["module_number"] = i + 1
            
            if "module_name" not in module:
                module["module_name"] = f"Module {i + 1}"
            
            if "module_slug" not in module:
                module["module_slug"] = f"module-{i + 1}"
            
            if "description" not in module:
                module["description"] = ""
            
            if "chapters" not in module:
                module["chapters"] = []
            
            if not isinstance(module["chapters"], list):
                module["chapters"] = []
            
            # Validate and fix chapter structure
            for j, chapter in enumerate(module["chapters"]):
                if "chapter_number" not in chapter:
                    chapter["chapter_number"] = chapter_counter
                    chapter_counter += 1
                
                if "title" not in chapter:
                    chapter["title"] = f"Chapter {chapter['chapter_number']}"
                
                if "description" not in chapter:
                    chapter["description"] = ""
                
                if "sections" not in chapter:
                    chapter["sections"] = []
                
                if "learning_objectives" not in chapter:
                    chapter["learning_objectives"] = []
        
        # Ensure topic, language, and audience are set
        outline["topic"] = roadmap.get("course_title", roadmap.get("topic", ""))
        outline["language"] = language
        outline["audience"] = roadmap.get("audience", roadmap.get("level", "intermediate"))
        
        return outline
    
    def _add_parts_structure(self, outline: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add legacy "parts" structure for backward compatibility.
        Converts modules to parts structure.
        
        Args:
            outline: Outline with modules structure
            
        Returns:
            Outline with both modules and parts structure
        """
        modules = outline.get("modules", [])
        parts = []
        
        for module in modules:
            part = {
                "part_number": module.get("module_number", 1),
                "title": module.get("module_name", ""),
                "description": module.get("description", ""),
                "chapters": module.get("chapters", [])
            }
            parts.append(part)
        
        outline["parts"] = parts
        return outline

