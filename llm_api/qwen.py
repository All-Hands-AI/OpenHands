import dashscope
import os

class qwen:

    @staticmethod
    def request_model(msg):
        response = dashscope.Generation.call(
            os.environ.get('model'),  
            messages=msg,   
            result_format='message',   
        )

        return response.output.choices[0]['message']['content']

    
    @staticmethod
    def request_submodel(msg):
        response = dashscope.Generation.call(
            os.environ.get('submodel'),  
            messages=msg,   
            result_format='message',   
        )
        
        return response.output.choices[0]['message']['content']


    @staticmethod
    def request_embed_model(text: str):
        '''
            没查到资料😭 兄弟们帮帮忙
        '''