#!/usr/bin/env python3
"""
Production-Ready Code Documentation Agent
Fixes all identified issues and provides robust, configurable documentation generation.
"""
from pathlib import Path
import sys
import asyncio
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table
from rich import print as rprint

from config import DocumentationConfig
from file_discovery import FileDiscovery
from production_parser import ProductionCodeParser
from enhanced_doc_generator import EnhancedDocumentationGenerator

class ProductionDocumentationAgent:
    """Production-ready documentation agent"""
    
    def __init__(self, config: DocumentationConfig):
        self.config = config
        self.console = Console()
        
        # Initialize components with config
        self.discovery = FileDiscovery()
        self.discovery.code_extensions = config.code_extensions
        self.discovery.ignore_dirs = config.ignore_dirs
        self.discovery.ignore_files = config.ignore_files
        
        self.parser = ProductionCodeParser(max_workers=4)
        self.doc_generator = EnhancedDocumentationGenerator(config.model_name)
    
    async def run(self, project_path: Path) -> bool:
        """Run the complete documentation generation process"""
        try:
            self.console.print("🚀 [bold green]Production Code Documentation Agent[/bold green]")
            self.console.print(f"📁 Project: {project_path}")
            self.console.print(f"🤖 Model: {self.config.model_name}")
            self.console.print()
            
            # Step 1: Discovery
            files = await self._discover_files(project_path)
            if not files:
                self.console.print("[red]❌ No code files found![/red]")
                return False
            
            # Step 2: Analysis
            analyses = await self._analyze_files(files, project_path)
            if not analyses:
                self.console.print("[red]❌ No files could be analyzed![/red]")
                return False
            
            # Step 3: Show analysis summary
            self._show_analysis_summary(analyses)
            
            # Step 4: Generate documentation
            success = await self._generate_documentation(analyses, project_path)
            
            return success
            
        except KeyboardInterrupt:
            self.console.print("\n[yellow]⚠️ Operation cancelled by user[/yellow]")
            return False
        except Exception as e:
            self.console.print(f"[red]❌ Unexpected error: {e}[/red]")
            import traceback
            traceback.print_exc()
            return False
    
    async def _discover_files(self, project_path: Path) -> list:
        """Step 1: Discover code files"""
        self.console.print("🔍 [yellow]Step 1: Discovering code files...[/yellow]")
        
        try:
            files = self.discovery.discover_files(project_path)
            
            # Filter by size
            valid_files = []
            for file_path in files:
                try:
                    if file_path.stat().st_size <= self.config.max_file_size:
                        valid_files.append(file_path)
                    else:
                        print(f"Skipping large file: {file_path}")
                except OSError:
                    continue
            
            self.console.print(f"✅ Found {len(valid_files)} analyzable files (filtered from {len(files)} total)")
            return valid_files
            
        except Exception as e:
            self.console.print(f"[red]❌ Error discovering files: {e}[/red]")
            return []
    
    async def _analyze_files(self, files: list, project_root: Path) -> list:
        """Step 2: Analyze file contents"""
        self.console.print("🧠 [yellow]Step 2: Analyzing code structure...[/yellow]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=self.console
        ) as progress:
            
            task = progress.add_task("Analyzing files...", total=len(files))
            
            analyses = await self.parser.analyze_files_batch(
                files, 
                project_root,
                batch_size=self.config.batch_size,
                max_file_size=self.config.max_file_size
            )
            
            progress.update(task, completed=len(files))
        
        self.console.print(f"✅ Successfully analyzed {len(analyses)} files")
        return analyses
    
    def _show_analysis_summary(self, analyses: list):
        """Display analysis summary table"""
        self.console.print("\n📊 [yellow]Analysis Summary[/yellow]")
        
        # Create summary table
        table = Table(title="Code Analysis Results")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        total_lines = sum(a.lines for a in analyses)
        total_functions = sum(len(a.functions) for a in analyses)
        total_classes = sum(len(a.classes) for a in analyses)
        total_methods = sum(len(a.methods) for a in analyses)
        avg_complexity = sum(a.complexity_score for a in analyses) / len(analyses) if analyses else 0
        avg_doc_coverage = sum(a.docstring_coverage for a in analyses) / len(analyses) if analyses else 0
        
        table.add_row("Files Analyzed", str(len(analyses)))
        table.add_row("Total Lines", f"{total_lines:,}")
        table.add_row("Functions", str(total_functions))
        table.add_row("Classes", str(total_classes))
        table.add_row("Methods", str(total_methods))
        table.add_row("Avg Complexity", f"{avg_complexity:.1f}")
        table.add_row("Avg Documentation", f"{avg_doc_coverage:.1f}%")
        
        self.console.print(table)
        self.console.print()
    
    async def _generate_documentation(self, analyses: list, project_root: Path) -> bool:
        """Step 3: Generate AI documentation"""
        self.console.print("🤖 [yellow]Step 3: Generating AI documentation...[/yellow]")
        
        try:
            # Limit files for documentation to avoid overwhelming the AI
            significant_files = [
                a for a in analyses 
                if a.lines >= self.config.min_lines_for_detailed_doc
            ][:self.config.max_files_to_document]
            
            if not significant_files:
                significant_files = analyses[:self.config.max_files_to_document]
            
            self.console.print(f"📝 Generating documentation for {len(significant_files)} significant files...")
            
            # Generate documentation
            documentation = await self.doc_generator.generate_enhanced_documentation(significant_files)
            
            # Save to file
            output_path = project_root / self.config.output_filename
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(documentation)
            
            # Success message
            self.console.print(f"🎉 [bold green]Documentation generated successfully![/bold green]")
            self.console.print(f"📄 Output: {output_path}")
            self.console.print(f"📏 Size: {len(documentation):,} characters")
            
            return True
            
        except Exception as e:
            self.console.print(f"[red]❌ Error generating documentation: {e}[/red]")
            return False

async def main():
    console = Console()
    
    # Parse arguments
    if len(sys.argv) not in [2, 3]:
        console.print("[red]Usage: python production_main.py <project_directory> [config.json][/red]")
        console.print("Example: python production_main.py /path/to/project")
        console.print("Example: python production_main.py /path/to/project custom_config.json")
        sys.exit(1)
    
    project_path = Path(sys.argv[1])
    config_path = Path(sys.argv[2]) if len(sys.argv) == 3 else Path("doc_config.json")
    
    if not project_path.exists():
        console.print(f"[red]❌ Project directory does not exist: {project_path}[/red]")
        sys.exit(1)
    
    # Load configuration
    config = DocumentationConfig.from_file(config_path)
    
    # Save default config if it doesn't exist
    if not config_path.exists():
        config.save_to_file(config_path)
        console.print(f"📄 Created default config file: {config_path}")
    
    # Run documentation agent
    agent = ProductionDocumentationAgent(config)
    success = await agent.run(project_path)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())