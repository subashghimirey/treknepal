import spacy
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from .models import Trek

# Load spaCy medium model once
nlp = spacy.load("en_core_web_md")

# Simple in-memory cache to avoid recalculating trek vectors
trek_vector_cache = {}

def compute_average_vector_from_text(text):
    """
    Processes the full text and averages token vectors,
    excluding stop words, punctuation, and non-vector tokens.
    """
    doc = nlp(text.lower())
    vectors = [token.vector for token in doc if token.has_vector and not token.is_stop and not token.is_punct]
    return np.mean(vectors, axis=0) if vectors else np.zeros(nlp.vocab.vectors_length)

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
    Uses caching for trek vectors to speed up recommendations.
    """
    if not user_profile.interests:
        return Trek.objects.none()

    # Compute user vector
    user_text = " ".join(user_profile.interests)
    user_vector = compute_average_vector_from_text(user_text)

    # If user vector is empty, return nothing
    if np.linalg.norm(user_vector) == 0:
        return Trek.objects.none()

    treks = list(Trek.objects.all())
    similarities = []

    for trek in treks:
        trek_id = trek.id

        # Retrieve or compute trek vector
        if trek_id in trek_vector_cache:
            trek_vector = trek_vector_cache[trek_id]
        else:
            combined_text = " ".join([
                trek.name or '',
                trek.duration or '',
                trek.difficulty or '',
                trek.description or '',
                trek.historical_significance or '',
                " ".join(flatten_list(trek.nearby_attractions)),
                " ".join(flatten_list(trek.tags)),
            ])
            trek_vector = compute_average_vector_from_text(combined_text)
            trek_vector_cache[trek_id] = trek_vector

        # Skip zero vectors (meaning no meaningful content)
        if np.linalg.norm(trek_vector) == 0:
            continue

        # Compute cosine similarity
        score = cosine_similarity([user_vector], [trek_vector])[0][0]
        similarities.append((trek, score))

    # Sort by similarity
    similarities.sort(key=lambda x: x[1], reverse=True)
    recommendations = [trek for trek, score in similarities if score > 0][:top_n]

    print(f"Recommended {len(recommendations)} treks for user {user_profile.user.username} based on interests: {user_profile.interests}")
    return recommendations
