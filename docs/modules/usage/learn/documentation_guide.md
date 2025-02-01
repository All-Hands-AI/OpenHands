# OpenHands Documentation and Developer Experience Guide

This guide covers documentation systems, developer tooling, and developer experience improvements for OpenHands systems.

## Table of Contents
1. [Documentation System](#documentation-system)
2. [Developer Tools](#developer-tools)
3. [Code Generation](#code-generation)
4. [Developer Experience](#developer-experience)

## Documentation System

### 1. Documentation Generator

Implementation of documentation generation system:

```python
from typing import Dict, List, Any, Optional
import ast
import inspect
import re
import markdown
import yaml
from pathlib import Path

class DocNode:
    """Documentation node"""
    
    def __init__(
        self,
        name: str,
        doc_type: str,
        content: str,
        metadata: dict = None
    ):
        self.name = name
        self.doc_type = doc_type
        self.content = content
        self.metadata = metadata or {}
        self.children: List[DocNode] = []
        
    def add_child(self, node: 'DocNode'):
        """Add child node"""
        self.children.append(node)
        
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'name': self.name,
            'type': self.doc_type,
            'content': self.content,
            'metadata': self.metadata,
            'children': [
                child.to_dict()
                for child in self.children
            ]
        }

class DocumentationGenerator:
    """Documentation generation system"""
    
    def __init__(self):
        self.root = DocNode("root", "root", "")
        self.processors: Dict[str, Callable] = {}
        
    def add_processor(
        self,
        doc_type: str,
        processor: Callable
    ):
        """Add documentation processor"""
        self.processors[doc_type] = processor
        
    async def generate_docs(
        self,
        source_path: str,
        output_path: str
    ):
        """Generate documentation"""
        # Process source files
        await self._process_source(
            Path(source_path),
            self.root
        )
        
        # Generate output
        await self._generate_output(
            self.root,
            Path(output_path)
        )
        
    async def _process_source(
        self,
        path: Path,
        parent: DocNode
    ):
        """Process source files"""
        if path.is_file():
            # Process file
            if path.suffix == '.py':
                await self._process_python_file(path, parent)
            elif path.suffix == '.md':
                await self._process_markdown_file(path, parent)
            elif path.suffix == '.yaml':
                await self._process_yaml_file(path, parent)
        else:
            # Process directory
            for item in path.iterdir():
                if item.name.startswith('_'):
                    continue
                await self._process_source(item, parent)
                
    async def _process_python_file(
        self,
        path: Path,
        parent: DocNode
    ):
        """Process Python source file"""
        with open(path) as f:
            content = f.read()
            
        # Parse Python code
        tree = ast.parse(content)
        
        # Create module node
        module_node = DocNode(
            path.stem,
            "module",
            ast.get_docstring(tree) or "",
            {'path': str(path)}
        )
        parent.add_child(module_node)
        
        # Process classes and functions
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.ClassDef):
                await self._process_class(node, module_node)
            elif isinstance(node, ast.FunctionDef):
                await self._process_function(node, module_node)
                
    async def _process_class(
        self,
        node: ast.ClassDef,
        parent: DocNode
    ):
        """Process Python class"""
        class_node = DocNode(
            node.name,
            "class",
            ast.get_docstring(node) or "",
            {
                'bases': [
                    base.id for base in node.bases
                    if isinstance(base, ast.Name)
                ]
            }
        )
        parent.add_child(class_node)
        
        # Process methods
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                await self._process_function(item, class_node)
                
    async def _process_function(
        self,
        node: ast.FunctionDef,
        parent: DocNode
    ):
        """Process Python function"""
        func_node = DocNode(
            node.name,
            "function",
            ast.get_docstring(node) or "",
            {
                'args': [
                    arg.arg for arg in node.args.args
                    if arg.arg != 'self'
                ],
                'returns': self._get_return_annotation(node)
            }
        )
        parent.add_child(func_node)
        
    def _get_return_annotation(
        self,
        node: ast.FunctionDef
    ) -> Optional[str]:
        """Get function return annotation"""
        if node.returns:
            if isinstance(node.returns, ast.Name):
                return node.returns.id
            elif isinstance(node.returns, ast.Subscript):
                return node.returns.value.id
        return None
        
    async def _process_markdown_file(
        self,
        path: Path,
        parent: DocNode
    ):
        """Process Markdown file"""
        with open(path) as f:
            content = f.read()
            
        # Parse frontmatter
        metadata = {}
        if content.startswith('---'):
            end = content.find('---', 3)
            if end != -1:
                frontmatter = content[3:end]
                try:
                    metadata = yaml.safe_load(frontmatter)
                    content = content[end + 4:]
                except yaml.YAMLError:
                    pass
                    
        # Create document node
        doc_node = DocNode(
            path.stem,
            "document",
            content,
            metadata
        )
        parent.add_child(doc_node)
        
    async def _generate_output(
        self,
        node: DocNode,
        output_path: Path
    ):
        """Generate documentation output"""
        # Create output directory
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Process node
        processor = self.processors.get(node.doc_type)
        if processor:
            await processor(node, output_path)
            
        # Process children
        for child in node.children:
            await self._generate_output(
                child,
                output_path / child.name
            )
```

## Developer Tools

### 1. CLI Tool System

Implementation of developer CLI tools:

```python
import click
import asyncio
from typing import Dict, Any

class CLIContext:
    """CLI context information"""
    
    def __init__(self):
        self.config = {}
        self.verbose = False
        
    def set_config(self, config: dict):
        """Set configuration"""
        self.config = config
        
    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self.config.get(key, default)

class CLICommand:
    """Base CLI command"""
    
    def __init__(
        self,
        name: str,
        help: str = None
    ):
        self.name = name
        self.help = help
        self.subcommands: Dict[str, CLICommand] = {}
        
    def add_subcommand(
        self,
        command: 'CLICommand'
    ):
        """Add subcommand"""
        self.subcommands[command.name] = command
        
    @property
    def click_command(self) -> click.Command:
        """Get Click command"""
        @click.command(
            name=self.name,
            help=self.help
        )
        @click.pass_context
        def command(ctx, *args, **kwargs):
            # Create context
            cli_ctx = CLIContext()
            cli_ctx.verbose = ctx.obj.get('verbose', False)
            
            # Execute command
            asyncio.run(
                self.execute(cli_ctx, *args, **kwargs)
            )
            
        # Add subcommands
        for subcmd in self.subcommands.values():
            command.add_command(subcmd.click_command)
            
        return command
        
    async def execute(
        self,
        context: CLIContext,
        *args,
        **kwargs
    ):
        """Execute command"""
        raise NotImplementedError

class DevTools:
    """Developer tools system"""
    
    def __init__(self):
        self.commands: Dict[str, CLICommand] = {}
        
    def add_command(
        self,
        command: CLICommand
    ):
        """Add CLI command"""
        self.commands[command.name] = command
        
    def run(self):
        """Run CLI application"""
        # Create root command
        @click.group()
        @click.option(
            '--verbose',
            is_flag=True,
            help='Enable verbose output'
        )
        @click.pass_context
        def cli(ctx, verbose):
            ctx.obj = {'verbose': verbose}
            
        # Add commands
        for command in self.commands.values():
            cli.add_command(command.click_command)
            
        # Run CLI
        cli()
```

### 2. Code Generator

Implementation of code generation system:

```python
from jinja2 import Environment, FileSystemLoader
import inflection

class CodeTemplate:
    """Code template definition"""
    
    def __init__(
        self,
        name: str,
        template: str,
        context: dict = None
    ):
        self.name = name
        self.template = template
        self.context = context or {}
        
    def render(
        self,
        **kwargs
    ) -> str:
        """Render template"""
        # Update context
        context = self.context.copy()
        context.update(kwargs)
        
        # Add utility functions
        context.update({
            'pluralize': inflection.pluralize,
            'singularize': inflection.singularize,
            'camelize': inflection.camelize,
            'underscore': inflection.underscore
        })
        
        # Render template
        return self.template.format(**context)

class CodeGenerator:
    """Code generation system"""
    
    def __init__(
        self,
        template_path: str
    ):
        self.env = Environment(
            loader=FileSystemLoader(template_path)
        )
        self.templates: Dict[str, CodeTemplate] = {}
        
    def add_template(
        self,
        name: str,
        template_file: str,
        context: dict = None
    ):
        """Add code template"""
        template = self.env.get_template(template_file)
        self.templates[name] = CodeTemplate(
            name,
            template.render(),
            context
        )
        
    async def generate(
        self,
        template_name: str,
        output_path: str,
        context: dict = None
    ):
        """Generate code from template"""
        template = self.templates.get(template_name)
        if not template:
            raise ValueError(
                f"Unknown template: {template_name}"
            )
            
        # Render template
        code = template.render(**(context or {}))
        
        # Write output
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            f.write(code)
```

## Developer Experience

### 1. Developer Portal

Implementation of developer portal:

```python
class DevPortal:
    """Developer portal system"""
    
    def __init__(self):
        self.sections: Dict[str, 'PortalSection'] = {}
        
    def add_section(
        self,
        section: 'PortalSection'
    ):
        """Add portal section"""
        self.sections[section.name] = section
        
    async def generate(
        self,
        output_path: str
    ):
        """Generate developer portal"""
        output_dir = Path(output_path)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate sections
        for section in self.sections.values():
            await section.generate(output_dir)
            
        # Generate index
        await self._generate_index(output_dir)
        
    async def _generate_index(
        self,
        output_dir: Path
    ):
        """Generate portal index"""
        index = {
            'sections': [
                section.to_dict()
                for section in self.sections.values()
            ]
        }
        
        with open(output_dir / 'index.json', 'w') as f:
            json.dump(index, f, indent=2)

class PortalSection:
    """Portal section definition"""
    
    def __init__(
        self,
        name: str,
        title: str,
        description: str = None
    ):
        self.name = name
        self.title = title
        self.description = description
        self.pages: List[PortalPage] = []
        
    def add_page(
        self,
        page: 'PortalPage'
    ):
        """Add section page"""
        self.pages.append(page)
        
    async def generate(
        self,
        output_dir: Path
    ):
        """Generate section content"""
        section_dir = output_dir / self.name
        section_dir.mkdir(exist_ok=True)
        
        # Generate pages
        for page in self.pages:
            await page.generate(section_dir)
            
        # Generate section index
        with open(section_dir / 'index.json', 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
            
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'name': self.name,
            'title': self.title,
            'description': self.description,
            'pages': [
                page.to_dict()
                for page in self.pages
            ]
        }

class PortalPage:
    """Portal page definition"""
    
    def __init__(
        self,
        name: str,
        title: str,
        content: str,
        metadata: dict = None
    ):
        self.name = name
        self.title = title
        self.content = content
        self.metadata = metadata or {}
        
    async def generate(
        self,
        output_dir: Path
    ):
        """Generate page content"""
        # Convert content to HTML
        html = markdown.markdown(self.content)
        
        # Write page
        with open(output_dir / f"{self.name}.html", 'w') as f:
            f.write(html)
            
        # Write metadata
        with open(output_dir / f"{self.name}.json", 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
            
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'name': self.name,
            'title': self.title,
            'metadata': self.metadata
        }
```

Remember to:
- Document code thoroughly
- Provide developer tools
- Generate documentation
- Create developer portal
- Maintain documentation
- Support code generation
- Improve developer experience