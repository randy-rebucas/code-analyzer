import os
import sys
from typing import List, Dict
import pylint.lint
from flake8.api import legacy as flake8
import black
import isort

class ProjectAnalyzer:
    def __init__(self, project_path: str):
        self.project_path = project_path
        self.python_files = []
        self.results = {
            'pylint': [],
            'flake8': [],
            'formatting': []
        }

    def find_python_files(self) -> None:
        """Recursively find all Python files in the project directory."""
        for root, _, files in os.walk(self.project_path):
            for file in files:
                if file.endswith('.py'):
                    self.python_files.append(os.path.join(root, file))

    def run_pylint(self) -> None:
        """Run Pylint on the project files."""
        try:
            pylint_opts = ['--output-format=json']
            pylint.lint.Run(self.python_files + pylint_opts, exit=False)
        except Exception as e:
            self.results['pylint'].append(f"Error running Pylint: {str(e)}")

    def run_flake8(self) -> None:
        """Run Flake8 on the project files."""
        style_guide = flake8.get_style_guide()
        for file_path in self.python_files:
            try:
                report = style_guide.check_files([file_path])
                if report.get_statistics('E'):
                    self.results['flake8'].append({
                        'file': file_path,
                        'errors': report.get_statistics('E')
                    })
            except Exception as e:
                self.results['flake8'].append(f"Error checking {file_path}: {str(e)}")

    def check_formatting(self) -> None:
        """Check code formatting using Black and isort."""
        for file_path in self.python_files:
            try:
                # Check Black formatting
                with open(file_path, 'r') as f:
                    content = f.read()
                try:
                    black.format_file_contents(content, fast=True, mode=black.FileMode())
                except black.NothingChanged:
                    pass
                except Exception as e:
                    self.results['formatting'].append({
                        'file': file_path,
                        'tool': 'black',
                        'error': str(e)
                    })

                # Check import sorting
                if not isort.check_file(file_path):
                    self.results['formatting'].append({
                        'file': file_path,
                        'tool': 'isort',
                        'error': 'Imports are not properly sorted'
                    })
            except Exception as e:
                self.results['formatting'].append(f"Error checking {file_path}: {str(e)}")

    def analyze(self) -> Dict:
        """Run all analysis tools and return results."""
        print("Starting project analysis...")
        
        self.find_python_files()
        if not self.python_files:
            return {"error": "No Python files found in the project"}

        print(f"Found {len(self.python_files)} Python files")
        
        print("Running Pylint...")
        self.run_pylint()
        
        print("Running Flake8...")
        self.run_flake8()
        
        print("Checking code formatting...")
        self.check_formatting()
        
        return self.results

def main():
    if len(sys.argv) != 2:
        print("Usage: python code_analyzer.py <project_path>")
        sys.exit(1)

    project_path = sys.argv[1]
    if not os.path.exists(project_path):
        print(f"Error: Path '{project_path}' does not exist")
        sys.exit(1)

    analyzer = ProjectAnalyzer(project_path)
    results = analyzer.analyze()

    # Print results in a formatted way
    print("\nAnalysis Results:")
    print("================")
    
    for tool, issues in results.items():
        print(f"\n{tool.upper()} Results:")
        if not issues:
            print("No issues found")
        else:
            for issue in issues:
                print(f"- {issue}")

if __name__ == "__main__":
    main()
