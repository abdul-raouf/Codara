import ollama
from typing import List, Dict
from dataclasses import dataclass
from advanced_parser import AdvancedFileAnalysis, CodeElement
import json

class EnhancedDocumentationGenerator:
    def __init__(self, model_name: str = "codellama:13b"):
        self.model_name = model_name
        self.client = ollama.Client()
    
    def create_enhanced_overview_prompt(self, analyses: List[AdvancedFileAnalysis]) -> str:
        """Create a comprehensive project overview prompt"""
        
        # Gather advanced statistics
        total_files = len(analyses)
        total_lines = sum(a.lines for a in analyses)
        total_functions = sum(len(a.functions) for a in analyses)
        total_classes = sum(len(a.classes) for a in analyses)
        total_methods = sum(len(a.methods) for a in analyses)
        
        # Calculate average complexity and documentation coverage
        avg_complexity = sum(a.complexity_score for a in analyses) / len(analyses) if analyses else 0
        avg_doc_coverage = sum(a.docstring_coverage for a in analyses) / len(analyses) if analyses else 0
        
        # Get all unique dependencies
        all_dependencies = set()
        for analysis in analyses:
            all_dependencies.update(analysis.dependencies)
        
        # Create detailed file breakdown
        file_details = []
        for analysis in analyses:
            file_details.append(f"""
- **{analysis.relative_path}** ({analysis.language})
  - Lines: {analysis.lines}
  - Functions: {len(analysis.functions)}
  - Classes: {len(analysis.classes)}
  - Methods: {len(analysis.methods)}
  - Complexity: {analysis.complexity_score}
  - Doc Coverage: {analysis.docstring_coverage:.1f}%
  - Key Exports: {', '.join(analysis.exports[:3])}""")
        
        prompt = f"""
You are creating comprehensive technical documentation. Analyze this codebase and provide a detailed overview.

## PROJECT METRICS
- **Files:** {total_files}
- **Total Lines:** {total_lines:,}
- **Functions:** {total_functions}
- **Classes:** {total_classes} 
- **Methods:** {total_methods}
- **Average Complexity:** {avg_complexity:.1f}
- **Documentation Coverage:** {avg_doc_coverage:.1f}%

## DEPENDENCIES
{', '.join(sorted(all_dependencies))}

## FILE BREAKDOWN
{''.join(file_details)}

Generate a professional project overview with these sections:
1. **Executive Summary** - What this project does and its main purpose
2. **Architecture Analysis** - Code organization, design patterns, structure quality
3. **Technical Stack** - Languages, frameworks, key dependencies
4. **Code Quality Assessment** - Complexity, documentation, maintainability
5. **Key Components** - Main modules and their responsibilities
6. **Development Insights** - Recommendations for improvement or notable strengths

Use markdown formatting and be specific about what you observe in the code.
"""
        return prompt
    
    def create_detailed_file_prompt(self, analysis: AdvancedFileAnalysis) -> str:
        """Create detailed documentation prompt for a specific file"""
        
        # Format functions with details
        function_details = []
        for func in analysis.functions[:5]:  # Limit to first 5
            params = f"({', '.join(func.parameters)})" if func.parameters else "()"
            decorators = f"@{', @'.join(func.decorators)}" if func.decorators else ""
            docstring = f"Has docstring: {bool(func.docstring)}"
            function_details.append(f"  - `{func.name}{params}` - Line {func.line_number} - {docstring}")
        
        # Format classes with details
        class_details = []
        for cls in analysis.classes:
            decorators = f"@{', @'.join(cls.decorators)}" if cls.decorators else ""
            docstring = f"Has docstring: {bool(cls.docstring)}"
            class_details.append(f"  - `{cls.name}` - Line {cls.line_number} - {docstring}")
        
        prompt = f"""
Document this {analysis.language} file with detailed technical analysis.

## FILE OVERVIEW
- **Path:** {analysis.relative_path}
- **Size:** {analysis.lines} lines, {analysis.size} bytes
- **Complexity Score:** {analysis.complexity_score}
- **Documentation Coverage:** {analysis.docstring_coverage:.1f}%

## CODE STRUCTURE

### Functions ({len(analysis.functions)})
{''.join(function_details) if function_details else "  - No functions found"}

### Classes ({len(analysis.classes)})
{''.join(class_details) if class_details else "  - No classes found"}

### Methods ({len(analysis.methods)})
{'  - ' + str(len(analysis.methods)) + ' methods found in classes'}

### Dependencies
{', '.join(analysis.dependencies) if analysis.dependencies else 'No external dependencies'}

### Public Interface
{', '.join(analysis.exports[:10]) if analysis.exports else 'No public exports identified'}

Create comprehensive documentation with:
1. **File Purpose** - What this file accomplishes
2. **Architecture Role** - How it fits in the larger system
3. **Key Components** - Detailed explanation of main functions/classes
4. **API Interface** - What other files can use from this module
5. **Implementation Notes** - Notable patterns, algorithms, or design decisions
6. **Quality Assessment** - Code quality, maintainability observations

Be technical and specific. Use markdown formatting.
"""
        return prompt
    
    async def generate_enhanced_documentation(self, analyses: List[AdvancedFileAnalysis]) -> str:
        """Generate comprehensive documentation using advanced analysis"""
        
        print("🤖 Generating enhanced documentation with detailed code analysis...")
        
        # Generate project overview
        overview_prompt = self.create_enhanced_overview_prompt(analyses)
        overview_response = self.client.chat(
            model=self.model_name,
            messages=[{'role': 'user', 'content': overview_prompt}],
            options={'temperature': 0.3, 'max_tokens': 2000}
        )
        
        doc = "# 📋 Comprehensive Project Documentation\n\n"
        doc += "*Generated with Advanced Code Analysis*\n\n"
        doc += overview_response['message']['content']
        doc += "\n\n---\n\n"
        
        # Generate detailed file documentation for significant files
        significant_files = [a for a in analyses if a.lines > 20 or len(a.functions) > 2]
        
        for i, analysis in enumerate(significant_files[:4], 1):
            print(f"🤖 Generating detailed documentation for {analysis.relative_path} ({i}/{min(4, len(significant_files))})")
            
            file_prompt = self.create_detailed_file_prompt(analysis)
            file_response = self.client.chat(
                model=self.model_name,
                messages=[{'role': 'user', 'content': file_prompt}],
                options={'temperature': 0.3, 'max_tokens': 1500}
            )
            
            doc += f"# 📁 {analysis.relative_path}\n\n"
            doc += file_response['message']['content']
            doc += "\n\n---\n\n"
        
        # Add technical appendix
        doc += self.create_technical_appendix(analyses)
        
        return doc
    
    def create_technical_appendix(self, analyses: List[AdvancedFileAnalysis]) -> str:
        """Create technical appendix with metrics and insights"""
        
        appendix = "# 📊 Technical Appendix\n\n"
        
        # Complexity analysis
        appendix += "## Code Complexity Analysis\n\n"
        appendix += "| File | Lines | Functions | Classes | Complexity | Doc Coverage |\n"
        appendix += "|------|-------|-----------|---------|------------|-------------|\n"
        
        for analysis in analyses:
            appendix += f"| `{analysis.relative_path}` | {analysis.lines} | {len(analysis.functions)} | {len(analysis.classes)} | {analysis.complexity_score} | {analysis.docstring_coverage:.1f}% |\n"
        
        # Dependency graph
        all_deps = set()
        for analysis in analyses:
            all_deps.update(analysis.dependencies)
        
        appendix += f"\n## Dependencies ({len(all_deps)})\n\n"
        for dep in sorted(all_deps):
            appendix += f"- `{dep}`\n"
        
        return appendix