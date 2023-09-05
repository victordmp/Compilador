import os
import sys
import logging
from sys import argv
from myerror import MyError
from anytree import RenderTree, findall_by_attr, LevelOrderIter
from anytree.exporter import DotExporter, UniqueDotExporter

logging.basicConfig(
     level = logging.DEBUG,
     filename = "sema.log",
     filemode = "w",
     format = "%(filename)10s:%(lineno)4d:%(message)s"
)
log = logging.getLogger()
error_handler = MyError('SemaErrors', showErrorMessage=True)
root = None

variablesError = []

def addVaribleError(name, scope):
    variablesError.append({
        'name': name,
        'scope': scope
    })

def variableHasError(name, scope):
    for variable in variablesError:
        if variable['name'] == name and variable['scope'] == scope:
            return True
    return False

def symbolTable():
    res = findall_by_attr(root, "declaracao")
    variables = []
    for p in res:
        item = [node for pre, fill, node in RenderTree(p)]
        if (item[1].name == "declaracao_variaveis"):
            variable = variableDeclaration(node1=item[1], scope="global")
            if variableIsDeclared(table=variables, name=variable['name'], scope='global'):
                typeVar = getType(table=variables, name=variable['name'], scope='global')
                print(error_handler.newError('WAR-SEM-VAR-DECL-PREV').format(variable['name'], typeVar))
            else:
                variables.append(variable)
        elif (item[1].name == "declaracao_funcao"):
            if item[2].name == "tipo":
                name = item[7].name
                token = item[6].name
                type = item[4].name
                line = item[4].line
            else:
                name = item[4].name
                token = item[3].name
                type = 'vazio'
                line = item[4].line

            variable = {
                "declarationType": 'func',
                "type": type,
                "line": line,
                "token": token,
                "name": name,
                "scope": "global",
                "used": "S" if name == "principal" else "N",
                "dimension": 0,
                "sizeDimension1": 1,
                "sizeDimension2": 0,
                "parameters": parametersDeclaration(item)
            }
            if variableIsDeclared(table=variables, name=name, scope='global'):
                typeVar = getType(table=variables, name=name, scope='global')
                print(error_handler.newError('WAR-SEM-FUNC-DECL-PREV').format(name, typeVar))
            else:
                variables.append(variable)
                functionDeclaration(node1=item[1], scope=name, table=variables)
    return variables

def parametersDeclaration(node1):
    parameters = []
    for item in node1:
        if item.name == 'cabecalho':
            aux = item.children[2]
            parametersFound = findall_by_attr(aux, "parametro")
            for p2 in parametersFound:
                parameter = {} 
                parameter['type'] = p2.children[0].children[0].children[0].name
                parameter['name'] = p2.children[2].children[0].name
                parameters.append(parameter)
    return parameters

def functionDeclaration(node1, scope, table):
    res = findall_by_attr(node1, "declaracao_variaveis")
    for p in res:
        variable = variableDeclaration(node1=p, scope=scope)
        if variableIsDeclared(table=table, name=variable['name'], scope=scope):
            typeVar = getType(table=table, name=variable['name'], scope=scope)
            print(error_handler.newError('WAR-SEM-VAR-DECL-PREV').format(variable['name'], typeVar))
        else:
            table.append(variable)

def variableDeclaration(node1, scope):
    d1 = 1
    d2 = 0
    dimension = 0 
    renderNodeTree = [node for pre, fill, node in RenderTree(node1)]
    for i in range(len(renderNodeTree)):
        if (renderNodeTree[i].name == 'tipo'):
            type = renderNodeTree[i+2].name
            line = renderNodeTree[i+2].line
        elif (renderNodeTree[i].name == 'ID'): 
            token = renderNodeTree[i].name
            name = renderNodeTree[i+1].name
        elif (renderNodeTree[i].name == 'fecha_colchete'):
            dimension+=1
            if renderNodeTree[i-2].name == 'NUM_PONTO_FLUTUANTE':
                if not variableHasError(name, scope):
                    addVaribleError(name,scope)
                    print(error_handler.newError('ERR-SEM-ARRAY-INDEX-NOT-INT').format(name))
            index = renderNodeTree[i-1].name
            if (dimension == 2):
                d2 = index
            else:
                d1 = index

    variable = {
        'declarationType': 'var',
        'type': type,
        'line': line,
        'token': token,
        'name': name,
        'scope': scope,
        'init': 'N',
        'used': 'N',
        'dimension': dimension,
        'sizeDimension1': d1,
        'sizeDimension2': d2,
        'errors': 0
    }

    return variable

