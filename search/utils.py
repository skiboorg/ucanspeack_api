from django.db.models import Q
from django.contrib.postgres.search import TrigramSimilarity


def perform_search(model, fields, values, query, limit=20):
    q_filter = Q()

    for f in fields:
        q_filter |= Q(**{f"{f}__icontains": query})

    qs = model.objects.filter(q_filter)

    similarity = None
    for f in fields:
        s = TrigramSimilarity(f, query)
        similarity = s if similarity is None else similarity + s

    qs = qs.annotate(rank=similarity).order_by("-rank")

    return list(qs.values(*values)[:limit])
