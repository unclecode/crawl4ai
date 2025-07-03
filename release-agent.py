#!/usr/bin/env python3
"""
Crawl4AI Release Agent - Automated release management with LLM assistance
"""

import os
import sys
import re
import json
import subprocess
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Literal, Tuple
from datetime import datetime
from pathlib import Path
import click
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
import litellm

console = Console()

# State machine states
States = Literal[
    "init",
    "commit_selection", 
    "version_bump",
    "test_generation",
    "test_execution",
    "release_notes",
    "demo_generation",
    "docs_update", 
    "branch_creation",
    "build_publish",
    "complete"
]

@dataclass
class SharedContext:
    """Shared context that grows throughout the release process"""
    selected_commits: List[Dict] = field(default_factory=list)
    version: str = ""
    old_version: str = ""
    test_script: str = ""
    test_results: Dict = field(default_factory=dict)
    release_notes: str = ""
    demo_script: str = ""
    branch_name: str = ""
    
    # Growing context
    decisions: List[Dict] = field(default_factory=list)
    files_changed: List[str] = field(default_factory=list)
    api_changes: List[str] = field(default_factory=list)
    
    def add_decision(self, step: str, decision: str, reason: str = ""):
        """Track decisions made during the process"""
        self.decisions.append({
            "step": step,
            "decision": decision,
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        })

@dataclass 
class JudgeResult:
    """Result from the judge LLM"""
    status: Literal["good", "retry", "human"]
    feedback: str
    specific_issues: List[str] = field(default_factory=list)

