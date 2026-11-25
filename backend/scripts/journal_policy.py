"""Visibility policy for ACM and IEEE journal articles in bibliographies."""
import re

TRANSACTION_PUBLISHERS = {
    'ieee': re.compile(r'^IEEE\s+(?:Trans\.(?:\s|$)|Transactions?\b)', re.IGNORECASE),
    'acm': re.compile(r'^ACM\s+(?:Trans\.(?:\s|$)|Transactions?\b)', re.IGNORECASE),
}
ACM_IEEE_JOURNAL_NAME = re.compile(r'^(?:ACM|IEEE|Proc\.\s*ACM|J\.\s*ACM)\b', re.IGNORECASE)
ACM_IEEE_DOI_PREFIXES = ('10.1145/', '10.1109/')


def is_acm_or_ieee_journal(paper):
    """Use DBLP venue text and DOI prefixes; conference records are unaffected."""
    if paper.get('type') != 'article':
        return False
    venue = paper.get('journal') or paper.get('venue') or ''
    return bool(ACM_IEEE_JOURNAL_NAME.match(venue) or any(
        doi.lower().startswith(ACM_IEEE_DOI_PREFIXES) for doi in paper.get('dois', [])))


def is_transaction_journal(paper):
    """Whether an article belongs to an ACM or IEEE Transactions journal."""
    return transaction_publisher(paper) is not None


def transaction_publisher(paper):
    """Return the publisher for a Transactions article, or None."""
    if paper.get('type') != 'article':
        return None
    venue = paper.get('journal') or paper.get('venue') or ''
    for publisher, pattern in TRANSACTION_PUBLISHERS.items():
        if pattern.match(venue):
            return publisher
    return None


def is_visible_paper(paper):
    """Allow ranked papers and ACM/IEEE journal articles in Transactions series."""
    if any(item.get('source') in {'csrankings', 'core-a-star', 'core-a'}
           for item in paper.get('memberships', [])):
        return True
    if not is_acm_or_ieee_journal(paper):
        return True
    return is_transaction_journal(paper)
