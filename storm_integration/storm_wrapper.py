"""STORM wrapper for generating learning material content."""

import os
import sys
from typing import Dict, Any, Optional, Callable
from pathlib import Path

# Lazy import STORM modules to avoid DLL errors on Windows
# We'll import them only when needed
STORM_AVAILABLE = False
StormRunner = None
StormRunnerArgument = None
LMConfig = None

def _try_import_storm():
    """Try to import STORM modules. Returns True if successful."""
    global STORM_AVAILABLE, StormRunner, StormRunnerArgument, LMConfig
    
    if STORM_AVAILABLE:
        return True
    
    try:
        # Setup STORM environment before importing
        from storm_integration.config import setup_storm_environment, get_storm_lm_config
        setup_storm_environment()
        
        # Now try to import STORM modules
        from knowledge_storm import StormRunner as _StormRunner, StormRunnerArgument as _StormRunnerArgument
        from knowledge_storm.interface import LMConfig as _LMConfig
        
        StormRunner = _StormRunner
        StormRunnerArgument = _StormRunnerArgument
        LMConfig = _LMConfig
        STORM_AVAILABLE = True
        return True
    except OSError as e:
        # DLL loading error (Windows PyTorch issue)
        print(f"Warning: STORM cannot be loaded due to DLL error: {e}")
        print("This is likely a PyTorch compatibility issue on Windows.")
        print("STORM features will be disabled. Using fallback content generation.")
        return False
    except ImportError as e:
        print(f"Warning: STORM modules not available: {e}")
        print("STORM features will be disabled. Using fallback content generation.")
        return False
    except Exception as e:
        print(f"Warning: Error initializing STORM: {e}")
        print("STORM features will be disabled. Using fallback content generation.")
        return False


