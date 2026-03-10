"""
Domain guardrail system for restricting SLM to dentistry/oral health content
"""
import re
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class DentistryGuardrail:
    """Guardrail to ensure only dentistry-related content is processed"""

    # Dentistry/oral health related keywords (positive indicators)
    DENTAL_KEYWORDS = [
        # Core dental terms
        'dental', 'dentist', 'dentistry', 'tooth', 'teeth', 'oral', 'periodontal',
        'cavity', 'caries', 'filling', 'root canal', 'extraction', 'implant',
        'orthodont', 'orthodontic', 'orthodontics', 'braces', 'invisalign',
        'denture', 'crown', 'bridge', 'gingiv', 'gingivitis', 'gingival',
        'periodontitis', 'plaque', 'tartar', 'enamel', 'dentin', 'pulp', 'gum',
        'gingiva', 'alveolar', 'maxillofacial', 'prosthodont', 'prosthodontics',
        'endodont', 'endodontics', 'pedodont', 'pedodontics', 'pediatric dentistry',
        'oral surgery', 'dental hygiene', 'fluoride', 'dental plaque',
        'dental calculus', 'tooth decay', 'gum disease',
        # Medical procedures related to dentistry
        'dental prophylaxis', 'scaling', 'polishing', 'whitening', 'veneer',
        'dental bonding', 'sealant', 'dental radiograph', 'x-ray', 'dental imaging',
        # Dental conditions
        'malocclusion', 'overbite', 'underbite', 'crossbite', 'open bite',
        'tooth abscess', 'dental trauma', 'tooth fracture', 'dental erosion',
        'tooth sensitivity', 'dry socket', 'pericoronitis', 'peri-implantitis',
        'oral cancer', 'oral lesion', 'cold sore', 'canker sore', 'thrush',
        # Dental materials
        'amalgam', 'composite', 'porcelain', 'titanium', 'zirconia',
        'dental cement', 'impression material', 'dental alloy',
        # Research/academic terms (specific to dental research)
        'dental research', 'oral health research', 'clinical study dental',
        'dental journal', 'dental literature', 'evidence-based dentistry'
    ]

    # Non-dentistry keywords (negative indicators - stronger rejection)
    NON_DENTAL_KEYWORDS = [
        # Technology/computing
        'software', 'programming', 'coding', 'algorithm', 'database', 'api',
        'machine learning', 'deep learning', 'neural network', 'blockchain',
        'web development', 'mobile app', 'frontend', 'backend', 'cloud computing',
        # Finance/business
        'stock market', 'investment portfolio', 'cryptocurrency', 'trading',
        'accounting', 'financial statement', 'marketing strategy',
        # General topics clearly not dental
        'recipe', 'cooking', 'sports score', 'weather forecast', 'horoscope',
        'political election', 'legal advice not dental', 'real estate'
    ]

    REJECTION_MESSAGE = "Sorry I cannot help you with that"

    def __init__(self, strict_mode: bool = True):
        """
        Initialize guardrail

        Args:
            strict_mode: If True, reject ambiguous queries. If False, allow borderline cases.
        """
        self.strict_mode = strict_mode
        self.dental_pattern = re.compile(
            r'\b(' + '|'.join(re.escape(kw) for kw in self.DENTAL_KEYWORDS) + r')\b',
            re.IGNORECASE
        )
        self.non_dental_pattern = re.compile(
            r'\b(' + '|'.join(re.escape(kw) for kw in self.NON_DENTAL_KEYWORDS) + r')\b',
            re.IGNORECASE
        )

    def check_input(self, text: str, context: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """
        Check if input is dentistry-related

        Args:
            text: Input text to check
            context: Optional context (e.g., paper content) - if provided and is dental, allow the question

        Returns:
            Tuple of (is_allowed, rejection_reason)
            - is_allowed: True if input should be processed, False if rejected
            - rejection_reason: None if allowed, error message if rejected
        """
        if not text or not text.strip():
            return True, None

        text_lower = text.lower()

        # Check for strong non-dental indicators (immediate rejection)
        # But allow research methodology terms even if they overlap with non-dental keywords
        non_dental_matches = self.non_dental_pattern.findall(text_lower)

        # Research methodology terms that should be allowed even with non-dental keywords
        research_methodology_terms = [
            'sample', 'sample size', 'statistical', 'method', 'methods', 'methodology',
            'study design', 'results', 'findings', 'outcomes', 'follow-up', 'follow up',
            'conclusion', 'abstract', 'introduction', 'discussion', 'analysis'
        ]

        # Check if question is about research methodology (allow these)
        is_research_question = any(term in text_lower for term in research_methodology_terms)

        # If context is provided and is dental-related, allow research questions
        if context and is_research_question:
            context_dental_matches = self.dental_pattern.findall(context.lower())
            if context_dental_matches:
                # Paper content is dental, and question is about research methodology
                logger.info(f"Allowed research question about dental paper: {text[:100]}")
                return True, None

        # Block non-dental questions (unless they're research questions about dental papers)
        if non_dental_matches and self.strict_mode and not is_research_question:
            logger.info(f"Rejected non-dental query: {non_dental_matches}")
            return False, self.REJECTION_MESSAGE

        # If context is provided and is dental-related, allow other questions too
        if context:
            context_dental_matches = self.dental_pattern.findall(context.lower())
            if context_dental_matches:
                # Paper content is dental, so allow questions about it
                logger.info(f"Allowed question about dental paper: {text[:100]}")
                return True, None

        # Check for dental indicators in the question itself
        dental_matches = self.dental_pattern.findall(text_lower)
        if dental_matches:
            return True, None

        # For questions without clear dental keywords AND no dental context
        if len(text.split()) < 5 and not dental_matches:
            # Very short query without dental keywords
            if self.strict_mode:
                return False, self.REJECTION_MESSAGE
            else:
                return True, None
        else:
            # Longer query without clear dental keywords
            if self.strict_mode:
                return False, self.REJECTION_MESSAGE
            else:
                logger.warning(f"Ambiguous query allowed (non-strict mode): {text[:100]}")
                return True, None

    def check_response(self, response: str) -> Tuple[bool, str]:
        """
        Check if model response is dentistry-related (post-processing validation)

        Args:
            response: Model-generated response

        Returns:
            Tuple of (is_valid, response_to_return)
            - If valid: (True, original_response)
            - If invalid: (False, REJECTION_MESSAGE)
        """
        if not response or not response.strip():
            return True, response

        response_lower = response.lower()

        # Check if response discusses non-dental topics
        non_dental_matches = self.non_dental_pattern.findall(response_lower)
        if non_dental_matches and self.strict_mode:
            logger.warning(f"Model generated non-dental response: {response[:100]}")
            return False, self.REJECTION_MESSAGE

        # Check if response has at least some dental content
        dental_matches = self.dental_pattern.findall(response_lower)
        if dental_matches or not self.strict_mode:
            return True, response

        # Response has no dental content in strict mode
        logger.warning(f"Response lacks dental content: {response[:100]}")
        return False, self.REJECTION_MESSAGE
