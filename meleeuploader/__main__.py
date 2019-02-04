import sys

from .main import main, ult

if any(x in sys.argv for x in ("ult", "ultimate", "smash5", "sm5sh")):
    ult()
else:
    main()
