STATUS_LABELS = {"ava": "available", "sold": "sold", "ref": "refunded", "sale": "sold (sale)"}


def label_status(status):
    return STATUS_LABELS.get(status, status)
