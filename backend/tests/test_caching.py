"""
Test suite for summary caching functionality
"""
import unittest
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.rag.vector_store import VectorStore

class TestSummaryCaching(unittest.TestCase):
    """Test summary caching in VectorStore"""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures - run once for all tests"""
        import os
        mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017')
        cls.vector_store = VectorStore(mongo_uri=mongo_uri, db_name='intellico_test')

    def setUp(self):
        """Clean up before each test"""
        # Delete test summaries if they exist
        self.vector_store.delete_summary('test_paper_123')

    def tearDown(self):
        """Clean up after each test"""
        # Delete test summaries
        self.vector_store.delete_summary('test_paper_123')

    def test_store_and_retrieve_summary(self):
        """Test storing and retrieving a cached summary"""
        paper_id = 'test_paper_123'

        # Create test summary data
        summary_data = {
            'summary': 'This is a test summary of a dental research paper.',
            'section_summaries': {
                'abstract': 'Test abstract summary',
                'introduction': 'Test introduction summary'
            },
            'key_findings': {
                'main_findings': 'Test main findings',
                'methodology': 'Test methodology'
            },
            'metadata': {
                'total_chunks': 10,
                'sections_processed': 2,
                'method': 'multi_stage_hierarchical',
                'processing_time_ms': 5000
            }
        }

        # Store summary
        result_id = self.vector_store.store_summary(paper_id, summary_data)
        self.assertIsNotNone(result_id)
        print(f"✓ Summary stored with ID: {result_id}")

        # Retrieve summary
        cached_summary = self.vector_store.get_summary(paper_id)
        self.assertIsNotNone(cached_summary)
        self.assertEqual(cached_summary['summary'], summary_data['summary'])
        self.assertEqual(cached_summary['section_summaries']['abstract'], summary_data['section_summaries']['abstract'])
        self.assertEqual(cached_summary['cache_stats']['times_accessed'], 1)
        print(f"✓ Summary retrieved successfully (accessed {cached_summary['cache_stats']['times_accessed']} time)")

        # Access again to test increment
        cached_summary_2 = self.vector_store.get_summary(paper_id)
        self.assertEqual(cached_summary_2['cache_stats']['times_accessed'], 2)
        print(f"✓ Summary accessed again (accessed {cached_summary_2['cache_stats']['times_accessed']} times)")

    def test_cache_miss(self):
        """Test retrieving non-existent summary returns None"""
        cached_summary = self.vector_store.get_summary('non_existent_paper')
        self.assertIsNone(cached_summary)
        print("✓ Cache miss returns None correctly")

    def test_delete_summary(self):
        """Test deleting a cached summary"""
        paper_id = 'test_paper_123'

        # Store a summary
        summary_data = {
            'summary': 'Test summary to delete',
            'section_summaries': {},
            'key_findings': {},
            'metadata': {}
        }
        self.vector_store.store_summary(paper_id, summary_data)

        # Verify it exists
        cached_summary = self.vector_store.get_summary(paper_id)
        self.assertIsNotNone(cached_summary)
        print("✓ Summary stored for deletion test")

        # Delete it
        success = self.vector_store.delete_summary(paper_id)
        self.assertTrue(success)
        print("✓ Summary deleted successfully")

        # Verify it's gone
        cached_summary = self.vector_store.get_summary(paper_id)
        self.assertIsNone(cached_summary)
        print("✓ Deleted summary returns None on retrieval")

    def test_delete_non_existent_summary(self):
        """Test deleting non-existent summary returns False"""
        success = self.vector_store.delete_summary('non_existent_paper')
        self.assertFalse(success)
        print("✓ Deleting non-existent summary returns False")

    def test_cache_stats(self):
        """Test cache statistics calculation"""
        paper_id = 'test_paper_123'

        # Store multiple summaries
        for i in range(3):
            summary_data = {
                'summary': f'Test summary {i}',
                'section_summaries': {},
                'key_findings': {},
                'metadata': {
                    'processing_time_ms': 5000 + (i * 1000)
                }
            }
            self.vector_store.store_summary(f'{paper_id}_{i}', summary_data)

        # Get stats
        stats = self.vector_store.get_cache_stats()
        self.assertIn('total_cached_summaries', stats)
        self.assertIn('average_access_count', stats)
        self.assertIn('total_processing_time_saved_ms', stats)
        self.assertGreater(stats['total_cached_summaries'], 0)
        print(f"✓ Cache stats: {stats}")

        # Clean up
        for i in range(3):
            self.vector_store.delete_summary(f'{paper_id}_{i}')

    def test_metadata_preservation(self):
        """Test that metadata is preserved correctly"""
        paper_id = 'test_paper_123'

        summary_data = {
            'summary': 'Test summary with metadata',
            'section_summaries': {
                'abstract': 'Abstract',
                'methodology': 'Methods'
            },
            'key_findings': {
                'main_findings': 'Findings',
                'clinical_significance': 'Clinical'
            },
            'metadata': {
                'total_chunks': 15,
                'sections_processed': 6,
                'method': 'multi_stage_hierarchical',
                'processing_time_ms': 12000
            }
        }

        self.vector_store.store_summary(paper_id, summary_data)
        cached = self.vector_store.get_summary(paper_id)

        self.assertEqual(cached['metadata']['total_chunks'], 15)
        self.assertEqual(cached['metadata']['sections_processed'], 6)
        self.assertEqual(cached['metadata']['method'], 'multi_stage_hierarchical')
        self.assertEqual(cached['metadata']['processing_time_ms'], 12000)
        self.assertEqual(len(cached['section_summaries']), 2)
        self.assertEqual(len(cached['key_findings']), 2)
        print("✓ All metadata preserved correctly")

if __name__ == '__main__':
    unittest.main(verbosity=2)