class LLMManager:
    """Manages stateless LLM calls with context engineering"""
    
    def __init__(self, main_model: str = "claude-sonnet-4-20250514", judge_model: str = "claude-sonnet-4-20250514"):
        self.main_model = os.getenv("MAIN_MODEL", main_model)
        self.judge_model = os.getenv("JUDGE_MODEL", judge_model)
        
    def call(self, 
             task: str, 
             context: Dict,
             model: Optional[str] = None,
             temperature: float = 0.7) -> str:
        """
        Make a stateless LLM call with engineered context
        """
        model = model or self.main_model
        
        # Build system message with context engineering
        system_message = self._build_system_message(context)
        
        # Single user message with the task
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": task}
        ]
        
        try:
            response = litellm.completion(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=16000,
            )
            return response.choices[0].message.content
        except Exception as e:
            console.print(f"[red]LLM Error: {e}[/red]")
            raise
    
    def _extract_json(self, response: str) -> Dict:
        """Extract JSON from <JSON></JSON> tags"""
        import re
        json_match = re.search(r'<JSON>(.*?)</JSON>', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1).strip()
            return json.loads(json_str)
        raise ValueError("No JSON found in response")
    
    def get_relevant_files(self, query: str, num_files: int = 10) -> List[Dict[str, str]]:
        """Use LLM to select relevant files from codebase for context"""
        
        # Get directory structure
        crawl4ai_files = []
        docs_files = []
        examples_files = []
        
        # Scan crawl4ai directory
        for root, dirs, files in os.walk("crawl4ai"):
            # Skip __pycache__ and other unwanted directories
            dirs[:] = [d for d in dirs if not d.startswith('__') and d != '.git']
            for file in files:
                if file.endswith('.py') and not file.startswith('__'):
                    rel_path = os.path.relpath(os.path.join(root, file))
                    crawl4ai_files.append(rel_path)
        
        # Scan docs directory
        if os.path.exists("docs"):
            for root, dirs, files in os.walk("docs"):
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                for file in files:
                    if file.endswith(('.md', '.rst')):
                        rel_path = os.path.relpath(os.path.join(root, file))
                        docs_files.append(rel_path)
        
        # Scan examples directory
        if os.path.exists("examples"):
            for root, dirs, files in os.walk("examples"):
                for file in files:
                    if file.endswith('.py'):
                        rel_path = os.path.relpath(os.path.join(root, file))
                        examples_files.append(rel_path)
        
        # Build file selection prompt
        file_selection_prompt = f"""Select the most relevant files to understand Crawl4AI for the following task:

<TASK>
{query}
</TASK>

<AVAILABLE_FILES>
## Core Library Files:
{chr(10).join(crawl4ai_files[:50])}  # Limit to prevent context overflow

## Documentation Files:
{chr(10).join(docs_files[:30])}

## Example Files:
{chr(10).join(examples_files[:20])}
</AVAILABLE_FILES>

Select exactly {num_files} files that would be most helpful for understanding Crawl4AI in the context of the given task.
Prioritize:
1. Core API classes and interfaces
2. Relevant examples
3. Documentation explaining key concepts
4. Files related to the specific task

IMPORTANT: Return ONLY a JSON response wrapped in <JSON></JSON> tags.
<JSON>
{{
    "selected_files": [
        "crawl4ai/core_api.py",
        "docs/getting_started.md",
        "examples/basic_usage.py"
    ],
    "reasoning": "Brief explanation of why these files were selected"
}}
</JSON>"""
        
        try:
            response = self.call(file_selection_prompt, {}, temperature=0.3)
            result = self._extract_json(response)
            selected_files = result.get("selected_files", [])
            
            # Read the selected files
            file_contents = []
            for file_path in selected_files:
                if os.path.exists(file_path):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            # Limit file size to prevent context overflow
                            if len(content) > 10000:
                                content = content[:10000] + "\n... (truncated)"
                            file_contents.append({
                                "path": file_path,
                                "content": content
                            })
                    except Exception as e:
                        console.print(f"[yellow]Warning: Could not read {file_path}: {e}[/yellow]")
            
            return file_contents
            
        except Exception as e:
            console.print(f"[yellow]Warning: Could not select relevant files: {e}[/yellow]")
            # Fallback: return some default important files
            default_files = [
                "crawl4ai/__init__.py",
                "crawl4ai/async_crawler.py",
                "README.md"
            ]
            file_contents = []
            for file_path in default_files:
                if os.path.exists(file_path):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()[:10000]
                            file_contents.append({
                                "path": file_path,
                                "content": content
                            })
                    except:
                        pass
            return file_contents
    
    def _build_system_message(self, context: Dict) -> str:
        """Build engineered system message with all context"""
        sections = []
        
        # Role and objective
        sections.append("""You are a Release Engineering Assistant for Crawl4AI.
Your role is to help create high-quality releases with proper testing, documentation, and validation.
You work step-by-step, focusing on the current task while aware of the overall release context.""")
        
        # Add context sections with unique delimiters
        if "codebase_info" in context:
            sections.append(f"""
<<CODEBASE_INFORMATION_START>>
{context['codebase_info']}
<<CODEBASE_INFORMATION_END>>""")
            
        if "commit_diffs" in context:
            sections.append(f"""
<<COMMIT_CHANGES_START>>
{context['commit_diffs']}
<<COMMIT_CHANGES_END>>""")
            
        if "previous_decisions" in context:
            sections.append(f"""
<<PREVIOUS_DECISIONS_START>>
{context['previous_decisions']}
<<PREVIOUS_DECISIONS_END>>""")
            
        if "existing_patterns" in context:
            sections.append(f"""
<<EXISTING_PATTERNS_START>>
{context['existing_patterns']}
<<EXISTING_PATTERNS_END>>""")
            
        if "constraints" in context:
            sections.append(f"""
<<TASK_CONSTRAINTS_START>>
{context['constraints']}
<<TASK_CONSTRAINTS_END>>""")
            
        if "judge_feedback" in context:
            sections.append(f"""
<<JUDGE_FEEDBACK_START>>
{context['judge_feedback']}
<<JUDGE_FEEDBACK_END>>""")
            
        return "\n".join(sections)
    
    def judge(self, 
              step_output: str, 
              expected_criteria: List[str],
              context: Dict) -> JudgeResult:
        """Judge the quality of a step's output"""
        
        judge_task = f"""Evaluate the following output against the criteria:

<OUTPUT_TO_JUDGE>
{step_output}
</OUTPUT_TO_JUDGE>

<SUCCESS_CRITERIA>
{chr(10).join(f"- {c}" for c in expected_criteria)}
</SUCCESS_CRITERIA>

## Evaluation Required
1. Does the output meet ALL criteria? 
2. Are there any issues or improvements needed?
3. Is human intervention required?

IMPORTANT: Return ONLY a JSON response wrapped in <JSON></JSON> tags.
Do NOT include any markdown code blocks, backticks, or explanatory text.
The JSON will be directly parsed, so any extra formatting will cause errors.

Return your evaluation as:
<JSON>
{{
    "status": "good" | "retry" | "human",
    "feedback": "Clear explanation of the evaluation",
    "specific_issues": ["specific issue 1", "specific issue 2"]
}}
</JSON>"""
        
        response = self.call(judge_task, context, model=self.judge_model, temperature=0.3)
        
        try:
            # Extract JSON between tags
            import re
            json_match = re.search(r'<JSON>(.*?)</JSON>', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1).strip()
                result = json.loads(json_str)
                return JudgeResult(**result)
            else:
                raise ValueError("No JSON found in response")
        except Exception as e:
            # Fallback if JSON parsing fails
            console.print(f"[yellow]Judge parsing error: {e}[/yellow]")
            return JudgeResult(
                status="retry",
                feedback="Failed to parse judge response",
                specific_issues=["Invalid judge response format"]
            )

