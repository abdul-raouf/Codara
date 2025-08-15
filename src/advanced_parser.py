import tree_sitter
from tree_sitter import Language, Parser
import tree_sitter_python
import tree_sitter_javascript
from pathlib import Path
from typing import Dict, List, Set, Optional
from dataclasses import dataclass
import ast

@dataclass
class CodeElement:
    """Represents a code element (function, class, etc.)"""
    name: str
    type: str  # 'function', 'class', 'method', 'variable'
    line_number: int
    docstring: Optional[str] = None
    parameters: List[str] = None
    decorators: List[str] = None

@dataclass
class AdvancedFileAnalysis:
    """Enhanced file analysis with detailed code structure"""
    path: Path
    relative_path: Path
    language: str
    lines: int
    size: int
    
    # Enhanced code elements
    functions: List[CodeElement]
    classes: List[CodeElement]
    methods: List[CodeElement]  # Methods inside classes
    imports: List[str]
    
    # New advanced features
    complexity_score: int
    docstring_coverage: float
    dependencies: Set[str]
    exports: List[str]  # What this file exports/provides

class AdvancedCodeParser:
    def __init__(self):
        # Initialize tree-sitter languages
        self.python_language = tree_sitter_python.language()
        self.js_language = tree_sitter_javascript.language()
        
        self.language_map = {
            '.py': self.python_language,
            '.js': self.js_language,
            '.ts': self.js_language,  # TypeScript uses JS parser
            '.jsx': self.js_language,
            '.tsx': self.js_language
        }
    
    def parse_python_with_ast(self, content: str) -> tuple:
        """Use Python's AST for more accurate parsing"""
        functions = []
        classes = []
        methods = []
        imports = []
        complexity = 0
        
        try:
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                # Functions
                if isinstance(node, ast.FunctionDef):
                    docstring = ast.get_docstring(node)
                    params = [arg.arg for arg in node.args.args]
                    decorators = [ast.unparse(d) for d in node.decorator_list]
                    
                    element = CodeElement(
                        name=node.name,
                        type='function',
                        line_number=node.lineno,
                        docstring=docstring,
                        parameters=params,
                        decorators=decorators
                    )
                    
                    # Check if it's a method (inside a class)
                    for parent in ast.walk(tree):
                        if isinstance(parent, ast.ClassDef):
                            if node in ast.walk(parent):
                                element.type = 'method'
                                methods.append(element)
                                break
                    else:
                        functions.append(element)
                    
                    # Calculate complexity (rough estimate)
                    complexity += len([n for n in ast.walk(node) 
                                     if isinstance(n, (ast.If, ast.For, ast.While, ast.Try))])
                
                # Classes
                elif isinstance(node, ast.ClassDef):
                    docstring = ast.get_docstring(node)
                    decorators = [ast.unparse(d) for d in node.decorator_list]
                    
                    classes.append(CodeElement(
                        name=node.name,
                        type='class',
                        line_number=node.lineno,
                        docstring=docstring,
                        decorators=decorators
                    ))
                
                # Imports
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(f"import {alias.name}")
                
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    names = [alias.name for alias in node.names]
                    imports.append(f"from {module} import {', '.join(names)}")
        
        except SyntaxError:
            # Fallback to basic parsing if AST fails
            pass
        
        return functions, classes, methods, imports, complexity
    
    def calculate_docstring_coverage(self, elements: List[CodeElement]) -> float:
        """Calculate percentage of functions/classes with docstrings"""
        if not elements:
            return 0.0
        
        documented = sum(1 for elem in elements if elem.docstring)
        return (documented / len(elements)) * 100
    
    def extract_dependencies(self, imports: List[str]) -> Set[str]:
        """Extract unique dependencies from import statements"""
        dependencies = set()
        
        for imp in imports:
            if imp.startswith('import '):
                module = imp.split('import ')[1].split('.')[0].split(' as ')[0]
                dependencies.add(module)
            elif imp.startswith('from '):
                module = imp.split('from ')[1].split(' import')[0]
                dependencies.add(module)
        
        return dependencies
    
    async def analyze_file_advanced(self, file_path: Path, content: str, 
                                   project_root: Path) -> AdvancedFileAnalysis:
        """Perform advanced analysis of a single file"""
        
        extension = file_path.suffix.lower()
        relative_path = file_path.relative_to(project_root)
        lines = len(content.split('\n'))
        size = len(content.encode('utf-8'))
        
        # Use appropriate parser based on file type
        if extension == '.py':
            functions, classes, methods, imports, complexity = self.parse_python_with_ast(content)
            language = 'python'
        else:
            # For now, fall back to basic parsing for non-Python files
            functions, classes, methods, imports, complexity = [], [], [], [], 0
            language = 'unknown'
        
        # Calculate metrics
        all_elements = functions + classes
        docstring_coverage = self.calculate_docstring_coverage(all_elements)
        dependencies = self.extract_dependencies(imports)
        
        # Extract exports (for Python, this would be __all__ or public functions/classes)
        exports = [elem.name for elem in all_elements if not elem.name.startswith('_')]
        
        return AdvancedFileAnalysis(
            path=file_path,
            relative_path=relative_path,
            language=language,
            lines=lines,
            size=size,
            functions=functions,
            classes=classes,
            methods=methods,
            imports=imports,
            complexity_score=complexity,
            docstring_coverage=docstring_coverage,
            dependencies=dependencies,
            exports=exports
        )