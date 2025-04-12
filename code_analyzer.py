import os
import sys
from typing import List, Dict
import pylint.lint
from flake8.api import legacy as flake8
import black
import isort
# Add new imports for JS/TS linting
import subprocess
import json

class ProjectAnalyzer:
    def __init__(self, project_path: str):
        self.project_path = project_path
        self.python_files = []
        self.js_ts_files = []  # New list for JS/TS files
        self.results = {
            'pylint': [],
            'flake8': [],
            'formatting': [],
            'eslint': [],  # New result category for ESLint
            'prettier': []  # New result category for Prettier
        }

    def find_files(self) -> None:
        """Recursively find all Python, JavaScript, and TypeScript files in the project directory."""
        for root, _, files in os.walk(self.project_path):
            for file in files:
                if file.endswith('.py'):
                    self.python_files.append(os.path.join(root, file))
                elif file.endswith(('.js', '.jsx', '.ts', '.tsx')):
                    self.js_ts_files.append(os.path.join(root, file))

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

    def run_eslint(self) -> None:
        """Run ESLint on JavaScript and TypeScript files."""
        if not self.js_ts_files:
            return

        try:
            # Check if ESLint is installed
            result = subprocess.run(['npx', 'eslint', '--version'], 
                                 capture_output=True, text=True)
            if result.returncode != 0:
                self.results['eslint'].append("Error: ESLint is not installed. Please install it using 'npm install eslint'")
                return

            # Run ESLint
            for file_path in self.js_ts_files:
                result = subprocess.run(
                    ['npx', 'eslint', '--format=json', file_path],
                    capture_output=True,
                    text=True
                )
                
                if result.stdout:
                    issues = json.loads(result.stdout)
                    if issues:
                        self.results['eslint'].append({
                            'file': file_path,
                            'issues': issues
                        })
        except Exception as e:
            self.results['eslint'].append(f"Error running ESLint: {str(e)}")

    def check_prettier(self) -> None:
        """Check formatting using Prettier for JS/TS files."""
        if not self.js_ts_files:
            return

        try:
            # Check if npx/prettier is installed
            try:
                result = subprocess.run(['npx', 'prettier', '--version'],
                                     capture_output=True, text=True)
                if result.returncode != 0:
                    self.results['prettier'].append("Error: Prettier is not installed. Please install it using 'npm install prettier'")
                    return
            except FileNotFoundError:
                self.results['prettier'].append("Error: npx not found. Please ensure Node.js and npm are installed and in your PATH")
                return

            # Check files only if prettier is available
            for file_path in self.js_ts_files:
                try:
                    result = subprocess.run(
                        ['npx', 'prettier', '--check', file_path],
                        capture_output=True,
                        text=True
                    )
                    
                    if result.returncode != 0:
                        self.results['prettier'].append({
                            'file': file_path,
                            'error': 'File is not properly formatted'
                        })
                except Exception as e:
                    self.results['prettier'].append({
                        'file': file_path,
                        'error': f"Error checking file: {str(e)}"
                    })
        except Exception as e:
            self.results['prettier'].append(f"Error running Prettier: {str(e)}")

    def analyze(self) -> Dict:
        """Run all analysis tools and return results."""
        print("Starting project analysis...")
        
        self.find_files()  # Updated method name
        
        if not self.python_files and not self.js_ts_files:
            return {"error": "No Python or JavaScript/TypeScript files found in the project"}

        print(f"Found {len(self.python_files)} Python files and {len(self.js_ts_files)} JavaScript/TypeScript files")
        
        if self.python_files:
            print("Running Pylint...")
            self.run_pylint()
            
            print("Running Flake8...")
            self.run_flake8()
            
            print("Checking Python code formatting...")
            self.check_formatting()
        
        if self.js_ts_files:
            print("Running ESLint...")
            self.run_eslint()
            
            print("Checking JS/TS formatting with Prettier...")
            self.check_prettier()
        
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
