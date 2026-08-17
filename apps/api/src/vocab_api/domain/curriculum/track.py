from enum import StrEnum


class Track(StrEnum):
    GRAMMAR = "grammar"
    VOCABULARY = "vocabulary"
    PHRASAL_VERBS = "phrasal_verbs"
    COLLOCATIONS = "collocations"
    IDIOMS = "idioms"
    BUSINESS = "business"
    FUNCTIONS = "functions"  # reserved: no v1 modules authored