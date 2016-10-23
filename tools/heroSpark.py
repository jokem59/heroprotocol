import imp
from pyspark.sql import SparkSession

# imports module from separate directory
formatter = imp.load_source('formatter', '/Users/JoeK/heroprotocol/tools/formatter.py')

dictInitData = formatter.createDictInitData('/Users/JoeK/heroprotocol/tools/init_data')
replayId = formatter.getReplayId(dictInitData)

# always searches pwd from where script is executed
df = formatter.createJsonAEDH('/Users/JoeK/heroprotocol/tools/header.txt', replayId)

spark = SparkSession \
    .builder \
    .appName("JSON format test") \
    .config("spark.some.config.option", "some-value") \
    .getOrCreate()

# Expects file to be at /Users/JoeK/spark-2.0.1-bin-hadoop2.7/python/
df = spark.createDataFrame(df)
print "\n"
df.show()
print "\n"
