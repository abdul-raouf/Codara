 
from pathlib import Path
from typing import List, Set
import fnmatch

class FileDiscovery:
    def __init__(self):
        # Common code file extensions
        self.code_extensions = {
            '.py', '.js', '.ts', '.jsx', '.tsx',
            '.java', '.cpp', '.c', '.h', '.hpp',
            '.cs', '.php', '.rb', '.go', '.rs',
            '.swift', '.kt', '.scala', '.sh',
            '.sql', '.html', '.css', '.scss',
            '.json', '.yaml', '.yml', '.xml'
        }
        
        # Directories to ignore
        self.ignore_dirs = {
            'node_modules', '.git', '__pycache__', '.pytest_cache',
            'venv', 'env', '.env', 'build', 'dist',
            '.next', '.nuxt', 'target', 'bin', 'obj'
        }
        
        # Files to ignore
        self.ignore_files = {
            '.gitignore', '.env', '.env.local',
            'package-lock.json', 'yarn.lock',
            '*.min.js', '*.min.css'
        }
    
    def should_ignore_dir(self, dir_path: Path) -> bool:
        """Check if directory should be ignored"""
        return dir_path.name in self.ignore_dirs
    
    def should_ignore_file(self, file_path: Path) -> bool:
        """Check if file should be ignored"""
        # Check if file name matches ignore patterns
        for pattern in self.ignore_files:
            if fnmatch.fnmatch(file_path.name, pattern):
                return True
        
        # Check if extension is not in our code extensions
        return file_path.suffix.lower() not in self.code_extensions
    
    def discover_files(self, project_path: Path) -> List[Path]:
        """Discover all code files in the project directory"""
        project_path = Path(project_path)
        
        if not project_path.exists():
            raise ValueError(f"Project path does not exist: {project_path}")
        
        code_files = []
        
        for item in project_path.rglob('*'):
            # Skip if it's a directory
            if item.is_dir():
                continue
            
            # Skip if any parent directory should be ignored
            if any(self.should_ignore_dir(parent) for parent in item.parents):
                continue
            
            # Skip if file should be ignored
            if self.should_ignore_file(item):
                continue
            
            code_files.append(item)
        
        return sorted(code_files)
    
    def get_project_stats(self, files: List[Path]) -> dict:
        """Get basic statistics about the discovered files"""
        stats = {
            'total_files': len(files),
            'by_extension': {},
            'total_size': 0
        }
        
        for file_path in files:
            ext = file_path.suffix.lower()
            stats['by_extension'][ext] = stats['by_extension'].get(ext, 0) + 1
            
            try:
                stats['total_size'] += file_path.stat().st_size
            except OSError:
                pass  # Skip files we can't read
        
        return stats