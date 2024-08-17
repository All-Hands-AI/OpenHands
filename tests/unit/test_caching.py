import pytest

from opendevin.core.config import LLMConfig
from opendevin.llm.llm import LLM

sample_text = """
Carnegie Mellon University (CMU) is a private research university in Pittsburgh, Pennsylvania. The institution was established in 1900 by Andrew Carnegie as the Carnegie Technical Schools. In 1912, it became the Carnegie Institute of Technology and began granting four-year degrees. In 1967, it became Carnegie Mellon University through its merger with the Mellon Institute of Industrial Research, founded in 1913 by Andrew Mellon and Richard B. Mellon and formerly a part of the University of Pittsburgh.[11]
The university consists of seven colleges, including the College of Engineering, the School of Computer Science, and the Tepper School of Business.[12] The university has its main campus located 5 miles (8 km) from Downtown Pittsburgh. It also has over a dozen degree-granting locations in six continents, including campuses in Qatar, Silicon Valley, and Kigali, Rwanda (Carnegie Mellon University Africa) and partnerships with universities nationally and globally.[13] Carnegie Mellon enrolls 15,818 students across its multiple campuses from 117 countries and employs more than 1,400 faculty members.[14]
Carnegie Mellon is known for its advances in research and new fields of study, home to many firsts in computer science (including the first machine learning, robotics, and computational biology departments), pioneering the field of management science,[15] and the first drama program in the United States. Carnegie Mellon is a member of the Association of American Universities and is classified among "R1: Doctoral Universities – Very High Research Activity".[16]
Carnegie Mellon competes in NCAA Division III athletics as a founding member of the University Athletic Association. Carnegie Mellon fields eight men's teams and nine women's teams as the Tartans.[17] The university's faculty and alumni include 20 Nobel Prize laureates and 13 Turing Award winners and have received 142 Emmy Awards, 52 Tony Awards, and 13 Academy Awards.[18]
History
Andrew Carnegie
Andrew Carnegie, founder of the Carnegie Technical Schools.
Andrew Mellon
Andrew Mellon, co-founder of the Mellon Institute.
The Carnegie Technical Schools were founded in 1900 in Pittsburgh, Pennsylvania[19] by the Scottish-American industrialist and philanthropist Andrew Carnegie, who wrote "My heart is in the work", when he donated the funds to create the institution. Carnegie's vision was to open a vocational training school for the sons and daughters of working-class Pittsburghers, many of whom worked in his mills. Carnegie was inspired for the design of his school by the Pratt Institute in Brooklyn, New York, founded by industrialist Charles Pratt in 1887.[20] In 1912, the institution changed its name to Carnegie Institute of Technology (CIT) and began offering four-year degrees. During this time, CIT consisted of four constituent schools: the School of Fine and Applied Arts, the School of Apprentices and Journeymen, the School of Science and Technology, and the Margaret Morrison Carnegie School for Women.
The Mellon Institute of Industrial Research was founded in 1913 by banker and industrialist brothers Andrew Mellon (who went on to become U.S. Treasury Secretary) and Richard B. Mellon in honor of their father, Thomas Mellon, patriarch of the Mellon family. The Institute began as a research organization that performed contract work for government and industry, initially as a department within the University of Pittsburgh. In 1927, the Mellon Institute was incorporated as an independent nonprofit. In 1937, the Mellon Institute's iconic building was completed on Fifth Avenue.[21]
In 1967, with support from Paul Mellon, the Carnegie Institute of Technology merged with the Mellon Institute of Industrial Research to become Carnegie Mellon University. In 1973, Carnegie Mellon's coordinate women's college, the Margaret Morrison Carnegie College, merged its academic programs with the rest of the university.[22] The industrial research mission of the Mellon Institute survived the merger as the Carnegie Mellon Research Institute (CMRI) and continued doing work on contract to industry and government. In 2001, CMRI's programs were subsumed by other parts of the university or spun off into autonomous entities.[23]
Carnegie Mellon's 157.2 acre (63 ha) main campus is five miles (8 km) from downtown Pittsburgh, between Schenley Park and the neighborhoods of Squirrel Hill, Shadyside, and Oakland.[5] Carnegie Mellon is bordered to the west by the campus of the University of Pittsburgh. Carnegie Mellon owns 81 buildings in the Oakland and Squirrel Hill neighborhoods of Pittsburgh.
For decades, the center of student life on campus was Skibo Hall, the university's student union. Built in the 1950s, Skibo Hall's design was typical of mid-century modern architecture but was poorly equipped to deal with advances in computer and internet connectivity. The original Skibo Hall was razed in the summer of 1994 and replaced by a new student union that is fully Wi-Fi enabled. Known as the University Center, the building was dedicated in 1996. In 2014, Carnegie Mellon re-dedicated the University Center as the Cohon University Center in recognition of the eighth president of the university, Jared Cohon.[24]
A large grassy area known as "The Cut" forms the backbone of the campus, with a separate grassy area known as "The Mall" running perpendicular. The Cut was formed by filling in a ravine (hence the name) with soil from a nearby hill that was leveled to build the College of Fine Arts building.
The northwestern part of the campus (home to Hamburg Hall, Newell-Simon Hall, Smith Hall, and Gates Hillman Complex) was acquired from the United States Bureau of Mines in the 1980s.
Carnegie Mellon has been purchasing 100 renewable energy for its electricity since 2011.[25]
During the 1970s and 1980s, the tenure of president Richard Cyert (1972–1990) witnessed a period of growth and development. The research budget grew from roughly $12 million annually in the early 1970s to more than $110 million in the late 1980s. Researchers in new fields like robotics and software engineering helped the university to build its reputation. One example was the introduction of the "Andrew" computing network in the mid-1980s. This project linking all computers and workstations on campus set the standard for educational computing and established Carnegie Mellon as a technology leader in education and research. On April 24, 1985, cmu.edu, Carnegie Mellon's Internet domain, became one of the first six .edu domain names.
In April 2015, Carnegie Mellon, in collaboration with Jones Lang LaSalle, announced the planning of a second office space structure, alongside the Robert Mehrabian Collaborative Innovation Center, an upscale and full-service hotel, and retail and dining development along Forbes Avenue. This complex will connect to the Tepper Quadrangle, the Heinz College, the Tata Consultancy Services Building, and the Gates-Hillman Center to create an innovation corridor on the university campus. The effort is intended to continue to attract major corporate partnerships to create opportunities for research, teaching, and employment with students and faculty.[38]
On October 30, 2019, Carnegie Mellon publicly announced the launch of "Make Possible: The Campaign for Carnegie Mellon University", a campaign which seeks to raise $2 billion to advance the university's priorities, including campus development.[39] Alongside the Tepper Quad and Hamburg Hall, Carnegie Mellon finished construction in 2020 on TCS Hall, an innovation center made possible with a $35 million gift from Tata Consultancy Services.[40] Carnegie Mellon plans to collaborate with Emerald Cloud Lab to construct the world's first cloud lab in a university setting. The Carnegie Mellon University Cloud Lab is planned to be completed by the spring of 2023. Carnegie Mellon also plans to construct a new mechanical engineering building by fall 2023 (Scaife Hall), a new $105 million athletics center by fall 2024 (Highmark Center for Health, Wellness and Athletics), a $210 million Science Futures Building (R.K. Mellon Hall of Sciences) by 2026,[41] as well as a Robotics Innovation Center at Hazelwood Green, in addition to new dormitories and other buildings in the coming years.[42]
"""


