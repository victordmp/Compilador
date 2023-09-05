import os
from sys import argv
import logging

logging.basicConfig(
     level = logging.DEBUG,
     filename = "parser.log",
     filemode = "w",
     format = "%(filename)10s:%(lineno)4d:%(message)s"
)
log = logging.getLogger()

import ply.yacc as yacc
# Get the token map from the lexer.  This is required.
from tpplex import tokens
import tppsema
from mytree import MyNode
from anytree.exporter import DotExporter, UniqueDotExporter
from myerror import MyError

error_handler = MyError('ParserErrors', showErrorMessage=True)
root = None

# Sub-árvore.
#       (programa)
#           |
#   (lista_declaracoes)
#     /     |      \
#   ...    ...     ...

def p_programa(p):
    """programa : lista_declaracoes"""

    global root

    programa = MyNode(name='programa', type='PROGRAMA', line=p.lexer.lineno)

    root = programa
    p[0] = programa
    p[1].parent = programa

#    (lista_declaracoes)                          (lista_declaracoes)
#          /           \                                    |
# (lista_declaracoes)  (declaracao)                    (declaracao)


def p_lista_declaracoes(p):
    """lista_declaracoes : lista_declaracoes declaracao
                        | declaracao
    """
    pai = MyNode(name='lista_declaracoes', type='LISTA_DECLARACOES', line=p.lexer.lineno)
    p[0] = pai
    p[1].parent = pai

    if len(p) > 2:
        p[2].parent = pai

def p_lista_declaracoes_error(p):
    """lista_declaracoes : error declaracao
                        | lista_declaracoes error
    """
    error_type = 'ERR-SYN-LISTA-DECLARACOES'
    error_name = error_handler.newError(error_type)
    print(error_name)
    pai = MyNode(name=error_name, type=error_type, line=p.lexer.lineno)
    p[0] = pai

# Sub-árvore.
#      (declaracao)
#           |
#  (declaracao_variaveis ou
#   inicializacao_variaveis ou
#   declaracao_funcao)


def p_declaracao(p):
    """declaracao : declaracao_variaveis
                | inicializacao_variaveis
                | declaracao_funcao
    """
    pai = MyNode(name='declaracao', type='DECLARACAO', line=p.lexer.lineno)
    p[0] = pai
    p[1].parent = pai

# Sub-árvore.
#      (declaracao_variaveis)
#      / p[1]    |           \
# (tipo)    (DOIS_PONTOS)    (lista_variaveis)
#                |
#               (:)


def p_declaracao_variaveis(p):
    """declaracao_variaveis : tipo DOIS_PONTOS lista_variaveis"""
    pai = MyNode(name='declaracao_variaveis', type='DECLARACAO_VARIAVEIS', line=p.lexer.lineno)
    p[0] = pai

    p[1].parent = pai

    filho = MyNode(name='DOIS_PONTOS', type='DOIS_PONTOS', parent=pai, line=p.lexer.lineno)
    filho_sym = MyNode(name=p[2], type='SIMBOLO', parent=filho, line=p.lexer.lineno)
    p[2] = filho

    p[3].parent = pai

def p_declaracao_variavais_error(p):
    """declaracao_variaveis : error DOIS_PONTOS lista_variaveis
                            | tipo error lista_variaveis
                            | tipo DOIS_PONTOS error
    """
    error_type = 'ERR-SYN-LISTA-DECLARACAO-VARIAVEIS'
    error_name = error_handler.newError(error_type)
    print(error_name)
    pai = MyNode(name=error_name, type=error_type, line=p.lexer.lineno)
    p[0] = pai

# Sub-árvore.
#   (inicializacao_variaveis)
#              |
#         (atribuicao)


def p_inicializacao_variaveis(p):
    """inicializacao_variaveis : atribuicao"""

    pai = MyNode(name='inicializacao_variaveis', type='INICIALIZACAO_VARIAVEIS', line=p.lexer.lineno)
    p[0] = pai
    p[1].parent = pai

def p_lista_variaveis(p):
    """lista_variaveis : lista_variaveis VIRGULA var
                        | var
    """
    pai = MyNode(name='lista_variaveis', type='LISTA_VARIAVEIS', line=p.lexer.lineno)
    p[0] = pai
    if len(p) > 2:
        p[1].parent = pai
        filho = MyNode(name='virgula', type='VIRGULA', parent=pai, line=p.lexer.lineno)
        filho_sym = MyNode(name=',', type='SIMBOLO', parent=filho, line=p.lexer.lineno)
        p[3].parent = pai
    else:
       p[1].parent = pai

def p_lista_variaveis_error(p):
    """lista_variaveis : error VIRGULA var
                        | lista_variaveis error var
                        | lista_variaveis VIRGULA error
    """
    error_type = 'ERR-SYN-LISTA-VARIAVEIS'
    error_name = error_handler.newError(error_type)
    print(error_name)
    pai = MyNode(name=error_name, type=error_type, line=p.lexer.lineno)
    p[0] = pai

def p_var(p):
    """var : ID
            | ID indice
    """
    pai = MyNode(name='var', type='VAR', line=p.lexer.lineno)
    p[0] = pai
    filho = MyNode(name='ID', type='ID', parent=pai, line=p.lexer.lineno)
    filho_id = MyNode(name=p[1], type='ID', parent=filho, line=p.lexer.lineno)
    p[1] = filho
    if len(p) > 2:
        p[2].parent = pai

