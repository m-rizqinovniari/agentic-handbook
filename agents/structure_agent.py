"""Structure Agent for generating learning material outlines."""

import json
from typing import Dict, Any, List
from utils.azure_openai import get_azure_openai_client, get_deployment_name


class StructureAgent:
    """Agent that generates hierarchical outline structure for learning materials."""
    
    def __init__(self):
        """Initialize Structure Agent."""
        self.client = get_azure_openai_client()
        self.deployment_name = get_deployment_name()
    
    def generate_outline(
        self, 
        topic: str, 
        language: str, 
        audience: str
    ) -> Dict[str, Any]:
        """
        Generate hierarchical outline with parts and chapters.
        
        Args:
            topic: Main topic for the learning material
            language: Language code (e.g., 'id', 'en')
            audience: Target audience level ('beginner', 'intermediate', 'advanced')
            
        Returns:
            Dictionary containing outline structure with parts and chapters
        """
        language_name = self._get_language_name(language)
        audience_description = self._get_audience_description(audience, language)
        
        prompt = self._build_prompt(topic, language_name, audience_description, language)
        
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
        return self._validate_outline(outline_json, topic)
    
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
    
    def _get_audience_description(self, audience: str, language: str) -> str:
        """Get audience description in appropriate language."""
        if language == "id":
            descriptions = {
                "beginner": "pemula yang baru memulai",
                "intermediate": "tingkat menengah dengan pengetahuan dasar",
                "advanced": "tingkat lanjut dengan pengalaman yang cukup"
            }
        else:
            descriptions = {
                "beginner": "beginners who are just starting",
                "intermediate": "intermediate level with basic knowledge",
                "advanced": "advanced level with sufficient experience"
            }
        return descriptions.get(audience, descriptions["beginner"])
    
    def _get_system_prompt(self, language: str) -> str:
        """Get system prompt based on language."""
        if language == "id":
            return """Anda adalah ahli dalam menyusun struktur pembelajaran yang efektif. 
Tugas Anda adalah membuat outline hierarkis untuk materi pembelajaran yang terorganisir dengan baik.
Outline harus dibagi menjadi Parts (bagian) dan Chapters (bab) dengan struktur yang logis dan mudah dipahami.
Output harus dalam format JSON yang valid."""
        else:
            return """You are an expert in creating effective learning structures.
Your task is to create a hierarchical outline for learning materials that is well-organized.
The outline should be divided into Parts and Chapters with a logical and easy-to-understand structure.
Output must be in valid JSON format."""
    
    def _build_prompt(
        self, 
        topic: str, 
        language_name: str, 
        audience_description: str,
        language: str
    ) -> str:
        """Build the prompt for outline generation."""
        if language == "id":
            return f"""Buatkan outline lengkap dan terstruktur untuk materi pembelajaran tentang "{topic}".

PERSYARATAN STRUKTUR PEMBELAJARAN:
1. Materi akan ditulis dalam bahasa {language_name}
2. Target audience adalah {audience_description}
3. Outline harus mengikuti ALUR PEMBELAJARAN PROGRESIF:
   - Part 1: Fondasi dan Konsep Dasar (pengenalan, dasar-dasar, prinsip fundamental)
   - Part 2-N: Pengembangan Konsep (konsep menengah, aplikasi, praktik)
   - Part Terakhir: Penerapan Lanjutan (konsep lanjutan, studi kasus, best practices)

4. Setiap Part harus memiliki beberapa Chapters (bab) yang saling berhubungan
5. Setiap Chapter harus memiliki:
   - Sections (sub-bab) yang DETAIL dan SPESIFIK - minimal 4-6 sections per chapter
   - Learning objectives yang SPESIFIK dan DAPAT DIUKUR - minimal 3-5 objectives
   - Deskripsi yang JELAS tentang apa yang akan dipelajari dalam chapter ini

6. Sections harus dirancang untuk pembelajaran bertahap:
   - Section awal: Pengenalan dan konsep dasar
   - Section tengah: Penjelasan mendalam dan detail
   - Section akhir: Contoh praktis, studi kasus, atau aplikasi

STRUKTUR YANG DIHARAPKAN:
- 3-5 Parts untuk topik yang kompleks, 2-3 Parts untuk topik sederhana
- 4-6 Chapters per Part (cukup untuk pembelajaran mendalam)
- Setiap Chapter harus memiliki 4-6 Sections yang spesifik
- Learning objectives harus spesifik, dapat diukur, dan mencakup:
  * Pemahaman konseptual
  * Aplikasi praktis
  * Analisis dan evaluasi (untuk level intermediate/advanced)

PENTING:
- Sections harus cukup detail agar dapat dijelaskan dengan mendalam (bukan hanya 1-2 sections)
- Learning objectives harus mendorong pemahaman mendalam, bukan hanya hafalan
- Struktur harus memungkinkan pembelajaran progresif dari dasar ke lanjutan

Format output JSON:
{{
  "topic": "{topic}",
  "language": "{language}",
  "audience": "{audience_description}",
  "parts": [
    {{
      "part_number": 1,
      "title": "Judul Part",
      "description": "Deskripsi lengkap tentang part ini dan bagaimana part ini membangun fondasi pembelajaran",
      "chapters": [
        {{
          "chapter_number": 1,
          "title": "Judul Chapter",
          "description": "Deskripsi lengkap chapter yang menjelaskan apa yang akan dipelajari, mengapa penting, dan bagaimana kaitannya dengan chapter sebelumnya",
          "sections": [
            "Section 1: [Judul spesifik yang jelas]",
            "Section 2: [Judul spesifik yang jelas]",
            "Section 3: [Judul spesifik yang jelas]",
            "Section 4: [Judul spesifik yang jelas]"
          ],
          "learning_objectives": [
            "Objective 1: [Spesifik dan dapat diukur]",
            "Objective 2: [Spesifik dan dapat diukur]",
            "Objective 3: [Spesifik dan dapat diukur]"
          ]
        }}
      ]
    }}
  ]
}}"""
        else:
            return f"""Create a complete and well-structured outline for learning materials about "{topic}".

LEARNING STRUCTURE REQUIREMENTS:
1. Material will be written in {language_name}
2. Target audience is {audience_description}
3. Outline must follow a PROGRESSIVE LEARNING FLOW:
   - Part 1: Foundations and Basic Concepts (introduction, fundamentals, core principles)
   - Part 2-N: Concept Development (intermediate concepts, applications, practices)
   - Final Part: Advanced Application (advanced concepts, case studies, best practices)

4. Each Part must have several Chapters that are interconnected
5. Each Chapter must have:
   - Sections (sub-sections) that are DETAILED and SPECIFIC - minimum 4-6 sections per chapter
   - Learning objectives that are SPECIFIC and MEASURABLE - minimum 3-5 objectives
   - Clear description of what will be learned in this chapter

6. Sections must be designed for progressive learning:
   - Early sections: Introduction and basic concepts
   - Middle sections: In-depth explanations and details
   - Final sections: Practical examples, case studies, or applications

EXPECTED STRUCTURE:
- 3-5 Parts for complex topics, 2-3 Parts for simple topics
- 4-6 Chapters per Part (enough for in-depth learning)
- Each Chapter must have 4-6 specific Sections
- Learning objectives must be specific, measurable, and cover:
  * Conceptual understanding
  * Practical application
  * Analysis and evaluation (for intermediate/advanced levels)

IMPORTANT:
- Sections must be detailed enough to be explained in-depth (not just 1-2 sections)
- Learning objectives must encourage deep understanding, not just memorization
- Structure must enable progressive learning from basics to advanced

JSON output format:
{{
  "topic": "{topic}",
  "language": "{language}",
  "audience": "{audience_description}",
  "parts": [
    {{
      "part_number": 1,
      "title": "Part Title",
      "description": "Complete description of this part and how it builds the learning foundation",
      "chapters": [
        {{
          "chapter_number": 1,
          "title": "Chapter Title",
          "description": "Complete chapter description explaining what will be learned, why it's important, and how it relates to previous chapters",
          "sections": [
            "Section 1: [Specific and clear title]",
            "Section 2: [Specific and clear title]",
            "Section 3: [Specific and clear title]",
            "Section 4: [Specific and clear title]"
          ],
          "learning_objectives": [
            "Objective 1: [Specific and measurable]",
            "Objective 2: [Specific and measurable]",
            "Objective 3: [Specific and measurable]"
          ]
        }}
      ]
    }}
  ]
}}"""
    
    def _validate_outline(self, outline: Dict[str, Any], topic: str) -> Dict[str, Any]:
        """
        Validate and ensure outline structure is correct.
        
        Args:
            outline: Generated outline dictionary
            topic: Original topic
            
        Returns:
            Validated outline dictionary
        """
        # Ensure required fields exist
        if "parts" not in outline:
            raise ValueError("Outline must contain 'parts' field")
        
        if not isinstance(outline["parts"], list) or len(outline["parts"]) == 0:
            raise ValueError("Outline must have at least one part")
        
        # Validate and fix part structure
        for i, part in enumerate(outline["parts"]):
            if "part_number" not in part:
                part["part_number"] = i + 1
            if "chapters" not in part:
                part["chapters"] = []
            if not isinstance(part["chapters"], list):
                part["chapters"] = []
            
            # Validate and fix chapter structure
            for j, chapter in enumerate(part["chapters"]):
                if "chapter_number" not in chapter:
                    chapter["chapter_number"] = j + 1
                if "sections" not in chapter:
                    chapter["sections"] = []
                if "learning_objectives" not in chapter:
                    chapter["learning_objectives"] = []
                if "description" not in chapter:
                    chapter["description"] = ""
        
        # Ensure topic is set
        outline["topic"] = topic
        
        return outline