def test_anthropic_model_caching_behavior_sync():
    llm = LLM(config=LLMConfig(model='anthropic/claude-3-5-sonnet-20240620'))

    messages = [
        {
            'role': 'system',
            'content': [
                {
                    'type': 'text',
                    'text': 'Analyze this text for caching.'
                    + sample_text
                    + sample_text,
                },
            ],
        },
        {'role': 'user', 'content': 'What are the key points?'},
    ]

    response1 = llm._completion(messages=messages)
    assert response1 is not None
    assert 'choices' in response1
    print(response1)

    response2 = llm._completion(messages=messages)
    assert response2 is not None
    assert 'choices' in response2

    cache_read_input_tokens1 = response1.usage.cache_read_input_tokens
    cache_read_input_tokens2 = response2.usage.cache_read_input_tokens
    assert cache_read_input_tokens2 >= cache_read_input_tokens1
    assert cache_read_input_tokens2 != 0


@pytest.mark.asyncio
async def test_anthropic_model_caching_behavior():
    llm = LLM(config=LLMConfig(model='anthropic/claude-3-5-sonnet-20240620'))

    # Initial message that will be cached
    messages = [
        {
            'role': 'system',
            'content': [
                {
                    'type': 'text',
                    'text': 'Analyze this text for caching.'
                    + sample_text
                    + sample_text,
                },
            ],
        },
        {'role': 'user', 'content': 'What are the key points?'},
    ]

    response1 = await llm._async_completion(messages=messages)
    assert response1 is not None
    assert 'choices' in response1

    # Perform the same request again
    response2 = await llm._async_completion(messages=messages)
    assert response2 is not None
    assert 'choices' in response2

    # Extract cache_read_input_tokens from both responses
    cache_read_input_tokens1 = response1.usage.cache_read_input_tokens
    cache_read_input_tokens2 = response2.usage.cache_read_input_tokens
    # Check if cache_read_input_tokens of response2 is greater than response1
    assert cache_read_input_tokens2 >= cache_read_input_tokens1
    assert cache_read_input_tokens2 != 0


# @pytest.mark.asyncio
# async def test_gemini_model_without_cache_control():
#     llm = LLM(config=LLMConfig(model='gemini-1.5-flash'))
#     messages = [
#         {"role": "system", "content": "You are an AI assistant."},
#         {"role": "user", "content": "What are the key points?"},
#     ]
#     response = await llm._async_completion(messages=messages)
#     assert response is not None
#     assert 'choices' in response


@pytest.mark.asyncio
async def test_anthropic_model_streaming():
    llm = LLM(config=LLMConfig(model='anthropic/claude-3-5-sonnet-20240620'))
    messages = [
        {'role': 'system', 'content': 'You are an AI assistant.'},
        {
            'role': 'user',
            'content': 'Stream the document analysis.' + sample_text + sample_text,
        },
    ]
    async for chunk in llm._async_streaming_completion(messages=messages):
        assert 'choices' in chunk
        assert 'delta' in chunk['choices'][0]