def p_var_error(p):
    """var : error indice
            | ID error
    """
    error_type = 'ERR-SYN-VAR'
    error_name = error_handler.newError(error_type)
    print(error_name)
    pai = MyNode(name=error_name, type=error_type, line=p.lexer.lineno)
    p[0] = pai    

def p_indice(p):
    """indice : indice ABRE_COLCHETE expressao FECHA_COLCHETE
                | ABRE_COLCHETE expressao FECHA_COLCHETE
    """
    pai = MyNode(name='indice', type='INDICE', line=p.lexer.lineno)
    p[0] = pai
    if len(p) == 5:
        p[1].parent = pai   # indice

        filho2 = MyNode(name='abre_colchete', type='ABRE_COLCHETE', parent=pai, line=p.lexer.lineno)
        filho_sym2 = MyNode(name=p[2], type='SIMBOLO', parent=filho2, line=p.lexer.lineno)
        p[2] = filho2

        p[3].parent = pai  # expressao

        filho4 = MyNode(name='fecha_colchete', type='FECHA_COLCHETE', parent=pai, line=p.lexer.lineno)
        filho_sym4 = MyNode(name=p[4], type='SIMBOLO', parent=filho4, line=p.lexer.lineno)
        p[4] = filho4
    else:
        filho1 = MyNode(name='abre_colchete', type='ABRE_COLCHETE', parent=pai, line=p.lexer.lineno)
        filho_sym1 = MyNode(name=p[1], type='SIMBOLO', parent=filho1, line=p.lexer.lineno)
        p[1] = filho1

        p[2].parent = pai  # expressao

        filho3 = MyNode(name='fecha_colchete', type='FECHA_COLCHETE', parent=pai, line=p.lexer.lineno)
        filho_sym3 = MyNode(name=p[3], type='SIMBOLO', parent=filho3, line=p.lexer.lineno)
        p[3] = filho3

def p_indice_error(p):
    """indice : error ABRE_COLCHETE expressao FECHA_COLCHETE
                | indice error expressao FECHA_COLCHETE
                | indice ABRE_COLCHETE error FECHA_COLCHETE
                | indice ABRE_COLCHETE expressao error
                | indice ABRE_COLCHETE error
                | error expressao FECHA_COLCHETE
                | ABRE_COLCHETE error FECHA_COLCHETE
                | ABRE_COLCHETE expressao error
                | ABRE_COLCHETE error
    """
    error_type = 'ERR-SYN-INDICE'
    error_name = error_handler.newError(error_type)
    print(error_name)
    pai = MyNode(name=error_name, type=error_type, line=p.lexer.lineno)
    p[0] = pai

# Sub-árvore:
#    (tipo)
#      |
#  (FLUTUANTE)
def p_tipo(p):
    """tipo : INTEIRO
        | FLUTUANTE
    """

    pai = MyNode(name='tipo', type='TIPO', line=p.lexer.lineno)
    p[0] = pai
    # p[1] = MyNode(name=p[1], type=p[1].upper(), parent=pai, line=p.lexer.lineno)

    if p[1] == "inteiro":
        filho1 = MyNode(name='INTEIRO', type='INTEIRO', parent=pai, line=p.lexer.lineno)
        filho_sym = MyNode(name=p[1], type=p[1].upper(), parent=filho1, line=p.lexer.lineno)
        p[1] = filho1
    else:
        filho1 = MyNode(name='FLUTUANTE', type='FLUTUANTE', parent=pai, line=p.lexer.lineno)
        filho_sym = MyNode(name=p[1], type=p[1].upper(), parent=filho1, line=p.lexer.lineno)

def p_declaracao_funcao(p):
    """declaracao_funcao : tipo cabecalho 
                        | cabecalho 
    """
    pai = MyNode(name='declaracao_funcao', type='DECLARACAO_FUNCAO', line=p.lexer.lineno)
    p[0] = pai
    p[1].parent = pai

    if len(p) == 3:
        p[2].parent = pai

def p_declaracao_funcao_error(p):
    """declaracao_funcao : error cabecalho 
                        | tipo error
    """
    error_type = 'ERR-SYN-DECLARACAO-FUNCAO'
    error_name = error_handler.newError(error_type)
    print(error_name)
    pai = MyNode(name=error_name, type=error_type, line=p.lexer.lineno)
    p[0] = pai

def p_cabecalho(p):
    """cabecalho : ID ABRE_PARENTESE lista_parametros FECHA_PARENTESE corpo FIM"""

    pai = MyNode(name='cabecalho', type='CABECALHO', line=p.lexer.lineno)
    p[0] = pai

    filho1 = MyNode(name='ID', type='ID', parent=pai, line=p.lexer.lineno)
    filho_id = MyNode(name=p[1], type='ID', parent=filho1, line=p.lexer.lineno)
    p[1] = filho1

    filho2 = MyNode(name='ABRE_PARENTESE', type='ABRE_PARENTESE', parent=pai, line=p.lexer.lineno)
    filho_sym2 = MyNode(name='(', type='SIMBOLO', parent=filho2, line=p.lexer.lineno)
    p[2] = filho2

    p[3].parent = pai  # lista_parametros

    filho4 = MyNode(name='FECHA_PARENTESE', type='FECHA_PARENTESE', parent=pai, line=p.lexer.lineno)
    filho_sym4 = MyNode(name=')', type='SIMBOLO', parent=filho4, line=p.lexer.lineno)
    p[4] = filho4

    p[5].parent = pai  # corpo

    filho6 = MyNode(name='FIM', type='FIM', parent=pai, line=p.lexer.lineno)
    filho_id = MyNode(name='fim', type='FIM', parent=filho6, line=p.lexer.lineno)
    p[6] = filho6


