"""Input handler for reading and validating JSON input files."""

import json
import os
from typing import Dict, Any
from pathlib import Path


class InputHandler:
    """Handler for reading and validating input JSON files."""
    
    REQUIRED_FIELDS = ["topik", "bahasa", "audience"]
    VALID_LANGUAGES = ["id", "en", "es", "fr", "de", "pt", "zh", "ja", "ko"]
    VALID_AUDIENCES = ["beginner", "intermediate", "advanced"]
    
    def __init__(self, input_file: str):
        """
        Initialize input handler.
        
        Args:
            input_file: Path to JSON input file
        """
        self.input_file = Path(input_file)
        self.data: Dict[str, Any] = {}
    
    def read(self) -> Dict[str, Any]:
        """
        Read and validate input JSON file.
        
        Returns:
            Dictionary containing validated input data
            
        Raises:
            FileNotFoundError: If input file doesn't exist
            ValueError: If JSON is invalid or missing required fields
        """
        if not self.input_file.exists():
            raise FileNotFoundError(f"Input file not found: {self.input_file}")
        
        try:
            with open(self.input_file, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}")
        
        self._validate()
        return self.data
    
    def _validate(self) -> None:
        """
        Validate input data.
        
        Raises:
            ValueError: If validation fails
        """
        # Check required fields
        missing_fields = [field for field in self.REQUIRED_FIELDS 
                         if field not in self.data]
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
        
        # Validate topik
        if not isinstance(self.data["topik"], str) or not self.data["topik"].strip():
            raise ValueError("Field 'topik' must be a non-empty string")
        
        # Validate bahasa
        if self.data["bahasa"] not in self.VALID_LANGUAGES:
            raise ValueError(
                f"Invalid 'bahasa'. Must be one of: {', '.join(self.VALID_LANGUAGES)}"
            )
        
        # Validate audience
        if self.data["audience"] not in self.VALID_AUDIENCES:
            raise ValueError(
                f"Invalid 'audience'. Must be one of: {', '.join(self.VALID_AUDIENCES)}"
            )
    
    def get_topic(self) -> str:
        """Get topic from input data."""
        return self.data.get("topik", "")
    
    def get_language(self) -> str:
        """Get language code from input data."""
        return self.data.get("bahasa", "id")
    
    def get_audience(self) -> str:
        """Get audience level from input data."""
        return self.data.get("audience", "beginner")

