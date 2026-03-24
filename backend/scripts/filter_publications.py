TOP_VENUES = [
    "ICML", "NeurIPS", "CVPR", "ACL",
    "KDD", "AAAI", "IJCAI"
]

def is_top_venue(venue):
    return any(v in venue for v in TOP_VENUES)