def mainFunctionExists(table):
    for i in range(len(table)):
        if table[i]['declarationType'] == 'func' and table[i]['name'] == 'principal':
            return True
    return False

def variableIsDeclared(table, name, scope):
    for i in range(len(table)):
        if table[i]['name'] == name and (table[i]['scope'] == 'global' or table[i]['scope'] == scope):
            return True
        elif scope != 'global' and table[i]['declarationType'] == 'func':
            parameters = table[i]['parameters']
            for j in parameters:
                if j['name'] == name:
                    return True
    return False

def getType(table, name, scope):
    for i in range(len(table)):
        if table[i]['name'] == name and (table[i]['scope'] == 'global' or table[i]['scope'] == scope):
            return table[i]['type']
        elif scope != 'global' and table[i]['declarationType'] == 'func':
            parameters = table[i]['parameters']
            for j in parameters:
                if j['name'] == name:
                    return table[i]['type']
    return None

def getScope(node):
    anchestors = list(node.anchestors)
    for i in range(len(anchestors)):
        if anchestors[i].name == 'cabecalho' and anchestors[i].children[0].name == 'ID':
            scope = anchestors[i].children[0].children[0].name
            return scope
    return 'global'

def valueIsIndex(node):
    anchestors = list(node.anchestors)
    for i in range(len(anchestors)):
        if anchestors[i].name == 'indice':
            return True
    return False

def valueIsArgument(node):
    anchestors = list(node.anchestors)
    for i in range(len(anchestors)):
        if anchestors[i].name == 'lista_argumentos':
            return True
    return False

def getFactors(node1, table, scope):
    res = findall_by_attr(node1, "fator")
    factors = []
    for p in res:
        if not valueIsIndex(p) and not valueIsArgument(p):
            factor = p.children[0].name
            factor = factor if factor != 'chamada_funcao' else 'func'
            
            value = p.children[0].children[0].children[0].name
            type = p.children[0].children[0].name
            real_scope = scope if factor != 'func' else 'global'
            type = ('inteiro' if type == 'NUM_INTEIRO' else 'flutuante') if factor == 'numero' else getType(table,value,real_scope)
            
            if type != None:
                factors.append({
                    'factor': factor,
                    'type': type,
                    'value': value
                })
    return factors

def getTypeFactors(factors, type):
    type_factor = type
    for factor in factors:
        if factor['type'] != type:
            type_factor = factor['type']
    return type_factor

def getCountParameters(node):
    i = 1
    item = node
    while item.name == 'lista_argumentos':
        if item.name == 'lista_argumentos' and len(item.children) > 1 and item.children[1].name == 'VIRGULA':
            i+=1
        item = item.children[0]
    return i

def checkCoercions(table, name, scope, node):
    factors = getFactors(node, table, scope)
    type = None
    for i in range(len(table)):
        type = None

        try:
            parameters = table[i]['parameters']
        except:
            parameters = None

        if table[i]['name'] == name and (table[i]['scope'] == 'global' or table[i]['scope'] == scope):
            type = table[i]['type']
        elif parameters != None and len(parameters) > 0:
            for parameter in parameters:
                if parameter['name'] == name:
                    type = parameter['type']
        
        if type != None:
            if len(factors) == 1:
                type_factor = factors[0]['type']
                if type_factor != type:
                    value_factor = factors[0]['value']
                    factor = factors[0]['factor']
                    if factor == 'var':
                        print(error_handler.newError('WAR-SEM-ATR-DIFF-TYPES-IMP-COERC-OF-VAR').format(value_factor, type_factor, name, type))
                    elif factor == 'func':
                        print(error_handler.newError('WAR-SEM-ATR-DIFF-TYPES-IMP-COERC-OF-RET-VAL').format(value_factor, type_factor, name, type))
                    else:
                        print(error_handler.newError('WAR-SEM-ATR-DIFF-TYPES-IMP-COERC-OF-NUM').format(value_factor, type_factor, name, type))                        
            else:
                type_factor = getTypeFactors(factors, type)
                if type_factor != type:
                    value_factor = 'expressao'
                    print(error_handler.newError('WAR-SEM-ATR-DIFF-TYPES-IMP-COERC-OF-EXP').format(value_factor, type_factor, name, type))

