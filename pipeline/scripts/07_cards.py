from olp.aggregate.cards import build_labour
import os
d = build_labour(); sizes = [os.path.getsize(d / f) for f in os.listdir(d)]; print(d, len(sizes), "png; max", max(sizes) // 1024, "KB")
