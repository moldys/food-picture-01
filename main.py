# food-picture-01 entry (Python 3.13, standard library only): copies the committed
# PNG to /output/entry.png. Deterministic — both runs write the same bytes.
import os, shutil

here = os.path.dirname(os.path.abspath(__file__))
out = os.environ.get('MAKEFUN_OUTPUT_DIR', '/output')
os.makedirs(out, exist_ok=True)
src = os.path.join(here, 'entry.png')
dst = os.path.join(out, 'entry.png')
shutil.copyfile(src, dst)  # same bytes every run