def initVariables(table, name, scope, node):
    if variableIsDeclared(table=table, name=name, scope=scope):
        checkCoercions(table=table, name=name, scope=scope, node=node)
        for i in range(len(table)):
            if table[i]['name'] == name and (table[i]['scope'] == 'global' or table[i]['scope'] == scope):
                table[i]['init'] = 'Y'
    else:
        res = findall_by_attr(node, 'chamada_funcao')
        if not res and not variableHasError(name, scope):
            addVaribleError(name,scope)
            print(error_handler.newError('ERR-SEM-VAR-NOT-DECL').format(name))

def usedVariables(table, name, scope, node):
    if variableIsDeclared(table=table, name=name, scope=scope):
        for i in range(len(table)):
            if table[i]['name'] == name and (table[i]['scope'] == 'global' or table[i]['scope'] == scope):
                table[i]['used'] = 'Y'
    else:
        res = findall_by_attr(node, 'chamada_funcao')
        if not res and not variableHasError(name, scope):
            addVaribleError(name,scope)
            print(error_handler.newError('ERR-SEM-VAR-NOT-DECL').format(name))

def verifyVariables(table):
    res = findall_by_attr(root, "acao")
    for p in res:
        renderNodeTree = [node for pre, fill, node in RenderTree(p)]
        for node1 in renderNodeTree:
            renderNode1Tree = [node for pre, fill, node in RenderTree(node1)]
            if node1.name == 'expressao':
                if renderNode1Tree[1].name == 'atribuicao':
                    scope = getScope(node1)
                    name = renderNode1Tree[4].name
                    initVariables(table=table, name=name, scope=scope, node=node1)                    
                else:
                    for index in range(len(renderNode1Tree)):
                        if renderNode1Tree[index].name == 'ID':
                            scope = getScope(node1)
                            name = renderNode1Tree[index+1].name
                            usedVariables(table=table, name=name, scope=scope, node=node1)
            elif node1.name == 'leia':
                for index in range(len(renderNode1Tree)):
                    if renderNode1Tree[index].name == 'ID':
                        scope = getScope(node1)
                        name = renderNode1Tree[index+1].name
                        initVariables(table=table, name=name, scope=scope, node=node1)   
            elif node1.name in ['se','repita','escreva','retorna']:
                for index in range(len(renderNode1Tree)):
                    if renderNode1Tree[index].name == 'ID':
                        scope = getScope(node1)
                        name = renderNode1Tree[index+1].name
                        usedVariables(table=table, name=name, scope=scope, node=node1)
            elif node1.name == 'chamada_funcao':
                scope = getScope(node1)
                name = node1.children[0].children[0].name
                usedVariables(table=table, name=name, scope=scope, node=node1)

def verifyVariableIsUsed(table):
    for i in range(len(table)):
        name = table[i]['name']
        scope = table[i]['scope']
        if table[i]['declarationType'] == 'var' and table[i]['errors'] <= 0 and not variableHasError(name, scope):    
            if table[i]['init'] == 'N' and table[i]['used'] == 'N':
                print(error_handler.newError('WAR-SEM-VAR-DECL-NOT-USED').format(name))
            elif table[i]['init'] == 'Y' and table[i]['used'] == 'N':
                print(error_handler.newError('WAR-SEM-VAR-DECL-INIT-NOT-USED').format(name))
            elif table[i]['init'] == 'N':
                print(error_handler.newError('WAR-SEM-VAR-DECL-NOT-INIT').format(name))