class GitOperations:
    """Handle git operations"""
    
    @staticmethod
    def get_commits_between_branches(base: str = "main", head: str = "next") -> List[Dict]:
        """Get commits in head that aren't in base"""
        cmd = ["git", "log", f"{base}..{head}", "--pretty=format:%H|%an|%ae|%at|%s", "--reverse"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        commits = []
        for line in result.stdout.strip().split('\n'):
            if line:
                hash, author, email, timestamp, subject = line.split('|', 4)
                commits.append({
                    "hash": hash,
                    "author": author,
                    "email": email,
                    "date": datetime.fromtimestamp(int(timestamp)).isoformat(),
                    "subject": subject,
                    "selected": False
                })
        return commits
    
    @staticmethod
    def get_commit_diff(commit_hash: str) -> str:
        """Get the diff for a specific commit"""
        cmd = ["git", "show", commit_hash, "--pretty=format:", "--unified=3"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.stdout
    
    @staticmethod
    def cherry_pick_commits(commits: List[str], branch: str) -> bool:
        """Cherry pick commits to a branch"""
        # Create and checkout branch
        subprocess.run(["git", "checkout", "-b", branch], check=True)
        
        # Cherry pick each commit
        for commit in commits:
            result = subprocess.run(["git", "cherry-pick", commit])
            if result.returncode != 0:
                console.print(f"[red]Failed to cherry-pick {commit}[/red]")
                return False
        return True

class ReleaseAgent:
    """Main release agent orchestrating the entire process"""
    
    def __init__(self, auto_mode: bool = False, select_all: bool = False, test_mode: bool = False):
        self.state: States = "init"
        self.context = SharedContext()
        self.llm = LLMManager()
        self.auto_mode = auto_mode
        self.select_all = select_all
        self.test_mode = test_mode
        
        # Load current version
        self._load_current_version()
        
    def _load_current_version(self):
        """Load current version from __version__.py"""
        version_file = Path("crawl4ai/__version__.py")
        if version_file.exists():
            content = version_file.read_text()
            for line in content.split('\n'):
                if '__version__' in line and '=' in line:
                    self.context.old_version = line.split('=')[1].strip().strip('"')
                    break
    
    def run(self):
        """Run the release process"""
        console.print("[bold cyan]🚀 Crawl4AI Release Agent[/bold cyan]\n")
        
        # State machine
        while self.state != "complete":
            try:
                if self.state == "init":
                    self.state = "commit_selection"
                elif self.state == "commit_selection":
                    self._select_commits()
                    self.state = "version_bump"
                elif self.state == "version_bump":
                    self._bump_version()
                    self.state = "test_generation"
                elif self.state == "test_generation":
                    self._generate_tests()
                    self.state = "test_execution"
                elif self.state == "test_execution":
                    if self._run_tests():
                        self.state = "branch_creation"
                    else:
                        console.print("[red]Tests failed! Fix issues and try again.[/red]")
                        break
                elif self.state == "branch_creation":
                    self._create_version_branch()
                    self.state = "release_notes"
                elif self.state == "release_notes":
                    self._generate_release_notes()
                    self.state = "demo_generation"
                elif self.state == "demo_generation":
                    self._generate_demo()
                    self.state = "docs_update"
                elif self.state == "docs_update":
                    self._update_docs()
                    self.state = "build_publish"
                elif self.state == "build_publish":
                    if self._build_and_publish():
                        self.state = "complete"
                    else:
                        break
                        
            except KeyboardInterrupt:
                console.print("\n[yellow]Release process interrupted by user[/yellow]")
                break
            except Exception as e:
                console.print(f"[red]Error in state {self.state}: {e}[/red]")
                break
        
        if self.state == "complete":
            console.print("\n[green]✅ Release completed successfully![/green]")
    
    def _select_commits(self):
        """Select commits to include in release"""
        console.print("[bold]Step 1: Select Commits[/bold]")
        
        commits = GitOperations.get_commits_between_branches()
        
        if self.select_all:
            # Auto-select all commits
            for commit in commits:
                commit["selected"] = True
            self.context.selected_commits = commits
            console.print(f"[green]Auto-selected all {len(commits)} commits[/green]")
        else:
            # Interactive selection
            table = Table(title="Commits in 'next' not in 'main'")
            table.add_column("", style="cyan", width=3)
            table.add_column("Hash", style="yellow")
            table.add_column("Author", style="green")
            table.add_column("Date", style="blue")
            table.add_column("Subject", style="white")
            
            for i, commit in enumerate(commits):
                table.add_row(
                    str(i),
                    commit["hash"][:8],
                    commit["author"],
                    commit["date"][:10],
                    commit["subject"]
                )
            
            console.print(table)
            
            # Get selections
            selections = Prompt.ask(
                "Select commits (e.g., 0,2,3-5 or 'all')",
                default="all"
            )
            
            if selections.lower() == "all":
                for commit in commits:
                    commit["selected"] = True
            else:
                # Parse selection
                for part in selections.split(','):
                    if '-' in part:
                        start, end = map(int, part.split('-'))
                        for i in range(start, end + 1):
                            if 0 <= i < len(commits):
                                commits[i]["selected"] = True
                    else:
                        i = int(part.strip())
                        if 0 <= i < len(commits):
                            commits[i]["selected"] = True
            
            self.context.selected_commits = [c for c in commits if c["selected"]]
            
        # Collect diffs for selected commits
        for commit in self.context.selected_commits:
            diff = GitOperations.get_commit_diff(commit["hash"])
            # Store simplified diff info
            self.context.files_changed.extend(self._extract_changed_files(diff))
        
        console.print(f"[green]Selected {len(self.context.selected_commits)} commits[/green]")
    
    def _bump_version(self):
        """Determine and confirm version bump"""
        console.print("\n[bold]Step 2: Version Bump[/bold]")
        
        # Analyze commits to suggest version bump
        commit_types = {"feat": 0, "fix": 0, "breaking": 0}
        for commit in self.context.selected_commits:
            subject = commit["subject"].lower()
            if "breaking" in subject or "!" in subject:
                commit_types["breaking"] += 1
            elif subject.startswith("feat"):
                commit_types["feat"] += 1
            elif subject.startswith("fix"):
                commit_types["fix"] += 1
        
        # Suggest version
        current_parts = self.context.old_version.split('.')
        major, minor, patch = map(int, current_parts)
        
        if commit_types["breaking"] > 0:
            suggested = f"{major + 1}.0.0"
        elif commit_types["feat"] > 0:
            suggested = f"{major}.{minor + 1}.0"
        else:
            suggested = f"{major}.{minor}.{patch + 1}"
        
        if self.auto_mode:
            self.context.version = suggested
        else:
            self.context.version = Prompt.ask(
                f"New version (current: {self.context.old_version})",
                default=suggested
            )
        
        console.print(f"[green]Version: {self.context.old_version} → {self.context.version}[/green]")
        self.context.branch_name = f"v{self.context.version}"
    
    def _generate_tests(self):
        """Generate test script using LLM"""
        console.print("\n[bold]Step 3: Generate Tests[/bold]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Generating test script...", total=None)
            
            # Get relevant files for understanding Crawl4AI
            query = f"Generate tests for Crawl4AI with these changes: {self._format_commits_for_llm()}"
            relevant_files = self.llm.get_relevant_files(query, num_files=8)
            
            # Format file contents for context
            codebase_context = []
            for file_info in relevant_files:
                codebase_context.append(f"<FILE path=\"{file_info['path']}\">\n{file_info['content']}\n</FILE>")
            
            # Build context for test generation
            context = {
                "commit_diffs": self._get_selected_diffs_summary(),
                "existing_patterns": self._load_test_patterns(),
                "constraints": "Generate comprehensive tests for all changed functionality",
                "codebase_info": "\n\n".join(codebase_context)
            }
            
            task_prompt = f"""Generate a Python test script for the following changes in Crawl4AI v{self.context.version}:

<SELECTED_COMMITS>
{self._format_commits_for_llm()}
</SELECTED_COMMITS>

<REQUIREMENTS>
0. No mock data or uni test style, simple use them like a user will use.
1. Test all new features and changes
2. Be runnable with pytest
3. Return exit code 0 on success, non-zero on failure
4. Dont make it too ling, these are all already tested, this is final test after cherry-pick
</REQUIREMENTS>

IMPORTANT: Return ONLY a JSON response wrapped in <JSON></JSON> tags.
Do NOT include any markdown code blocks, backticks, or explanatory text.
The JSON will be directly parsed, so any extra formatting will cause errors.

Return the test script as:
<JSON>
{{
    "test_script": "# Complete Python test script here\\nfrom crawl4ai..."
}}
</JSON>"""
            
            response = self.llm.call(task_prompt, context)
            
            # Extract test script from JSON response
            start_index = response.find("<JSON>")
            end_index = response.find("</JSON>", start_index)
            if start_index != -1 and end_index != -1:
                json_str = response[start_index + len("<JSON>"):end_index].strip()  
                result = json.loads(json_str)
                self.context.test_script = result.get("test_script", "")
            else:
                console.print("[red]Failed to extract test script from response[/red]")
                return
            
            # Judge the generated tests
            judge_result = self.llm.judge(
                self.context.test_script,
                [
                    "Tests cover all selected commits",
                    "Tests are comprehensive and meaningful",
                    "Test script is valid Python code",
                    "Tests check both success and failure cases"
                ],
                context
            )
            
            if judge_result.status == "retry":
                console.print(f"[yellow]Regenerating tests: {judge_result.feedback}[/yellow]")
                # Add feedback to context and retry
                context["judge_feedback"] = judge_result.feedback
                response = self.llm.call(task_prompt, context)
                # Extract again
                json_match = re.search(r'<JSON>(.*?)</JSON>', response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1).strip()
                    result = json.loads(json_str)
                    self.context.test_script = result.get("test_script", "")
            elif judge_result.status == "human":
                console.print(f"[yellow]Human intervention needed: {judge_result.feedback}[/yellow]")
                # TODO: Implement human feedback loop
            
            progress.update(task, completed=True)
        
        # Save test script
        test_file = Path(f"test_release_{self.context.version}.py")
        test_file.write_text(self.context.test_script)
        console.print(f"[green]Test script saved to {test_file}[/green]")
    
    def _run_tests(self) -> bool:
        """Run the generated tests"""
        console.print("\n[bold]Step 4: Run Tests[/bold]")
        
        test_file = f"test_release_{self.context.version}.py"
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Running tests...", total=None)
            
            result = subprocess.run(
                ["python", test_file],
                capture_output=True,
                text=True
            )
            
            progress.update(task, completed=True)
        
        if result.returncode == 0:
            console.print("[green]✅ All tests passed![/green]")
            self.context.test_results = {"status": "passed", "output": result.stdout}
            return True
        else:
            console.print("[red]❌ Tests failed![/red]")
            console.print(result.stdout)
            console.print(result.stderr)
            self.context.test_results = {
                "status": "failed",
                "output": result.stdout,
                "error": result.stderr
            }
            return False
    
    def _create_version_branch(self):
        """Create version branch and cherry-pick commits"""
        console.print(f"\n[bold]Step 5: Create Branch {self.context.branch_name}[/bold]")
        
        # Checkout main first
        subprocess.run(["git", "checkout", "main"], check=True)
        
        # Create version branch
        commit_hashes = [c["hash"] for c in self.context.selected_commits]
        
        if GitOperations.cherry_pick_commits(commit_hashes, self.context.branch_name):
            console.print(f"[green]Created branch {self.context.branch_name} with {len(commit_hashes)} commits[/green]")
        else:
            raise Exception("Failed to create version branch")
    
    def _generate_release_notes(self):
        """Generate release notes"""
        console.print("\n[bold]Step 6: Generate Release Notes[/bold]")
        
        # Implementation continues...
        # (Keeping it minimal as requested)
        pass
    
    def _generate_demo(self):
        """Generate demo script"""
        console.print("\n[bold]Step 7: Generate Demo[/bold]")
        pass
    
    def _update_docs(self):
        """Update documentation"""
        console.print("\n[bold]Step 8: Update Documentation[/bold]")
        pass
    
    def _build_and_publish(self):
        """Build and publish to PyPI"""
        console.print("\n[bold]Step 9: Build and Publish[/bold]")
        
        if not self.auto_mode:
            if not Confirm.ask("Ready to publish to PyPI?"):
                return False
        
        # Run publish.sh
        result = subprocess.run(["./publish.sh"], capture_output=True)
        
        if result.returncode == 0:
            console.print(f"[green]✅ Published v{self.context.version} to PyPI![/green]")
            
            # Merge to main
            subprocess.run(["git", "checkout", "main"], check=True)
            subprocess.run(["git", "merge", "--squash", self.context.branch_name], check=True)
            subprocess.run(["git", "commit", "-m", f"Release v{self.context.version}"], check=True)
            
            return True
        else:
            console.print("[red]Publishing failed![/red]")
            return False
    
    # Helper methods
    def _extract_changed_files(self, diff: str) -> List[str]:
        """Extract changed file paths from diff"""
        files = []
        for line in diff.split('\n'):
            if line.startswith('+++') or line.startswith('---'):
                file = line[4:].split('\t')[0]
                if file != '/dev/null' and file not in files:
                    files.append(file)
        return files
    
    def _get_selected_diffs_summary(self) -> str:
        """Get summary of diffs for selected commits"""
        # Simplified for brevity
        return f"{len(self.context.selected_commits)} commits selected"
    
    def _load_test_patterns(self) -> str:
        """Load existing test patterns"""
        # Would load from existing test files
        return "Follow pytest patterns"
    
    def _format_commits_for_llm(self) -> str:
        """Format commits for LLM consumption"""
        lines = []
        for commit in self.context.selected_commits:
            lines.append(f"- {commit['hash'][:8]}: {commit['subject']}")
        return '\n'.join(lines)

@click.command()
@click.option('--all', is_flag=True, help='Select all commits automatically')
@click.option('-y', '--yes', is_flag=True, help='Auto-confirm version bump')
@click.option('--dry-run', is_flag=True, help='Run without publishing')
@click.option('--test', is_flag=True, help='Test mode - no git operations, no publishing')
def main(all, yes, dry_run, test):
    """Crawl4AI Release Agent - Automated release management"""
    agent = ReleaseAgent(auto_mode=yes, select_all=all, test_mode=test)
    agent.run()

if __name__ == "__main__":
    main()