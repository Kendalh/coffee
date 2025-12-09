Please only make changes to the @test-dashscope.py. You need to optimize the prompt sending to the LLM to meet my requirements. The prompt should accept structured JSON inputs that are raw coffee bean feature like below: (Translate the Chinese into English words to fit JSON format)
<input_prompt>
{
    产地：xx,
    品种：xx,
    密度: xx,
    海拔: xx, 
    含水量: xx,
    处理方式: xx,
    等级: xx,
    期待风味: xx
    
}
</input_prompt>
The output should be a roasting profile that is structured in JSON format like below: 
<output_format>
{
    general_suggestions: xx 
    artisan_alog: {...}
}
</output_format>
The general suggestions like when and how the roastinng phases are progressed should be put into the "general_suggestions" field. The Artisan software accepted alog file data (notice it's aslo JSON format) should be put into the "artisan_alog" field. 

------------

Create a data class for "desired_flavor". It should contains values of the following:
明亮果酸型(Bright & Fruity Acidity),
花香茶感型(Floral & Tea-like),
果汁感热带水果型(Juicy & Tropical Fruit),
均衡圆润型(Balanced & Clean),
巧克力坚果调型(Chocolate & Nutty),
焦糖甜感型(Caramel Sweetness),
酒香发酵型(Winey & Fermented),
烟熏木质型(Earthy & Spicy). 
For the tests in @test_api.py, randomly pick one falvor as input. 

-------------
