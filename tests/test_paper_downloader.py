import unittest
from unittest.mock import Mock, patch, MagicMock
import os
import tempfile
from urllib.parse import urlparse

from src.paper_downloader import PaperDownloader, ArXivDownloader, SpringerDownloader, IEEEDownloader


class TestPaperDownloader(unittest.TestCase):
    """Test cases for PaperDownloader class"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_minio_client = Mock()
        self.downloader = PaperDownloader(minio_client=self.mock_minio_client)

    def test_init_basic(self):
        """Test basic initialization"""
        downloader = PaperDownloader()
        self.assertIsNone(downloader.minio_client)
        self.assertEqual(downloader.timeout, 30)
        self.assertEqual(downloader.max_retries, 3)
        self.assertEqual(downloader.user_agent, 'Mozilla/5.0')

    def test_init_with_minio_client(self):
        """Test initialization with MinIO client"""
        downloader = PaperDownloader(minio_client=self.mock_minio_client)
        self.assertEqual(downloader.minio_client, self.mock_minio_client)

    def test_init_with_custom_params(self):
        """Test initialization with custom parameters"""
        downloader = PaperDownloader(
            minio_client=self.mock_minio_client,
            timeout=60,
            max_retries=5,
            user_agent='Custom User Agent'
        )
        self.assertEqual(downloader.timeout, 60)
        self.assertEqual(downloader.max_retries, 5)
        self.assertEqual(downloader.user_agent, 'Custom User Agent')

    def test_is_supported_url_arxiv(self):
        """Test URL support detection for arXiv"""
        arxiv_urls = [
            'https://arxiv.org/pdf/2101.00001.pdf',
            'https://arxiv.org/pdf/2101.00001',
            'http://arxiv.org/pdf/2101.00001.pdf',
            'https://arxiv.org/abs/2101.00001'
        ]
        
        for url in arxiv_urls:
            self.assertTrue(self.downloader.is_supported_url(url), f"Failed for: {url}")

    def test_is_supported_url_springer(self):
        """Test URL support detection for Springer"""
        springer_urls = [
            'https://link.springer.com/content/pdf/10.1007/978-3-030-12345-6_1.pdf',
            'https://link.springer.com/content/pdf/10.1007/s11276-021-02800-7.pdf',
            'http://link.springer.com/content/pdf/10.1007/978-3-030-12345-6_1.pdf'
        ]
        
        for url in springer_urls:
            self.assertTrue(self.downloader.is_supported_url(url), f"Failed for: {url}")

    def test_is_supported_url_ieee(self):
        """Test URL support detection for IEEE"""
        ieee_urls = [
            'https://ieeexplore.ieee.org/document/1234567',
            'https://ieeexplore.ieee.org/document/9876543',
            'http://ieeexplore.ieee.org/document/1234567'
        ]
        
        for url in ieee_urls:
            self.assertTrue(self.downloader.is_supported_url(url), f"Failed for: {url}")

    def test_is_supported_url_direct_pdf(self):
        """Test URL support detection for direct PDF links"""
        pdf_urls = [
            'https://example.com/paper.pdf',
            'http://example.com/document.pdf',
            'https://example.com/file.pdf?download=true'
        ]
        
        for url in pdf_urls:
            self.assertTrue(self.downloader.is_supported_url(url), f"Failed for: {url}")

    def test_is_supported_url_unsupported(self):
        """Test URL support detection for unsupported URLs"""
        unsupported_urls = [
            'https://example.com/page.html',
            'https://example.com/',
            'https://youtube.com/watch?v=abc123',
            'https://example.com/doc.docx'
        ]
        
        for url in unsupported_urls:
            self.assertFalse(self.downloader.is_supported_url(url), f"Should fail for: {url}")

    def test_download_paper_arxiv_success(self):
        """Test successful arXiv paper download"""
        mock_response = Mock()
        mock_response.content = b'PDF content'
        mock_response.headers = {'Content-Type': 'application/pdf'}
        
        self.mock_minio_client.upload_file.return_value = True
        
        with patch('requests.get', return_value=mock_response), \
             patch('src.paper_downloader.ArXivDownloader') as mock_arxiv_class:
            
            mock_arxiv = Mock()
            mock_arxiv.download.return_value = {
                'success': True,
                'content': b'PDF content',
                'filename': 'arxiv_2101.00001.pdf',
                'content_type': 'application/pdf'
            }
            mock_arxiv_class.return_value = mock_arxiv
            
            result = self.downloader.download_paper('https://arxiv.org/pdf/2101.00001')
            
            self.assertTrue(result['success'])
            self.assertEqual(result['object_name'], 'arxiv_2101.00001.pdf')
            self.assertEqual(result['original_filename'], '2101.00001.pdf')
            self.assertEqual(result['content_type'], 'application/pdf')
            self.mock_minio_client.upload_file.assert_called_once()

    def test_download_paper_with_custom_object_name(self):
        """Test paper download with custom object name"""
        mock_response = Mock()
        mock_response.content = b'PDF content'
        mock_response.headers = {'Content-Type': 'application/pdf'}
        
        self.mock_minio_client.upload_file.return_value = True
        
        with patch('requests.get', return_value=mock_response), \
             patch('src.paper_downloader.ArXivDownloader') as mock_arxiv_class:
            
            mock_arxiv = Mock()
            mock_arxiv.download.return_value = {
                'success': True,
                'content': b'PDF content',
                'filename': 'arxiv_2101.00001.pdf',
                'content_type': 'application/pdf'
            }
            mock_arxiv_class.return_value = mock_arxiv
            
            result = self.downloader.download_paper(
                'https://arxiv.org/pdf/2101.00001',
                object_name='custom_name.pdf'
            )
            
            self.assertTrue(result['success'])
            self.assertEqual(result['object_name'], 'custom_name.pdf')

    def test_download_paper_download_failure(self):
        """Test paper download when download fails"""
        with patch('src.paper_downloader.ArXivDownloader') as mock_arxiv_class:
            
            mock_arxiv = Mock()
            mock_arxiv.download.return_value = {
                'success': False,
                'error': 'Download failed'
            }
            mock_arxiv_class.return_value = mock_arxiv
            
            result = self.downloader.download_paper('https://arxiv.org/pdf/2101.00001')
            
            self.assertFalse(result['success'])
            self.assertEqual(result['error'], 'Download failed')

    def test_download_paper_upload_failure(self):
        """Test paper download when MinIO upload fails"""
        mock_response = Mock()
        mock_response.content = b'PDF content'
        mock_response.headers = {'Content-Type': 'application/pdf'}
        
        self.mock_minio_client.upload_file.return_value = False
        
        with patch('requests.get', return_value=mock_response), \
             patch('src.paper_downloader.ArXivDownloader') as mock_arxiv_class:
            
            mock_arxiv = Mock()
            mock_arxiv.download.return_value = {
                'success': True,
                'content': b'PDF content',
                'filename': 'arxiv_2101.00001.pdf',
                'content_type': 'application/pdf'
            }
            mock_arxiv_class.return_value = mock_arxiv
            
            result = self.downloader.download_paper('https://arxiv.org/pdf/2101.00001')
            
            self.assertFalse(result['success'])
            self.assertIn('MinIO upload failed', result['error'])

    def test_download_paper_no_minio_client(self):
        """Test paper download without MinIO client"""
        downloader = PaperDownloader(minio_client=None)
        
        mock_response = Mock()
        mock_response.content = b'PDF content'
        mock_response.headers = {'Content-Type': 'application/pdf'}
        
        with patch('requests.get', return_value=mock_response), \
             patch('tempfile.NamedTemporaryFile') as mock_temp_file:
            
            mock_temp = Mock()
            mock_temp.name = '/tmp/test.pdf'
            mock_temp.__enter__.return_value = mock_temp
            mock_temp.__exit__.return_value = None
            mock_temp_file.return_value = mock_temp
            
            result = downloader.download_paper('https://arxiv.org/pdf/2101.00001')
            
            self.assertTrue(result['success'])
            self.assertEqual(result['local_path'], '/tmp/test.pdf')

    def test_batch_download_papers_success(self):
        """Test successful batch download"""
        urls = [
            'https://arxiv.org/pdf/2101.00001',
            'https://arxiv.org/pdf/2101.00002'
        ]
        
        self.mock_minio_client.upload_file.return_value = True
        
        with patch.object(self.downloader, 'download_paper') as mock_download:
            mock_download.side_effect = [
                {
                    'success': True,
                    'object_name': 'arxiv_2101.00001.pdf',
                    'url': 'https://arxiv.org/pdf/2101.00001',
                    'size': 1024
                },
                {
                    'success': True,
                    'object_name': 'arxiv_2101.00002.pdf',
                    'url': 'https://arxiv.org/pdf/2101.00002',
                    'size': 2048
                }
            ]
            
            result = self.downloader.batch_download_papers(urls)
            
            self.assertTrue(result['success'])
            self.assertEqual(result['total'], 2)
            self.assertEqual(result['success_count'], 2)
            self.assertEqual(result['failure_count'], 0)
            self.assertEqual(len(result['results']), 2)

    def test_batch_download_papers_partial_failure(self):
        """Test batch download with partial failures"""
        urls = [
            'https://arxiv.org/pdf/2101.00001',
            'https://arxiv.org/pdf/2101.00002',
            'https://arxiv.org/pdf/2101.00003'
        ]
        
        with patch.object(self.downloader, 'download_paper') as mock_download:
            mock_download.side_effect = [
                {
                    'success': True,
                    'object_name': 'arxiv_2101.00001.pdf',
                    'url': 'https://arxiv.org/pdf/2101.00001',
                    'size': 1024
                },
                {
                    'success': False,
                    'error': 'Download failed',
                    'url': 'https://arxiv.org/pdf/2101.00002'
                },
                {
                    'success': True,
                    'object_name': 'arxiv_2101.00003.pdf',
                    'url': 'https://arxiv.org/pdf/2101.00003',
                    'size': 3072
                }
            ]
            
            result = self.downloader.batch_download_papers(urls)
            
            self.assertTrue(result['success'])
            self.assertEqual(result['total'], 3)
            self.assertEqual(result['success_count'], 2)
            self.assertEqual(result['failure_count'], 1)
            self.assertEqual(len(result['results']), 3)

    def test_batch_download_papers_all_fail(self):
        """Test batch download when all downloads fail"""
        urls = [
            'https://arxiv.org/pdf/2101.00001',
            'https://arxiv.org/pdf/2101.00002'
        ]
        
        with patch.object(self.downloader, 'download_paper') as mock_download:
            mock_download.side_effect = [
                {
                    'success': False,
                    'error': 'Download failed',
                    'url': 'https://arxiv.org/pdf/2101.00001'
                },
                {
                    'success': False,
                    'error': 'Network error',
                    'url': 'https://arxiv.org/pdf/2101.00002'
                }
            ]
            
            result = self.downloader.batch_download_papers(urls)
            
            self.assertFalse(result['success'])
            self.assertEqual(result['total'], 2)
            self.assertEqual(result['success_count'], 0)
            self.assertEqual(result['failure_count'], 2)

    def test_batch_download_papers_empty_list(self):
        """Test batch download with empty URL list"""
        result = self.downloader.batch_download_papers([])
        
        self.assertTrue(result['success'])
        self.assertEqual(result['total'], 0)
        self.assertEqual(result['success_count'], 0)
        self.assertEqual(result['failure_count'], 0)

    def test_get_paper_info_arxiv(self):
        """Test getting paper info for arXiv URL"""
        with patch('src.paper_downloader.ArXivDownloader') as mock_arxiv_class:
            mock_arxiv = Mock()
            mock_arxiv.get_paper_info.return_value = {
                'title': 'Test Paper Title',
                'authors': ['Author 1', 'Author 2'],
                'abstract': 'This is a test abstract',
                'published_date': '2024-01-01',
                'doi': '10.48550/arXiv.2101.00001'
            }
            mock_arxiv_class.return_value = mock_arxiv
            
            result = self.downloader.get_paper_info('https://arxiv.org/pdf/2101.00001')
            
            self.assertEqual(result['title'], 'Test Paper Title')
            self.assertEqual(result['authors'], ['Author 1', 'Author 2'])
            self.assertEqual(result['abstract'], 'This is a test abstract')

    def test_get_paper_info_unsupported_url(self):
        """Test getting paper info for unsupported URL"""
        result = self.downloader.get_paper_info('https://example.com/page.html')
        
        self.assertIsNone(result)

    def test_generate_object_name_arxiv(self):
        """Test object name generation for arXiv URLs"""
        test_cases = [
            ('https://arxiv.org/pdf/2101.00001.pdf', 'arxiv_2101.00001.pdf'),
            ('https://arxiv.org/pdf/2101.00001', 'arxiv_2101.00001.pdf'),
            ('https://arxiv.org/abs/2101.00001', 'arxiv_2101.00001.pdf'),
            ('https://arxiv.org/pdf/1234.56789.pdf', 'arxiv_1234.56789.pdf')
        ]
        
        for url, expected in test_cases:
            result = self.downloader._generate_object_name(url)
            self.assertEqual(result, expected, f"Failed for URL: {url}")

    def test_generate_object_name_other(self):
        """Test object name generation for other URLs"""
        test_cases = [
            ('https://example.com/paper.pdf', 'paper.pdf'),
            ('https://example.com/very-long-filename-that-should-be-truncated.pdf', 'very-long-filename-that-should-be-truncated.pdf'),
            ('https://example.com/document.pdf?download=true', 'document.pdf'),
            ('https://example.com/', 'untitled.pdf')
        ]
        
        for url, expected in test_cases:
            result = self.downloader._generate_object_name(url)
            self.assertEqual(result, expected, f"Failed for URL: {url}")


class TestArXivDownloader(unittest.TestCase):
    """Test cases for ArXivDownloader class"""

    def setUp(self):
        """Set up test fixtures"""
        self.downloader = ArXivDownloader()

    def test_init(self):
        """Test initialization"""
        downloader = ArXivDownloader()
        self.assertEqual(downloader.base_url, 'https://arxiv.org')
        self.assertEqual(downloader.timeout, 30)
        self.assertEqual(downloader.max_retries, 3)

    def test_extract_arxiv_id_from_url(self):
        """Test arXiv ID extraction from URL"""
        test_cases = [
            ('https://arxiv.org/pdf/2101.00001.pdf', '2101.00001'),
            ('https://arxiv.org/pdf/2101.00001', '2101.00001'),
            ('https://arxiv.org/abs/2101.00001', '2101.00001'),
            ('https://arxiv.org/abs/1234.56789v2', '1234.56789'),
            ('https://arxiv.org/pdf/1234.56789.pdf', '1234.56789')
        ]
        
        for url, expected_id in test_cases:
            result = self.downloader._extract_arxiv_id_from_url(url)
            self.assertEqual(result, expected_id, f"Failed for URL: {url}")

    def test_extract_arxiv_id_invalid_url(self):
        """Test arXiv ID extraction from invalid URL"""
        invalid_urls = [
            'https://example.com/paper.pdf',
            'https://arxiv.org/',
            'https://arxiv.org/search/',
            'https://arxiv.org/list/cs.AI/recent'
        ]
        
        for url in invalid_urls:
            result = self.downloader._extract_arxiv_id_from_url(url)
            self.assertIsNone(result, f"Should return None for URL: {url}")

    def test_get_download_url(self):
        """Test download URL generation"""
        test_cases = [
            ('2101.00001', 'https://arxiv.org/pdf/2101.00001.pdf'),
            ('1234.56789', 'https://arxiv.org/pdf/1234.56789.pdf'),
            ('1234.56789v2', 'https://arxiv.org/pdf/1234.56789.pdf')
        ]
        
        for arxiv_id, expected_url in test_cases:
            result = self.downloader.get_download_url(arxiv_id)
            self.assertEqual(result, expected_url, f"Failed for ID: {arxiv_id}")

    def test_get_paper_info_success(self):
        """Test successful paper info retrieval"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'entry': {
                'title': 'Test Paper Title',
                'author': [{'name': 'Author 1'}, {'name': 'Author 2'}],
                'summary': 'This is a test abstract',
                'published': '2024-01-01T00:00:00Z',
                'id': 'http://arxiv.org/abs/2101.00001'
            }
        }
        
        with patch('requests.get', return_value=mock_response):
            result = self.downloader.get_paper_info('2101.00001')
            
            self.assertEqual(result['title'], 'Test Paper Title')
            self.assertEqual(result['authors'], ['Author 1', 'Author 2'])
            self.assertEqual(result['abstract'], 'This is a test abstract')
            self.assertEqual(result['published_date'], '2024-01-01')
            self.assertEqual(result['doi'], '10.48550/arXiv.2101.00001')

    def test_get_paper_info_failure(self):
        """Test paper info retrieval when API fails"""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("API Error")
        
        with patch('requests.get', return_value=mock_response):
            result = self.downloader.get_paper_info('2101.00001')
            
            self.assertIsNone(result)


