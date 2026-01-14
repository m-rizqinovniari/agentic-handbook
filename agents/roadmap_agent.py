"""Roadmap Agent for generating comprehensive course roadmap."""

import json
from typing import Dict, Any, Optional
from pathlib import Path
from utils.azure_openai import get_azure_openai_client, get_deployment_name


class RoadmapAgent:
    """Agent that generates course roadmap in roadmap.sh-like format."""
    
    def __init__(self):
        """Initialize Roadmap Agent."""
        self.client = get_azure_openai_client()
        self.deployment_name = get_deployment_name()
    
    def generate_roadmap(
        self,
        topic: str,
        course_requirements: Dict[str, Any],
        language: str = "id",
        audience: str = "intermediate",
        output_dir: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        Generate course roadmap structure.
        
        Args:
            topic: Main topic for the course
            course_requirements: Dictionary from CourseQuestionnaire
            language: Language code (e.g., 'id', 'en')
            audience: Target audience level
            output_dir: Optional directory to save roadmap JSON
            
        Returns:
            Dictionary containing roadmap structure
        """
        language_name = self._get_language_name(language)
        audience_description = self._get_audience_description(audience, language)
        
        prompt = self._build_prompt(
            topic=topic,
            course_requirements=course_requirements,
            language_name=language_name,
            audience_description=audience_description,
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
        
        roadmap_json = json.loads(response.choices[0].message.content)
        
        # Validate and structure the roadmap
        validated_roadmap = self._validate_roadmap(roadmap_json, topic, language, audience)
        
        # Save to file if output_dir provided
        if output_dir:
            output_path = Path(output_dir) / "course_roadmap.json"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(validated_roadmap, f, indent=2, ensure_ascii=False)
        
        return validated_roadmap
    
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
        return descriptions.get(audience, descriptions["intermediate"])
    
    def _get_system_prompt(self, language: str) -> str:
        """Get system prompt based on language."""
        if language == "id":
            return """Anda adalah ahli dalam membuat roadmap course pembelajaran yang komprehensif dan terstruktur.

Tugas Anda adalah membuat roadmap course yang:
1. KOMPREHENSIF - Mencakup semua aspek penting dari topik dari dasar hingga tingkat lanjut
2. TERSTRUKTUR - Dibagi menjadi fase-fase pembelajaran yang logis dan progresif
3. DETAIL - Setiap fase memiliki modul-modul yang jelas dengan deskripsi, waktu estimasi, dan topik-topik yang akan dipelajari
4. PRAKTIS - Mempertimbangkan kebutuhan praktis dan aplikasi real-world
5. PROGRESIF - Alur pembelajaran yang membangun dari konsep dasar ke konsep yang lebih kompleks

Roadmap harus dalam format JSON yang valid dengan struktur yang jelas."""
        else:
            return """You are an expert in creating comprehensive and well-structured course roadmaps.

Your task is to create a course roadmap that is:
1. COMPREHENSIVE - Covers all important aspects of the topic from basics to advanced level
2. STRUCTURED - Divided into logical and progressive learning phases
3. DETAILED - Each phase has clear modules with descriptions, time estimates, and topics to be learned
4. PRACTICAL - Considers practical needs and real-world applications
5. PROGRESSIVE - Learning flow that builds from basic concepts to more complex ones

The roadmap must be in valid JSON format with clear structure."""
    
    def _build_prompt(
        self,
        topic: str,
        course_requirements: Dict[str, Any],
        language_name: str,
        audience_description: str,
        language: str
    ) -> str:
        """Build the prompt for roadmap generation."""
        
        # Extract requirements
        learning_goals = course_requirements.get("learning_goals", "")
        time_dedication = course_requirements.get("time_dedication", "")
        prior_knowledge = course_requirements.get("prior_knowledge", "")
        learning_focus = course_requirements.get("learning_focus", "")
        expected_outcomes = course_requirements.get("expected_outcomes", "")
        
        # Map learning focus
        focus_map = {
            "1": "Teori mendalam" if language == "id" else "In-depth theory",
            "2": "Praktik dan implementasi" if language == "id" else "Practice and implementation",
            "3": "Kombinasi teori dan praktik" if language == "id" else "Combination of theory and practice",
            "4": "Studi kasus dan aplikasi real-world" if language == "id" else "Case studies and real-world applications"
        }
        learning_focus_text = focus_map.get(learning_focus, learning_focus)
        
        if language == "id":
            return f"""Buatkan roadmap course pembelajaran yang KOMPREHENSIF untuk topik: "{topic}"

KONTEKS KURSUS:
- Topik: {topic}
- Bahasa: {language_name}
- Target Audience: {audience_description}
- Tujuan Pembelajaran: {learning_goals}
- Waktu Dedikasi: {time_dedication}
- Pengetahuan Awal: {prior_knowledge}
- Fokus Pembelajaran: {learning_focus_text}
- Hasil yang Diharapkan: {expected_outcomes}

PERSYARATAN ROADMAP:
1. Roadmap harus KOMPREHENSIF dan mencakup semua aspek penting dari topik
2. Dibagi menjadi 3-5 fase pembelajaran yang progresif:
   - Fase Foundation: Konsep dasar, pengenalan, fondasi yang kuat
   - Fase Intermediate: Pengembangan konsep, aplikasi dasar, praktik
   - Fase Advanced: Konsep lanjutan, aplikasi kompleks, best practices
   - (Opsional) Fase Expert: Topik spesialisasi, optimasi, edge cases

3. Setiap fase harus memiliki:
   - Deskripsi yang jelas tentang apa yang akan dipelajari
   - 2-4 modul pembelajaran
   - Setiap modul harus memiliki:
     * Nama modul yang jelas dan deskriptif
     * Deskripsi lengkap tentang konten modul
     * Estimasi waktu pembelajaran (disesuaikan dengan waktu dedikasi: {time_dedication})
     * Prerequisites (jika ada)
     * Daftar topik-topik utama yang akan dipelajari

4. Roadmap harus mempertimbangkan:
   - Fokus pembelajaran: {learning_focus_text}
   - Hasil yang diharapkan: {expected_outcomes}
   - Pengetahuan awal: {prior_knowledge}
   - Waktu yang tersedia: {time_dedication}

5. Alur pembelajaran harus LOGIS dan PROGRESIF:
   - Setiap fase membangun dari fase sebelumnya
   - Modul-modul dalam fase harus saling terkait
   - Prerequisites harus jelas dan masuk akal

FORMAT OUTPUT JSON:
{{
  "course_title": "Judul Course yang Komprehensif",
  "course_description": "Deskripsi lengkap course yang menjelaskan apa yang akan dipelajari, untuk siapa, dan manfaatnya",
  "estimated_duration": "Estimasi total durasi (contoh: '8 minggu', '40 jam')",
  "level": "{audience_description}",
  "course_objectives": [
    "Objective 1: Spesifik dan dapat diukur",
    "Objective 2: Spesifik dan dapat diukur",
    "Objective 3: Spesifik dan dapat diukur"
  ],
  "learning_path": [
    {{
      "phase": "Foundation",
      "description": "Deskripsi lengkap tentang fase ini dan apa yang akan dipelajari",
      "modules": [
        {{
          "module_name": "Nama Modul",
          "description": "Deskripsi lengkap modul",
          "estimated_time": "Estimasi waktu (contoh: '2 minggu', '10 jam')",
          "prerequisites": ["Prerequisite 1", "Prerequisite 2"],
          "topics": ["Topic 1", "Topic 2", "Topic 3"]
        }}
      ]
    }},
    {{
      "phase": "Intermediate",
      "description": "...",
      "modules": [...]
    }},
    {{
      "phase": "Advanced",
      "description": "...",
      "modules": [...]
    }}
  ]
}}

PENTING:
- Pastikan roadmap MENCUKUPI untuk course yang komprehensif
- Setiap modul harus memiliki konten yang cukup untuk pembelajaran mendalam
- Estimasi waktu harus realistis berdasarkan waktu dedikasi: {time_dedication}
- Roadmap harus mengarah ke hasil yang diharapkan: {expected_outcomes}
- Gunakan format JSON yang valid"""
        else:
            return f"""Create a COMPREHENSIVE course roadmap for topic: "{topic}"

COURSE CONTEXT:
- Topic: {topic}
- Language: {language_name}
- Target Audience: {audience_description}
- Learning Goals: {learning_goals}
- Time Dedication: {time_dedication}
- Prior Knowledge: {prior_knowledge}
- Learning Focus: {learning_focus_text}
- Expected Outcomes: {expected_outcomes}

ROADMAP REQUIREMENTS:
1. Roadmap must be COMPREHENSIVE and cover all important aspects of the topic
2. Divided into 3-5 progressive learning phases:
   - Foundation Phase: Basic concepts, introduction, strong foundation
   - Intermediate Phase: Concept development, basic applications, practice
   - Advanced Phase: Advanced concepts, complex applications, best practices
   - (Optional) Expert Phase: Specialization topics, optimization, edge cases

3. Each phase must have:
   - Clear description of what will be learned
   - 2-4 learning modules
   - Each module must have:
     * Clear and descriptive module name
     * Complete description of module content
     * Time estimate (adjusted to time dedication: {time_dedication})
     * Prerequisites (if any)
     * List of main topics to be learned

4. Roadmap must consider:
   - Learning focus: {learning_focus_text}
   - Expected outcomes: {expected_outcomes}
   - Prior knowledge: {prior_knowledge}
   - Available time: {time_dedication}

5. Learning flow must be LOGICAL and PROGRESSIVE:
   - Each phase builds on previous phases
   - Modules within phase must be interconnected
   - Prerequisites must be clear and reasonable

JSON OUTPUT FORMAT:
{{
  "course_title": "Comprehensive Course Title",
  "course_description": "Complete course description explaining what will be learned, for whom, and benefits",
  "estimated_duration": "Total duration estimate (e.g., '8 weeks', '40 hours')",
  "level": "{audience_description}",
  "course_objectives": [
    "Objective 1: Specific and measurable",
    "Objective 2: Specific and measurable",
    "Objective 3: Specific and measurable"
  ],
  "learning_path": [
    {{
      "phase": "Foundation",
      "description": "Complete description of this phase and what will be learned",
      "modules": [
        {{
          "module_name": "Module Name",
          "description": "Complete module description",
          "estimated_time": "Time estimate (e.g., '2 weeks', '10 hours')",
          "prerequisites": ["Prerequisite 1", "Prerequisite 2"],
          "topics": ["Topic 1", "Topic 2", "Topic 3"]
        }}
      ]
    }},
    {{
      "phase": "Intermediate",
      "description": "...",
      "modules": [...]
    }},
    {{
      "phase": "Advanced",
      "description": "...",
      "modules": [...]
    }}
  ]
}}

IMPORTANT:
- Ensure roadmap is SUFFICIENT for a comprehensive course
- Each module must have enough content for in-depth learning
- Time estimates must be realistic based on time dedication: {time_dedication}
- Roadmap must lead to expected outcomes: {expected_outcomes}
- Use valid JSON format"""
    
    def _validate_roadmap(
        self,
        roadmap: Dict[str, Any],
        topic: str,
        language: str,
        audience: str
    ) -> Dict[str, Any]:
        """
        Validate and ensure roadmap structure is correct.
        
        Args:
            roadmap: Generated roadmap dictionary
            topic: Original topic
            language: Language code
            audience: Audience level
            
        Returns:
            Validated roadmap dictionary
        """
        # Ensure required fields exist
        if "course_title" not in roadmap:
            roadmap["course_title"] = topic
        
        if "course_description" not in roadmap:
            roadmap["course_description"] = f"Comprehensive course about {topic}"
        
        if "learning_path" not in roadmap:
            roadmap["learning_path"] = []
        
        if not isinstance(roadmap["learning_path"], list) or len(roadmap["learning_path"]) == 0:
            raise ValueError("Roadmap must have at least one phase in learning_path")
        
        # Validate and fix phase structure
        for i, phase in enumerate(roadmap["learning_path"]):
            if "phase" not in phase:
                phase["phase"] = f"Phase {i + 1}"
            
            if "description" not in phase:
                phase["description"] = ""
            
            if "modules" not in phase:
                phase["modules"] = []
            
            if not isinstance(phase["modules"], list):
                phase["modules"] = []
            
            # Validate and fix module structure
            for j, module in enumerate(phase["modules"]):
                if "module_name" not in module:
                    module["module_name"] = f"Module {j + 1}"
                
                if "description" not in module:
                    module["description"] = ""
                
                if "estimated_time" not in module:
                    module["estimated_time"] = ""
                
                if "prerequisites" not in module:
                    module["prerequisites"] = []
                
                if "topics" not in module:
                    module["topics"] = []
        
        # Ensure topic, language, and audience are set
        roadmap["topic"] = topic
        roadmap["language"] = language
        roadmap["audience"] = audience
        
        # Set default estimated_duration if not present
        if "estimated_duration" not in roadmap:
            roadmap["estimated_duration"] = ""
        
        # Set default level if not present
        if "level" not in roadmap:
            roadmap["level"] = audience
        
        # Set default course_objectives if not present
        if "course_objectives" not in roadmap:
            roadmap["course_objectives"] = []
        
        return roadmap

