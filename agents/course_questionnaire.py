"""Interactive questionnaire for course requirements gathering."""

import json
from typing import Dict, Any, Optional
from pathlib import Path


class CourseQuestionnaire:
    """Interactive questionnaire to gather course requirements."""
    
    def __init__(self, language: str = "id"):
        """
        Initialize Course Questionnaire.
        
        Args:
            language: Language code for questions (default: "id")
        """
        self.language = language
        self.answers: Dict[str, Any] = {}
    
    def conduct_interview(self, output_dir: Optional[Path] = None) -> Dict[str, Any]:
        """
        Conduct interactive interview with maximum 5 questions.
        
        Args:
            output_dir: Optional directory to save requirements JSON
            
        Returns:
            Dictionary containing all answers
        """
        questions = self._build_questions()
        
        print("\n" + "="*60)
        if self.language == "id":
            print("KUESIONER KURSUS PEMBELAJARAN")
            print("Silakan jawab pertanyaan berikut untuk membantu generate course yang sesuai kebutuhan Anda.")
        else:
            print("COURSE QUESTIONNAIRE")
            print("Please answer the following questions to help generate a course that meets your needs.")
        print("="*60 + "\n")
        
        for i, question_data in enumerate(questions, 1):
            question = question_data["question"]
            key = question_data["key"]
            validation = question_data.get("validation")
            options = question_data.get("options")
            
            print(f"\n[{i}/5] {question}")
            
            if options:
                print("\nPilihan:")
                for opt_key, opt_label in options.items():
                    print(f"  {opt_key}) {opt_label}")
            
            while True:
                answer = input("\nJawaban: ").strip()
                
                if not answer:
                    if self.language == "id":
                        print("Jawaban tidak boleh kosong. Silakan coba lagi.")
                    else:
                        print("Answer cannot be empty. Please try again.")
                    continue
                
                # Validate if validation function provided
                if validation:
                    try:
                        validated_answer = validation(answer)
                        self.answers[key] = validated_answer
                        break
                    except ValueError as e:
                        print(f"Error: {e}")
                        continue
                else:
                    self.answers[key] = answer
                    break
        
        # Save to file if output_dir provided
        if output_dir:
            output_path = Path(output_dir) / "course_requirements.json"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(self.answers, f, indent=2, ensure_ascii=False)
            
            if self.language == "id":
                print(f"\n✓ Hasil kuesioner disimpan ke: {output_path}")
            else:
                print(f"\n✓ Questionnaire results saved to: {output_path}")
        
        print("\n" + "="*60)
        if self.language == "id":
            print("Kuesioner selesai! Terima kasih.")
        else:
            print("Questionnaire completed! Thank you.")
        print("="*60 + "\n")
        
        return self.answers
    
    def _build_questions(self) -> list:
        """Build list of questions based on language."""
        if self.language == "id":
            return [
                {
                    "key": "learning_goals",
                    "question": "Apa yang spesifik ingin Anda pelajari dari topik ini?\n(Contoh: implementasi praktis, teori mendalam, studi kasus industri, tools dan teknologi tertentu)",
                    "validation": None
                },
                {
                    "key": "time_dedication",
                    "question": "Berapa lama waktu yang dapat Anda dedikasikan untuk belajar?\n(Contoh: 2 jam per minggu, 5 jam per minggu, 10 jam per minggu, atau format lain)",
                    "validation": None
                },
                {
                    "key": "prior_knowledge",
                    "question": "Apa pengetahuan awal yang sudah Anda miliki terkait topik ini?\n(Contoh: pemula total, sudah tahu dasar-dasar, sudah punya pengalaman praktis)",
                    "validation": None
                },
                {
                    "key": "learning_focus",
                    "question": "Fokus pembelajaran yang diinginkan?",
                    "options": {
                        "1": "Teori mendalam",
                        "2": "Praktik dan implementasi",
                        "3": "Kombinasi teori dan praktik",
                        "4": "Studi kasus dan aplikasi real-world"
                    },
                    "validation": lambda x: self._validate_option(x, ["1", "2", "3", "4"])
                },
                {
                    "key": "expected_outcomes",
                    "question": "Setelah menyelesaikan course ini, apa yang ingin Anda capai atau mampu lakukan?\n(Contoh: mampu membangun sistem X, memahami konsep Y, mengimplementasikan Z)",
                    "validation": None
                }
            ]
        else:
            return [
                {
                    "key": "learning_goals",
                    "question": "What specifically do you want to learn from this topic?\n(Example: practical implementation, in-depth theory, industry case studies, specific tools and technologies)",
                    "validation": None
                },
                {
                    "key": "time_dedication",
                    "question": "How much time can you dedicate to learning?\n(Example: 2 hours per week, 5 hours per week, 10 hours per week, or other format)",
                    "validation": None
                },
                {
                    "key": "prior_knowledge",
                    "question": "What prior knowledge do you already have about this topic?\n(Example: complete beginner, know the basics, have practical experience)",
                    "validation": None
                },
                {
                    "key": "learning_focus",
                    "question": "What learning focus do you prefer?",
                    "options": {
                        "1": "In-depth theory",
                        "2": "Practice and implementation",
                        "3": "Combination of theory and practice",
                        "4": "Case studies and real-world applications"
                    },
                    "validation": lambda x: self._validate_option(x, ["1", "2", "3", "4"])
                },
                {
                    "key": "expected_outcomes",
                    "question": "After completing this course, what do you want to achieve or be able to do?\n(Example: able to build system X, understand concept Y, implement Z)",
                    "validation": None
                }
            ]
    
    def _validate_option(self, answer: str, valid_options: list) -> str:
        """
        Validate that answer is one of the valid options.
        
        Args:
            answer: User's answer
            valid_options: List of valid option keys
            
        Returns:
            Validated answer
            
        Raises:
            ValueError: If answer is not valid
        """
        if answer not in valid_options:
            if self.language == "id":
                raise ValueError(f"Pilihan tidak valid. Silakan pilih salah satu: {', '.join(valid_options)}")
            else:
                raise ValueError(f"Invalid option. Please choose one of: {', '.join(valid_options)}")
        return answer

