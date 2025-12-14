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

Write a python program that can accept a list of PDF file based raw coffee bean quotations, parse the contents using LLM (refer to the @roast_plan_recommender.py code on how to call the QWen LLM), and generate CSV files. More detailed requirements are provided as follows: 
1) The PDF files are named as <Brand>_<YYYYMM> format, eg. (金粽_202501.pdf), Generate corresponding CSV files in the similar format. You need to generate two CSV file per PDF. One for beans in "常用生豆报价单" section, one in "精品生豆" section.
2) Optimize the prompt provided here to the LLM to make the PDF context extraction more reliable and accurate. 
## prompt to LLM for parsing PDF contents 
Parsing the PDF raw coffee bean quotations and generate CSV format coffee bean features. Generate two CSVs for "常用生豆报价单" and "精品生豆" sections. For each line in CSV, you should parse the features like: 咖啡豆名，风味，产区，品种，等级，含水量，处理法，密度值，海拔，规格，产季，每公斤价格，每5公斤价格，整包价格。A few more cautions for the content extractions: 
1) If there is any content contains ',', which is the CSV file delimiter, replace the ',' to ' ' (space)
2) For the 咖啡豆名 field, remove all the spaces in the name
3) If there are fields you can't extract, simply leave them blank (eg. there could be beans that don't have a per-KG price or per-5KG-price)
