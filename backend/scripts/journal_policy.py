"""Visibility policy for ACM and IEEE journal articles in bibliographies."""
import re

TRANSACTION_JOURNAL = re.compile(r'^(?:ACM|IEEE)\s+Trans\.', re.IGNORECASE)
ACM_IEEE_JOURNAL_NAME = re.compile(r'^(?:ACM|IEEE|Proc\.\s*ACM|J\.\s*ACM)\b', re.IGNORECASE)
ACM_IEEE_DOI_PREFIXES = ('10.1145/', '10.1109/')


def is_acm_or_ieee_journal(paper):
    """Use DBLP venue text and DOI prefixes; conference records are unaffected."""
    if paper.get('type') != 'article':
        return False
    venue = paper.get('journal') or paper.get('venue') or ''
    return bool(ACM_IEEE_JOURNAL_NAME.match(venue) or any(
        doi.lower().startswith(ACM_IEEE_DOI_PREFIXES) for doi in paper.get('dois', [])))


def is_visible_paper(paper):
    """Allow ACM/IEEE journal articles only when published in a Transactions series."""
    if not is_acm_or_ieee_journal(paper):
        return True
    venue = paper.get('journal') or paper.get('venue') or ''
    return bool(TRANSACTION_JOURNAL.match(venue))
