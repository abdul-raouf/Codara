import aiofiles
from pathlib import Path
from typing import Dict, List, Optional
import asyncio
from dataclasses import dataclass

@dataclass
class FileAnalysis:
    """Data class to hold file analysis results"""
    path: Path
    relative_path: Path
    extension: str
    size: int
    lines: int
    content: str
    functions: List[str]
    classes: List[str]
    imports: List[str]
    language: str

class FileAnalyzer:
    def __init__(self):
        self.language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'javascript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.h': 'c',
            '.cs': 'csharp',
            '.php': 'php',
            '.rb': 'ruby',
            '.go': 'go',
            '.rs': 'rust',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.html': 'html',
            '.css': 'css',
            '.sql': 'sql',
            '.json': 'json',
            '.yaml': 'yaml',
            '.yml': 'yaml'
        }
    
    async def read_file_content(self, file_path: Path) -> Optional[str]:
        """Safely read file content with encoding detection"""
        try:
            # Try UTF-8 first
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                return await f.read()
        except UnicodeDecodeError:
            # Fallback to latin-1 if UTF-8 fails
            try:
                async with aiofiles.open(file_path, 'r', encoding='latin-1') as f:
                    return await f.read()
            except Exception as e:
                print(f"Warning: Could not read {file_path}: {e}")
                return None
        except Exception as e:
            print(f"Warning: Could not read {file_path}: {e}")
            return None
    
    def extract_python_elements(self, content: str) -> tuple:
        """Extract functions, classes, and imports from Python code"""
        functions = []
        classes = []
        imports = []
        
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Extract function definitions
            if line.startswith('def ') and '(' in line:
                func_name = line.split('def ')[1].split('(')[0].strip()
                functions.append(func_name)
            
            # Extract class definitions
            elif line.startswith('class ') and ':' in line:
                class_name = line.split('class ')[1].split(':')[0].split('(')[0].strip()
                classes.append(class_name)
            
            # Extract imports
            elif line.startswith('import ') or line.startswith('from '):
                imports.append(line)
        
        return functions, classes, imports
    
    def extract_javascript_elements(self, content: str) -> tuple:
        """Extract functions, classes, and imports from JavaScript/TypeScript"""
        functions = []
        classes = []
        imports = []
        
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Extract function definitions
            if ('function ' in line and '(' in line) or \
               ('=> ' in line and ('const ' in line or 'let ' in line or 'var ' in line)):
                if 'function ' in line:
                    try:
                        func_name = line.split('function ')[1].split('(')[0].strip()
                        functions.append(func_name)
                    except:
                        pass
                else:  # Arrow function
                    try:
                        func_name = line.split('=')[0].replace('const', '').replace('let', '').replace('var', '').strip()
                        functions.append(func_name)
                    except:
                        pass
            
            # Extract class definitions
            elif line.startswith('class '):
                try:
                    class_name = line.split('class ')[1].split(' ')[0].split('{')[0].strip()
                    classes.append(class_name)
                except:
                    pass
            
            # Extract imports
            elif line.startswith('import ') or line.startswith('from '):
                imports.append(line)
        
        return functions, classes, imports
    
    def extract_basic_elements(self, content: str, language: str) -> tuple:
        """Extract basic elements based on file language"""
        if language == 'python':
            return self.extract_python_elements(content)
        elif language in ['javascript', 'typescript']:
            return self.extract_javascript_elements(content)
        else:
            # For other languages, just return empty lists for now
            return [], [], []
    
    async def analyze_file(self, file_path: Path, project_root: Path) -> Optional[FileAnalysis]:
        """Analyze a single file and extract its information"""
        content = await self.read_file_content(file_path)
        
        if content is None:
            return None
        
        # Basic file info
        extension = file_path.suffix.lower()
        language = self.language_map.get(extension, 'unknown')
        relative_path = file_path.relative_to(project_root)
        
        # Count lines
        lines = len(content.split('\n'))
        
        # Extract code elements
        functions, classes, imports = self.extract_basic_elements(content, language)
        
        return FileAnalysis(
            path=file_path,
            relative_path=relative_path,
            extension=extension,
            size=len(content.encode('utf-8')),
            lines=lines,
            content=content,
            functions=functions,
            classes=classes,
            imports=imports,
            language=language
        )
    
    async def analyze_files_batch(self, file_paths: List[Path], project_root: Path, 
                                 batch_size: int = 10) -> List[FileAnalysis]:
        """Analyze multiple files concurrently in batches"""
        analyses = []
        
        for i in range(0, len(file_paths), batch_size):
            batch = file_paths[i:i + batch_size]
            
            # Process batch concurrently
            batch_tasks = [self.analyze_file(file_path, project_root) for file_path in batch]
            batch_results = await asyncio.gather(*batch_tasks)
            
            # Filter out None results
            valid_results = [result for result in batch_results if result is not None]
            analyses.extend(valid_results)
            
            print(f"Analyzed batch {i//batch_size + 1}: {len(valid_results)} files")
        
        return analyses