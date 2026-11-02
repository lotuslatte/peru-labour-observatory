from olp.aggregate.territory import build
p = build(); print(p, p.stat().st_size // 1024, "kB")