class TestSpringerDownloader(unittest.TestCase):
    """Test cases for SpringerDownloader class"""

    def setUp(self):
        """Set up test fixtures"""
        self.downloader = SpringerDownloader()

    def test_init(self):
        """Test initialization"""
        downloader = SpringerDownloader()
        self.assertEqual(downloader.base_url, 'https://link.springer.com')
        self.assertEqual(downloader.timeout, 30)
        self.assertEqual(downloader.max_retries, 3)

    def test_extract_doi_from_url(self):
        """Test DOI extraction from URL"""
        test_cases = [
            ('https://link.springer.com/content/pdf/10.1007/978-3-030-12345-6_1.pdf', '10.1007/978-3-030-12345-6_1'),
            ('https://link.springer.com/content/pdf/10.1007/s11276-021-02800-7.pdf', '10.1007/s11276-021-02800-7'),
            ('https://link.springer.com/chapter/10.1007/978-3-030-12345-6_1', '10.1007/978-3-030-12345-6_1'),
            ('https://link.springer.com/article/10.1007/s11276-021-02800-7', '10.1007/s11276-021-02800-7')
        ]
        
        for url, expected_doi in test_cases:
            result = self.downloader._extract_doi_from_url(url)
            self.assertEqual(result, expected_doi, f"Failed for URL: {url}")

    def test_get_download_url(self):
        """Test download URL generation"""
        test_cases = [
            ('10.1007/978-3-030-12345-6_1', 'https://link.springer.com/content/pdf/10.1007/978-3-030-12345-6_1.pdf'),
            ('10.1007/s11276-021-02800-7', 'https://link.springer.com/content/pdf/10.1007/s11276-021-02800-7.pdf')
        ]
        
        for doi, expected_url in test_cases:
            result = self.downloader.get_download_url(doi)
            self.assertEqual(result, expected_url, f"Failed for DOI: {doi}")


