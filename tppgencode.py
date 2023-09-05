import os
import sys
import logging
from sys import argv
from myerror import MyError

from llvmlite import ir
from llvmlite import binding as llvm

logging.basicConfig(
     level = logging.DEBUG,
     filename = "gencode.log",
     filemode = "w",
     format = "%(filename)10s:%(lineno)4d:%(message)s"
)
log = logging.getLogger()
error_handler = MyError('GenCodeErrors', showErrorMessage=True)
root = None


class GenCode():
    def __init__(self):
        # Código de Inicialização.
        llvm.initialize()
        llvm.initialize_all_targets()
        llvm.initialize_native_target()
        llvm.initialize_native_asmprinter()

        # Cria o módulo.
        self.module = ir.Module('meu_modulo.bc')
        self.module.triple = llvm.get_process_triple()
        target = llvm.Target.from_triple(self.module.triple)
        target_machine = target.create_target_machine()
        self.module.data_layout = target_machine.target_data

        # Define os tipos
        self.FLOAT = ir.FloatType()
        self.INT = ir.IntType(32)
        self.ZERO = ir.Constant(ir.IntType(32), 0)

        # Define as funções de leia e escreva
        self.escrevaInteiro = ir.Function(self.module,ir.FunctionType(ir.VoidType(), [ir.IntType(32)]),name="escrevaInteiro")
        self.escrevaFlutuante = ir.Function(self.module,ir.FunctionType(ir.VoidType(),[ir.FloatType()]),name="escrevaFlutuante")
        self.leiaInteiro = ir.Function(self.module,ir.FunctionType(ir.IntType(32),[]),name="leiaInteiro")
        self.leiaFlutuante = ir.Function(self.module,ir.FunctionType(ir.FloatType(),[]),name="leiaFlutuante")

        # Declara os blocos
        self.entry_block = None
        self.exit_block = None
        self.block = None

        # Lista de funções
        self.functions = []

        # Declaração de variaveis globais
        self.vars_global = []
        # Declaração de variaveis locais
        self.vars_local = []
        # Declaração de parametros da função
        self.args_func = []

    def declaration(self, tree):
        declaractions = tree.children[0].children
        for decl in declaractions:
            if decl.name == 'declaracao_funcao':
                self.functionDeclaration(decl)
            elif decl.name == 'declaracao_variaveis':
                self.vars_global.extend(self.variableDeclaration(decl))
            else:
                print('inicialização de variveis')
        self.saveCode()

    def functionDeclaration(self, tree):
        # Reseta o lista de variaveis locais e argumentos
        self.vars_local = []
        self.args_func = []

        if tree.children[0].name in ['inteiro', 'flutuante']:
            name = tree.children[1].name
            params = tree.children[3]
            body = tree.children[5]
            type = self.getType(tree.children[0].name)
        else:
            name = tree.children[0].name
            params = tree.children[2]
            body = tree.children[4]
            type = ir.VoidType()

        if name == 'principal':
            name = 'main'

        # Pega os parametros da função
        parameters = self.parameters(params)

        # Declara a função
        func_type = ir.FunctionType(type, parameters['types'])
        func = ir.Function(self.module, func_type, name)

        for i in range(len(func.args)):
            func.args[i].name = parameters['names'][i]

        # Guarda a função declarada em uma array de funções
        self.functions.append(func)

        # Guarda os argumentos da função em array global
        self.args_func = func.args

        # Cria blovos de entra e saída
        self.entry_block = func.append_basic_block("bloco_entrada")
        
        # Entra no bloco de entrada
        self.block = ir.IRBuilder(self.entry_block)

        # Realisa as operações do corpo
        self.body(body, func)

    def variableDeclaration(self, tree, isGlobal=True):
        variables = tree.children[2].children
        decl_variables = []
        type = self.getType(tree.children[0].name)
        for var in variables:
            name = var.children[0].name
            if len(var.children) == 1:
                if isGlobal:
                    value = ir.GlobalVariable(self.module, type, name)
                    value.initializer = ir.Constant(type, None)
                else:
                    value = self.block.alloca(type, name=name)
            else:
                index = var.children[1].children
                index_ref = self.expression(index[1])
                value_type = ir.ArrayType(ir.IntType(32), 1000)
                if len(index) > 3:
                    # Array bidimencionalself
                    index_ref = self.expression(index[4])
                    value_type = ir.ArrayType(value_type, 10)
                if isGlobal:
                    value = ir.GlobalVariable(self.module, value_type, name)
                    value.linkage = "common"
                    value.initializer = ir.Constant(value_type, 0)
                else:
                    value = self.block.alloca(value_type, name=name)
            value.align = 4
            decl_variables.append(value)
        return decl_variables
    
    def assignment(self, tree):
        name = tree.children[0].children[0].name
        var_ass = self.getVar(name)

        if len(tree.children[0].children) > 1:
            index = self.expression(tree.children[0].children[1].children[1])
            array_1 = self.block.gep(var_ass, [self.INT(0), index], name='array_1')
            var_ass = array_1
        
        expr = self.expression(tree.children[2])
        self.block.store(expr, var_ass, align=4)

    def body(self, tree, func: ir.Function):
        listt = tree.children
        hasReturn = False
        for item in listt:
            if item.name == 'declaracao_variaveis':
                self.vars_local.extend(self.variableDeclaration(item, isGlobal=False))
            elif item.name == 'chamada_funcao':
                self.callFunction(tree)
            elif item.name == 'atribuicao':
                self.assignment(item)
            elif item.name in ['escreva','leia', 'retorna']:
                if item.name == 'retorna':
                    hasReturn = True
                self.externalFunctions(item,func)
            elif item.name == 'se':
                self.ifExpression(item,func)
            elif item.name == 'repita':
                self.repeat(item,func)
        return hasReturn
    
    def repeat(self, tree, func: ir.Function):
        loop = self.block.append_basic_block('loop')
        lopp_val = self.block.append_basic_block('loop_val')
        loop_end = self.block.append_basic_block('loop_end')

        # Pula para o laço do loop
        self.block.branch(loop)

        # Posiciona no inicio do bloco do loop e define o que o loop irá executar
        self.block.position_at_end(loop)
        self.body(tree.children[1], func)

        # Pula para o laço de validação
        self.block.branch(lopp_val)

        # Posiciona no inicio do bloco de validação e define o que o loop de validação irá executar
        self.block.position_at_end(lopp_val)

        # Gera a expressão de comparação
        cond = self.expression(tree.children[3])

        # Compara se a expressão é verdadeira ou não, caso for pula para o bloco do loop, caso contrário pula para o bloco do loop end
        self.block.cbranch(cond, loop_end, loop)

        # Posiciona no inicio do bloco do fim do loop (saída do laço) e define o que o será executado após o fim (o resto do programa)  
        self.block.position_at_end(loop_end)

    def ifExpression(self, tree, func: ir.Function):
        if len(tree.children) == 5:
            iftrue = func.append_basic_block('iftrue')
            ifend = func.append_basic_block('ifend')

            # Condicional
            cond = self.expression(tree.children[1])
            self.block.cbranch(cond, iftrue, ifend)

            # Se
            self.block.position_at_end(iftrue)
            hasReturn = self.body(tree.children[3], func)
            if not hasReturn:
                self.block.branch(ifend)

            self.block.position_at_end(ifend)
        else:
            iftrue = func.append_basic_block('iftrue')
            iffalse = func.append_basic_block('iffalse')
            ifend = None

            # Condicional
            cond = self.expression(tree.children[1])
            self.block.cbranch(cond, iftrue, iffalse)

            # Se
            self.block.position_at_end(iftrue)
            hasReturn = self.body(tree.children[3], func)
            if not hasReturn:
                ifend = func.append_basic_block('ifend')
                self.block.branch(ifend)

            # Senão
            self.block.position_at_end(iffalse)
            hasReturn = self.body(tree.children[5], func)
            if not hasReturn:
                ifend = func.append_basic_block('ifend')
                self.block.branch(ifend)

            if ifend != None:
                self.block.position_at_end(ifend)

    def externalFunctions(self, tree, func: ir.Function):
        if tree.name == 'escreva':
            var = self.expression(tree.children[2])
            type = var.type
            if type == self.INT:
                self.block.call(self.escrevaInteiro, args=[var])
            else:
                self.block.call(self.escrevaFlutuante, args=[var])
        elif tree.name == 'leia':
            var = self.getVar(tree.children[2].children[0].name)
            type = var.type.pointee
            if type == self.INT:
                ret = self.block.call(self.leiaInteiro, args=[])
            else:
                ret = self.block.call(self.leiaFlutuante, args=[])
            self.block.store(ret, var, align=4)
        elif tree.name == 'retorna':
            res = self.expression(tree.children[2])
            self.exit_block = func.append_basic_block("bloco_saida")
            self.block.branch(self.exit_block)
            self.block = ir.IRBuilder(self.exit_block)
            self.block.ret(res)

    def callFunction(self, tree):
        name = tree.children[0].name
        func = self.getFunction(name)
        variables = self.arguments(tree.children[2])
        return self.block.call(func, args=variables)
    
    def arguments(self, tree):
        list_args = tree.children
        args = []
        for arg in list_args:
            name = arg.name
            if name != 'vazio':
                aux = self.expression(arg)
                args.append(aux)
        return args

    def parameters(self, tree):
        list_params = tree.children
        params_name = []
        params_types = []
        for param in list_params:
            if param.name != 'vazio':
                name = param.children[2].name
                type = self.getType(param.children[0].name)
                params_name.append(name)
                params_types.append(type)
        ret = {
            'names': params_name,
            'types': params_types
        }
        return ret 
    
    def expression(self, tree):
        aux = tree.children
        arg1 = None
        arg2 = None
        index = 0 if aux[0].name != '(' else 1

        name = aux[index].name
        if aux[index].name == 'chamada_funcao':
            arg1 = self.callFunction(aux[index])
        elif name == 'var':
            res = self.getVar(aux[index].children[0].name)
            if res == None:
                res = self.getArgs(aux[index].children[0].name)
                arg1 = res
            else:
                if len(aux[index].children) > 1:
                    index_array = self.expression(aux[index].children[1].children[1])
                    array_1 = self.block.gep(res, [self.INT(0), index_array], name='array_1')
                    res = array_1
                arg1 = self.block.load(res)
        elif 'NUM_' in name:
            val_aux = aux[index].children[0].name
            if val_aux in ['0']:
                arg1 = self.ZERO
            else:
                type_aux = self.getType(name)
                val_aux = float(val_aux) if type_aux == self.FLOAT else int(val_aux)
                arg1 = ir.Constant(type_aux, val_aux)
        
        if len(tree.children) > 1:
            name = aux[index+2].name
            if aux[index+2].name == 'chamada_funcao':
                arg2 = self.callFunction(aux[index+2])
            elif name == 'var':
                res = self.getVar(aux[index+2].children[0].name)
                if res == None:
                    res = self.getArgs(aux[index+2].children[0].name)
                    arg2 = res
                else:
                    if len(aux[index+2].children) > 1:
                        index_array = self.expression(aux[index+2].children[1].children[1])
                        array_1 = self.block.gep(res, [self.INT(0), index_array], name='array_1')
                        res = array_1
                    arg2 = self.block.load(res)
            elif 'NUM_' in name:
                val_aux = aux[index+2].children[0].name
                if val_aux in ['0']:
                    arg2 = self.ZERO
                else:
                    type_aux = self.getType(name)
                    val_aux = float(val_aux) if type_aux == self.FLOAT else int(val_aux)
                    arg2 = ir.Constant(type_aux, val_aux)
            else:
                arg2 = self.expression(aux[index+2])

            operator = aux[index+1].name          
            if(operator == "+"): return self.block.add(arg1, arg2, name='summ')
            elif(operator == "-"): return self.block.sub(arg1, arg2, name='sub')
            elif(operator == "*"): return self.block.mul(arg1, arg2, name='mult')
            elif(operator == "/"): return self.block.sdiv(arg1, arg2, name='div')
            elif(operator in ["<",">","=",">=","<=","&&","||"]): 
                operator = "==" if operator == '=' else operator
                return self.block.icmp_signed(operator, arg1, arg2, name='se_entao')
        return arg1

    def getType(self, type_name):
        return self.INT if type_name == 'inteiro' or type_name == 'NUM_INTEIRO' else self.FLOAT        

    def getFunction(self, function_name):
        for func in self.functions:
            if func.name == function_name:
                return func
    
    def getArgs(self, var_name):
        # Verifica os parametros da função
        for paramFunc in self.args_func:
            if paramFunc.name == var_name:
                return paramFunc
        return None
    
    def getVar(self, var_name):
        # Verifica as variaveis globais
        for varGlobal in self.vars_global:
            if varGlobal.name == var_name:
                return varGlobal   
        # Verifica as variaveis locais
        for varLocal in self.vars_local:
            if varLocal.name == var_name:
                return varLocal
        return None

    def saveCode(self):
        file = open('meu_modulo.ll', 'w')
        file.write(str(self.module))
        file.close()
        # print(self.module)

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

# Programa Principal.
if __name__ == "__main__":
    main()