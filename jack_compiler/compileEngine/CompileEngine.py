from pathlib import Path

class CompileEngine:
    def __init__(self, tokens:list,xml_path:Path):
        self.tokens = tokens
        self.xml_path=None
        self.level=0#缩进层数
        self.xml_path=xml_path
        self.xml=[]

        self.constructor()



    def _is_symbol(self, token, char=None):
        """判断 token 是否为符号，可选指定符号字符"""
        if not token.startswith('<symbol>'):
            return False
        if char is None:
            return True
        # 格式固定为 '<symbol> X </symbol>'
        parts = token.split()
        return len(parts) > 1 and parts[1] == char

    def _is_operator(self, token):
        """判断 token 是否为二元运算符（+ - * / & | < > =）"""
        if not self._is_symbol(token):
            return False
        op_char = token.split()[1]
        return op_char in '+-*/&|<>='

    def constructor(self):
        #每个文件初始从class开始编译
        self.compileClass()
        #写入文件，注意转义符替换特殊符号
        with open(str(self.xml_path),'a',encoding='utf-8') as f:
            for xml in self.xml:
                i = xml.find('<')
                if i != -1:
                    after_last_space = xml[i:]
                    if after_last_space=='<symbol> < </symbol>':
                        f.write(xml[:i] +'<symbol> &lt; </symbol>'+ '\n')
                        continue
                    elif after_last_space == '<symbol> > </symbol>':
                        f.write(xml[:i] + '<symbol> &gt; </symbol>' + '\n')
                        continue
                    elif after_last_space == '<symbol> & </symbol>':
                        f.write(xml[:i] + '<symbol> &amp; </symbol>' + '\n')
                        continue
                f.write(xml+'\n')


    #根据grammar递归调用，进入函数后根据grammar写入xml，self保存递归层数，进入函数+退出函数—
    #每个函数负责始终和向下判断是否调用
    def compileClass(self):
        #处理'class' className '{'
        self.xml.append(self.level*' '+'<class>')
        self.level+=1
        while self.tokens:
            self.xml.append(self.level * ' ' + self.tokens[0])
            if self.tokens[0] == '<symbol> { </symbol>':
                break
            self.tokens.pop(0)
        self.tokens.pop(0)
        self.compileClassVarDec()
        self.level -= 1
        self.xml.append(self.level*' '+'</class>')





    def compileClassVarDec(self):
        #处理classVarDec，if none，不写入
        writeClassVarDec=False#标记有没有写过起始符
        while self.tokens:
            if self.tokens[0][9:].startswith('static') or self.tokens[0][9:].startswith('field'):
                if not writeClassVarDec:
                    self.xml.append(self.level * ' ' + '<ClassVarDec>')
                    self.level += 1
                    writeClassVarDec=True
                self.xml.append(self.level * ' ' + self.tokens[0])
                self.tokens.pop(0)
                self.compileVarDec()#VarDec消费';'
                # 处理</ClassVarDec>
                self.level -= 1
                self.xml.append(self.level * ' ' + '</ClassVarDec>')
            else:
                break
        self.compileSubroutineDec()







    def compileSubroutineDec(self):
        #处理SubroutineDec，可能有多个，所以还需要循环处理
        while self.tokens and (self.tokens[0]=='<keyword> function </keyword>' or self.tokens[0]=='<keyword> constructor </keyword>' or self.tokens[0]=='<keyword> method </keyword>'):
            self.xml.append(self.level * ' ' + '<SubroutineDec>')
            self.level += 1
            # 消费 'function'/'constructor'/'method'
            self.xml.append(self.level * ' ' + self.tokens.pop(0))
            # 消费返回类型
            self.xml.append(self.level * ' ' + self.tokens.pop(0))
            # 消费函数名
            self.xml.append(self.level * ' ' + self.tokens.pop(0))
            # 消费 '('
            self.xml.append(self.level * ' ' + self.tokens.pop(0))
            # 参数列表
            self.compileParameterList()
            # 消费 ')'
            self.xml.append(self.level * ' ' + self.tokens.pop(0))
            # 函数体
            self.compileSubroutineBody()
            self.level -= 1
            self.xml.append(self.level * ' ' + '</SubroutineDec>')






    def compileParameterList(self):
        #处理ParameterList，遇到)就结束
        if self.tokens[0][1:].startswith('symbol'):#没有参数，起始符和终止符在同一行
            self.xml.append(self.level * ' ' + '<parameterList> </parameterList>')
            return

        self.xml.append(self.level * ' ' + '<parameterList>')
        self.level += 1
        while self.tokens:
            if self.tokens[0].startswith('<symbol>'):#结束
                self.level -= 1
                self.xml.append(self.level * ' ' + '</parameterList>')
                return
            self.xml.append(self.level * ' ' + self.tokens[0])
            self.tokens.pop(0)







    def compileSubroutineBody(self):
        #处理SubroutineBody
        self.xml.append(self.level * ' ' + '<SubroutineBody>')
        self.level += 1
        self.xml.append(self.level * ' ' + self.tokens[0])#<symbol> { </symbol>
        self.tokens.pop(0)
        while self.tokens[0]=='<keyword> var </keyword>':#VarDec*
            self.compileVarDec()
        self.compileStatements()#Statements
        self.xml.append(self.level * ' ' + self.tokens[0])#<symbol> } </symbol>
        self.tokens.pop(0)
        self.level -= 1
        self.xml.append(self.level * ' ' + '</SubroutineBody>')





    def compileVarDec(self):
        #处理VarDec
        self.xml.append(self.level * ' ' + '<VarDec>')
        self.level += 1
        while True:
            self.xml.append(self.level * ' ' + self.tokens[0])
            if self.tokens[0]=='<symbol> ; </symbol>':
                break
            self.tokens.pop(0)
        self.tokens.pop(0)
        self.level -= 1
        self.xml.append(self.level * ' ' + '</VarDec>')





    def compileStatements(self):
        #多条statement，'}'为终止符
        self.xml.append(self.level * ' ' + '<Statements>')
        self.level += 1
        while True:
            if self.tokens[0]=='<symbol> } </symbol>':
                break
            elif  self.tokens[0] == '<keyword> let </keyword>':
                self.compileLet()
            elif  self.tokens[0] == '<keyword> if </keyword>':
                self.compileIf()
            elif  self.tokens[0] == '<keyword> while </keyword>':
                self.compileWhile()
            elif  self.tokens[0] == '<keyword> do </keyword>':
                self.compileDo()
            elif  self.tokens[0] == '<keyword> return </keyword>':
                self.compileReturn()
            else:
                raise TypeError(f'{self.tokens[0]} is not a statement')
        self.level -= 1
        self.xml.append(self.level * ' ' + '</Statements>')

    #我草statement还能是空的

    def compileLet(self):
        self.xml.append(self.level * ' ' + '<letStatement>')
        self.level += 1
        # let
        self.xml.append(self.level * ' ' + self.tokens.pop(0))
        # varName
        self.xml.append(self.level * ' ' + self.tokens.pop(0))
        # 可选数组访问
        if self.tokens and self._is_symbol(self.tokens[0], '['):
            self.xml.append(self.level * ' ' + self.tokens.pop(0))
            self.compileExpression()
            self.xml.append(self.level * ' ' + self.tokens.pop(0))  # ']'
        # '='
        self.xml.append(self.level * ' ' + self.tokens.pop(0))
        # 右边表达式
        self.compileExpression()
        # ';'
        self.xml.append(self.level * ' ' + self.tokens.pop(0))
        self.level -= 1
        self.xml.append(self.level * ' ' + '</letStatement>')




    def compileIf(self):
        """
        if(expression){
            statements
        }else{
        }
        """
        self.xml.append(self.level * ' ' + '<ifStatement>')
        self.level += 1
        # if
        self.xml.append(self.level * ' ' + self.tokens.pop(0))
        # '('
        self.xml.append(self.level * ' ' + self.tokens.pop(0))
        self.compileExpression()
        # ')'
        self.xml.append(self.level * ' ' + self.tokens.pop(0))
        # '{'
        self.xml.append(self.level * ' ' + self.tokens.pop(0))
        self.compileStatements()
        # '}'
        self.xml.append(self.level * ' ' + self.tokens.pop(0))
        # else 部分（可选）
        if self.tokens and self.tokens[0] == '<keyword> else </keyword>':
            self.xml.append(self.level * ' ' + self.tokens.pop(0))
            self.xml.append(self.level * ' ' + self.tokens.pop(0))  # '{'
            self.compileStatements()
            self.xml.append(self.level * ' ' + self.tokens.pop(0))  # '}'
        self.level -= 1
        self.xml.append(self.level * ' ' + '</ifStatement>')









    def compileWhile(self):
        """
        while(expression){
            statement
        }
        和ifstatement差不多
        """

        self.xml.append(self.level * ' ' + '<whileStatement>')
        self.level += 1
        # while
        self.xml.append(self.level * ' ' + self.tokens.pop(0))
        # '('
        self.xml.append(self.level * ' ' + self.tokens.pop(0))
        self.compileExpression()
        # ')'
        self.xml.append(self.level * ' ' + self.tokens.pop(0))
        # '{'
        self.xml.append(self.level * ' ' + self.tokens.pop(0))
        self.compileStatements()
        # '}'
        self.xml.append(self.level * ' ' + self.tokens.pop(0))

        self.level -= 1
        self.xml.append(self.level * ' ' + '</whileStatement>')






    def compileDo(self):
        #do SubroutineCall，SubroutineCall属于term，起始符直接都成dostatement了
        #虽然project里是把subcall归并到do里，但我管它丫的，反正后面都要改
        self.xml.append(self.level * ' ' + '<doStatement>')
        self.level += 1

        self.xml.append(self.level * ' ' + self.tokens[0])
        self.tokens.pop(0)#do
        self.compileTerm()
        self.xml.append(self.level * ' ' + self.tokens[0])
        self.tokens.pop(0)#';'

        self.level -= 1
        self.xml.append(self.level * ' ' + '</doStatement>')






    def compileReturn(self):
        #return (expression);
        self.xml.append(self.level * ' ' + '<returnStatement>')
        self.level += 1


        self.xml.append(self.level * ' ' + self.tokens[0])
        self.tokens.pop(0)
        if self.tokens[0] != '<symbol> ; </symbol>':
            self.compileExpression()
        self.xml.append(self.level * ' ' + self.tokens[0])
        self.tokens.pop(0)


        self.level -= 1
        self.xml.append(self.level * ' ' + '</returnStatement>')







    def compileExpression(self):
        """
        解析表达式: term (op term)*
        终止符: ; , ) } 以及 let 语句中的 =（但 = 在表达式中是比较运算符，不终止）
        """
        self.xml.append(self.level * ' ' + '<expression>')
        self.level += 1

        # 第一个 term
        self.compileTerm()

        # 后续的 op term
        while self.tokens and self._is_operator(self.tokens[0]):
            # 输出运算符
            self.xml.append(self.level * ' ' + self.tokens.pop(0))
            # 下一个 term
            self.compileTerm()

        self.level -= 1
        self.xml.append(self.level * ' ' + '</expression>')









    def compileTerm(self):
        """
        uni label:
            constant int
            constant str
            constant keyword
        identifier:
            varName
            varName[expression]
            subroutineCall
        symbol:
            (expression)
            unaryOp term

        这我编译nm呢
        keyword也算term那我class，function，statement全都要传进来，烦死了，反正xml里也没这么干，等会把keyword从term里删了
        """
        self.xml.append(self.level * ' ' + '<term>')
        self.level += 1

        while True:#只是为了模拟switch-case，不是真循环
            if self.tokens[0][1:].startswith('integerConstant'):
                self.xml.append(self.level * ' ' + self.tokens[0])
                self.tokens.pop(0)
                break
            if self.tokens[0][1:].startswith('stringConstant'):
                self.xml.append(self.level * ' ' + self.tokens[0])
                self.tokens.pop(0)
                break
            """
            if self.tokens[0][1:].startswith('keyword'):
                self.xml.append(self.level * ' ' + self.tokens[0])
                self.tokens.pop(0)
                break
            """
            if self.tokens[0][1:].startswith('identifier'):
                #varName
                #varName[expression]
                #subroutineCall
                if self.tokens[1]=='<symbol> [ </symbol>':
                    for i in range(2):
                        self.xml.append(self.level * ' ' + self.tokens[0])
                        self.tokens.pop(0)

                    self.compileExpression()

                    self.xml.append(self.level * ' ' + self.tokens[0])
                    self.tokens.pop(0)

                elif self.tokens[1] == '<symbol> ( </symbol>':
                    for i in range(2):
                        self.xml.append(self.level * ' ' + self.tokens[0])
                        self.tokens.pop(0)

                    self.compileExpressionList()

                    self.xml.append(self.level * ' ' + self.tokens[0])
                    self.tokens.pop(0)

                elif self.tokens[1] == '<symbol> . </symbol>':#class.function也是函数
                    for i in range(4):
                        self.xml.append(self.level * ' ' + self.tokens[0])
                        self.tokens.pop(0)

                    self.compileExpressionList()

                    self.xml.append(self.level * ' ' + self.tokens[0])
                    self.tokens.pop(0)
                elif self.tokens[1].startswith('<symbol>') and self.tokens[1] not in['<symbol> [ </symbol>', '<symbol> ( </symbol>', '<symbol> . </symbol>']:
                    self.xml.append(self.level * ' ' + self.tokens[0])
                    self.tokens.pop(0)
                else:raise TypeError(f'{self.tokens[0]} is not a varname or array[expression] or function/method/constructor')
                break
            if self.tokens[0][1:].startswith('symbol') and self.tokens[0] not in['<symbol> [ </symbol>', '<symbol> ( </symbol>', '<symbol> . </symbol>']:
                #(expression)
                #unaryOp term
                if self.tokens[0]=='<symbol> ( </symbol>':
                    self.xml.append(self.level * ' ' + self.tokens[0])
                    self.tokens.pop(0)
                    self.compileExpression()
                    self.xml.append(self.level * ' ' + self.tokens[0])
                    self.tokens.pop(0)
                else:
                    self.xml.append(self.level * ' ' + self.tokens[0])
                    self.tokens.pop(0)
                    self.compileTerm()
                break
            else:
                raise TypeError(f'{self.tokens[0]} is not a term又是他宝贝的哪个b报错了')

        self.level -= 1
        self.xml.append(self.level * ' ' + '</term>')











    def compileExpressionList(self):
        #expression(,expression)*
        # subroutineCall时使用，即传参
        #分隔符为','，调用compileExpression，终止符为')'
        self.xml.append(self.level * ' ' + '<ExpressionList>')
        self.level += 1

        while self.tokens:
            if self.tokens[0]=='<symbol> ) </symbol>':
                break
            if self.tokens[0]=='<symbol> , </symbol>':
                self.xml.append(self.level * ' ' + self.tokens[0])
                self.tokens.pop(0)
            self.compileExpression()

        self.level -= 1
        self.xml.append(self.level * ' ' + '</ExpressionList>')

#总算把大概写完了wcnmd
