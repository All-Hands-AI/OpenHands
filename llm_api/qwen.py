import dashscope
import os


# DO NOT INVOKE DIRECTLY
class qwen:

    dashscope.api_key = os.environ.get('access_key')

    @staticmethod
    def request_model(msg, role, temperature, top_p, penalty_score):
        response = dashscope.Generation.call(
            os.environ.get('model'),  
            messages=msg,   
            result_format='message',
            temperature=temperature,
            top_p=top_p,
            penalty_score=penalty_score 
        )

        return response.output.choices[0]['message']['content']

    
    @staticmethod
    def request_submodel(msg, role, temperature, top_p, penalty_score):
        response = dashscope.Generation.call(
            os.environ.get('submodel'),  
            messages=msg,   
            result_format='message',
            temperature=temperature,
            top_p=top_p,
            penalty_score=penalty_score 
        )
        
        return response.output.choices[0]['message']['content']


    @staticmethod
    def request_embed_model(text: str):
        '''
            没查到资料😭 兄弟们帮帮忙
        '''