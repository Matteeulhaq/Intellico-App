"""
Test suite for domain guardrails
"""
import unittest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.guardrails.domain_guardrail import DentistryGuardrail

class TestDentistryGuardrail(unittest.TestCase):
    """Test dentistry domain guardrail"""

    def setUp(self):
        """Set up test fixtures"""
        self.guardrail = DentistryGuardrail(strict_mode=True)
        self.guardrail_lenient = DentistryGuardrail(strict_mode=False)

    def test_dental_questions_allowed(self):
        """Test that dental questions are allowed"""
        dental_questions = [
            "What is the best treatment for periodontal disease?",
            "How do dental implants work?",
            "What are the symptoms of gingivitis?",
            "Explain the root canal procedure",
            "What is the role of fluoride in tooth decay prevention?",
            "Compare amalgam and composite fillings",
            "What causes dental caries?",
            "How does orthodontic treatment work?",
            "What is the impact of oral health on quality of life?",
            "Explain dental plaque formation"
        ]

        for question in dental_questions:
            is_allowed, reason = self.guardrail.check_input(question)
            self.assertTrue(is_allowed, f"Question should be allowed: {question}")
            self.assertIsNone(reason)

    def test_non_dental_questions_rejected(self):
        """Test that non-dental questions are rejected"""
        non_dental_questions = [
            "How do I write Python code?",
            "What is the stock price of Apple?",
            "How do I bake a chocolate cake?",
            "Who won the World Cup?",
            "How does blockchain work?",
            "What is the weather forecast?",
            "How do I start a business?",
            "Explain quantum computing",
            "What is machine learning?",
            "How do I create a mobile app?"
        ]

        for question in non_dental_questions:
            is_allowed, reason = self.guardrail.check_input(question)
            self.assertFalse(is_allowed, f"Question should be rejected: {question}")
            self.assertEqual(reason, "Sorry I cannot help you with that")

    def test_context_aware_allowance(self):
        """Test that dental context allows borderline questions"""
        dental_context = """
        This paper discusses the effectiveness of fluoride treatment
        in preventing dental caries in children.
        """

        borderline_questions = [
            "What does the study show?",  # No dental keywords but context is dental
            "What are the main findings?",  # No dental keywords but context is dental
            "What is the conclusion?",  # No dental keywords but context is dental
        ]

        for question in borderline_questions:
            is_allowed, reason = self.guardrail.check_input(question, dental_context)
            self.assertTrue(is_allowed, f"Should allow with dental context: {question}")
            self.assertIsNone(reason)

    def test_response_validation(self):
        """Test response validation"""
        # Valid dental response
        valid_response = "Dental implants are artificial tooth roots placed in the jawbone."
        is_valid, result = self.guardrail.check_response(valid_response)
        self.assertTrue(is_valid)
        self.assertEqual(result, valid_response)

        # Invalid response (non-dental)
        invalid_response = "Python is a programming language used for web development."
        is_valid, result = self.guardrail.check_response(invalid_response)
        self.assertFalse(is_valid)
        self.assertEqual(result, "Sorry I cannot help you with that")

    def test_lenient_mode(self):
        """Test lenient mode allows more queries"""
        ambiguous_questions = [
            "What are the main findings?",
            "How does this work?",
            "What is the conclusion?",
        ]

        for question in ambiguous_questions:
            # Strict mode rejects
            is_allowed_strict, _ = self.guardrail.check_input(question)
            self.assertFalse(is_allowed_strict, f"Strict mode should reject: {question}")

            # Lenient mode allows
            is_allowed_lenient, _ = self.guardrail_lenient.check_input(question)
            self.assertTrue(is_allowed_lenient, f"Lenient mode should allow: {question}")

    def test_empty_input(self):
        """Test empty input handling"""
        is_allowed, reason = self.guardrail.check_input("")
        self.assertTrue(is_allowed)  # Empty input is allowed (will be caught by validation)
        self.assertIsNone(reason)

    def test_mixed_content(self):
        """Test mixed content (dental + non-dental)"""
        # If contains dental keywords, should allow
        mixed_question = "How do I code a website about dental implants?"
        is_allowed, reason = self.guardrail.check_input(mixed_question)
        self.assertTrue(is_allowed, f"Should allow mixed content with dental keywords: {mixed_question}")

    def test_edge_case_medical_non_dental(self):
        """Test edge cases of medical but non-dental questions"""
        non_dental_medical = [
            "What is the treatment for diabetes?",
            "How does heart surgery work?",
            "What causes hypertension?",
        ]

        for question in non_dental_medical:
            is_allowed, reason = self.guardrail.check_input(question)
            # These should be rejected in strict mode
            self.assertFalse(is_allowed, f"Should reject non-dental medical: {question}")

    def test_specific_dental_terms(self):
        """Test specific dental terminology"""
        specific_terms = [
            "What is peri-implantitis?",
            "Explain the process of dental prophylaxis",
            "What is malocclusion?",
            "How does scaling work?",
            "What is dental bonding?"
        ]

        for question in specific_terms:
            is_allowed, reason = self.guardrail.check_input(question)
            self.assertTrue(is_allowed, f"Should allow specific dental term: {question}")

    def test_technology_terminology_in_dental_context(self):
        """Test that technology terms in dental context are allowed"""
        dental_tech_questions = [
            "How is digital radiography used in dentistry?",
            "What are dental imaging techniques?",
            "How do CAD/CAM systems work in dentistry?"
        ]

        for question in dental_tech_questions:
            is_allowed, reason = self.guardrail.check_input(question)
            self.assertTrue(is_allowed, f"Should allow technology in dental context: {question}")

    def test_context_aware_guardrail_allows_research_questions(self):
        """Test that guardrail allows legitimate research questions when context is dental"""
        dental_context = "This study examined the effectiveness of fluoride treatments in preventing dental caries in children."

        # Research methodology questions (should be allowed with dental context)
        methodology_questions = [
            "What was the sample size?",
            "What statistical methods did they use?",
            "What were the primary outcomes?",
            "How long was the follow-up period?",
            "Describe the methodology",
            "What were the main results?",
            "What was the study design?"
        ]

        for question in methodology_questions:
            is_allowed, _ = self.guardrail.check_input(question, context=dental_context)
            self.assertTrue(is_allowed, f"Should allow research question with dental context: {question}")

    def test_guardrail_blocks_non_dental_topics_even_with_context(self):
        """Test that guardrail still blocks clearly non-dental topics even with dental context"""
        dental_context = "This study examined the effectiveness of fluoride treatments in preventing dental caries in children."

        # Use questions that contain actual non-dental keywords from the NON_DENTAL_KEYWORDS list
        non_dental_questions = [
            "How do I learn programming?",  # Contains "programming"
            "What's the recipe for chocolate cake?",  # Contains "recipe" and "cooking"
            "Should I invest in cryptocurrency?",  # Contains "cryptocurrency" (variant of "cryptocurrency")
            "How do I build a mobile app?",  # Contains "mobile app"
            "Explain machine learning algorithms",  # Contains "machine learning" and "algorithm"
            "How does web development work?",  # Contains "web development"
        ]

        for question in non_dental_questions:
            is_allowed, _ = self.guardrail.check_input(question, context=dental_context)
            self.assertFalse(is_allowed, f"Should block non-dental question even with dental context: {question}")

    def test_guardrail_allows_explicit_dental_questions(self):
        """Test that guardrail allows explicit dental questions without context"""
        dental_questions = [
            "What is the best treatment for gingivitis?",
            "How do dental implants work?",
            "What are the symptoms of periodontal disease?"
        ]

        for question in dental_questions:
            is_allowed, _ = self.guardrail.check_input(question)
            self.assertTrue(is_allowed, f"Should allow explicit dental question: {question}")