def verifyFunctionReturn(table):
    res = findall_by_attr(root, 'declaracao_funcao')
    for p in res:
        renderNodeTree = [node for pre, fill, node in RenderTree(p)]
        for node1 in renderNodeTree:
            if node1.name == 'cabecalho':
                renderNode1Tree = [node for pre, fill, node in RenderTree(node1)]
                returns = findall_by_attr(node1, 'retorna')
                funcName = renderNode1Tree[2].name
                if not returns:                
                    for i in range(len(table)):
                        if table[i]['name'] == funcName and table[i]['declarationType'] == 'func' and table[i]['declarationType'] != 'vazio':
                            print(error_handler.newError('ERR-SEM-FUNC-RET-TYPE-ERROR').format(funcName,table[i]['type'],'vazio'))
                else:
                    for return1 in returns:
                        if return1.children:
                            expression = return1.children[2]
                            if expression.name == 'expressao':
                                scope = getScope(return1)
                                factors = getFactors(expression,table,scope)
                                for i in range(len(table)):
                                    if table[i]['name'] == funcName and table[i]['declarationType'] == 'func':
                                        type = table[i]['type']
                                        type_factor = getTypeFactors(factors, type)
                                        if type_factor != type:
                                            print(error_handler.newError('ERR-SEM-FUNC-RET-TYPE-ERROR').format(funcName,type,type_factor))

def verifyCallFunctions(table):
    res = findall_by_attr(root, 'chamada_funcao')
    for p in res:
        renderNodeTree = [node for pre, fill, node in RenderTree(p)]
        name = renderNodeTree[2].name
        if variableIsDeclared(table=table, name=name, scope='global'):
            scopeCall = getScope(p)
            if name == 'principal':
                if scopeCall == 'principal':
                    print(error_handler.newError('WAR-SEM-CALL-REC-FUNC-MAIN').format(name))
                print(error_handler.newError('ERR-SEM-CALL-FUNC-MAIN-NOT-ALLOWED'))
            else:
                node1 = renderNodeTree[5]
                if node1.name == 'lista_argumentos':
                    if node1.children[0].name != 'vazio':
                        numberArguments = getCountParameters(node1)
                        for i in range(len(table)):
                            if table[i]['name'] == name and table[i]['declarationType'] == 'func':
                                parameters = table[i]['parameters']
                                if numberArguments < len(parameters):
                                    print(error_handler.newError('ERR-SEM-CALL-FUNC-WITH-FEW-ARGS').format(name))
                                elif numberArguments > len(parameters):
                                    print(error_handler.newError('ERR-SEM-CALL-FUNC-WITH-MANY-ARGS').format(name))
        else:
            print(error_handler.newError('ERR-SEM-CALL-FUNC-NOT-DECL').format(name))            

def verifyFunctionsIsUsed(table):
    for i in range(len(table)):
        if table[i]['declarationType'] == 'func':
            name = table[i]['name']
            if table[i]['used'] == 'N':
                print(error_handler.newError('WAR-SEM-FUNC-DECL-NOT-USED').format(name))

def verifyFunctions(table):
    verifyFunctionReturn(table)
    verifyCallFunctions(table)
    verifyFunctionsIsUsed(table)

def checkRules():
    table = symbolTable()
    if (not mainFunctionExists(table)):
        print(error_handler.newError('ERR-SEM-MAIN-NOT-DECL'))
    verifyVariables(table)
    verifyVariableIsUsed(table)
    verifyFunctions(table)

## Poda da arvore

list_string = [
    'ID',
    'ABRE_PARENTESE',
    'FECHA_PARENTESE',
    'FIM',
    'abre_colchete',
    'fecha_colchete'
]

def pruneDeclaration(tree):
    item = tree.children[0]
    dec = ()
    while item.name == 'lista_declaracoes':
        if item.name == 'lista_declaracoes':
            if len(item.children) == 1:
                node = item.children[0]
            else:
                node = item.children[1]
            dec = node.children + dec
        item = item.children[0]
    
    for i in dec:
        if i.name == 'declaracao_funcao':
            pruneFunctionDeclaration(i)
        elif i.name == 'declaracao_variaveis':
            pruneVaribleDeclaration(i)
        else:
            pruneInitVariable(i)
    tree.children[0].children = dec