def p_cabecalho_error(p):
    """cabecalho : error ABRE_PARENTESE lista_parametros FECHA_PARENTESE corpo FIM
                | ID error lista_parametros FECHA_PARENTESE corpo FIM
                | ID ABRE_PARENTESE error FECHA_PARENTESE corpo FIM
                | ID ABRE_PARENTESE lista_parametros error corpo FIM
                | ID ABRE_PARENTESE lista_parametros FECHA_PARENTESE error FIM
                | ID ABRE_PARENTESE lista_parametros FECHA_PARENTESE corpo error
                | ID ABRE_PARENTESE lista_parametros FECHA_PARENTESE corpo
    """
    error_type = 'ERR-SYN-CABECALHO'
    error_name = error_handler.newError(error_type)
    print(error_name)
    pai = MyNode(name=error_name, type=error_type, line=p.lexer.lineno)
    p[0] = pai


def p_lista_parametros(p):
    """lista_parametros : lista_parametros VIRGULA parametro
                    | parametro
                    | vazio
    """

    pai = MyNode(name='lista_parametros', type='LISTA_PARAMETROS', line=p.lexer.lineno)
    p[0] = pai
    p[1].parent = pai

    if len(p) > 2:
        filho2 = MyNode(name='virgula', type='VIRGULA', parent=pai, line=p.lexer.lineno)
        filho_sym2 = MyNode(name=',', type='SIMBOLO', parent=filho2, line=p.lexer.lineno)
        p[2] = filho2
        p[3].parent = pai

def p_lista_parametros_error(p):
    """lista_parametros : error VIRGULA parametro
                | lista_parametros error parametro
                | lista_parametros VIRGULA error
    """
    error_type = 'ERR-SYN-LISTA-PARAMETROS'
    error_name = error_handler.newError(error_type)
    print(error_name)
    pai = MyNode(name=error_name, type=error_type, line=p.lexer.lineno)
    p[0] = pai

def p_parametro(p):
    """parametro : tipo DOIS_PONTOS ID
                | parametro ABRE_COLCHETE FECHA_COLCHETE
    """

    pai = MyNode(name='parametro', type='PARAMETRO', line=p.lexer.lineno)
    p[0] = pai
    p[1].parent = pai

    if p[2] == ':':
        filho2 = MyNode(name='DOIS_PONTOS', type='DOIS_PONTOS', parent=pai, line=p.lexer.lineno)
        filho_sym2 = MyNode(name=':', type='SIMBOLO', parent=filho2, line=p.lexer.lineno)
        p[2] = filho2

        filho3 = MyNode(name='id', type='ID', parent=pai, line=p.lexer.lineno)
        filho_id = MyNode(name=p[3], type='ID', parent=filho3, line=p.lexer.lineno)
    else:
        filho2 = MyNode(name='abre_colchete', type='ABRE_COLCHETE', parent=pai, line=p.lexer.lineno)
        filho_sym2 = MyNode(name='[', type='SIMBOLO', parent=filho2, line=p.lexer.lineno)
        p[2] = filho2

        filho3 = MyNode(name='fecha_colchete', type='FECHA_COLCHETE', parent=pai, line=p.lexer.lineno)
        filho_sym3 = MyNode(name=']', type='SIMBOLO', parent=filho3, line=p.lexer.lineno)
        p[3] = filho3


def p_parametro_error(p):
    """parametro : error DOIS_PONTOS ID
                | tipo error ID
                | tipo DOIS_PONTOS error
                | error ABRE_COLCHETE FECHA_COLCHETE
                | parametro error FECHA_COLCHETE
                | parametro ABRE_COLCHETE error
    """
    error_type = 'ERR-SYN-PARAMETRO'
    error_name = error_handler.newError(error_type)
    print(error_name)
    pai = MyNode(name=error_name, type=error_type, line=p.lexer.lineno)
    p[0] = pai

def p_corpo(p):
    """corpo : corpo acao
            | vazio
    """

    pai = MyNode(name='corpo', type='CORPO', line=p.lexer.lineno)
    p[0] = pai
    p[1].parent = pai

    if len(p) > 2:
        p[2].parent = pai

def p_corpo_error(p):
    """corpo : error acao
            | corpo error
    """
    error_type = 'ERR-SYN-CORPO'
    error_name = error_handler.newError(error_type)
    print(error_name)
    pai = MyNode(name=error_name, type=error_type, line=p.lexer.lineno)
    p[0] = pai

def p_acao(p):
    """acao : expressao
        | declaracao_variaveis
        | se
        | repita
        | leia
        | escreva
        | retorna
    """
    pai = MyNode(name='acao', type='ACAO', line=p.lexer.lineno)
    p[0] = pai
    p[1].parent = pai

# Sub-árvore:
#       ________ (se) ________________________________
#      /    /          \      \         \      \      \
# (SE) (expressao)  (ENTAO)  (corpo) (SENAO) (corpo) (FIM)
#  |       |           |
# (se)   (...)      (então) ....


