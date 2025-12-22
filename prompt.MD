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

----------------
Write a program csv_merger.py, that take a list of coffee bean feature JSON and merge them into a CSV format file. Detailed requirements are as follows:
1) the program should accept a wildcast file list pattern and process the files that meet that pattern (eg. silver_data/金棕_202505_* will take all the JSON files meet that pattern), and generate a CSV with the same prefix (eg. 金粽_202505_all.csv)
2) it should extract whether the it's common or premium bean based on the input file name (pattern: <provider>_<YYYYMM>_<type>_<chunk>.json). Extract as a new field "type" and value it either "common" or "premium".
3) the JSON parser should take all the "coffee_beans" array and take each JSON object as a line of the CSV file. Include all the existing fields plus the "type" filed. 
4) For the name, flavor_profile, origin fields. Replace all the "," or "，" (Chinese comma character), "、" to a space 
5) For harvest_season, only retain the year as YYYY format (it should be a number)
6) Introduce a new filed "country", parse the country value from the name (it should be the first space delimetered)
7) Remove the lines if name is empty/None

---------------------
Now I need to populate the coffee bean CSV data files into a relational database. Detailed steps as follows: 
1) create a local SQLlite DB
2) provid DDLs to create table/schemas (in the sql folder) for 
a) the coffee_bean table that should take all the CSV fields, additionally add "provider", "data_year" and "data_month" field. These fileds should be determined from the CSV file name (pattern: <provider>_<YYYYMM>.csv)
b) maintain a latest data table for each provider (eg. if the latest data file for 金粽 is 202512, the table should keep the provider name, data year and data month info)
c) create a python program sqlite_populator.py, to take a coffee bean csv file and populate these data into the coffee_bean table; update the latest data table if needed. 

----------------
Need a couple changes
1) The coffee_bean_schema should not have incremental ID as the primary key. Make the (data_year, data_month, name) as the primary key (I need to insert override entries to repopulate data)
2) The latest_data should also not have the incremental ID as the primary key. Make the provider as the primary key. 
3) harvest_season field should be INTEGER (make code changes as needed)
4) the @sqlite_populator.py should take a few command line options to 
 a) drop all the tables
 b) re-create all 
 c) accept a one or more .csv data file and populate (insert override) data


 ----------------
 Write a program in the @flavor_categorization.py to use LLM (please take reference to the @text_llm_parser.py code) (non-streaming node) to categorize the flavor_profiles into flavor_category. 
 1) The program should take a list of JSON file fomatted like @金粽_202512_common_1.json
 2) Take all the 'flavor_profile' & 'code' into a shorter json array
 3) Call LLM to categorize the flavor_profile into a simplifed flavor_category. A sample prompt will look like this. Please optimize the prompt as needed. 
 ## prompt
 Please map the detailed coffee bean flavor description (As a JSON array in the <flavor_profiles> section), into a simplifed flavor category. There are 8 categories with brief description as provided in the <flavor_category> section. 
 
 You should retur a JSON array like follows: 
 [
    {code: "xxx", flavor_profile: "orignal text", flavor_category: "mapped category from 8"},
    ...
 ]

<flavor_profiles> 

```json
[
  {code: "S12", flavor_profile: "花香， 浆果， 红酒， 樱桃， 巧克力， 风味干净。"},
  {code: "E1", flavor_profile: "红酒， 莓果， 热带水果， 焦糖， 巧克力。"},
  ....
]
```
</flavor_profiles> 

<flavor_category>
[
  {
    "flavor_category": "明亮果酸型",
    "description": "柠檬、青苹果、葡萄柚、莓果、白葡萄酒感"
  },
  {
    "flavor_category": "花香茶感型",
    "description": "茉莉、洋甘菊、乌龙茶、蜂蜜、柑橘皮"
  },
  {
    "flavor_category": "果汁感热带水果型",
    "description": "百香果、芒果、菠萝、荔枝、发酵酒香"
  },
  {
    "flavor_category": "均衡圆润型",
    "description": "杏仁、焦糖、蜂蜜、轻微柑橘酸、顺滑口感"
  },
  {
    "flavor_category": "巧克力坚果调型",
    "description": "黑巧克力、榛子、杏仁酱、烤面包、奶油"
  },
  {
    "flavor_category": "焦糖甜感型",
    "description": "焦糖、太妃糖、枫糖、烤瓜子"
  },
  {
    "flavor_category": "酒香发酵型",
    "description": "红酒、威士忌桶、酵素感、蓝莓酱"
  },
  {
    "flavor_category": "烟熏木质型",
    "description": "雪松、烟草、香料、泥土、药草"
  }
]
</flavor_category>
4) Modify the original input JSON file, and attach a new field "flavor_cateogy" for each coffee bean as parsed the by the LLM output.