def pruneFunctionDeclaration(tree):
    dec = ()
    if len(tree.children) == 1:
        dec += tree.children[0].children
    else:
        dec += tree.children[0].children[0].children
        for child in tree.children[1].children:
            if child.name in list_string:
                dec += child.children
            elif child.name == 'corpo':
                dec += (pruneBody(child),)
            elif child.name == 'lista_parametros':
                item = child
                dec1 = ()
                while item.name == 'lista_parametros':
                    if item.children[0].name == 'vazio':
                        aux = item.children[0]
                        dec1 = (aux,) + dec1
                    elif len(item.children) == 1:
                        dec1 = (pruneParameter(item.children[0]),) + dec1
                    else:
                        dec1 = (pruneParameter(item.children[2]),) + dec1
                    item = item.children[0]
                child.children = dec1
                dec += (child,)
            else:
                dec += (child,)
    tree.children = dec
 
def pruneVaribleDeclaration(tree):
    dec = ()
    dec += tree.children[0].children[0].children
    dec += tree.children[1].children

    # Lista de Variaveis
    dec1 = ()
    item = tree.children[2]
    while item.name == 'lista_variaveis':
        if item.name == 'lista_variaveis':
            if len(item.children) == 1:
                dec1 = (pruneVariable(item.children[0]),) + dec1
            else:
                dec1 = (pruneVariable(item.children[2]),) + dec1
        item = item.children[0]
    tree.children[2].children = dec1
    dec += (tree.children[2],)
    tree.children = dec
    return tree

def pruneInitVariable(tree):
    pruneAssignment(tree.children[0])

def pruneAssignment(tree):
    dec = ()
    dec += (pruneVariable(tree.children[0]),)
    dec += (tree.children[1].children[0],)
    tree.children[2].children = pruneExpression(tree.children[2])
    dec += (tree.children[2],)
    tree.children = dec
    return tree

def pruneVariable(tree):
    aux = tree
    dec = ()
    dec1 = ()

    dec += (aux.children[0].children[0],)
    if len(aux.children) > 1:
        aux1 = aux.children[1].children
        if len(aux.children[1].children) == 4:
            # primeiro []
            dec1 += aux1[0].children[0].children
            aux1[0].children[1].children = pruneExpression(aux1[0].children[1])
            dec1 += (aux1[0].children[1],)
            dec1 += aux1[0].children[2].children
            # segundo []
            dec1 += aux1[1].children
            aux1[2].children = pruneExpression(aux1[2])
            dec1 += (aux1[2],)
            dec1 += aux1[3].children
        else:
            dec1 += aux1[0].children
            aux1[1].children = pruneExpression(aux1[1])
            dec1 += (aux1[1],)
            dec1 += aux1[2].children
        aux.children[1].children = dec1
        dec += (aux.children[1],)
    
    tree.children = dec
    return tree

def pruneExpression(tree):
    aux = tree.children
    name = tree.name
    while len(aux) == 1 and name != 'expressao_unaria':
        name = aux[0].name
        aux = aux[0].children
    
    dec = ()
    if aux[0].parent.name == 'expressao_unaria':
        if len(aux) == 1:
            if aux[0].children[0].name == 'chamada_funcao':
                dec += (pruneCallFunction(aux[0].children[0]),)
            elif aux[0].children[0].name == 'var':
                dec += (pruneVariable(aux[0].children[0]),)
            elif aux[0].children[0].name == 'numero':
                dec += aux[0].children[0].children
            else:
                dec += aux[0].children[0].children
                dec += pruneExpression(aux[0].children[1])
                dec += aux[0].children[2].children
        else:
            dec += aux[0].children[0].children
            dec += aux[1].children[0].children
        aux = dec
    else:
       dec += pruneExpression(aux[0])
       dec += (aux[1].children[0].children[0],)
       dec += pruneExpression(aux[2])
       aux = dec
    
    return aux

