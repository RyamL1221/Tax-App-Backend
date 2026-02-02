"""
Property-based test for import declaration completeness.

This test verifies that for any Python module in the password_recovery/ directory
that imports an external package (not in Python standard library), that package
is declared in requirements.txt.
"""

import os
import ast
import sys
import pytest


class TestImportDeclarationCompletenessProperty:
    """Property-based test for import declaration completeness."""
    
    def test_import_declaration_completeness(self):
        """
        **Validates: Requirements 2.4**
        Feature: fix-password-recovery-dependencies, Property 2: Import Declaration Completeness
        
        For any Python module in the password_recovery/ directory that imports
        an external package (not in Python standard library), that package
        SHALL be declared in requirements.txt.
        
        This ensures all runtime dependencies are explicitly declared so SAM build
        packages them. Missing declarations cause import errors at runtime.
        """
        # Get the path to password_recovery directory
        test_dir = os.path.dirname(os.path.abspath(__file__))
        password_recovery_dir = os.path.dirname(test_dir)
        requirements_path = os.path.join(password_recovery_dir, 'requirements.txt')
        
        # Read requirements.txt and extract package names
        with open(requirements_path, 'r') as f:
            requirements_content = f.read()
        
        declared_packages = set()
        for line in requirements_content.split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                # Extract package name (before >= or other operators)
                if '>=' in line:
                    package_name = line.split('>=')[0].strip()
                elif '==' in line:
                    package_name = line.split('==')[0].strip()
                elif '<=' in line:
                    package_name = line.split('<=')[0].strip()
                elif '>' in line:
                    package_name = line.split('>')[0].strip()
                elif '<' in line:
                    package_name = line.split('<')[0].strip()
                else:
                    package_name = line.strip()
                
                declared_packages.add(package_name.lower())
        
        # Get all Python files in password_recovery directory (excluding tests)
        python_files = []
        local_modules = set()  # Track local module names
        for filename in os.listdir(password_recovery_dir):
            if filename.endswith('.py') and filename != '__init__.py':
                python_files.append(os.path.join(password_recovery_dir, filename))
                # Add the module name (without .py) to local modules
                module_name = filename[:-3]  # Remove .py extension
                local_modules.add(module_name.lower())
        
        # Python standard library modules (common ones that might be imported)
        # This is a comprehensive list of stdlib modules for Python 3.9+
        stdlib_modules = {
            'abc', 'aifc', 'argparse', 'array', 'ast', 'asynchat', 'asyncio', 'asyncore',
            'atexit', 'audioop', 'base64', 'bdb', 'binascii', 'binhex', 'bisect', 'builtins',
            'bz2', 'calendar', 'cgi', 'cgitb', 'chunk', 'cmath', 'cmd', 'code', 'codecs',
            'codeop', 'collections', 'colorsys', 'compileall', 'concurrent', 'configparser',
            'contextlib', 'contextvars', 'copy', 'copyreg', 'cProfile', 'crypt', 'csv',
            'ctypes', 'curses', 'dataclasses', 'datetime', 'dbm', 'decimal', 'difflib',
            'dis', 'distutils', 'doctest', 'email', 'encodings', 'enum', 'errno', 'faulthandler',
            'fcntl', 'filecmp', 'fileinput', 'fnmatch', 'formatter', 'fractions', 'ftplib',
            'functools', 'gc', 'getopt', 'getpass', 'gettext', 'glob', 'graphlib', 'grp',
            'gzip', 'hashlib', 'heapq', 'hmac', 'html', 'http', 'imaplib', 'imghdr', 'imp',
            'importlib', 'inspect', 'io', 'ipaddress', 'itertools', 'json', 'keyword',
            'lib2to3', 'linecache', 'locale', 'logging', 'lzma', 'mailbox', 'mailcap',
            'marshal', 'math', 'mimetypes', 'mmap', 'modulefinder', 'msilib', 'msvcrt',
            'multiprocessing', 'netrc', 'nis', 'nntplib', 'numbers', 'operator', 'optparse',
            'os', 'ossaudiodev', 'parser', 'pathlib', 'pdb', 'pickle', 'pickletools', 'pipes',
            'pkgutil', 'platform', 'plistlib', 'poplib', 'posix', 'posixpath', 'pprint',
            'profile', 'pstats', 'pty', 'pwd', 'py_compile', 'pyclbr', 'pydoc', 'queue',
            'quopri', 'random', 're', 'readline', 'reprlib', 'resource', 'rlcompleter',
            'runpy', 'sched', 'secrets', 'select', 'selectors', 'shelve', 'shlex', 'shutil',
            'signal', 'site', 'smtpd', 'smtplib', 'sndhdr', 'socket', 'socketserver', 'spwd',
            'sqlite3', 'ssl', 'stat', 'statistics', 'string', 'stringprep', 'struct',
            'subprocess', 'sunau', 'symbol', 'symtable', 'sys', 'sysconfig', 'syslog',
            'tabnanny', 'tarfile', 'telnetlib', 'tempfile', 'termios', 'test', 'textwrap',
            'threading', 'time', 'timeit', 'tkinter', 'token', 'tokenize', 'trace', 'traceback',
            'tracemalloc', 'tty', 'turtle', 'turtledemo', 'types', 'typing', 'unicodedata',
            'unittest', 'urllib', 'uu', 'uuid', 'venv', 'warnings', 'wave', 'weakref',
            'webbrowser', 'winreg', 'winsound', 'wsgiref', 'xdrlib', 'xml', 'xmlrpc',
            'zipapp', 'zipfile', 'zipimport', 'zlib', '_thread'
        }
        
        # Also add botocore as it's a dependency of boto3 (transitive)
        # We don't need to declare transitive dependencies in requirements.txt
        transitive_dependencies = {'botocore'}
        
        # Collect all external imports from all Python files
        external_imports = set()
        
        for python_file in python_files:
            with open(python_file, 'r') as f:
                try:
                    tree = ast.parse(f.read(), filename=python_file)
                except SyntaxError as e:
                    pytest.fail(f"Syntax error in {python_file}: {e}")
                    continue
            
            # Extract all import statements
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    # import module
                    for alias in node.names:
                        module_name = alias.name.split('.')[0]  # Get top-level module
                        if (module_name not in stdlib_modules and 
                            module_name not in transitive_dependencies and
                            module_name.lower() not in local_modules):
                            external_imports.add(module_name.lower())
                
                elif isinstance(node, ast.ImportFrom):
                    # from module import something
                    if node.module:
                        module_name = node.module.split('.')[0]  # Get top-level module
                        if (module_name not in stdlib_modules and 
                            module_name not in transitive_dependencies and
                            module_name.lower() not in local_modules):
                            external_imports.add(module_name.lower())
        
        # Property: For ANY external import, it must be declared in requirements.txt
        missing_packages = external_imports - declared_packages
        
        # Provide detailed error message if packages are missing
        assert len(missing_packages) == 0, \
            f"External packages imported but not declared in requirements.txt: {missing_packages}. " \
            f"All external dependencies must be declared in requirements.txt so SAM build " \
            f"can package them with the Lambda functions. Without these declarations, " \
            f"Lambda functions will fail at runtime with import errors. " \
            f"\nDeclared packages: {declared_packages} " \
            f"\nExternal imports found: {external_imports} " \
            f"\nMissing packages: {missing_packages}"
        
        # Additional check: Verify we found at least some external imports
        # (sanity check that our parsing is working)
        assert len(external_imports) > 0, \
            "No external imports found in password_recovery Python files. " \
            "This is unexpected - the code should import at least boto3 and bcrypt. " \
            "Check that the import parsing logic is working correctly."
        
        # Note: requirements.txt may contain more packages than are currently imported
        # (e.g., email-validator, PyJWT for future use or consistency with other Lambda functions)
        # This is acceptable - the property only requires that all imports are declared,
        # not that all declarations are used.
        
        # Log success for visibility
        print(f"\n✓ Import declaration completeness verified:")
        print(f"  - Found {len(external_imports)} external imports: {sorted(external_imports)}")
        print(f"  - All are declared in requirements.txt: {sorted(declared_packages)}")
        print(f"  - Note: requirements.txt may contain additional packages for consistency or future use")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
