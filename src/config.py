from dataclasses import dataclass, field
from typing import Set, List, Optional
from pathlib import Path
import json

@dataclass
class DocumentationConfig:
    """Configuration for the documentation agent"""
    
    # Model settings
    model_name: str = "codellama:13b"
    temperature: float = 0.3
    max_tokens: int = 1500
    
    # File filtering
    code_extensions: Set[str] = field(default_factory=lambda: {
        '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.h', 
        '.cs', '.php', '.rb', '.go', '.rs', '.swift', '.kt', '.scala'
    })
    
    ignore_dirs: Set[str] = field(default_factory=lambda: {
        'node_modules', '.git', '__pycache__', '.pytest_cache', 'venv', 
        'env', '.env', 'build', 'dist', '.next', '.nuxt', 'target', 'bin', 'obj'
    })
    
    ignore_files: Set[str] = field(default_factory=lambda: {
        '.gitignore', '.env*', 'package-lock.json', 'yarn.lock', '*.min.js', '*.min.css'
    })
    
    # Analysis settings
    max_file_size: int = 1024 * 1024  # 1MB
    batch_size: int = 10
    max_files_to_document: int = 10
    min_lines_for_detailed_doc: int = 20
    
    # Output settings
    output_filename: str = "PROJECT_DOCUMENTATION.md"
    include_technical_appendix: bool = True
    include_complexity_analysis: bool = True
    
    @classmethod
    def from_file(cls, config_path: Path) -> 'DocumentationConfig':
        """Load configuration from JSON file"""
        if config_path.exists():
            with open(config_path, 'r') as f:
                data = json.load(f)
                return cls(**data)
        return cls()
    
    def save_to_file(self, config_path: Path):
        """Save configuration to JSON file"""
        # Convert sets to lists for JSON serialization
        data = {
            'model_name': self.model_name,
            'temperature': self.temperature,
            'max_tokens': self.max_tokens,
            'code_extensions': list(self.code_extensions),
            'ignore_dirs': list(self.ignore_dirs),
            'ignore_files': list(self.ignore_files),
            'max_file_size': self.max_file_size,
            'batch_size': self.batch_size,
            'max_files_to_document': self.max_files_to_document,
            'min_lines_for_detailed_doc': self.min_lines_for_detailed_doc,
            'output_filename': self.output_filename,
            'include_technical_appendix': self.include_technical_appendix,
            'include_complexity_analysis': self.include_complexity_analysis
        }
        
        with open(config_path, 'w') as f:
            json.dump(data, f, indent=2)