"""
Unit tests for specific import verification.

These tests verify that the import fixes for the Lambda function are correct
and that all required modules can be imported without errors.

Feature: fix-tax-document-lambda-imports
**Validates: Requirements 1.3, 1.4**
"""

import pytest
import ast
import os


class TestImportVerification:
    """Unit tests for verifying import correctness."""
    
    def test_document_generator_can_be_imported(self):
        """
        **Validates: Requirements 1.3**
        
        Test that document_generator.py can be imported without errors.
        
        This test verifies that:
        1. The document_generator module can be imported successfully
        2. No ImportError is raised during import
        3. The module is properly initialized
        """
        # Import the module - should not raise ImportError
        from tax_document_generation import document_generator
        
        # Verify the module is imported
        assert document_generator is not None, \
            "document_generator module should be imported successfully"
        
        # Verify the generate_document function exists
        assert hasattr(document_generator, 'generate_document'), \
            "document_generator should have generate_document function"
    
    def test_generation_error_can_be_imported(self):
        """
        **Validates: Requirements 1.3**
        
        Test that GenerationError can be imported from exceptions module.
        
        This test verifies that:
        1. GenerationError can be imported from the exceptions module
        2. No ImportError is raised during import
        3. GenerationError is a proper exception class
        """
        # Import GenerationError - should not raise ImportError
        from tax_document_generation.exceptions import GenerationError
        
        # Verify the exception class is imported
        assert GenerationError is not None, \
            "GenerationError should be imported successfully"
        
        # Verify it's an exception class
        assert issubclass(GenerationError, Exception), \
            "GenerationError should be a subclass of Exception"
        
        # Verify it can be raised
        with pytest.raises(GenerationError):
            raise GenerationError("Test error")
    
    def test_field_mapper_can_be_imported(self):
        """
        **Validates: Requirements 1.4**
        
        Test that FieldMapper can be imported from field_mapper module.
        
        This test verifies that:
        1. FieldMapper can be imported from the field_mapper module
        2. No ImportError is raised during import
        3. FieldMapper is a proper class
        """
        # Import FieldMapper - should not raise ImportError
        from tax_document_generation.field_mapper import FieldMapper
        
        # Verify the class is imported
        assert FieldMapper is not None, \
            "FieldMapper should be imported successfully"
        
        # Verify it's a class
        assert isinstance(FieldMapper, type), \
            "FieldMapper should be a class"
        
        # Verify it can be instantiated
        mapper = FieldMapper("1099-DIV")
        assert mapper is not None, \
            "FieldMapper should be instantiable"
    
    def test_document_generator_has_no_relative_imports(self):
        """
        **Validates: Requirements 1.4**
        
        Test that document_generator module has no relative imports in its source.
        
        This test verifies that:
        1. The document_generator.py source code contains no relative imports
        2. All imports use absolute import syntax
        3. No "from ." import statements exist
        """
        # Get the path to document_generator.py
        import tax_document_generation
        module_dir = os.path.dirname(tax_document_generation.__file__)
        doc_gen_path = os.path.join(module_dir, 'document_generator.py')
        
        # Read the source code
        with open(doc_gen_path, 'r') as f:
            source_code = f.read()
        
        # Parse the source code into an AST
        tree = ast.parse(source_code)
        
        # Find all import statements
        relative_imports = []
        
        for node in ast.walk(tree):
            # Check for "from ... import ..." statements
            if isinstance(node, ast.ImportFrom):
                # node.level > 0 indicates a relative import
                # node.level == 1 means "from .module import ..."
                # node.level == 2 means "from ..module import ..."
                if node.level > 0:
                    module_name = node.module or "(current package)"
                    relative_imports.append(f"from {'.' * node.level}{module_name} import ...")
        
        # Verify no relative imports exist
        assert len(relative_imports) == 0, \
            f"document_generator.py should have no relative imports, found: {relative_imports}"
    
    def test_document_generator_imports_exceptions_absolutely(self):
        """
        **Validates: Requirements 1.3**
        
        Test that document_generator imports from exceptions using absolute import.
        
        This test verifies that:
        1. The import statement uses "from exceptions import ..."
        2. The import statement does NOT use "from .exceptions import ..."
        3. The absolute import pattern is followed
        """
        # Get the path to document_generator.py
        import tax_document_generation
        module_dir = os.path.dirname(tax_document_generation.__file__)
        doc_gen_path = os.path.join(module_dir, 'document_generator.py')
        
        # Read the source code
        with open(doc_gen_path, 'r') as f:
            source_code = f.read()
        
        # Parse the source code into an AST
        tree = ast.parse(source_code)
        
        # Find the exceptions import
        found_absolute_import = False
        found_relative_import = False
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module == 'exceptions' and node.level == 0:
                    # Absolute import: "from exceptions import ..."
                    found_absolute_import = True
                elif node.module == 'exceptions' and node.level > 0:
                    # Relative import: "from .exceptions import ..."
                    found_relative_import = True
        
        # Verify absolute import exists and relative import does not
        assert found_absolute_import, \
            "document_generator.py should import from exceptions using absolute import"
        
        assert not found_relative_import, \
            "document_generator.py should NOT import from .exceptions using relative import"
    
    def test_document_generator_imports_field_mapper_absolutely(self):
        """
        **Validates: Requirements 1.4**
        
        Test that document_generator imports from field_mapper using absolute import.
        
        This test verifies that:
        1. The import statement uses "from field_mapper import ..."
        2. The import statement does NOT use "from .field_mapper import ..."
        3. The absolute import pattern is followed
        """
        # Get the path to document_generator.py
        import tax_document_generation
        module_dir = os.path.dirname(tax_document_generation.__file__)
        doc_gen_path = os.path.join(module_dir, 'document_generator.py')
        
        # Read the source code
        with open(doc_gen_path, 'r') as f:
            source_code = f.read()
        
        # Parse the source code into an AST
        tree = ast.parse(source_code)
        
        # Find the field_mapper import
        found_absolute_import = False
        found_relative_import = False
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module == 'field_mapper' and node.level == 0:
                    # Absolute import: "from field_mapper import ..."
                    found_absolute_import = True
                elif node.module == 'field_mapper' and node.level > 0:
                    # Relative import: "from .field_mapper import ..."
                    found_relative_import = True
        
        # Verify absolute import exists and relative import does not
        assert found_absolute_import, \
            "document_generator.py should import from field_mapper using absolute import"
        
        assert not found_relative_import, \
            "document_generator.py should NOT import from .field_mapper using relative import"
    
    def test_all_required_imports_work_together(self):
        """
        **Validates: Requirements 1.3, 1.4**
        
        Test that all required imports work together without conflicts.
        
        This test verifies that:
        1. document_generator, exceptions, and field_mapper can all be imported
        2. No import conflicts exist
        3. All modules are properly initialized
        """
        # Import all required modules
        from tax_document_generation import document_generator
        from tax_document_generation.exceptions import GenerationError
        from tax_document_generation.field_mapper import FieldMapper
        
        # Verify all imports succeeded
        assert document_generator is not None
        assert GenerationError is not None
        assert FieldMapper is not None
        
        # Verify they can be used together
        mapper = FieldMapper("1099-DIV")
        assert mapper is not None
        
        # Verify GenerationError can be raised
        with pytest.raises(GenerationError):
            raise GenerationError("Test error")
        
        # Verify generate_document function exists
        assert hasattr(document_generator, 'generate_document')