def p_se(p):
    """se : SE expressao ENTAO corpo FIM
          | SE expressao ENTAO corpo SENAO corpo FIM
    """

    pai = MyNode(name='se', type='SE', line=p.lexer.lineno)
    p[0] = pai

    filho1 = MyNode(name='SE', type='SE', parent=pai, line=p.lexer.lineno)
    filho_se = MyNode(name=p[1], type='SE', parent=filho1, line=p.lexer.lineno)
    p[1] = filho1

    p[2].parent = pai

    filho3 = MyNode(name='ENTAO', type='ENTAO', parent=pai, line=p.lexer.lineno)
    filho_entao = MyNode(name=p[3], type='ENTAO', parent=filho3, line=p.lexer.lineno)
    p[3] = filho3

    p[4].parent = pai

    if len(p) == 8:
        filho5 = MyNode(name='SENAO', type='SENAO', parent=pai, line=p.lexer.lineno)
        filho_senao = MyNode(name=p[5], type='SENAO', parent=filho5, line=p.lexer.lineno)
        p[5] = filho5

        p[6].parent = pai

        filho7 = MyNode(name='FIM', type='FIM', parent=pai, line=p.lexer.lineno)
        filho_fim = MyNode(name=p[7], type='FIM', parent=filho7, line=p.lexer.lineno)
        p[7] = filho7
    else:
        filho5 = MyNode(name='fim', type='FIM', parent=pai, line=p.lexer.lineno)
        filho_fim = MyNode(name=p[5], type='FIM', parent=filho5, line=p.lexer.lineno)
        p[5] = filho5


def p_se_error(p):
    """se : error expressao ENTAO corpo FIM
        | SE error ENTAO corpo FIM
        | SE expressao error corpo FIM
        | SE expressao ENTAO error FIM
        | SE expressao ENTAO corpo error
        | error expressao ENTAO corpo SENAO corpo FIM
        | SE error ENTAO corpo SENAO corpo FIM
        | SE expressao error corpo SENAO corpo FIM
        | SE expressao ENTAO error SENAO corpo FIM
        | SE expressao ENTAO corpo error corpo FIM
        | SE expressao ENTAO corpo SENAO error FIM
        | SE expressao ENTAO corpo SENAO corpo error
    """
    error_type = 'ERR-SYN-SE'
    error_name = error_handler.newError(error_type)
    print(error_name)
    pai = MyNode(name=error_name, type=error_type, line=p.lexer.lineno)
    p[0] = pai

def p_repita(p):
    """repita : REPITA corpo ATE expressao"""

    pai = MyNode(name='repita', type='REPITA', line=p.lexer.lineno)
    p[0] = pai

    filho1 = MyNode(name='REPITA', type='REPITA', parent=pai, line=p.lexer.lineno)
    filho_repita = MyNode(name=p[1], type='REPITA', parent=filho1, line=p.lexer.lineno)
    p[1] = filho1

    p[2].parent = pai  # corpo.

    filho3 = MyNode(name='ATE', type='ATE', parent=pai, line=p.lexer.lineno)
    filho_ate = MyNode(name=p[3], type='ATE', parent=filho3, line=p.lexer.lineno)
    p[3] = filho3

    p[4].parent = pai   # expressao.


def p_repita_error(p):
    """repita : error corpo ATE expressao
            | REPITA error ATE expressao
            | REPITA corpo error expressao
            | REPITA corpo ATE error
    """
    error_type = 'ERR-SYN-REPITA'
    error_name = error_handler.newError(error_type)
    print(error_name)
    pai = MyNode(name=error_name, type=error_type, line=p.lexer.lineno)
    p[0] = pai

def p_atribuicao(p):
    """atribuicao : var ATRIBUICAO expressao"""

    pai = MyNode(name='atribuicao', type='ATRIBUICAO', line=p.lexer.lineno)
    p[0] = pai

    p[1].parent = pai

    filho2 = MyNode(name='ATRIBUICAO', type='ATRIBUICAO', parent=pai, line=p.lexer.lineno)
    filho_sym2 = MyNode(name=':=', type='SIMBOLO', parent=filho2, line=p.lexer.lineno)
    p[2] = filho2

    p[3].parent = pai

def p_atribuicao_error(p):
    """atribuicao : error ATRIBUICAO expressao
            | var error expressao
            | var ATRIBUICAO error
    """
    error_type = 'ERR-SYN-ATRIBUICAO'
    error_name = error_handler.newError(error_type)
    print(error_name)
    pai = MyNode(name=error_name, type=error_type, line=p.lexer.lineno)
    p[0] = pai

def p_leia(p):
    """leia : LEIA ABRE_PARENTESE var FECHA_PARENTESE"""

    pai = MyNode(name='leia', type='LEIA', line=p.lexer.lineno)
    p[0] = pai

    filho1 = MyNode(name='LEIA', type='LEIA', parent=pai, line=p.lexer.lineno)
    filho_sym1 = MyNode(name=p[1], type='LEIA', parent=filho1, line=p.lexer.lineno)
    p[1] = filho1

    filho2 = MyNode(name='ABRE_PARENTESE', type='ABRE_PARENTESE', parent=pai, line=p.lexer.lineno)
    filho_sym2 = MyNode(name='(', type='SIMBOLO', parent=filho2, line=p.lexer.lineno)
    p[2] = filho2

    p[3].parent = pai  # var

    filho4 = MyNode(name='FECHA_PARENTESE', type='FECHA_PARENTESE', parent=pai, line=p.lexer.lineno)
    filho_sym4 = MyNode(name=')', type='SIMBOLO', parent=filho4, line=p.lexer.lineno)
    p[4] = filho4

