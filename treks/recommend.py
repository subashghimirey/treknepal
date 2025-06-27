
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from .models import Trek

def recommend_treks(user_profile, top_n=6):
    if not user_profile.interests:
        return Trek.objects.none()

    SYNONYMS = {
    "mountains": ["mountain", "hill", "range", "ridge"],
    "culture": ["heritage", "tradition", "cultural"],
    "view": ["sight", "scenery", "landscape", "panorama"],
    "adventure": ["exploration", "expedition", "journey", "quest"],
    "nature": ["wildlife", "flora", "fauna", "environment"],
}

    def expand_interests(interests):
        expanded = []
        for word in interests:
            expanded.extend(SYNONYMS.get(word.lower(), [word]))
        return expanded

    user_words = expand_interests(user_profile.interests)
    user_text = " ".join(user_words).lower()

    treks = list(Trek.objects.all())
 
    corpus = [
    f"{trek.name or ''} {trek.region or ''} {trek.difficulty or ''} "
    f"{trek.description or ''} {' '.join(trek.tags or [])}".lower()
    for trek in treks
    ]

    corpus.append(user_text)

    tfidf = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf.fit_transform(corpus)

    user_vector = tfidf_matrix[-1]
    trek_vectors = tfidf_matrix[:-1]

    print(f"user_vector shape: {user_vector.shape} | trek_vectors shape: {trek_vectors.shape}")

    similarities = cosine_similarity(user_vector, trek_vectors).flatten()

    print(f"Similarities: {similarities}")

    sorted_indices = similarities.argsort()[::-1]

    recommendations = []
    for idx in sorted_indices[:top_n]:
        if similarities[idx] > 0.1:
            recommendations.append(treks[idx])

    print(f"Recommended {len(recommendations)} treks for user {user_profile.user.username} based on interests: {user_profile.interests}")
    return recommendations
