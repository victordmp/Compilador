import tppparser
import tppsema
from tppgencode import GenCode

if __name__ == "__main__":
    tppparser.main()
    if tppparser.root != None and tppparser.root.children != ():
        # Análise semantica
        tppsema.root = tppparser.root
        # tppsema.checkRules()
        tppsema.pruneTree()

        # Geração de código
        GenCode().declaration(tppsema.root)