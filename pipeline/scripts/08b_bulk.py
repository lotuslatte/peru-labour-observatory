from olp.aggregate.bulk import build
rows, size = build(); print(rows, "rows", size // 2**20, "MB")
