import sys

from .main import main, ult, s64, rivals, splatoon

print(sys.argv)

if any(("ult", "ultimate", "smash5", "sm5sh")):
    ult()
elif any(("s64", "64", "ssb")):
    s64()
elif any(("rivals", "roa", "rivalsofaether")):
    rivals()
elif any(("splatoon", "splat")):
    splatoon()
else:
    main()