def p_leia_error(p):
    """leia :  LEIA error expressao FECHA_PARENTESE
            | LEIA ABRE_PARENTESE error FECHA_PARENTESE
            | LEIA ABRE_PARENTESE expressao error
    """
    error_type = 'ERR-SYN-LEIA'
    error_name = error_handler.newError(error_type)
    print(error_name)
    pai = MyNode(name=error_name, type=error_type, line=p.lexer.lineno)
    p[0] = pai

def p_escreva(p):
    """escreva : ESCREVA ABRE_PARENTESE expressao FECHA_PARENTESE"""

    pai = MyNode(name='escreva', type='ESCREVA', line=p.lexer.lineno)
    p[0] = pai

    filho1 = MyNode(name='ESCREVA', type='ESCREVA', parent=pai, line=p.lexer.lineno)
    filho_sym1 = MyNode(name=p[1], type='ESCREVA', parent=filho1, line=p.lexer.lineno)
    p[1] = filho1

    filho2 = MyNode(name='ABRE_PARENTESE', type='ABRE_PARENTESE', parent=pai, line=p.lexer.lineno)
    filho_sym2 = MyNode(name='(', type='SIMBOLO', parent=filho2, line=p.lexer.lineno)
    p[2] = filho2

    p[3].parent = pai  # expressao.

    filho4 = MyNode(name='FECHA_PARENTESE', type='FECHA_PARENTESE', parent=pai, line=p.lexer.lineno)
    filho_sym4 = MyNode(name=')', type='SIMBOLO', parent=filho4, line=p.lexer.lineno)
    p[4] = filho4

def p_escreva_error(p):
    """escreva : ESCREVA error expressao FECHA_PARENTESE
                | ESCREVA ABRE_PARENTESE error FECHA_PARENTESE
                | ESCREVA ABRE_PARENTESE expressao error
    """
    error_type = 'ERR-SYN-ESCREVA'
    error_name = error_handler.newError(error_type)
    print(error_name)
    pai = MyNode(name=error_name, type=error_type, line=p.lexer.lineno)
    p[0] = pai

def p_retorna(p):
    """retorna : RETORNA ABRE_PARENTESE expressao FECHA_PARENTESE"""

    pai = MyNode(name='retorna', type='RETORNA', line=p.lexer.lineno)
    p[0] = pai

    filho1 = MyNode(name='RETORNA', type='RETORNA', parent=pai, line=p.lexer.lineno)
    filho_sym1 = MyNode(name=p[1], type='RETORNA', parent=filho1, line=p.lexer.lineno)
    p[1] = filho1

    filho2 = MyNode(name='ABRE_PARENTESE', type='ABRE_PARENTESE', parent=pai, line=p.lexer.lineno)
    filho_sym2 = MyNode(name='(', type='SIMBOLO', parent=filho2, line=p.lexer.lineno)
    p[2] = filho2

    p[3].parent = pai  # expressao.

    filho4 = MyNode(name='FECHA_PARENTESE', type='FECHA_PARENTESE', parent=pai, line=p.lexer.lineno)
    filho_sym4 = MyNode(name=')', type='SIMBOLO', parent=filho4, line=p.lexer.lineno)
    p[4] = filho4

def p_retorna_error(p):
    """retorna : RETORNA error expressao FECHA_PARENTESE
                | RETORNA ABRE_PARENTESE error FECHA_PARENTESE
                | RETORNA ABRE_PARENTESE expressao error
    """
    error_type = 'ERR-SYN-RETORNA'
    error_name = error_handler.newError(error_type)
    print(error_name)
    pai = MyNode(name=error_name, type=error_type, line=p.lexer.lineno)
    p[0] = pai

def p_expressao(p):
    """expressao : expressao_logica
                    | atribuicao
    """
    pai = MyNode(name='expressao', type='EXPRESSAO', line=p.lexer.lineno)
    p[0] = pai
    p[1].parent = pai

def p_expressao_logica(p):
    """expressao_logica : expressao_simples
                    | expressao_logica operador_logico expressao_simples
    """
    pai = MyNode(name='expressao_logica', type='EXPRESSAO_LOGICA', line=p.lexer.lineno)
    p[0] = pai
    p[1].parent = pai

    if len(p) > 2:
        p[2].parent = pai
        p[3].parent = pai

def p_expressao_logica_error(p):
    """expressao_logica : error operador_logico expressao_simples
                        | expressao_logica error expressao_simples
                        | expressao_logica operador_logico error
        """
    error_type = 'ERR-SYN-EXPRESSAO-LOGICA'
    error_name = error_handler.newError(error_type)
    print(error_name)
    pai = MyNode(name=error_name, type=error_type, line=p.lexer.lineno)
    p[0] = pai

def p_expressao_simples(p):
    """expressao_simples : expressao_aditiva
                        | expressao_simples operador_relacional expressao_aditiva
    """

    pai = MyNode(name='expressao_simples', type='EXPRESSAO_SIMPLES', line=p.lexer.lineno)
    p[0] = pai
    p[1].parent = pai

    if len(p) > 2:
        p[2].parent = pai
        p[3].parent = pai

