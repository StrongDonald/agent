import commune as c
import time
import os
# import agent as h

class Agent:
    prompt = """
        -- SYSTEM --
        YOU ARE A CODER, YOU ARE MR.ROBOT, YOU ARE TRYING TO BUILD IN A SIMPLE
        LEONARDO DA VINCI WAY, YOU ARE A agent, YOU ARE A GENIUS, YOU ARE A STAR, 
        YOU FINISH ALL OF YOUR REQUESTS WITH UTMOST PRECISION AND SPEED, YOU WILL ALWAYS 
        MAKE SURE THIS WORKS TO MAKE ANYONE CODE. YOU HAVE THE CONTEXT AND INPUTS FOR ASSISTANCE
        - Please use  to name the repository and
        - This is a a full repository construction and please
        - INCLUDE A README.md AND a scripts folder with the build.sh 
        - file to build hte environment in docker and a run.sh file 
        - to run the environment in docker
        - INCLUDE A TESTS folder for pytests
        -- CONTEXT --
        IF YOU HAVE A CONTEXT, THEN ONLY REPLACE FILES IN THE CONTEXT
        {context}
        -- OUTPUT FORMAT --
        <{output_start}(path/to/file)> # start of file
        FILE CONTENTS
        <{output_end}(path/to/file)> # end of file
        """
    edit_start = 'EDIT_START'
    edit_end = 'EDIT_END'
    output_start = 'OUTPUT_START'
    output_end = 'OUTPUT_END'

    def __init__(self, 
                 model = None,
                 key = None,
                **kwargs):
        
        self.model = c.module('model.openrouter')(model=model)
        self.models = self.model.models()
        self.key = c.get_key(key)

    def generate(self, 
                 text = 'whats 2+2?', 
                 *extra_text, 
                 temperature= 0.5, 
                 max_tokens= 1000000, 
                 model= 'anthropic/claude-3.5-sonnet', 
                 path = None,
                 context = None,
                 stream=True
                 ):
        
        if os.path.exists(path):
            context = path
        
        if len(extra_text) > 0:
            text = ' '.join(list(map(str, [text] +list(extra_text))))
        context = c.file2text(context) if context else ''
        text = self.prompt.format(output_start=self.output_start,  
                                  output_end=self.output_end, 
                                  context=context) + '\n' + text
        output =  self.model.generate( text,stream=stream, model=model, max_tokens=max_tokens, temperature=temperature )
        return self.process_output(output, path)
    
    def process_output(self, response, path=None):
        # generator = self.search_output('app')
        if path == None:
            return response
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
        assert os.path.exists(path), f'Path does not exist: {path}'
        path = os.path.abspath(path)
        buffer = '-------------'
        output_start = f'<{self.output_start}('
        output_end = f'<{self.output_end}('
        color = c.random_color()
        content = ''
        for token in response:
            content += str(token)
            is_file_in_content =  content.count(output_start) == 1 and content.count(output_end) == 1
            c.print(token, end='', color=color)
            if is_file_in_content:
                file_path = content.split(output_start)[1].split(')>')[0]
                file_path_tag = f'{output_start}{file_path})>'
                file_content = content.split(file_path_tag)[1].split(output_end)[0]
                self.write_file(path + '/' + file_path, file_content)
                c.print(buffer,'Writing file --> ', file_path, buffer, color=color)
                content = ''
                color = c.random_color()
        
        return {'path': path, 'msg': 'File written successfully'}

    def write_file(self,  path, data):
        path_dir = '/'.join(path.split('/')[:-1])
        if not os.path.exists(path_dir):
            os.makedirs(path_dir, exist_ok=True)
        with open(path, 'w') as f:
            f.write(data)

    def read_file( self, file_path):
        with open(file_path, 'r') as f:
            return f.read()
    

    def load_prompt( self, path):
        prompt_dir = '/'.join(__file__.split('/')[:-2]) + '/prompts'
        if prompt_dir not in path:
            path = prompt_dir  + path + '.txt'
        return self.read_file(path)


    def prompt_args(self):
        # get all of the names of the variables in the prompt
        prompt = self.prompt
        variables = []
        for line in prompt.split('\n'):
            if '{' in line and '}' in line:
                variable = line.split('{')[1].split('}')[0]
                variables.append(variable)
        return variables
