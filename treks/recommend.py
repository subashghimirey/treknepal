import spacy
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from .models import Trek

# Load spaCy medium model once (this will load ~100MB)
nlp = spacy.load("en_core_web_md")

def average_spacy_vector(words, nlp):
    """
    Given a list of words, return the average vector.
    Ignores words not in the spaCy vocab.
    """
    vectors = [nlp(word).vector for word in words if nlp(word).has_vector]
    if not vectors:
        return np.zeros(nlp.vocab.vectors_length)
    return np.mean(vectors, axis=0)

def flatten_list(json_list):
    """
    Flattens JSONFields that may be list of strings or list of dicts.
    """
    if not json_list:
        return []
    flattened = []
    for item in json_list:
        if isinstance(item, dict):
            flattened.extend(str(v) for v in item.values())
        else:
            flattened.append(str(item))
    return flattened

def recommend_treks(user_profile, top_n=6):
    """
    Recommends top N treks based on cosine similarity between
    user interest vector and trek content vectors.
    """
    if not user_profile.interests:
        return Trek.objects.none()

    user_words = [word.lower() for word in user_profile.interests]
    user_vector = average_spacy_vector(user_words, nlp)

    treks = list(Trek.objects.all())
    similarities = []

    for trek in treks:
        combined_text = [
            trek.name or '',
            trek.duration or '',
            trek.difficulty or '',
            trek.description or '',
            trek.historical_significance or '',
            " ".join(flatten_list(trek.nearby_attractions)),
            " ".join(flatten_list(trek.tags)),
        ]
        words = " ".join(combined_text).lower().split()
        trek_vector = average_spacy_vector(words, nlp)
        score = cosine_similarity([user_vector], [trek_vector])[0][0]
        similarities.append((trek, score))

    similarities.sort(key=lambda x: x[1], reverse=True)
    recommendations = [trek for trek, score in similarities if score > 0][:top_n]

    print(f"Recommended {len(recommendations)} treks for user {user_profile.user.username} based on interests: {user_profile.interests}")
    return recommendations
