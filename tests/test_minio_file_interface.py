import unittest
from unittest.mock import Mock, patch, MagicMock
import os
import tempfile
import shutil
from pathlib import Path

from src.minio_file_interface import MinIOFileInterface


class TestMinIOFileInterface(unittest.TestCase):
    """Test cases for MinIOFileInterface class"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_minio_client = Mock()
        self.interface = MinIOFileInterface(minio_client=self.mock_minio_client)
        self.temp_dir = tempfile.mkdtemp()
        self.original_temp_dir = tempfile.gettempdir()

    def tearDown(self):
        """Clean up test fixtures"""
        # Clean up temp directory
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_init_basic(self):
        """Test basic initialization"""
        interface = MinIOFileInterface()
        self.assertIsNone(interface.minio_client)
        self.assertEqual(interface.temp_dir, tempfile.gettempdir())
        self.assertEqual(interface.temp_files, [])

    def test_init_with_minio_client(self):
        """Test initialization with MinIO client"""
        interface = MinIOFileInterface(minio_client=self.mock_minio_client)
        self.assertEqual(interface.minio_client, self.mock_minio_client)

    def test_init_with_custom_temp_dir(self):
        """Test initialization with custom temp directory"""
        interface = MinIOFileInterface(temp_dir=self.temp_dir)
        self.assertEqual(interface.temp_dir, self.temp_dir)

    def test_init_creates_temp_dir(self):
        """Test that initialization creates temp directory if it doesn't exist"""
        non_existent_dir = os.path.join(self.temp_dir, 'non_existent')
        
        interface = MinIOFileInterface(temp_dir=non_existent_dir)
        
        self.assertTrue(os.path.exists(non_existent_dir))
        self.assertEqual(interface.temp_dir, non_existent_dir)

    def test_get_file_from_minio_success(self):
        """Test successful file retrieval from MinIO"""
        self.mock_minio_client.download_file.return_value = True
        
        result = self.interface.get_file_from_minio('test_object.pdf')
        
        self.assertTrue(result.endswith('test_object.pdf'))
        self.mock_minio_client.download_file.assert_called_once()
        
        # Check that temp file was registered
        self.assertEqual(len(self.interface.temp_files), 1)
        self.assertTrue(result in self.interface.temp_files)

    def test_get_file_from_minio_with_custom_name(self):
        """Test file retrieval with custom local path"""
        custom_path = os.path.join(self.temp_dir, 'custom_name.pdf')
        
        self.mock_minio_client.download_file.return_value = True
        
        result = self.interface.get_file_from_minio('test_object.pdf', custom_path)
        
        self.assertEqual(result, custom_path)
        self.mock_minio_client.download_file.assert_called_once_with(
            'test_object.pdf', custom_path
        )

    def test_get_file_from_minio_no_minio_client(self):
        """Test file retrieval without MinIO client"""
        interface = MinIOFileInterface(minio_client=None)
        
        with self.assertRaises(ValueError) as context:
            interface.get_file_from_minio('test_object.pdf')
        
        self.assertIn('MinIO client not configured', str(context.exception))

    def test_get_file_from_minio_download_failure(self):
        """Test file retrieval when download fails"""
        self.mock_minio_client.download_file.return_value = False
        
        result = self.interface.get_file_from_minio('test_object.pdf')
        
        self.assertIsNone(result)
        self.assertEqual(len(self.interface.temp_files), 0)

    def test_get_temp_file_path_basic(self):
        """Test temp file path generation"""
        result = self.interface.get_temp_file_path('test_object.pdf')
        
        self.assertTrue(result.endswith('test_object.pdf'))
        self.assertTrue(os.path.dirname(result).endswith('thesis_translator_temp'))

    def test_get_temp_file_path_with_custom_extension(self):
        """Test temp file path generation with custom extension"""
        result = self.interface.get_temp_file_path('test_object.pdf', '.tmp')
        
        self.assertTrue(result.endswith('.tmp'))

    def test_get_temp_file_path_no_extension(self):
        """Test temp file path generation for files without extension"""
        result = self.interface.get_temp_file_path('test_object')
        
        self.assertTrue(result.endswith('.pdf'))  # Default extension

    def test_get_temp_file_path_creates_directory(self):
        """Test that temp file path creation creates directory"""
        custom_temp_dir = os.path.join(self.temp_dir, 'custom_temp')
        interface = MinIOFileInterface(temp_dir=custom_temp_dir)
        
        result = interface.get_temp_file_path('test_object.pdf')
        
        self.assertTrue(os.path.exists(custom_temp_dir))
        self.assertTrue(result.startswith(custom_temp_dir))

    def test_cleanup_temp_files(self):
        """Test cleanup of temporary files"""
        # Create some temp files
        temp_file1 = os.path.join(self.temp_dir, 'temp1.pdf')
        temp_file2 = os.path.join(self.temp_dir, 'temp2.pdf')
        
        # Create files
        with open(temp_file1, 'w') as f:
            f.write('test content 1')
        with open(temp_file2, 'w') as f:
            f.write('test content 2')
        
        # Register files with interface
        interface = MinIOFileInterface(temp_dir=self.temp_dir)
        interface.temp_files = [temp_file1, temp_file2]
        
        # Ensure files exist
        self.assertTrue(os.path.exists(temp_file1))
        self.assertTrue(os.path.exists(temp_file2))
        
        # Cleanup
        interface.cleanup_temp_files()
        
        # Check files are deleted
        self.assertFalse(os.path.exists(temp_file1))
        self.assertFalse(os.path.exists(temp_file2))
        self.assertEqual(len(interface.temp_files), 0)

    def test_cleanup_temp_files_nonexistent(self):
        """Test cleanup of nonexistent temp files"""
        nonexistent_file = os.path.join(self.temp_dir, 'nonexistent.pdf')
        
        interface = MinIOFileInterface(temp_dir=self.temp_dir)
        interface.temp_files = [nonexistent_file]
        
        # Should not raise exception
        interface.cleanup_temp_files()
        
        self.assertEqual(len(interface.temp_files), 0)

    def test_cleanup_temp_files_directory(self):
        """Test cleanup when temp file is a directory"""
        temp_dir = os.path.join(self.temp_dir, 'temp_dir')
        os.makedirs(temp_dir)
        
        interface = MinIOFileInterface(temp_dir=self.temp_dir)
        interface.temp_files = [temp_dir]
        
        # Should not raise exception
        interface.cleanup_temp_files()
        
        # Directory should still exist (rmtree should handle it)
        self.assertEqual(len(interface.temp_files), 0)

    def test_process_pdf_from_minio_success(self):
        """Test successful PDF processing from MinIO"""
        # Mock dependencies
        mock_translator = Mock()
        mock_translator.translate_pdf.return_value = True
        
        # Create test PDF file
        test_pdf_path = os.path.join(self.temp_dir, 'test.pdf')
        with open(test_pdf_path, 'w') as f:
            f.write('test pdf content')
        
        # Mock MinIO download
        self.mock_minio_client.download_file.return_value = True
        
        # Mock temp file creation
        with patch.object(self.interface, 'get_temp_file_path') as mock_temp_path:
            mock_temp_path.return_value = test_pdf_path
            
            result = self.interface.process_pdf_from_minio(
                'test_object.pdf', 
                'output.md', 
                mock_translator
            )
            
            self.assertTrue(result)
            self.mock_minio_client.download_file.assert_called_once()
            mock_translator.translate_pdf.assert_called_once_with(test_pdf_path, 'output.md')
            self.assertEqual(len(self.interface.temp_files), 1)

    def test_process_pdf_from_minio_download_failure(self):
        """Test PDF processing when MinIO download fails"""
        mock_translator = Mock()
        
        self.mock_minio_client.download_file.return_value = False
        
        result = self.interface.process_pdf_from_minio(
            'test_object.pdf', 
            'output.md', 
            mock_translator
        )
        
        self.assertFalse(result)
        mock_translator.translate_pdf.assert_not_called()

    def test_process_pdf_from_minio_no_minio_client(self):
        """Test PDF processing without MinIO client"""
        interface = MinIOFileInterface(minio_client=None)
        mock_translator = Mock()
        
        with self.assertRaises(ValueError) as context:
            interface.process_pdf_from_minio(
                'test_object.pdf', 
                'output.md', 
                mock_translator
            )
        
        self.assertIn('MinIO client not configured', str(context.exception))

    def test_process_pdf_from_minio_translation_failure(self):
        """Test PDF processing when translation fails"""
        mock_translator = Mock()
        mock_translator.translate_pdf.return_value = False
        
        # Create test PDF file
        test_pdf_path = os.path.join(self.temp_dir, 'test.pdf')
        with open(test_pdf_path, 'w') as f:
            f.write('test pdf content')
        
        self.mock_minio_client.download_file.return_value = True
        
        with patch.object(self.interface, 'get_temp_file_path') as mock_temp_path:
            mock_temp_path.return_value = test_pdf_path
            
            result = self.interface.process_pdf_from_minio(
                'test_object.pdf', 
                'output.md', 
                mock_translator
            )
            
            self.assertFalse(result)
            self.mock_minio_client.download_file.assert_called_once()
            mock_translator.translate_pdf.assert_called_once()

    def test_context_manager_usage(self):
        """Test using interface as context manager"""
        with patch.object(self.interface, 'cleanup_temp_files') as mock_cleanup:
            with self.interface:
                pass
            
            mock_cleanup.assert_called_once()

    def test_generate_safe_filename(self):
        """Test safe filename generation"""
        test_cases = [
            ('file.pdf', 'file.pdf'),
            ('file name.pdf', 'file_name.pdf'),
            ('file@name#$.pdf', 'filename.pdf'),
            ('/path/to/file.pdf', 'file.pdf'),
            ('../../../file.pdf', 'file.pdf'),
            ('', 'untitled.pdf'),
            ('file', 'file.pdf'),
            ('con.pdf', '_con.pdf'),  # Windows reserved name
            ('aux.pdf', '_aux.pdf'),  # Windows reserved name
        ]
        
        for input_name, expected in test_cases:
            result = self.interface._generate_safe_filename(input_name)
            self.assertEqual(result, expected, f"Failed for input: {input_name}")

    def test_generate_unique_filename(self):
        """Test unique filename generation when file exists"""
        # Create a file
        existing_file = os.path.join(self.temp_dir, 'existing.pdf')
        with open(existing_file, 'w') as f:
            f.write('test content')
        
        interface = MinIOFileInterface(temp_dir=self.temp_dir)
        
        result = interface._generate_unique_filename('existing.pdf')
        
        self.assertNotEqual(result, 'existing.pdf')
        self.assertTrue(result.startswith('existing_'))
        self.assertTrue(result.endswith('.pdf'))

    def test_get_file_statistics(self):
        """Test getting file statistics"""
        # Create test files
        test_files = []
        for i in range(3):
            file_path = os.path.join(self.temp_dir, f'test_{i}.pdf')
            with open(file_path, 'w') as f:
                f.write(f'test content {i}' * 100)  # Make files different sizes
            test_files.append(file_path)
        
        interface = MinIOFileInterface(temp_dir=self.temp_dir)
        interface.temp_files = test_files
        
        stats = interface.get_file_statistics()
        
        self.assertEqual(stats['total_files'], 3)
        self.assertEqual(stats['temp_files'], 3)
        self.assertGreater(stats['total_size'], 0)
        self.assertEqual(len(stats['file_list']), 3)

    def test_get_file_statistics_no_files(self):
        """Test getting file statistics when no files exist"""
        interface = MinIOFileInterface(temp_dir=self.temp_dir)
        
        stats = interface.get_file_statistics()
        
        self.assertEqual(stats['total_files'], 0)
        self.assertEqual(stats['temp_files'], 0)
        self.assertEqual(stats['total_size'], 0)
        self.assertEqual(len(stats['file_list']), 0)

    def test_cleanup_old_files(self):
        """Test cleanup of old temporary files"""
        import time
        
        # Create old and new files
        old_file = os.path.join(self.temp_dir, 'old.pdf')
        new_file = os.path.join(self.temp_dir, 'new.pdf')
        
        with open(old_file, 'w') as f:
            f.write('old content')
        with open(new_file, 'w') as f:
            f.write('new content')
        
        # Set old file modification time to 2 hours ago
        old_time = time.time() - 7200  # 2 hours ago
        os.utime(old_file, (old_time, old_time))
        
        interface = MinIOFileInterface(temp_dir=self.temp_dir)
        interface.temp_files = [old_file, new_file]
        
        # Cleanup files older than 1 hour
        cleaned_count = interface.cleanup_old_files(max_age_hours=1)
        
        self.assertEqual(cleaned_count, 1)
        self.assertFalse(os.path.exists(old_file))
        self.assertTrue(os.path.exists(new_file))
        self.assertEqual(len(interface.temp_files), 1)

    def test_cleanup_all_temp_files_in_directory(self):
        """Test cleanup of all temp files in directory"""
        # Create additional temp files not in interface's list
        extra_file = os.path.join(self.temp_dir, 'extra.pdf')
        with open(extra_file, 'w') as f:
            f.write('extra content')
        
        registered_file = os.path.join(self.temp_dir, 'registered.pdf')
        with open(registered_file, 'w') as f:
            f.write('registered content')
        
        interface = MinIOFileInterface(temp_dir=self.temp_dir)
        interface.temp_files = [registered_file]
        
        # Cleanup all temp files
        interface.cleanup_all_temp_files()
        
        # Both files should be deleted
        self.assertFalse(os.path.exists(extra_file))
        self.assertFalse(os.path.exists(registered_file))

    def test_memory_efficient_cleanup(self):
        """Test memory efficient cleanup for large number of files"""
        # Create many small files
        many_files = []
        for i in range(100):
            file_path = os.path.join(self.temp_dir, f'test_{i}.pdf')
            with open(file_path, 'w') as f:
                f.write(f'test content {i}')
            many_files.append(file_path)
        
        interface = MinIOFileInterface(temp_dir=self.temp_dir)
        interface.temp_files = many_files
        
        # This should not cause memory issues
        interface.cleanup_temp_files()
        
        self.assertEqual(len(interface.temp_files), 0)
        for file_path in many_files:
            self.assertFalse(os.path.exists(file_path))


if __name__ == '__main__':
    unittest.main()