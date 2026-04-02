from pathlib import Path

from jack_compiler.jack_tokenizer.JackTokenizer import JackTokenizer
from jack_compiler.compileEngine.CompileEngine import CompileEngine


class JackCompiler:
    def __init__(self, jack_directory:Path):
        self.jack_directory = jack_directory
        self.jack_files = []
        self.get_vm_files()
        self.token_stream=[]
        self.xml_path = None
        self.tokenizer = None
        self.compileEngine = None
        self.compile()


    def get_vm_files(self):
        path = Path(self.jack_directory)
        self.jack_files = list(path.glob('*.jack'))


    def set_xml(self):
        self.xml_path = self.jack_directory / f"{self.jack_directory.name}.xml"
        import os
        if os.path.exists(self.xml_path):
            os.remove(self.xml_path)
        self.xml_path.touch()

    def compile(self):
        # 从main开始编译
        self.set_xml()

        if len(self.jack_files) > 0:
            try:
                jack_files_i = self.jack_files.index('Main')
            except ValueError:
                jack_files_i = 0


            self.tokenizer=JackTokenizer(self.jack_files[jack_files_i])
            self.compileEngine=CompileEngine(self.tokenizer.token_stream,self.xml_path)
            self.jack_files.pop(jack_files_i)
