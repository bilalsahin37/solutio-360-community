"""
Advanced Turkish NLP Processing Module
Enterprise-grade Turkish language processing inspired by LeewayHertz solutions
"""

import logging
import re
import unicodedata
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class TurkishTextAnalysis:
    """Turkish text analysis result"""

    original_text: str
    cleaned_text: str
    sentiment: str
    sentiment_score: float
    formality_level: str
    urgency_level: str
    emotional_intensity: str
    key_phrases: List[str]
    grammar_errors: List[str]
    suggested_response_tone: str
    cultural_context: Dict


class TurkishNLPProcessor:
    """
    Advanced Turkish NLP processor with cultural context awareness
    Features enterprise-level Turkish language understanding
    """

    def __init__(self):
        self.turkish_stopwords = {
            "ve",
            "veya",
            "ile",
            "için",
            "bu",
            "şu",
            "o",
            "bir",
            "de",
            "da",
            "ki",
            "mi",
            "mı",
            "mu",
            "mü",
            "ne",
            "gi",
            "gibi",
            "kadar",
            "daha",
            "en",
            "çok",
            "az",
            "hiç",
            "her",
            "bazı",
            "bütün",
            "tüm",
            "kendi",
            "onun",
            "bunun",
            "şunun",
            "benim",
            "senin",
            "bizim",
            "sizin",
            "onlar",
            "bunlar",
            "şunlar",
            "biz",
            "siz",
            "ben",
            "sen",
            "o",
        }

        # Turkish sentiment lexicon
        self.positive_words = {
            "mükemmel": 0.9,
            "harika": 0.8,
            "çok iyi": 0.8,
            "güzel": 0.7,
            "başarılı": 0.7,
            "memnun": 0.8,
            "beğendim": 0.7,
            "teşekkür": 0.6,
            "süper": 0.8,
            "muhteşem": 0.9,
            "fevkalade": 0.9,
            "olağanüstü": 0.8,
            "tatmin": 0.7,
            "hoşnut": 0.7,
            "keyifli": 0.6,
            "mutlu": 0.7,
            "sevindim": 0.7,
            "beğeni": 0.6,
            "kaliteli": 0.7,
            "profesyonel": 0.6,
        }

        self.negative_words = {
            "berbat": -0.9,
            "kötü": -0.7,
            "çok kötü": -0.8,
            "rezalet": -0.9,
            "başarısız": -0.7,
            "memnun değil": -0.8,
            "beğenmedim": -0.7,
            "şikayet": -0.6,
            "sorun": -0.5,
            "problem": -0.5,
            "hata": -0.6,
            "eksik": -0.5,
            "yetersiz": -0.6,
            "kusurlu": -0.7,
            "bozuk": -0.7,
            "çalışmıyor": -0.8,
            "işlemiyor": -0.7,
            "yavaş": -0.5,
            "geç": -0.4,
            "sinirli": -0.7,
            "kızgın": -0.7,
            "öfkeli": -0.8,
            "rahatsız": -0.6,
        }

        # Formality indicators
        self.formal_indicators = {
            "sayın",
            "saygılarımla",
            "saygılarımızla",
            "teşekkür ederim",
            "teşekkür ederiz",
            "memnun kalırım",
            "memnun kalırız",
            "rica ederim",
            "rica ederiz",
            "lütfen",
            "müsaade",
            "izin",
            "gerekmektedir",
            "bulunmaktadır",
            "yapılmaktadır",
        }

        self.informal_indicators = {
            "abi",
            "kardeş",
            "ya",
            "yani",
            "işte",
            "böyle",
            "şöyle",
            "falan",
            "filan",
            "bak",
            "yahu",
            "be",
            "lan",
            "vallahi",
            "gerçekten",
            "cidden",
            "harbiden",
        }

        # Urgency indicators
        self.urgent_keywords = {
            "acil": 0.9,
            "hemen": 0.8,
            "şimdi": 0.7,
            "derhal": 0.9,
            "ivedi": 0.8,
            "bekleyemem": 0.8,
            "sabırsızım": 0.7,
            "zaman kaybı": 0.6,
            "gecikme": 0.5,
            "geç kaldı": 0.6,
            "önemli": 0.5,
            "kritik": 0.8,
            "ciddi": 0.6,
        }

        # Emotional intensity markers
        self.high_intensity_markers = {
            "!!!",
            "!?",
            "ÇOKKKK",
            "ÇOK ÇOK",
            "KESINLIKLE",
            "ASLA",
            "HİÇBİR ZAMAN",
            "MUTLAKA",
            "LÜTFEN",
            "RICA EDIYORUM",
        }

        # Cultural context patterns
        self.cultural_patterns = {
            "religious_references": [
                "allah",
                "inşallah",
                "maşallah",
                "subhanallah",
                "elhamdülillah",
                "bismillah",
                "allahtan",
                "allah korusun",
                "allah bilir",
            ],
            "respect_forms": [
                "ağabey",
                "abla",
                "usta",
                "hoca",
                "bey",
                "hanım",
                "efendi",
                "beyefendi",
                "hanımefendi",
            ],
            "complaint_softeners": [
                "kusura bakmayın",
                "özür dilerim",
                "rahatsız ettiğim için",
                "vakti olduğunda",
                "müsait olduğunuzda",
                "eğer mümkünse",
            ],
        }

    def analyze_comprehensive(self, text: str) -> TurkishTextAnalysis:
        """
        Comprehensive Turkish text analysis with cultural context
        """
        try:
            # Clean and normalize text
            cleaned_text = self._clean_text(text)

            # Sentiment analysis
            sentiment, sentiment_score = self._analyze_sentiment(cleaned_text)

            # Formality level
            formality_level = self._detect_formality(cleaned_text)

            # Urgency level
            urgency_level = self._detect_urgency(cleaned_text)

            # Emotional intensity
            emotional_intensity = self._detect_emotional_intensity(text)

            # Key phrases extraction
            key_phrases = self._extract_key_phrases(cleaned_text)

            # Grammar error detection (simplified)
            grammar_errors = self._detect_grammar_errors(text)

            # Response tone suggestion
            response_tone = self._suggest_response_tone(sentiment, formality_level, urgency_level)

            # Cultural context analysis
            cultural_context = self._analyze_cultural_context(cleaned_text)

            return TurkishTextAnalysis(
                original_text=text,
                cleaned_text=cleaned_text,
                sentiment=sentiment,
                sentiment_score=sentiment_score,
                formality_level=formality_level,
                urgency_level=urgency_level,
                emotional_intensity=emotional_intensity,
                key_phrases=key_phrases,
                grammar_errors=grammar_errors,
                suggested_response_tone=response_tone,
                cultural_context=cultural_context,
            )

        except Exception as e:
            logger.error(f"Turkish NLP analysis error: {str(e)}")
            return self._fallback_analysis(text)

    def _clean_text(self, text: str) -> str:
        """Clean and normalize Turkish text"""

        # Unicode normalization
        text = unicodedata.normalize("NFKC", text)

        # Convert to lowercase
        text = text.lower()

        # Turkish character corrections
        replacements = {
            "ı": "ı",
            "i": "i",
            "ş": "ş",
            "ğ": "ğ",
            "ü": "ü",
            "ö": "ö",
            "ç": "ç",
            "İ": "i",
            "Ş": "ş",
            "Ğ": "ğ",
            "Ü": "ü",
            "Ö": "ö",
            "Ç": "ç",
        }

        for old, new in replacements.items():
            text = text.replace(old, new)

        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text).strip()

        # Remove excessive punctuation
        text = re.sub(r"[!]{3,}", "!!!", text)
        text = re.sub(r"[?]{3,}", "???", text)

        return text

    def _analyze_sentiment(self, text: str) -> Tuple[str, float]:
        """Analyze sentiment with Turkish-specific rules"""

        words = text.split()
        positive_score = 0
        negative_score = 0

        # Direct word matching
        for word in words:
            if word in self.positive_words:
                positive_score += self.positive_words[word]
            elif word in self.negative_words:
                negative_score += abs(self.negative_words[word])

        # Phrase matching
        for phrase, score in self.positive_words.items():
            if phrase in text:
                positive_score += score

        for phrase, score in self.negative_words.items():
            if phrase in text:
                negative_score += abs(score)

        # Negation handling
        negation_words = ["değil", "yok", "olmadı", "olmaz", "hayır"]
        for neg_word in negation_words:
            if neg_word in words:
                # Flip sentiment in context
                positive_score, negative_score = (
                    negative_score * 0.5,
                    positive_score * 0.5,
                )

        # Calculate final sentiment
        total_score = positive_score - negative_score

        if total_score > 0.3:
            sentiment = "positive"
        elif total_score < -0.3:
            sentiment = "negative"
        else:
            sentiment = "neutral"

        # Normalize score to -1 to 1 range
        normalized_score = max(-1, min(1, total_score))

        return sentiment, normalized_score

    def _detect_formality(self, text: str) -> str:
        """Detect formality level of Turkish text"""

        formal_count = sum(1 for indicator in self.formal_indicators if indicator in text)
        informal_count = sum(1 for indicator in self.informal_indicators if indicator in text)

        # Check for formal sentence structures
        formal_patterns = [
            r"gerekmektedir",
            r"bulunmaktadır",
            r"yapılmaktadır",
            r"edilmektedir",
            r"olunmaktadır",
        ]

        formal_structure_count = sum(1 for pattern in formal_patterns if re.search(pattern, text))

        total_formal = formal_count + formal_structure_count

        if total_formal > informal_count and total_formal > 0:
            return "formal"
        elif informal_count > 0:
            return "informal"
        else:
            return "neutral"

    def _detect_urgency(self, text: str) -> str:
        """Detect urgency level"""

        urgency_score = 0

        for keyword, score in self.urgent_keywords.items():
            if keyword in text:
                urgency_score += score

        # Check for time-sensitive phrases
        time_sensitive = [
            "bugün",
            "yarın",
            "hemen",
            "şimdi",
            "acele",
            "son dakika",
            "deadline",
            "son tarih",
            "geç kalıyor",
            "zaman kalmadı",
        ]

        for phrase in time_sensitive:
            if phrase in text:
                urgency_score += 0.3

        if urgency_score > 1.0:
            return "high"
        elif urgency_score > 0.5:
            return "medium"
        else:
            return "low"

    def _detect_emotional_intensity(self, text: str) -> str:
        """Detect emotional intensity"""

        intensity_score = 0

        # Check for intensity markers
        for marker in self.high_intensity_markers:
            if marker in text.upper():
                intensity_score += 1

        # Check for capitalization
        uppercase_ratio = sum(1 for c in text if c.isupper()) / len(text) if text else 0
        if uppercase_ratio > 0.3:
            intensity_score += 1

        # Check for repeated punctuation
        if "!!!" in text or "???" in text:
            intensity_score += 1

        # Check for repeated characters
        if re.search(r"(.)\1{2,}", text):
            intensity_score += 1

        if intensity_score >= 3:
            return "high"
        elif intensity_score >= 1:
            return "medium"
        else:
            return "low"

    def _extract_key_phrases(self, text: str) -> List[str]:
        """Extract key phrases from Turkish text"""

        # Remove stopwords and extract meaningful phrases
        words = text.split()
        filtered_words = [word for word in words if word not in self.turkish_stopwords]

        # Extract noun phrases (simplified)
        key_phrases = []

        # Add important single words
        important_words = [word for word in filtered_words if len(word) > 3]
        key_phrases.extend(important_words[:5])

        # Extract complaint-related phrases
        complaint_phrases = [
            "müşteri hizmetleri",
            "teknik destek",
            "ürün kalitesi",
            "teslimat sorunu",
            "ödeme problemi",
            "hesap sorunu",
            "şifre problemi",
            "giriş yapamıyorum",
            "çalışmıyor",
        ]

        for phrase in complaint_phrases:
            if phrase in text:
                key_phrases.append(phrase)

        return list(set(key_phrases))

    def _detect_grammar_errors(self, text: str) -> List[str]:
        """Detect common Turkish grammar errors (simplified)"""

        errors = []

        # Common Turkish grammar patterns
        error_patterns = {
            r"de\s+ki": "deki (bitişik yazılmalı)",
            r"bir\s+çok": "birçok (bitişik yazılmalı)",
            r"bir\s+şey": "birşey (bitişik yazılmalı)",
            r"ne\s+kadar": "nekadar (bitişik yazılmalı)",
            r"hiç\s+bir": "hiçbir (bitişik yazılmalı)",
        }

        for pattern, suggestion in error_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                errors.append(suggestion)

        return errors

    def _suggest_response_tone(self, sentiment: str, formality: str, urgency: str) -> str:
        """Suggest appropriate response tone"""

        if sentiment == "negative" and urgency == "high":
            return "empathetic_urgent"
        elif sentiment == "negative":
            return "empathetic_professional"
        elif formality == "formal":
            return "professional_formal"
        elif urgency == "high":
            return "prompt_professional"
        else:
            return "friendly_professional"

    def _analyze_cultural_context(self, text: str) -> Dict:
        """Analyze Turkish cultural context"""

        context = {
            "religious_references": False,
            "respect_forms_used": False,
            "politeness_level": "medium",
            "regional_dialect": None,
            "generation_indicator": None,
        }

        # Check for religious references
        if any(ref in text for ref in self.cultural_patterns["religious_references"]):
            context["religious_references"] = True

        # Check for respect forms
        if any(form in text for form in self.cultural_patterns["respect_forms"]):
            context["respect_forms_used"] = True

        # Determine politeness level
        politeness_indicators = sum(
            1 for softener in self.cultural_patterns["complaint_softeners"] if softener in text
        )

        if politeness_indicators > 1:
            context["politeness_level"] = "high"
        elif politeness_indicators == 1:
            context["politeness_level"] = "medium"
        else:
            context["politeness_level"] = "low"

        # Detect generational language patterns
        young_indicators = ["süper", "harika", "çok iyi", "mükemmel", "bayıldım"]
        old_indicators = ["memnun kaldım", "teşekkür ederim", "saygılarımla"]

        young_count = sum(1 for ind in young_indicators if ind in text)
        old_count = sum(1 for ind in old_indicators if ind in text)

        if young_count > old_count:
            context["generation_indicator"] = "younger"
        elif old_count > young_count:
            context["generation_indicator"] = "older"

        return context

    def _fallback_analysis(self, text: str) -> TurkishTextAnalysis:
        """Fallback analysis when main processing fails"""

        return TurkishTextAnalysis(
            original_text=text,
            cleaned_text=text.lower(),
            sentiment="neutral",
            sentiment_score=0.0,
            formality_level="neutral",
            urgency_level="medium",
            emotional_intensity="medium",
            key_phrases=[],
            grammar_errors=[],
            suggested_response_tone="professional",
            cultural_context={"politeness_level": "medium"},
        )

    def generate_response_template(self, analysis: TurkishTextAnalysis) -> str:
        """Generate appropriate Turkish response template"""

        templates = {
            "empathetic_urgent": """
                Sayın Müşterimiz,
                
                Yaşadığınız bu sorunu çok iyi anlıyor ve durumdan dolayı özür diliyoruz.
                Konunuz acil olarak ilgili departmanımıza iletilmiş olup, en kısa sürede
                çözüm için sizinle iletişime geçilecektir.
                
                Bu süreçte herhangi bir sorunuz olursa lütfen bizimle iletişime geçin.
                
                Saygılarımla,
                Müşteri Hizmetleri
            """,
            "empathetic_professional": """
                Sayın Müşterimiz,
                
                Yaşadığınız sorunu anlıyoruz ve bu konudaki endişenizi paylaşıyoruz.
                Durumunuz titizlikle incelenerek size en uygun çözümü sunmaya çalışacağız.
                
                Yakın zamanda sizinle iletişime geçilerek konu hakkında bilgi verilecektir.
                
                Anlayışınız için teşekkür ederiz.
                
                Saygılarımla,
                Müşteri Hizmetleri
            """,
            "professional_formal": """
                Sayın Müşterimiz,
                
                Talebiniz kayıt altına alınmıştır. Konunuz ilgili uzman ekibimiz
                tarafından değerlendirilecek ve size dönüş yapılacaktır.
                
                Değerli zamanınız için teşekkür ederiz.
                
                Saygılarımla,
                Müşteri Hizmetleri Departmanı
            """,
            "friendly_professional": """
                Merhaba,
                
                Bizimle paylaştığınız konu için teşekkür ederiz. 
                Konunuz incelenerek en kısa sürede size geri dönüş yapacağız.
                
                İyi günler dileriz.
                
                Müşteri Hizmetleri Ekibi
            """,
        }

        return templates.get(analysis.suggested_response_tone, templates["friendly_professional"])


# Global instance
turkish_nlp = TurkishNLPProcessor()
