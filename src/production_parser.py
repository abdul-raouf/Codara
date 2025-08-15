import ast
import asyncio
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Set, Optional, Dict, Any
import aiofiles

@dataclass
class CodeElement:
    """Represents a code element with proper defaults"""
    name: str
    type: str  # 'function', 'class', 'method', 'variable'
    line_number: int
    docstring: Optional[str] = None
    parameters: List[str] = field(default_factory=list)
    decorators: List[str] = field(default_factory=list)
    parent_class: Optional[str] = None  # For methods

@dataclass
class FileAnalysis:
    """Enhanced file analysis with proper defaults"""
    path: Path
    relative_path: Path
    language: str
    lines: int
    size: int
    
    # Code elements
    functions: List[CodeElement] = field(default_factory=list)
    classes: List[CodeElement] = field(default_factory=list)
    methods: List[CodeElement] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    
    # Metrics
    complexity_score: int = 0
    docstring_coverage: float = 0.0
    dependencies: Set[str] = field(default_factory=set)
    exports: List[str] = field(default_factory=list)

class ProductionCodeParser:
    """Production-ready code parser with proper async handling"""
    
    def __init__(self, max_workers: int = 4):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
        self.language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'javascript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.cs': 'csharp',
            '.php': 'php',
            '.rb': 'ruby',
            '.go': 'go',
            '.rs': 'rust'
        }
    
    def _parse_python_ast(self, content: str, file_path: Path) -> tuple:
        """Parse Python using AST - runs in thread to avoid blocking event loop"""
        functions = []
        classes = []
        methods = []
        imports = []
        complexity = 0
        
        try:
            tree = ast.parse(content)
            
            # Use a visitor pattern for cleaner parsing
            class CodeVisitor(ast.NodeVisitor):
                def __init__(self):
                    self.current_class = None
                    self.complexity = 0
                
                def visit_ClassDef(self, node):
                    docstring = ast.get_docstring(node)
                    decorators = [self._get_decorator_name(d) for d in node.decorator_list]
                    
                    class_element = CodeElement(
                        name=node.name,
                        type='class',
                        line_number=node.lineno,
                        docstring=docstring,
                        decorators=decorators
                    )
                    classes.append(class_element)
                    
                    # Visit class methods
                    old_class = self.current_class
                    self.current_class = node.name
                    self.generic_visit(node)
                    self.current_class = old_class
                
                def visit_FunctionDef(self, node):
                    docstring = ast.get_docstring(node)
                    parameters = [arg.arg for arg in node.args.args]
                    decorators = [self._get_decorator_name(d) for d in node.decorator_list]
                    
                    element = CodeElement(
                        name=node.name,
                        type='method' if self.current_class else 'function',
                        line_number=node.lineno,
                        docstring=docstring,
                        parameters=parameters,
                        decorators=decorators,
                        parent_class=self.current_class
                    )
                    
                    if self.current_class:
                        methods.append(element)
                    else:
                        functions.append(element)
                    
                    # Calculate complexity for this function
                    function_complexity = sum(1 for n in ast.walk(node) 
                                            if isinstance(n, (ast.If, ast.For, ast.While, 
                                                            ast.Try, ast.With, ast.Assert)))
                    self.complexity += function_complexity
                    
                    self.generic_visit(node)
                
                def visit_AsyncFunctionDef(self, node):
                    # Handle async functions the same way
                    self.visit_FunctionDef(node)
                
                def visit_Import(self, node):
                    for alias in node.names:
                        imports.append(f"import {alias.name}")
                
                def visit_ImportFrom(self, node):
                    module = node.module or ""
                    names = [alias.name for alias in node.names]
                    imports.append(f"from {module} import {', '.join(names)}")
                
                def _get_decorator_name(self, decorator):
                    """Extract decorator name safely"""
                    try:
                        if isinstance(decorator, ast.Name):
                            return decorator.id
                        elif isinstance(decorator, ast.Call):
                            if isinstance(decorator.func, ast.Name):
                                return decorator.func.id
                        return ast.unparse(decorator)
                    except:
                        return "unknown"
            
            visitor = CodeVisitor()
            visitor.visit(tree)
            complexity = visitor.complexity
            
        except SyntaxError as e:
            print(f"Warning: Syntax error in {file_path}: {e}")
        except Exception as e:
            print(f"Warning: Error parsing {file_path}: {e}")
        
        return functions, classes, methods, imports, complexity
    
    def _calculate_metrics(self, functions: List[CodeElement], 
                          classes: List[CodeElement], 
                          imports: List[str]) -> tuple:
        """Calculate derived metrics"""
        
        # Documentation coverage
        all_elements = functions + classes
        if all_elements:
            documented = sum(1 for elem in all_elements if elem.docstring)
            doc_coverage = (documented / len(all_elements)) * 100
        else:
            doc_coverage = 0.0
        
        # Dependencies
        dependencies = set()
        for imp in imports:
            if imp.startswith('import '):
                module = imp.split('import ')[1].split('.')[0].split(' as ')[0]
                if not module.startswith('.'):  # Skip relative imports
                    dependencies.add(module)
            elif imp.startswith('from '):
                try:
                    module = imp.split('from ')[1].split(' import')[0]
                    if not module.startswith('.'):  # Skip relative imports
                        dependencies.add(module)
                except:
                    pass
        
        # Exports (public functions and classes)
        exports = [elem.name for elem in all_elements if not elem.name.startswith('_')]
        
        return doc_coverage, dependencies, exports
    
    async def read_file_safe(self, file_path: Path, max_size: int = 1024*1024) -> Optional[str]:
        """Safely read file content with size limits"""
        try:
            # Check file size first
            if file_path.stat().st_size > max_size:
                print(f"Warning: Skipping large file {file_path} ({file_path.stat().st_size} bytes)")
                return None
            
            # Try UTF-8 first, fallback to latin-1
            for encoding in ['utf-8', 'latin-1']:
                try:
                    async with aiofiles.open(file_path, 'r', encoding=encoding) as f:
                        return await f.read()
                except UnicodeDecodeError:
                    continue
            
            return None
            
        except Exception as e:
            print(f"Warning: Could not read {file_path}: {e}")
            return None
    
    async def analyze_file(self, file_path: Path, project_root: Path, 
                          max_file_size: int = 1024*1024) -> Optional[FileAnalysis]:
        """Analyze a single file with proper async handling"""
        
        content = await self.read_file_safe(file_path, max_file_size)
        if content is None:
            return None
        
        extension = file_path.suffix.lower()
        language = self.language_map.get(extension, 'unknown')
        relative_path = file_path.relative_to(project_root)
        lines = len(content.split('\n'))
        size = len(content.encode('utf-8'))
        
        # Parse code in thread to avoid blocking event loop
        if language == 'python':
            loop = asyncio.get_event_loop()
            functions, classes, methods, imports, complexity = await loop.run_in_executor(
                self.executor, self._parse_python_ast, content, file_path
            )
        else:
            # For other languages, use basic parsing or add more parsers
            functions, classes, methods, imports, complexity = [], [], [], [], 0
        
        # Calculate metrics
        doc_coverage, dependencies, exports = self._calculate_metrics(
            functions, classes, imports
        )
        
        return FileAnalysis(
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
            docstring_coverage=doc_coverage,
            dependencies=dependencies,
            exports=exports
        )
    
    async def analyze_files_batch(self, file_paths: List[Path], project_root: Path,
                                 batch_size: int = 10, max_file_size: int = 1024*1024) -> List[FileAnalysis]:
        """Analyze files in batches with proper error handling"""
        analyses = []
        
        for i in range(0, len(file_paths), batch_size):
            batch = file_paths[i:i + batch_size]
            
            # Process batch concurrently
            tasks = [self.analyze_file(file_path, project_root, max_file_size) 
                    for file_path in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out None results and exceptions
            valid_results = []
            for result in batch_results:
                if isinstance(result, Exception):
                    print(f"Error in batch analysis: {result}")
                elif result is not None:
                    valid_results.append(result)
            
            analyses.extend(valid_results)
            print(f"✅ Analyzed batch {i//batch_size + 1}: {len(valid_results)} files")
        
        return analyses
    
    def __del__(self):
        """Clean up thread pool"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)