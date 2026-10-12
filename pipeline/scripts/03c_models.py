from olp.models import run_all
from olp.build_person import load_person
from olp.derive import derive
run_all(load_person, derive)
