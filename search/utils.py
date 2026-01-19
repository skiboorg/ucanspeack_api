from django.db.models import Q
from django.contrib.postgres.search import TrigramSimilarity

def get_attr(obj, path):
    for p in path.split("__"):
        obj = getattr(obj, p)
        if obj is None:
            return None
    return obj

def perform_search(model, fields, values, query, request, limit=20):
    q_filter = Q()
    for f in fields:
        q_filter |= Q(**{f"{f}__icontains": query})

    qs = model.objects.filter(q_filter)

    similarity = None
    for f in fields:
        s = TrigramSimilarity(f, query)
        similarity = s if similarity is None else similarity + s

    qs = qs.annotate(rank=similarity).order_by("-rank")

    result = []

    for obj in qs[:limit]:
        row = {}

        for f in values:
            val = get_attr(obj, f)

            # Если это FileField / ImageField → делаем АБСОЛЮТНЫЙ URL
            if hasattr(val, "url") and val:
                row[f] = request.build_absolute_uri(val.url)
            else:
                row[f] = val

        result.append(row)

    return result