class StormWrapper:
    """Wrapper for STORM to generate learning material content."""
    
    def __init__(
        self,
        language: str = "id",
        retriever: str = "bing",
        output_dir: Optional[str] = None
    ):
        """
        Initialize STORM wrapper.
        
        Args:
            language: Language code for content generation
            retriever: Retrieval method ('bing', 'wiki', or 'duckduckgo')
            output_dir: Directory for STORM output files
        """
        self.language = language
        self.retriever = retriever
        self.output_dir = Path(output_dir) if output_dir else Path("output/storm")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Try to import STORM
        self.storm_available = _try_import_storm()
        
        if self.storm_available:
            # Setup LM configuration
            from storm_integration.config import get_storm_lm_config
            lm_config_dict = get_storm_lm_config()
            self.lm_config = LMConfig(
                provider=lm_config_dict["provider"],
                model=lm_config_dict["model"],
                api_base=lm_config_dict["api_base"],
                api_key=lm_config_dict["api_key"],
                api_version=lm_config_dict["api_version"]
            )
            
            # Setup runner arguments
            self.runner_argument = StormRunnerArgument(
                retriever=retriever,
                do_research=True,
                do_generate_outline=False,  # We use our own Structure Agent
                do_generate_article=True,
                do_polish_article=True,
                output_dir=str(self.output_dir)
            )
        else:
            # Fallback: Use Azure OpenAI directly
            from utils.azure_openai import get_azure_openai_client, get_deployment_name
            try:
                self.client = get_azure_openai_client()
                self.deployment_name = get_deployment_name()
            except Exception as e:
                raise RuntimeError(f"Failed to initialize Azure OpenAI client: {e}")
            self.lm_config = None
            self.runner_argument = None
        
        self.runner: Optional[Any] = None
    
    def initialize(self) -> None:
        """Initialize STORM runner or fallback."""
        if not self.storm_available:
            # No initialization needed for fallback
            return
        
        try:
            self.runner = StormRunner(
                lm_config=self.lm_config,
                runner_argument=self.runner_argument
            )
        except Exception as e:
            print(f"Warning: Failed to initialize STORM runner: {e}")
            print("Falling back to direct Azure OpenAI content generation.")
            self.storm_available = False
            from utils.azure_openai import get_azure_openai_client, get_deployment_name
            self.client = get_azure_openai_client()
            self.deployment_name = get_deployment_name()
    
    def generate_content(
        self,
        topic: str,
        chapter_context: Optional[Dict[str, Any]] = None,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> str:
        """
        Generate content for a specific topic/chapter using STORM or fallback.
        
        Args:
            topic: Topic or chapter title to generate content for
            chapter_context: Optional context about the chapter (sections, objectives)
            progress_callback: Optional callback function for progress updates
            
        Returns:
            Generated markdown content
        """
        if not self.storm_available:
            # Use fallback: Direct Azure OpenAI generation
            return self._generate_content_fallback(topic, chapter_context, progress_callback)
        
        if not self.runner:
            self.initialize()
        
        # If STORM still not available after initialization, use fallback
        if not self.storm_available:
            return self._generate_content_fallback(topic, chapter_context, progress_callback)
        
        if progress_callback:
            progress_callback(f"Starting STORM research for: {topic}")
        
        # Build enhanced topic with context
        enhanced_topic = self._build_enhanced_topic(topic, chapter_context)
        
        try:
            # Run STORM pipeline
            if progress_callback:
                progress_callback(f"Researching topic: {enhanced_topic}")
            
            # STORM will do research, generate article, and polish
            result = self.runner.run(enhanced_topic)
            
            if progress_callback:
                progress_callback(f"Content generation completed for: {topic}")
            
            # Extract article content
            article = result.get("article", "")
            
            # Format for learning material (not Wikipedia style)
            formatted_content = self._format_for_learning_material(
                article, 
                topic, 
                chapter_context
            )
            
            return formatted_content
            
        except Exception as e:
            error_msg = f"Error generating content with STORM for {topic}: {e}"
            if progress_callback:
                progress_callback(f"Warning: {error_msg}")
                progress_callback("Falling back to direct content generation...")
            
            # Fallback to direct generation
            return self._generate_content_fallback(topic, chapter_context, progress_callback)
    
    def _build_enhanced_topic(
        self, 
        topic: str, 
        chapter_context: Optional[Dict[str, Any]]
    ) -> str:
        """Build enhanced topic string with context."""
        if not chapter_context:
            return topic
        
        enhanced = f"{topic}"
        
        if chapter_context.get("description"):
            enhanced += f"\n\nContext: {chapter_context['description']}"
        
        if chapter_context.get("sections"):
            sections = ", ".join(chapter_context["sections"])
            enhanced += f"\n\nKey sections to cover: {sections}"
        
        if chapter_context.get("learning_objectives"):
            objectives = "\n- ".join(chapter_context["learning_objectives"])
            enhanced += f"\n\nLearning objectives:\n- {objectives}"
        
        # Add language instruction
        language_instruction = self._get_language_instruction()
        enhanced += f"\n\n{language_instruction}"
        
        return enhanced
    
    def _get_language_instruction(self) -> str:
        """Get language instruction based on language code."""
        if self.language == "id":
            return "PENTING: Tulis semua konten dalam Bahasa Indonesia. Gunakan gaya penulisan yang ramah dan mudah dipahami untuk materi pembelajaran."
        elif self.language == "en":
            return "IMPORTANT: Write all content in English. Use a friendly and easy-to-understand writing style for learning materials."
        else:
            return f"IMPORTANT: Write all content in the target language (code: {self.language}). Use a friendly and easy-to-understand writing style for learning materials."
    
    def _format_for_learning_material(
        self,
        article: str,
        title: str,
        chapter_context: Optional[Dict[str, Any]]
    ) -> str:
        """
        Format STORM-generated article for learning material format.
        
        Args:
            article: Raw article from STORM
            title: Chapter/topic title
            chapter_context: Optional chapter context
            
        Returns:
            Formatted markdown content
        """
        # Start with title (only once)
        formatted = f"# {title}\n\n"
        
        # Track what we've added to avoid duplicates
        has_learning_objectives = False
        has_introduction = False
        title_added = True
        
        # Add learning objectives if available
        if chapter_context and chapter_context.get("learning_objectives"):
            obj_title = "## Tujuan Pembelajaran\n\n" if self.language == "id" else "## Learning Objectives\n\n"
            formatted += obj_title
            for obj in chapter_context["learning_objectives"]:
                formatted += f"- {obj}\n"
            formatted += "\n"
            formatted += "---\n\n"  # Add separator for better structure
            has_learning_objectives = True
        
        # Add description if available (as introduction context)
        if chapter_context and chapter_context.get("description"):
            intro_title = "## Pengantar\n\n" if self.language == "id" else "## Introduction\n\n"
            formatted += intro_title
            formatted += f"{chapter_context['description']}\n\n"
            formatted += "---\n\n"
            has_introduction = True
        
        # Process article content
        # Remove Wikipedia-style references if present and format citations
        lines = article.split('\n')
        processed_lines = []
        in_reference_section = False
        
        # Normalize title for comparison
        title_normalized = title.lower().strip()
        intro_title_normalized = ("## Pengantar" if self.language == "id" else "## Introduction").lower()
        obj_title_normalized = ("## Tujuan Pembelajaran" if self.language == "id" else "## Learning Objectives").lower()
        
        for i, line in enumerate(lines):
            # Skip reference sections (Wikipedia style)
            if line.strip().startswith('==') and ('Reference' in line or 'Referensi' in line):
                in_reference_section = True
                break
            if in_reference_section:
                continue
            
            # Skip duplicate title
            line_stripped = line.strip()
            if line_stripped.startswith('#') and title_normalized in line_stripped.lower():
                # Check if it's the main title (h1)
                if line_stripped.startswith('# ') and not line_stripped.startswith('##'):
                    continue  # Skip duplicate main title
            
            # Skip duplicate introduction
            if (line_stripped.lower().startswith('##') and 
                ('introduction' in line_stripped.lower() or 'pengantar' in line_stripped.lower()) and
                has_introduction):
                continue
            
            # Skip duplicate learning objectives
            if (line_stripped.lower().startswith('##') and 
                ('learning objectives' in line_stripped.lower() or 'tujuan pembelajaran' in line_stripped.lower()) and
                has_learning_objectives):
                continue
            
            # Process markdown headers (already in markdown format)
            if line_stripped.startswith('###'):
                # Level 3 header
                text = line_stripped[3:].strip()
                text = self._clean_section_title(text)
                # Add separator before new sections for better visual structure
                if processed_lines and processed_lines[-1].strip() and not processed_lines[-1].startswith('#'):
                    processed_lines.append("")
                processed_lines.append(f"### {text}")
            elif line_stripped.startswith('##'):
                # Level 2 header
                text = line_stripped[2:].strip()
                text = self._clean_section_title(text)
                # Skip if it's a duplicate introduction or learning objectives
                text_lower = text.lower()
                if has_introduction and ('introduction' in text_lower or 'pengantar' in text_lower):
                    continue
                if has_learning_objectives and ('learning objectives' in text_lower or 'tujuan pembelajaran' in text_lower):
                    continue
                # Add separator before major sections
                if processed_lines and processed_lines[-1].strip():
                    processed_lines.append("")
                    processed_lines.append("---")
                    processed_lines.append("")
                processed_lines.append(f"## {text}")
            # Convert Wikipedia-style headers to markdown
            elif line.startswith('==='):
                # Level 3 header
                text = line.strip('= ').strip()
                # Remove "Section" prefix if present
                text = self._clean_section_title(text)
                # Add separator before new sections for better visual structure
                if processed_lines and processed_lines[-1].strip() and not processed_lines[-1].startswith('#'):
                    processed_lines.append("")
                processed_lines.append(f"### {text}")
            elif line.startswith('=='):
                # Level 2 header
                text = line.strip('= ').strip()
                # Remove "Section" prefix if present
                text = self._clean_section_title(text)
                # Skip if it's a duplicate introduction or learning objectives
                text_lower = text.lower()
                if has_introduction and ('introduction' in text_lower or 'pengantar' in text_lower):
                    continue
                if has_learning_objectives and ('learning objectives' in text_lower or 'tujuan pembelajaran' in text_lower):
                    continue
                # Add separator before major sections
                if processed_lines and processed_lines[-1].strip():
                    processed_lines.append("")
                    processed_lines.append("---")
                    processed_lines.append("")
                processed_lines.append(f"## {text}")
            else:
                processed_lines.append(line)
        
        formatted += '\n'.join(processed_lines)
        
        # Ensure there's a summary section if not present
        summary_title = "## Ringkasan\n\n" if self.language == "id" else "## Summary\n\n"
        if summary_title.lower() not in formatted.lower():
            formatted += "\n\n---\n\n"
            formatted += summary_title
            summary_text = "*Ringkasan akan membantu memperkuat pemahaman tentang konsep-konsep utama yang telah dipelajari.*" if self.language == "id" else "*Summary will help reinforce understanding of the main concepts learned.*"
            formatted += summary_text + "\n\n"
        
        # Add reflection questions section if not present
        reflection_title = "## Pertanyaan Refleksi\n\n" if self.language == "id" else "## Reflection Questions\n\n"
        if reflection_title.lower() not in formatted.lower():
            formatted += "---\n\n"
            formatted += reflection_title
            reflection_text = "*Gunakan pertanyaan-pertanyaan berikut untuk merefleksikan dan memperdalam pemahaman Anda:*" if self.language == "id" else "*Use the following questions to reflect and deepen your understanding:*"
            formatted += reflection_text + "\n\n"
            formatted += "*[Pertanyaan refleksi akan ditambahkan]*\n" if self.language == "id" else "*[Reflection questions will be added]*\n"
        
        # Add citations section if references exist
        if '[1]' in article or '[2]' in article:
            formatted += "\n\n---\n\n"
            formatted += "## Referensi\n\n" if self.language == "id" else "## References\n\n"
            formatted += "*Referensi akan ditambahkan setelah proses research selesai.*\n" if self.language == "id" else "*References will be added after research is complete.*\n"
        
        return formatted
    
    def _clean_section_title(self, title: str) -> str:
        """
        Remove 'Section' prefix and clean up section titles.
        
        Args:
            title: Section title to clean
            
        Returns:
            Cleaned title without 'Section' prefix
        """
        # Remove common section prefixes
        title = title.strip()
        
        # Remove "Section 1:", "Section 1.", "Section 1 -", etc.
        import re
        title = re.sub(r'^Section\s+\d+[:\-\.]\s*', '', title, flags=re.IGNORECASE)
        title = re.sub(r'^Section\s+\d+\s+', '', title, flags=re.IGNORECASE)
        
        # Remove standalone "Section" at the start
        if title.lower().startswith('section '):
            title = title[8:].strip()
            # Remove leading number if present
            title = re.sub(r'^\d+[:\-\.]\s*', '', title)
        
        return title.strip()
    
    def _generate_content_fallback(
        self,
        topic: str,
        chapter_context: Optional[Dict[str, Any]] = None,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> str:
        """
        Fallback content generation using Azure OpenAI directly.
        Used when STORM is not available.
        
        Args:
            topic: Topic or chapter title
            chapter_context: Optional chapter context
            progress_callback: Optional progress callback
            
        Returns:
            Generated markdown content
        """
        if progress_callback:
            progress_callback(f"Generating content directly with Azure OpenAI for: {topic}")
        
        # Build prompt for content generation
        prompt = self._build_content_prompt(topic, chapter_context)
        
        try:
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {
                        "role": "system",
                        "content": self._get_system_prompt()
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_completion_tokens=16000  # Increased significantly for very detailed and comprehensive content
                # Note: temperature parameter removed - model only supports default value (1)
            )
            
            content = response.choices[0].message.content
            
            # Format for learning material
            formatted_content = self._format_for_learning_material(
                content,
                topic,
                chapter_context
            )
            
            if progress_callback:
                progress_callback(f"Content generation completed for: {topic}")
            
            return formatted_content
            
        except Exception as e:
            error_msg = f"Error generating content for {topic}: {e}"
            if progress_callback:
                progress_callback(f"Error: {error_msg}")
            raise RuntimeError(error_msg)
    
    def _build_content_prompt(
        self,
        topic: str,
        chapter_context: Optional[Dict[str, Any]]
    ) -> str:
        """Build prompt for direct content generation."""
        if self.language == "id":
            prompt = f"Tuliskan materi pembelajaran yang KOMPREHENSIF, MENDALAM, dan TERSTRUKTUR untuk topik: {topic}\n\n"
            
            if chapter_context:
                if chapter_context.get("description"):
                    prompt += f"Konteks: {chapter_context['description']}\n\n"
                
                if chapter_context.get("sections"):
                    sections = "\n".join([f"- {s}" for s in chapter_context["sections"]])
                    prompt += f"Section yang harus dicakup (setiap section harus dijelaskan dengan MENDALAM, minimal 3-4 paragraf penuh):\n{sections}\n\n"
                
                if chapter_context.get("learning_objectives"):
                    objectives = "\n".join([f"- {obj}" for obj in chapter_context["learning_objectives"]])
                    prompt += f"Tujuan pembelajaran:\n{objectives}\n\n"
            
            prompt += self._get_language_instruction()
            prompt += "\n\nPENTING - Instruksi Penulisan:\n\n"
            prompt += "1. STRUKTUR PEMBELAJARAN PROGRESIF:\n"
            prompt += "   - Mulai dengan Introduction yang memberikan konteks dan motivasi belajar topik ini\n"
            prompt += "   - Lanjutkan dengan penjelasan konsep dasar secara bertahap\n"
            prompt += "   - Kembangkan ke konsep yang lebih kompleks dengan penjelasan mendalam\n"
            prompt += "   - Berikan contoh konkret dan studi kasus untuk setiap konsep penting\n"
            prompt += "   - Akhiri dengan Summary yang memperkuat pemahaman\n\n"
            
            prompt += "2. KEDALAMAN KONTEN SANGAT TINGGI (NATURAL DAN SEIMBANG):\n"
            prompt += "   - Gunakan KOMBINASI paragraf penjelasan dan poin-poin yang natural sesuai konteks\n"
            prompt += "   - Untuk konsep kompleks: gunakan paragraf penuh yang SANGAT DETAIL (minimal 4-6 paragraf per konsep utama)\n"
            prompt += "   - Setiap konsep harus dijelaskan dengan SANGAT MENDALAM:\n"
            prompt += "     * Definisi yang jelas dan lengkap\n"
            prompt += "     * Latar belakang historis atau konteks munculnya konsep ini\n"
            prompt += "     * MENGAPA konsep ini penting dan relevan\n"
            prompt += "     * BAGAIMANA cara kerjanya secara detail (step-by-step jika perlu)\n"
            prompt += "     * KAPAN dan DI MANA digunakan dalam praktik\n"
            prompt += "     * Implikasi dan konsekuensi dari penggunaan konsep ini\n"
            prompt += "     * Hubungan dengan konsep lain (bagaimana saling terkait)\n"
            prompt += "     * Kelebihan dan keterbatasan\n"
            prompt += "     * Aplikasi praktis dan studi kasus nyata\n"
            prompt += "   - Untuk daftar, perbandingan, atau ringkasan: gunakan bullet points yang jelas\n"
            prompt += "   - Jangan semua paragraf, jangan semua poin-poin - sesuaikan dengan kebutuhan materi\n"
            prompt += "   - Setiap paragraf harus memberikan nilai tambah - hindari pengulangan yang tidak perlu\n"
            prompt += "   - Gunakan transisi yang halus antar paragraf untuk alur yang natural\n\n"
            
            prompt += "3. CONTOH, ANALOGI, STUDI KASUS, DAN VISUALISASI (SANGAT PENTING - GUNAKAN BANYAK):\n"
            prompt += "   - Setiap konsep penting HARUS memiliki minimal 2-3 contoh konkret atau analogi\n"
            prompt += "   - Gunakan contoh dari kehidupan sehari-hari, dunia nyata, atau industri\n"
            prompt += "   - Berikan studi kasus yang DETAIL dan LENGKAP (bukan hanya 1-2 kalimat)\n"
            prompt += "   - Setiap studi kasus harus menjelaskan: konteks, masalah, solusi, hasil, dan pelajaran\n"
            prompt += "   - Gunakan analogi yang mudah dipahami untuk konsep yang kompleks\n"
            prompt += "   - Berikan contoh sebelum dan sesudah untuk menunjukkan perbedaan\n"
            prompt += "   - WAJIB GUNAKAN TABLE untuk:\n"
            prompt += "     * Membandingkan 2+ konsep, fitur, atau pendekatan\n"
            prompt += "     * Menampilkan data, karakteristik, atau perbedaan\n"
            prompt += "     * Menyajikan ringkasan informasi yang terstruktur\n"
            prompt += "     * Minimal 2-3 table per chapter untuk konsep-konsep penting\n"
            prompt += "   - WAJIB GUNAKAN MERMAID DIAGRAM untuk:\n"
            prompt += "     * Flowchart untuk proses, alur kerja, atau decision flow\n"
            prompt += "     * Sequence diagram untuk interaksi atau komunikasi\n"
            prompt += "     * Graph untuk hubungan, hierarki, atau struktur\n"
            prompt += "     * State diagram untuk state machine atau lifecycle\n"
            prompt += "     * Minimal 2-4 diagram mermaid per chapter\n"
            prompt += "   - Format mermaid: gunakan ```mermaid di awal dan ``` di akhir\n"
            prompt += "   - Contoh flowchart: flowchart LR untuk left-right, TD untuk top-down\n"
            prompt += "   - Visualisasi sangat penting untuk pemahaman - jangan ragu menggunakannya\n\n"
            
            prompt += "4. FORMAT DAN ORGANISASI:\n"
            prompt += "   - Gunakan heading markdown yang jelas (## untuk section utama, ### untuk sub-section)\n"
            prompt += "   - HAPUS kata 'Section' dari judul section - langsung gunakan judul yang deskriptif\n"
            prompt += "   - Contoh: 'Section 1: Agents' → 'Agents' atau 'Understanding Agents'\n"
            prompt += "   - Setiap section harus memiliki konten yang natural (paragraf + poin sesuai kebutuhan)\n"
            prompt += "   - Gunakan pemisah (---) antara section untuk kejelasan visual\n"
            prompt += "   - JANGAN duplikasi judul chapter atau introduction\n"
            prompt += "   - Tambahkan Reflection Questions di akhir untuk mendorong pemikiran mendalam\n\n"
            
            prompt += "5. PANJANG KONTEN (SANGAT DETAIL):\n"
            prompt += "   - Target minimal 3000-5000 kata untuk chapter yang lengkap dan mendalam\n"
            prompt += "   - Setiap section utama harus memiliki minimal 800-1200 kata\n"
            prompt += "   - Lebih baik terlalu detail daripada terlalu singkat - detail adalah kunci pemahaman\n"
            prompt += "   - Pastikan pembaca dapat memahami topik dengan SANGAT BAIK hanya dari materi ini\n"
            prompt += "   - Tidak perlu referensi eksternal - semua yang penting harus ada di dalam chapter\n"
            prompt += "   - Setiap konsep harus dijelaskan sampai pembaca benar-benar paham\n\n"
            
            prompt += "6. PENJELASAN YANG KOMPREHENSIF:\n"
            prompt += "   - Untuk setiap konsep, jelaskan dari berbagai sudut pandang\n"
            prompt += "   - Sertakan perspektif teoritis dan praktis\n"
            prompt += "   - Jelaskan common mistakes atau kesalahan umum yang terjadi\n"
            prompt += "   - Berikan tips praktis atau best practices\n"
            prompt += "   - Jelaskan trade-offs dan pertimbangan dalam penggunaan konsep\n"
            prompt += "   - Sertakan perbandingan dengan pendekatan alternatif jika relevan\n\n"
            
            prompt += "HINDARI:\n"
            prompt += "- Menulis hanya bullet points tanpa penjelasan mendalam\n"
            prompt += "- Konten yang terlalu singkat (1-2 kalimat per poin)\n"
            prompt += "- Penjelasan yang dangkal atau hanya permukaan\n"
            prompt += "- Struktur yang tidak mengikuti alur pembelajaran\n"
            prompt += "- Penjelasan yang terlalu teknis tanpa konteks\n"
            prompt += "- Mengasumsikan pembaca sudah tahu konsep dasar tanpa menjelaskannya\n"
            prompt += "- Melewatkan detail penting yang diperlukan untuk pemahaman\n\n"
            
            prompt += "Format output dalam markdown dengan struktur yang jelas dan hierarki heading yang baik."
        else:
            prompt = f"Write COMPREHENSIVE, IN-DEPTH, and WELL-STRUCTURED learning material for topic: {topic}\n\n"
            
            if chapter_context:
                if chapter_context.get("description"):
                    prompt += f"Context: {chapter_context['description']}\n\n"
                
                if chapter_context.get("sections"):
                    sections = "\n".join([f"- {s}" for s in chapter_context["sections"]])
                    prompt += f"Sections to cover (each section must be explained IN-DEPTH, minimum 3-4 full paragraphs):\n{sections}\n\n"
                
                if chapter_context.get("learning_objectives"):
                    objectives = "\n".join([f"- {obj}" for obj in chapter_context["learning_objectives"]])
                    prompt += f"Learning objectives:\n{objectives}\n\n"
            
            prompt += self._get_language_instruction()
            prompt += "\n\nIMPORTANT - Writing Instructions:\n\n"
            prompt += "1. PROGRESSIVE LEARNING STRUCTURE:\n"
            prompt += "   - Start with Introduction that provides context and motivation to learn this topic\n"
            prompt += "   - Continue with basic concept explanations step by step\n"
            prompt += "   - Develop into more complex concepts with in-depth explanations\n"
            prompt += "   - Provide concrete examples and case studies for each important concept\n"
            prompt += "   - End with Summary that reinforces understanding\n\n"
            
            prompt += "2. VERY HIGH CONTENT DEPTH (NATURAL AND BALANCED):\n"
            prompt += "   - Use a COMBINATION of explanatory paragraphs and bullet points that feels natural for the context\n"
            prompt += "   - For complex concepts: use VERY DETAILED full paragraphs (minimum 4-6 paragraphs per main concept)\n"
            prompt += "   - Every concept must be explained VERY DEEPLY:\n"
            prompt += "     * Clear and complete definition\n"
            prompt += "     * Historical background or context of how this concept emerged\n"
            prompt += "     * WHY this concept is important and relevant\n"
            prompt += "     * HOW it works in detail (step-by-step if needed)\n"
            prompt += "     * WHEN and WHERE it's used in practice\n"
            prompt += "     * Implications and consequences of using this concept\n"
            prompt += "     * Relationships with other concepts (how they interconnect)\n"
            prompt += "     * Advantages and limitations\n"
            prompt += "     * Practical applications and real-world case studies\n"
            prompt += "   - For lists, comparisons, or summaries: use clear bullet points\n"
            prompt += "   - Don't make everything paragraphs, don't make everything bullet points - adapt to material needs\n"
            prompt += "   - Each paragraph must add value - avoid unnecessary repetition\n"
            prompt += "   - Use smooth transitions between paragraphs for natural flow\n\n"
            
            prompt += "3. EXAMPLES, ANALOGIES, CASE STUDIES, AND VISUALIZATIONS (VERY IMPORTANT - USE MANY):\n"
            prompt += "   - Every important concept MUST have minimum 2-3 concrete examples or analogies\n"
            prompt += "   - Use examples from daily life, real world, or industry\n"
            prompt += "   - Provide DETAILED and COMPLETE case studies (not just 1-2 sentences)\n"
            prompt += "   - Each case study must explain: context, problem, solution, results, and lessons learned\n"
            prompt += "   - Use easy-to-understand analogies for complex concepts\n"
            prompt += "   - Provide before and after examples to show differences\n"
            prompt += "   - MUST USE TABLES for:\n"
            prompt += "     * Comparing 2+ concepts, features, or approaches\n"
            prompt += "     * Displaying data, characteristics, or differences\n"
            prompt += "     * Presenting structured summary information\n"
            prompt += "     * Minimum 2-3 tables per chapter for important concepts\n"
            prompt += "   - MUST USE MERMAID DIAGRAMS for:\n"
            prompt += "     * Flowcharts for processes, workflows, or decision flows\n"
            prompt += "     * Sequence diagrams for interactions or communication\n"
            prompt += "     * Graphs for relationships, hierarchies, or structures\n"
            prompt += "     * State diagrams for state machines or lifecycles\n"
            prompt += "     * Minimum 2-4 mermaid diagrams per chapter\n"
            prompt += "   - Mermaid format: use ```mermaid at start and ``` at end\n"
            prompt += "   - Example flowchart: flowchart LR for left-right, TD for top-down\n"
            prompt += "   - Visualizations are crucial for understanding - don't hesitate to use them\n\n"
            
            prompt += "4. FORMAT AND ORGANIZATION:\n"
            prompt += "   - Use clear markdown headings (## for main sections, ### for sub-sections)\n"
            prompt += "   - REMOVE the word 'Section' from section titles - use descriptive titles directly\n"
            prompt += "   - Example: 'Section 1: Agents' → 'Agents' or 'Understanding Agents'\n"
            prompt += "   - Each section must have natural content (paragraphs + points as needed)\n"
            prompt += "   - Use separators (---) between sections for visual clarity\n"
            prompt += "   - DO NOT duplicate chapter title or introduction\n"
            prompt += "   - Add Reflection Questions at the end to encourage deep thinking\n\n"
            
            prompt += "5. CONTENT LENGTH (VERY DETAILED):\n"
            prompt += "   - Target minimum 3000-5000 words for a complete and in-depth chapter\n"
            prompt += "   - Each main section should have minimum 800-1200 words\n"
            prompt += "   - Better to be too detailed than too brief - detail is key to understanding\n"
            prompt += "   - Ensure readers can understand the topic VERY WELL from this material alone\n"
            prompt += "   - No need for external references - everything important must be in the chapter\n"
            prompt += "   - Every concept must be explained until readers truly understand\n\n"
            
            prompt += "6. COMPREHENSIVE EXPLANATIONS:\n"
            prompt += "   - For every concept, explain from various perspectives\n"
            prompt += "   - Include both theoretical and practical perspectives\n"
            prompt += "   - Explain common mistakes or common errors that occur\n"
            prompt += "   - Provide practical tips or best practices\n"
            prompt += "   - Explain trade-offs and considerations in using the concept\n"
            prompt += "   - Include comparisons with alternative approaches if relevant\n\n"
            
            prompt += "AVOID:\n"
            prompt += "- Writing only bullet points without deep explanations\n"
            prompt += "- Content that is too brief (1-2 sentences per point)\n"
            prompt += "- Shallow explanations or only surface-level content\n"
            prompt += "- Structure that doesn't follow a learning progression\n"
            prompt += "- Explanations that are too technical without context\n"
            prompt += "- Assuming readers already know basic concepts without explaining them\n"
            prompt += "- Skipping important details needed for understanding\n\n"
            
            prompt += "Format output in markdown with clear structure and good heading hierarchy."
        
        return prompt
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for content generation."""
        if self.language == "id":
            return """Anda adalah ahli dalam menulis materi pembelajaran yang komprehensif, mendalam, dan terstruktur dengan sangat baik.

Tugas Anda adalah menulis konten pembelajaran yang:
1. NATURAL DAN SEIMBANG - Gunakan kombinasi paragraf penjelasan dan poin-poin yang natural sesuai konteks materi
2. SANGAT DETAIL dan SANGAT MENDALAM - Penjelasan yang sangat lengkap dengan konteks, alasan, latar belakang, implikasi, dan pemahaman yang menyeluruh. Setiap konsep harus dijelaskan dari berbagai sudut pandang.
3. TERSTRUKTUR untuk PEMBELAJARAN - Mengikuti alur pembelajaran yang progresif: dari konsep dasar → penjelasan mendalam → contoh praktis → studi kasus → latihan pemahaman
4. MUDAH DIPAHAMI - Menggunakan bahasa yang jelas, contoh konkret yang banyak, analogi yang relevan, dan penjelasan bertahap yang sangat detail
5. SANGAT VISUAL - WAJIB menggunakan banyak table (minimal 2-3 per chapter) dan diagram mermaid (minimal 2-4 per chapter) untuk membantu pemahaman
6. KOMPREHENSIF - Minimal 3000-5000 kata per chapter dengan penjelasan yang sangat detail pada setiap konsep

Struktur yang harus diikuti:
- Introduction: Pengenalan topik dengan konteks yang jelas (HANYA SEKALI, jangan duplikasi)
- Learning Objectives: Tujuan pembelajaran yang spesifik
- Main Content: Dibagi menjadi section-section dengan penjelasan mendalam
  - Setiap section harus memiliki konten natural: paragraf untuk penjelasan konsep, bullet points untuk daftar/perbandingan
  - Gunakan contoh konkret dan studi kasus
  - WAJIB gunakan table untuk perbandingan (minimal 2-3 table per chapter)
  - WAJIB gunakan diagram mermaid untuk alur proses, interaksi, atau struktur (minimal 2-4 diagram per chapter)
  - Format mermaid: ```mermaid di awal, ``` di akhir
  - Jelaskan "mengapa" dan "bagaimana", bukan hanya "apa"
  - HAPUS kata "Section" dari judul section - langsung gunakan judul deskriptif
- Summary: Ringkasan yang memperkuat pemahaman
- Reflection Questions: Pertanyaan untuk mendorong pemikiran mendalam

HINDARI:
- Semua paragraf atau semua poin-poin - gunakan kombinasi yang natural
- Duplikasi judul chapter atau introduction
- Menggunakan kata "Section" di judul section
- Konten yang terlalu singkat (1 kalimat per poin)
- Struktur yang tidak mengikuti alur pembelajaran

Gunakan format markdown dengan heading yang jelas dan hierarki yang baik."""
        else:
            return """You are an expert in writing comprehensive, in-depth, and well-structured learning materials.

Your task is to write educational content that is:
1. NATURAL AND BALANCED - Use a combination of explanatory paragraphs and bullet points that feels natural for the context
2. VERY DETAILED and VERY IN-DEPTH - Very complete explanations with context, reasoning, background, implications, and comprehensive understanding. Every concept must be explained from various perspectives.
3. STRUCTURED for LEARNING - Following a progressive learning flow: basic concepts → in-depth explanations → practical examples → case studies → comprehension exercises
4. EASY TO UNDERSTAND - Using clear language, many concrete examples, relevant analogies, and very detailed step-by-step explanations
5. HIGHLY VISUAL - MUST use many tables (minimum 2-3 per chapter) and mermaid diagrams (minimum 2-4 per chapter) to aid understanding
6. COMPREHENSIVE - Minimum 3000-5000 words per chapter with very detailed explanations on every concept

Structure to follow:
- Introduction: Topic introduction with clear context (ONLY ONCE, do not duplicate)
- Learning Objectives: Specific learning objectives
- Main Content: Divided into sections with in-depth explanations
  - Each section must have natural content: paragraphs for concept explanations, bullet points for lists/comparisons
  - Use concrete examples and case studies
  - MUST use tables for comparisons (minimum 2-3 tables per chapter)
  - MUST use mermaid diagrams for process flows, interactions, or structures (minimum 2-4 diagrams per chapter)
  - Mermaid format: ```mermaid at start, ``` at end
  - Explain "why" and "how", not just "what"
  - REMOVE the word "Section" from section titles - use descriptive titles directly
- Summary: Summary that reinforces understanding
- Reflection Questions: Questions to encourage deep thinking

AVOID:
- All paragraphs or all bullet points - use a natural combination
- Duplicating chapter title or introduction
- Using the word "Section" in section titles
- Content that is too brief (1 sentence per point)
- Structure that doesn't follow a learning progression

Use markdown format with clear headings and good hierarchy."""
    
    def cleanup(self) -> None:
        """Cleanup resources."""
        # STORM runner doesn't need explicit cleanup
        pass