class TestGuardrailIntegration(unittest.TestCase):
    """Test guardrail integration scenarios"""

    def setUp(self):
        """Set up test fixtures"""
        self.guardrail = DentistryGuardrail(strict_mode=True)

    def test_full_workflow_dental_query(self):
        """Test full workflow with valid dental query"""
        question = "What is the treatment for periodontal disease?"

        # Pre-filter check
        is_allowed, rejection_reason = self.guardrail.check_input(question)
        self.assertTrue(is_allowed)
        self.assertIsNone(rejection_reason)

        # Simulate model response
        mock_response = "Periodontal disease treatment typically involves scaling and root planing to remove plaque and tartar."

        # Post-processing check
        is_valid, final_response = self.guardrail.check_response(mock_response)
        self.assertTrue(is_valid)
        self.assertEqual(final_response, mock_response)

    def test_full_workflow_non_dental_query(self):
        """Test full workflow with non-dental query"""
        question = "How do I write Python code?"

        # Pre-filter check
        is_allowed, rejection_reason = self.guardrail.check_input(question)
        self.assertFalse(is_allowed)
        self.assertEqual(rejection_reason, "Sorry I cannot help you with that")

    def test_post_processing_catches_non_dental_response(self):
        """Test that post-processing catches non-dental model responses"""
        # Simulate a dental question that gets a non-dental response
        dental_question = "What is dental caries?"

        # Pre-filter allows the question
        is_allowed, _ = self.guardrail.check_input(dental_question)
        self.assertTrue(is_allowed)

        # But model returns non-dental response (hallucination)
        non_dental_response = "Stock market investing involves buying shares of companies."

        # Post-processing should catch this
        is_valid, final_response = self.guardrail.check_response(non_dental_response)
        self.assertFalse(is_valid)
        self.assertEqual(final_response, "Sorry I cannot help you with that")

if __name__ == '__main__':
    unittest.main()