def p_expressao_simples_error(p):
    """expressao_simples : error operador_relacional expressao_aditiva
                        | expressao_simples error expressao_aditiva
                        | expressao_simples operador_relacional error
        """
    error_type = 'ERR-SYN-EXPRESSAO-SIMPLES'
    error_name = error_handler.newError(error_type)
    print(error_name)
    pai = MyNode(name=error_name, type=error_type, line=p.lexer.lineno)
    p[0] = pai

def p_expressao_aditiva(p):
    """expressao_aditiva : expressao_multiplicativa
                        | expressao_aditiva operador_soma expressao_multiplicativa
    """

    pai = MyNode(name='expressao_aditiva', type='EXPRESSAO_ADITIVA', line=p.lexer.lineno)
    p[0] = pai
    p[1].parent = pai

    if len(p) > 2:
        p[2].parent = pai
        p[3].parent = pai

def p_expressao_aditiva_error(p):
    """expressao_aditiva : error operador_soma expressao_multiplicativa
                        | expressao_aditiva error expressao_multiplicativa
                        | expressao_aditiva operador_soma error
        """
    error_type = 'ERR-SYN-EXPRESSAO-ADITIVA'
    error_name = error_handler.newError(error_type)
    print(error_name)
    pai = MyNode(name=error_name, type=error_type, line=p.lexer.lineno)
    p[0] = pai


def p_expressao_multiplicativa(p):
    """expressao_multiplicativa : expressao_unaria
                               | expressao_multiplicativa operador_multiplicacao expressao_unaria
        """

    pai = MyNode(name='expressao_multiplicativa', type='EXPRESSAO_MULTIPLICATIVA', line=p.lexer.lineno)
    p[0] = pai
    p[1].parent = pai

    if len(p) > 2:
        p[2].parent = pai
        p[3].parent = pai

def p_expressao_multiplicativa_error(p):
    """expressao_multiplicativa : error operador_multiplicacao expressao_unaria
                        | expressao_multiplicativa error expressao_unaria
                        | expressao_multiplicativa operador_multiplicacao error
        """
    error_type = 'ERR-SYN-EXPRESSAO-MULTIPLICATIVA'
    error_name = error_handler.newError(error_type)
    print(error_name)
    pai = MyNode(name=error_name, type=error_type, line=p.lexer.lineno)
    p[0] = pai


def p_expressao_unaria(p):
    """expressao_unaria : fator
                        | operador_soma fator
                        | operador_negacao fator
        """
    pai = MyNode(name='expressao_unaria', type='EXPRESSAO_UNARIA', line=p.lexer.lineno)
    p[0] = pai
    p[1].parent = pai

    if p[1] == '!':
        filho1 = MyNode(name='operador_negacao', type='OPERADOR_NEGACAO', parent=pai, line=p.lexer.lineno)
        filho_sym1 = MyNode(name=p[1], type='SIMBOLO', parent=filho1, line=p.lexer.lineno)
        p[1] = filho1
    else:
        p[1].parent = pai

    if len(p) > 2:
        p[2].parent = pai

def p_expressao_unaria_error(p):
    """expressao_unaria : error fator
                    | operador_soma error
                    | operador_negacao error
    """
    error_type = 'ERR-SYN-EXPRESSAO-UNARIA'
    error_name = error_handler.newError(error_type)
    print(error_name)
    pai = MyNode(name=error_name, type=error_type, line=p.lexer.lineno)
    p[0] = pai


def p_operador_relacional(p):
    """operador_relacional : MENOR
                            | MAIOR
                            | IGUAL
                            | DIFERENTE 
                            | MENOR_IGUAL
                            | MAIOR_IGUAL
    """
    pai = MyNode(name='operador_relacional', type='OPERADOR_RELACIONAL', line=p.lexer.lineno)
    p[0] = pai

    if p[1] == "<":
        filho = MyNode(name='MENOR', type='MENOR', parent=pai, line=p.lexer.lineno)
        filho_sym = MyNode(name=p[1], type='SIMBOLO', parent=filho, line=p.lexer.lineno)
    elif p[1] == ">":
        filho = MyNode(name='MAIOR', type='MAIOR', parent=pai, line=p.lexer.lineno)
        filho_sym = MyNode(name=p[1], type='SIMBOLO', parent=filho, line=p.lexer.lineno)
    elif p[1] == "=":
        filho = MyNode(name='IGUAL', type='IGUAL', parent=pai, line=p.lexer.lineno)
        filho_sym = MyNode(name=p[1], type='SIMBOLO', parent=filho, line=p.lexer.lineno)
    elif p[1] == "<>":
        filho = MyNode(name='DIFERENTE', type='DIFERENTE', parent=pai, line=p.lexer.lineno)
        filho_sym = MyNode(name=p[1], type='SIMBOLO', parent=filho, line=p.lexer.lineno)
    elif p[1] == "<=":
        filho = MyNode(name='MENOR_IGUAL', type='MENOR_IGUAL', parent=pai, line=p.lexer.lineno)
        filho_sym = MyNode(name=p[1], type='SIMBOLO', parent=filho, line=p.lexer.lineno)
    elif p[1] == ">=":
        filho = MyNode(name='MAIOR_IGUAL', type='MAIOR_IGUAL', parent=pai, line=p.lexer.lineno)
        filho_sym = MyNode(name=p[1], type='SIMBOLO', parent=filho, line=p.lexer.lineno)
    else:
        error_type = 'ERR-SYN-FATOR'
        error_name = error_handler.newError(error_type)
        print(error_name)

    p[1] = filho

