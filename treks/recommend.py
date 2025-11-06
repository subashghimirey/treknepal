import spacy
import numpy as np
from .models import Trek

# Load spaCy medium model once
nlp = spacy.load("en_core_web_md")

# Simple in-memory cache to avoid recalculating trek vectors
trek_vector_cache = {}

def compute_average_vector_from_text(text):

    doc = nlp(text.lower())
    vectors = [token.vector for token in doc if token.has_vector and not token.is_stop and not token.is_punct]
    return np.mean(vectors, axis=0) if vectors else np.zeros(nlp.vocab.vectors_length)

def flatten_list(json_list):

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
                # trek.name or '',
                # trek.duration or '',
                trek.difficulty or '',
                trek.description or '',
                trek.historical_significance or '',
                " ".join(flatten_list(trek.nearby_attractions)),
                " ".join(flatten_list(trek.tags)),
            ])
            trek_vector = compute_average_vector_from_text(combined_text)

            trek_vector_cache[trek_id] = trek_vector

 
        if np.linalg.norm(trek_vector) == 0:
            continue


        dot_product = np.dot(user_vector, trek_vector)
        magnitude_user = np.sqrt(np.sum(user_vector ** 2))
        magnitude_trek = np.sqrt(np.sum(trek_vector ** 2))
        
  
        if magnitude_user == 0 or magnitude_trek == 0:
            score = 0.0
        else:
            score = dot_product / (magnitude_user * magnitude_trek)

        similarities.append((trek, score))
    
    i=0
    for trek, score in similarities:
        print(f"Trek {i} : {trek.name}, Similarity Score: {score}")
        i+=1

    similarities.sort(key=lambda x: x[1], reverse=True)

    print(f"Computed similarities for {len(similarities)} treks.")
    print(f"Top similarity scores: {[score for trek, score in similarities[:top_n]]}")

    recommendations = [trek for trek, score in similarities if score > 0][:top_n]

    print(f"Recommended {len(recommendations)} treks for user {user_profile.user.username} based on interests: {user_profile.interests}")
    print(f"Recommended Treks: {[trek.name for trek in recommendations]}")
    return recommendations