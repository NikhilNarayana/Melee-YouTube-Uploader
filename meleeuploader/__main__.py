import sys

from .main import main, ult, s64, rivals, splatoon

print(sys.argv)

if any(x in sys.argv for x in ("ult", "ultimate", "smash5", "sm5sh")):
    ult()
elif any(x in sys.argv for x in ("s64", "64", "ssb")):
    s64()
elif any(x in sys.argv for x in ("rivals", "roa", "rivalsofaether")):
    rivals()
elif any(x in sys.argv for x in ("splatoon", "splat")):
    splatoon()
else:
    main()