def p_operador_soma(p):
    """operador_soma : MAIS
                    | MENOS
    """
    if p[1] == "+":
        mais = MyNode(name='MAIS', type='MAIS', line=p.lexer.lineno)
        mais_lexema = MyNode(name='+', type='SIMBOLO', parent=mais, line=p.lexer.lineno)
        p[0] = MyNode(name='operador_soma',
                      type='OPERADOR_SOMA', children=[mais], line=p.lexer.lineno)
    else:
       menos = MyNode(name='MENOS', type='MENOS', line=p.lexer.lineno)
       menos_lexema = MyNode(name='-', type='SIMBOLO', parent=menos, line=p.lexer.lineno)
       p[0] = MyNode(name='operador_soma',
                     type='OPERADOR_SOMA', children=[menos], line=p.lexer.lineno)

def p_operador_logico(p):
    """operador_logico : E
                    | OU
    """
    if p[1] == "&&":
        filho = MyNode(name='E', type='E', line=p.lexer.lineno)
        filho_lexema = MyNode(name=p[1], type='SIMBOLO', parent=filho, line=p.lexer.lineno)
        p[0] = MyNode(name='operador_logico',
                      type='OPERADOR_LOGICO', children=[filho], line=p.lexer.lineno)
    else:
        filho = MyNode(name='OU', type='OU', line=p.lexer.lineno)
        filho_lexema = MyNode(name=p[1], type='SIMBOLO', parent=filho, line=p.lexer.lineno)
        p[0] = MyNode(name='operador_logico',
                      type='OPERADOR_SOMA', children=[filho], line=p.lexer.lineno)

def p_operador_negacao(p):
    """operador_negacao : NAO"""

    if p[1] == "!":
        filho = MyNode(name='NAO', type='NAO', line=p.lexer.lineno)
        negacao_lexema = MyNode(name=p[1], type='SIMBOLO', parent=filho, line=p.lexer.lineno)
        p[0] = MyNode(name='operador_negacao',
                      type='OPERADOR_NEGACAO', children=[filho], line=p.lexer.lineno)

def p_operador_multiplicacao(p):
    """operador_multiplicacao : VEZES
                            | DIVIDE
        """
    if p[1] == "*":
        filho = MyNode(name='VEZES', type='VEZES', line=p.lexer.lineno)
        vezes_lexema = MyNode(name=p[1], type='SIMBOLO', parent=filho, line=p.lexer.lineno)
        p[0] = MyNode(name='operador_multiplicacao',
                      type='OPERADOR_MULTIPLICACAO', children=[filho], line=p.lexer.lineno)
    else:
       divide = MyNode(name='DIVIDE', type='DIVIDE', line=p.lexer.lineno)
       divide_lexema = MyNode(name=p[1], type='SIMBOLO', parent=divide, line=p.lexer.lineno)
       p[0] = MyNode(name='operador_multiplicacao',
                     type='OPERADOR_MULTIPLICACAO', children=[divide], line=p.lexer.lineno)

def p_fator(p):
    """fator : ABRE_PARENTESE expressao FECHA_PARENTESE
            | var
            | chamada_funcao
            | numero
        """
    pai = MyNode(name='fator', type='FATOR', line=p.lexer.lineno)
    p[0] = pai
    if len(p) > 2:
        filho1 = MyNode(name='ABRE_PARENTESE', type='ABRE_PARENTESE', parent=pai, line=p.lexer.lineno)
        filho_sym1 = MyNode(name=p[1], type='SIMBOLO', parent=filho1, line=p.lexer.lineno)
        p[1] = filho1

        p[2].parent = pai

        filho3 = MyNode(name='FECHA_PARENTESE', type='FECHA_PARENTESE', parent=pai, line=p.lexer.lineno)
        filho_sym3 = MyNode(name=p[3], type='SIMBOLO', parent=filho3, line=p.lexer.lineno)
        p[3] = filho3
    else:
        p[1].parent = pai


def p_fator_error(p):
    """fator : ABRE_PARENTESE error FECHA_PARENTESE
            | error expressao FECHA_PARENTESE
            | ABRE_PARENTESE expressao error
        """
    error_type = 'ERR-SYN-FATOR'
    error_name = error_handler.newError(error_type, line=p.lexer.lineno)
    print(error_name, line=p.lexer.lineno)
    pai = MyNode(name=error_name, type=error_type, line=p.lexer.lineno)
    p[0] = pai

def p_numero(p):
    """numero : NUM_INTEIRO
                | NUM_PONTO_FLUTUANTE
                | NUM_NOTACAO_CIENTIFICA
    """

    pai = MyNode(name='numero', type='NUMERO', line=p.lexer.lineno)
    p[0] = pai

    if str(p[1]).find('.') == -1:
        aux = MyNode(name='NUM_INTEIRO', type='NUM_INTEIRO', parent=pai, line=p.lexer.lineno)
        aux_val = MyNode(name=p[1], type='VALOR', parent=aux, line=p.lexer.lineno)
        p[1] = aux
    elif str(p[1]).find('e') >= 0:
        aux = MyNode(name='NUM_NOTACAO_CIENTIFICA',
                     type='NUM_NOTACAO_CIENTIFICA', parent=pai, line=p.lexer.lineno)
        aux_val = MyNode(name=p[1], type='VALOR', parent=aux, line=p.lexer.lineno)
        p[1] = aux
    else:
        aux = MyNode(name='NUM_PONTO_FLUTUANTE',
                     type='NUM_PONTO_FLUTUANTE', parent=pai, line=p.lexer.lineno)
        aux_val = MyNode(name=p[1], type='VALOR', parent=aux, line=p.lexer.lineno)
        p[1] = aux

