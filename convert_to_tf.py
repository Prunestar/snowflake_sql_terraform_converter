import re
import argparse

#TODO: fix naming convention issue with grant_table and schema etc. Find better way to align with the way the terraform hierarchy works compared to sql. 
#TODO: add functionality for other terraform snowflake functionality. 

class SnowflakeTerraformWriter():

    def __init__(self, sql_file_location):
        """initialision of class

        Args:
            sql_file_location (string): The path to a sql file. 
        """
        self.sql_file = open(sql_file_location)
        self.command_list = []
    
    def get_commands(self):
        """Formats the sql file into a dict of {comment: [list of commands up until next comment]}
        """
        sql_file2 = self.sql_file.read()
        data_list = sql_file2.split(';')
        self.sql_dict = {}
        for index in range(len(data_list)):
            item = data_list[index].replace('\n','')
            #print(item)
            if '--' in item:
                #print(item)
                self.sql_dict[item.lower().replace('\n','')] = []
                index_record = index
            else:
                if item:
                    self.sql_dict[data_list[index_record].lower().replace('\n','')].append(item)

    def set_database(self, commands):
        """Extracts the database from a sql command and sets it to the class db value

        Args:
            commands (list(string)): A list of use database commands (should be max length 1)
        """
        
        command = commands[0]
        db_name = command.lower().split('use database ')[1].upper()

        self.db = db_name

    def set_schema(self, commands):
        """Extracts the schema name from a "USE SCHEMA " sql command and sets it to the class schema value

        Args:
            commands (list(string)): List of commands max length=1. 
        """
        
        command = commands[0]
        sch_name = command.lower().split('use schema ')[1].upper()

        self.schema = sch_name
    

    def create_database(self, commands):
        """Appends to the command list a set of terraform commands to create databases in snowflake

        Args:
            commands (list(string)): List of commands of form CREATE DATABASE IF NOT EXISTS
        """
        
        for command in commands:
            db_name = command.lower().split('create database if not exists ')[1].upper()
            
            terraform_command = """resource "snowflake_database" "{0}" {{
    name                        = "{0}"
    }}""".format(db_name)

            self.command_list.append(terraform_command)
        

    def grant_database(self, commands):
        """Appends to the command list a set of terraform resources to grant database wide permission to a user

        Args:
            commands (list(string)): List of commands of form GRANT <PERMISSION> ON DATABASE <DB> TO <ROLE> 
        """
        

        for command in commands:
            privilege = command.lower().split('grant')[1].split(' ')[1].upper()
            db_name = command.lower().split('on database')[1].split(' ')[1].upper()
            role_name = command.lower().split('to')[1].split(' ')[1].upper()
            
            terraform_command = """resource snowflake_database_grant {0}_{2}_grant {{
    database_name = "{0}"

    privilege = "{1}"
    roles     = ["{2}"]
    }}""".format(db_name, privilege, role_name)

            self.command_list.append(terraform_command)



    def grant_schema(self, commands):
        """Appends to the command list a set of terraform resources to grant permission on all tables in a database or schema

        Args:
            commands (list(string)): List of commands of form GRANT <PERMISSION> ON DATABASE <DB> IN SCHEMA TO <ROLE> 
        """

        for command in commands:
            if 'future' in command.lower():
                future_flag = 'true'
            else:
                future_flag = 'false'
            privilege = command.lower().split('grant')[1].split(' ')[1].upper()
            db_name = command.lower().split('in database')[1].split(' ')[1].upper()
            role_name = command.lower().split('to')[1].split(' ')[1].upper()

            
            terraform_command = """resource snowflake_schema_grant {2}_schema_grant {{
    database_name = "{0}"

    privilege = "{1}"
    roles     = ["{2}"]

    on_future         = {3}
    with_grant_option = false
    }}""".format(db_name, privilege, role_name, future_flag)

            self.command_list.append(terraform_command)


    def create_schemas(self, commands):
        """Appends to the command list a set of terraform resources to create schemas in the set database

        Args:
            commands (list(string)): List of commands of form CREATE SCHEMA <schema>
        """

        db_name = self.db
        
        for command in commands:
            sch_name = command.lower().split('create schema if not exists ')[1].upper()
            
            terraform_command = """resource snowflake_schema {0}_{1}_schema {{
    database = "{0}"
    name     = "{1}"
    }}""".format(db_name, sch_name)

            self.command_list.append(terraform_command)
        

    def grant_table(self, commands):
        """Appends to the command list a set of terraform resources to grant permission on all tables in a schema or selected tables

        Args:
            commands (list(string)): List of commands of form GRANT <PERMISSION> ON <TABLES> IN SCHEMA TO <ROLE> 
        """

        db_name = self.db

        for command in commands:
            if 'future' in command.lower():
                future_flag = 'true'
            else:
                future_flag = 'false'
            
            privileges = re.search('grant(.*?)on', command.lower()).group(1)
            schema = re.search('schema(.*?)to', command.lower()).group(1).strip().upper()
            role = re.search(' to(.*)', command.lower()).group(1).strip().upper()

            for privilege in privileges.split(','):

                terraform_command = """resource snowflake_table_grant {0}_{1}_{2}_{3}_grant {{
                        database_name = "{0}"
                        schema_name = "{1}"

                        privilege = "{2}"
                        roles     = ["{3}"]

                        on_future         = {4}
                        }}""".format(db_name, schema, privilege.upper().strip(), role, future_flag )

                self.command_list.append(terraform_command)

    def create_tables(self, commands):
        """Appends to the command list a set of terraform resources to create schemas in the set database and set schema

        Args:
            commands (list(string)): List of commands of form CREATE TABLE IF NOT EXISTS <table> (column_name:type....,)
        """

        schema_name = self.schema
        db_name = self.db


        for num,command in enumerate(commands):
            #print(num,command)

            table_name = re.search('table(.*?)\(', command.lower()).group(1).replace('if not exists', '').upper().strip()
            columns = command.lower().split(',')
            first_column = columns[0].split('(')[1]
            last_column = columns[-1][:-1]
            columns[0] = first_column
            columns[-1] = last_column
            column_list = []

            for col_detail in columns:

                try:
                    column_terra_text = """
                    column {
                        name ="""+col_detail.replace('\n','').replace("\t"," ").strip().split('" ')[0]+'''"
                        type = "'''+col_detail.replace('\n','').replace("\t"," ").strip().split('" ')[1]+'''"
                    }
                    '''

                    column_list.append(column_terra_text)
                except:
                    print(col_detail.replace('\n','').strip().split('" '))
                    raise 'fucked it'
            
            columns_to_add = '\n'.join(column_list)

            terraform_command = """resource snowflake_table {1}_{2}_table {{
    database = "{0}"
    schema   = "{1}"
    name     = "{2}"

    {3}
    }}""".format(db_name, schema_name, table_name, columns_to_add)

            self.command_list.append(terraform_command)

    
    def write_tf(self, path):
        """Writes the arguments in the command list to a file at the given path

        Args:
            path (string): Path to write the terraform file to.
        """

        self.command_list.insert(0, '# A terraform file created from a sql file')

        with open(path, 'w') as fil:

            for item in self.command_list:
                fil.write(item)
                fil.write('\n\n')
    
if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--sql_path", help="the path to the sql file")
    parser.add_argument("--output_path", help="the path to write the terraform file to must end with file name e.g. /main.tf")
    args = parser.parse_args()

    snwt = SnowflakeTerraformWriter(args.sql_path)
    snwt.get_commands()

    for item in snwt.sql_dict:

        method_name = item.split(' ')[1]
        func = getattr(snwt, method_name)
        if callable(func):
            func(snwt.sql_dict[item])

    snwt.write_tf(args.output_path)