def pruneCallFunction(tree):
    dec = ()
    if len(tree.children) == 1:
        dec += tree.children[0].children
    else:
        dec += tree.children[0].children[0].children
        for child in tree.children:
            if child.name in list_string:
                dec += child.children
            elif child.name == 'lista_argumentos':
                item = child
                dec1 = ()
                while item.name == 'lista_argumentos':
                    if item.children[0].name == 'vazio':
                        aux = item.children[0]
                        dec1 = (aux,) + dec1
                    elif len(item.children) == 1:
                        aux = item.children[0]
                        aux.children = pruneExpression(item.children[0])
                        dec1 = (aux,) + dec1
                    else:
                        aux = item.children[2]
                        aux.children = pruneExpression(item.children[2])
                        dec1 = (aux,) + dec1
                    item = item.children[0]
                child.children = dec1
                dec += (child,)
            else:
                dec += (child,)
    tree.children = dec
    return tree

def pruneParameter(tree):
    dec = ()
    item = tree
    while item.name == 'parametro':
        if item.children[0].name == 'parametro':
            dec = item.children[2].children + dec
            dec = item.children[1].children + dec
        else:
            dec = item.children[2].children + dec
            dec = item.children[1].children + dec
            dec = item.children[0].children[0].children + dec
        item = item.children[0]
    tree.children = dec
    return tree

# leia, escreva, retorna
def pruneSpecialFunctions(tree):
    dec = ()
    dec += tree.children[0].children
    dec += tree.children[1].children
    if tree.name == 'leia':
        dec += (pruneVariable(tree.children[2]),)
    else:
        tree.children[2].children = pruneExpression(tree.children[2])
        dec += (tree.children[2],)
    dec += tree.children[3].children
    tree.children = dec
    return tree

def pruneIf(tree):
    dec = ()
    dec += tree.children[0].children # SE
    tree.children[1].children = pruneExpression(tree.children[1]) # expressao
    dec += (tree.children[1],) # expressao
    dec += tree.children[2].children # ENTAO
    dec += (pruneBody(tree.children[3]),) # corpo
    if len(tree.children) == 5:
        dec += (tree.children[4],) # FIM
    else:
        dec += (tree.children[4],) # SENAO
        dec += (pruneBody(tree.children[5]),) # corpo
        dec += (tree.children[6],) # FIM
    tree.children = dec
    return tree

def pruneRepeat(tree):
    dec = ()
    dec += tree.children[0].children # REPITA
    dec += (pruneBody(tree.children[1]),) # corpo
    dec += tree.children[2].children # ATE
    tree.children[3].children = pruneExpression(tree.children[3]) # expressao
    dec += (tree.children[3],) # expressao
    tree.children = dec
    return tree

def pruneBody(tree):
    dec = ()
    item = tree
    while item.name == 'corpo':
        if len(item.children) == 2:
            action = item.children[1].children[0]
            if action.name == 'expressao':
                if action.children[0].name == 'atribuicao':
                    dec = (pruneAssignment(action.children[0]),) + dec
                else:
                    action.children = pruneExpression(action)
                    dec = (action,) + dec
            elif action.name == 'declaracao_variaveis':
                dec = (pruneVaribleDeclaration(action),) + dec
            elif action.name == 'se':
                dec = (pruneIf(action),) + dec
            elif action.name == 'repita':
                dec = (pruneRepeat(action),) + dec
            else:
                dec = (pruneSpecialFunctions(action),) + dec
        item = item.children[0]
    tree.children = dec
    return tree

def pruneTree():
    tree = root
    pruneDeclaration(tree)
    UniqueDotExporter(tree).to_picture("prunedTree.png")

def main():
    if(len(sys.argv) < 2):
        raise TypeError(error_handler.newError('ERR-SEM-USE'))

    aux = argv[1].split('.')
    if aux[-1] != 'tpp':
      raise IOError(error_handler.newError('ERR-SEM-NOT-TPP'))
    elif not os.path.exists(argv[1]):
        raise IOError(error_handler.newError('ERR-SEM-FILE-NOT-EXISTS'))
    else:
        data = open(argv[1])
        source_file = data.read()

if __name__ == "__main__":
    main()