def p_chamada_funcao(p):
    """chamada_funcao : ID ABRE_PARENTESE lista_argumentos FECHA_PARENTESE"""

    pai = MyNode(name='chamada_funcao', type='CHAMADA_FUNCAO', line=p.lexer.lineno)
    p[0] = pai
    if len(p) > 2:
        filho1 = MyNode(name='ID', type='ID', parent=pai, line=p.lexer.lineno)
        filho_id = MyNode(name=p[1], type='ID', parent=filho1, line=p.lexer.lineno)
        p[1] = filho1

        filho2 = MyNode(name='ABRE_PARENTESE', type='ABRE_PARENTESE', parent=pai, line=p.lexer.lineno)
        filho_sym = MyNode(name=p[2], type='SIMBOLO', parent=filho2, line=p.lexer.lineno)
        p[2] = filho2

        p[3].parent = pai

        filho4 = MyNode(name='FECHA_PARENTESE', type='FECHA_PARENTESE', parent=pai, line=p.lexer.lineno)
        filho_sym = MyNode(name=p[4], type='SIMBOLO', parent=filho4, line=p.lexer.lineno)
        p[4] = filho4
    else:
        p[1].parent = pai

def p_chamada_funcao_error(p):
    """chamada_funcao : error ABRE_PARENTESE lista_argumentos FECHA_PARENTESE
                    | ID error lista_argumentos FECHA_PARENTESE
                    | ID ABRE_PARENTESE error FECHA_PARENTESE
                    | ID ABRE_PARENTESE lista_argumentos error
        """
    error_type = 'ERR-SYN-CHAMADA-FUNCAO'
    error_name = error_handler.newError(error_type)
    print(error_name)
    pai = MyNode(name=error_name, type=error_type, line=p.lexer.lineno)
    p[0] = pai

def p_lista_argumentos(p):
    """lista_argumentos : lista_argumentos VIRGULA expressao
                    | expressao
                    | vazio
        """
    pai = MyNode(name='lista_argumentos', type='LISTA_ARGUMENTOS', line=p.lexer.lineno)
    p[0] = pai

    if len(p) > 2:
        p[1].parent = pai

        filho2 = MyNode(name='VIRGULA', type='VIRGULA', parent=pai, line=p.lexer.lineno)
        filho_sym = MyNode(name=p[2], type='SIMBOLO', parent=filho2, line=p.lexer.lineno)
        p[2] = filho2

        p[3].parent = pai
    else:
        p[1].parent = pai

def p_lista_argumentos_error(p):
    """lista_argumentos : error VIRGULA expressao
                    | lista_argumentos error expressao
                    | lista_argumentos VIRGULA error
        """
    error_type = 'ERR-SYN-LISTA-ARGUMENTOS'
    error_name = error_handler.newError(error_type)
    print(error_name)
    pai = MyNode(name=error_name, type=error_type)
    p[0] = pai


def p_vazio(p):
    """vazio : """
    pai = MyNode(name='vazio', type='VAZIO', line=p.lexer.lineno)
    p[0] = pai

def define_column(input, lexpos):
    line_start = input.rfind("\n", 0, lexpos) + 1
    return (lexpos - line_start) + 1

def p_error(p):

    if p:
        token = p
        line = token.lineno
        column = define_column(token.lexer.lexdata, token.lexpos)
        print("Erro:[{line},{column}]: Erro próximo ao token '{token}'".format(
            line=line, column=column, token=token.value))

def main():
    numParameters = len(argv) # Número de parâmetros

    if numParameters != 2:
        error = "The number of parameters is invalid. "
        if numParameters < 2: 
            error += "Send a .tpp file as parameter."
            raise IOError(error_handler.newError('ERR-LEX-INVALID-PARAMETER-NOTFOUND'))
        raise IOError(error_handler.newError('ERR-LEX-INVALID-PARAMETER'))

    aux = argv[1].split('.')
    if aux[-1] != 'tpp':
      raise IOError(error_handler.newError('ERR-SYN-NOT-TPP'))
    elif not os.path.exists(argv[1]):
        raise IOError(error_handler.newError('ERR-SYN-FILE-NOT-EXISTS'))
    else:
        data = open(argv[1])
        source_file = data.read()
        parser.parse(source_file)

    if root and root.children != ():
        UniqueDotExporter(root).to_picture(argv[1] + ".unique.ast.png")
        DotExporter(root).to_dotfile(argv[1] + ".ast.dot")
        UniqueDotExporter(root).to_dotfile(argv[1] + ".unique.ast.dot")

    else:
        print(error_handler.newError('WAR-SYN-NOT-GEN-SYN-TREE'))
    return root

# Build the parser.
parser = yacc.yacc(method="LALR", optimize=True, start='programa', debug=False,
                   debuglog=log, write_tables=False, tabmodule='tpp_parser_tab')

if __name__ == "__main__":
    main()