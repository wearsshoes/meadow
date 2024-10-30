"""Unit tests for topic similarity detection"""

import unittest
from unittest.mock import patch, MagicMock
import os

class TestTopicSimilarity(unittest.TestCase):
    """Test topic similarity detection with different backends"""

    def setUp(self):
        self.test_topics = ['civic government', 'urban planning']
        self.test_text = """
        The city council meeting discussed the new urban development plan.
        Key points included zoning changes and public transportation improvements.
        """
        self.unrelated_text = """
        A recipe for chocolate cake requires flour, sugar, cocoa powder,
        and eggs. Mix well and bake at 350 degrees.
        """

    def test_fallback_embeddings(self):
        """Test similarity detection using sentence-transformers"""
        from meadow.core.topic_similarity import get_similarity_score
        score1 = get_similarity_score(self.test_text, self.test_topics)
        score2 = get_similarity_score(self.unrelated_text, self.test_topics)

        self.assertGreater(score1, 0.5, "Related text should have high similarity")
        self.assertLess(score2, 0.3, "Unrelated text should have low similarity")

    def test_threshold_config(self):
        """Test similarity threshold configuration"""
        from meadow.core.topic_similarity import check_topic_relevance

        # Should match with default threshold
        self.assertTrue(check_topic_relevance(self.test_text, self.test_topics))

        # Should not match with high threshold
        self.assertFalse(check_topic_relevance(self.test_text, self.test_topics, threshold=0.9))

if __name__ == '__main__':
    unittest.main()
