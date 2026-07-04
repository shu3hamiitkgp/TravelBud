from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, TEXT, Identity, inspect, select, update
from sqlalchemy_utils import database_exists, create_database
import os
from dotenv import load_dotenv

load_dotenv()

class DB:
    metadata = MetaData()
    
    def __init__(self):
        self.engine=create_engine('postgresql://'+str(os.environ.get('DB_USER_NAME'))+':'+str(os.environ.get('DB_PASSWORD'))+'@'+str(os.environ.get('DB_HOST'))+':5432/'+str(os.environ.get('DB_NAME')))
    
    def runQuery(self, query):
        with self.engine.connect() as conn:
            result = conn.execute(query)
        return result
    
    def selectAll(self, table):
        query = table.select()
        return self.runQuery(query)
    
    def selectWhere(self, table, column, value):
        query = table.select().where(table.c[column]==value)
        return self.runQuery(query)
    
    def insertRow(self, table, values):
        query = table.insert().values(values)
        return self.runQuery(query)
    
    def updateRow(self, table, column, value, whereColumn, whereValue):
        query = table.update().where(table.c[whereColumn]==whereValue).values({column: value})
        # query = update(table).values({column: value}).where(whereColumn == whereValue)
        return self.runQuery(query)
    
    def deleteByValue(self, table, column, value):
        query = table.delete().where(table.c[column] == value)
        return self.runQuery(query)
    
    def createTable(self, table):
        table.create(self.engine)

    def dropTable(self, table):
        table.drop(self.engine)

    def tableExists(self, tableName):
        return self.engine.dialect.has_table(self.engine.connect(), tableName)
    
    def getTableMetaData(self, tableName):
        return inspect(self.engine).get_columns(tableName)
    
    def getTableNames(self):     
        return self.engine.table_names()
    
    def getTable(self, tableName):
        if self.tableExists(tableName):
            return Table(tableName, self.metadata, autoload_with=self.engine)
        else:
            return "No such table exists"