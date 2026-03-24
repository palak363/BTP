def compute_score(papers):
    score = 0

    for p in papers:
        try:
            year = int(p["year"])

            if year >= 2020:
                score += 2
            else:
                score += 1

        except:
            continue

    return score