class TestIEEEDownloader(unittest.TestCase):
    """Test cases for IEEEDownloader class"""

    def setUp(self):
        """Set up test fixtures"""
        self.downloader = IEEEDownloader()

    def test_init(self):
        """Test initialization"""
        downloader = IEEEDownloader()
        self.assertEqual(downloader.base_url, 'https://ieeexplore.ieee.org')
        self.assertEqual(downloader.timeout, 30)
        self.assertEqual(downloader.max_retries, 3)

    def test_extract_document_id_from_url(self):
        """Test document ID extraction from URL"""
        test_cases = [
            ('https://ieeexplore.ieee.org/document/1234567', '1234567'),
            ('https://ieeexplore.ieee.org/document/9876543', '9876543'),
            ('https://ieeexplore.ieee.org/document/1', '1')
        ]
        
        for url, expected_id in test_cases:
            result = self.downloader._extract_document_id_from_url(url)
            self.assertEqual(result, expected_id, f"Failed for URL: {url}")

    def test_get_download_url(self):
        """Test download URL generation"""
        test_cases = [
            ('1234567', 'https://ieeexplore.ieee.org/document/1234567'),
            ('9876543', 'https://ieeexplore.ieee.org/document/9876543')
        ]
        
        for doc_id, expected_url in test_cases:
            result = self.downloader.get_download_url(doc_id)
            self.assertEqual(result, expected_url, f"Failed for document ID: {doc_id}")


if __name__ == '__main__':
    unittest.main()