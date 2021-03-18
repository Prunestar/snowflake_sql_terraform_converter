# snowflake_sql_terraform_converter
A script that dynamically constructs terraform files to create resources in snowflake given a sql file. 

## Usage 

```bash
python <path-to>/convert_to_tf.py --sql_path <path_to_sql_file> --output_path <path_to_desired_output_file>
```

## SQL File Structure

The sql file must have blocks of commands seperated by **;** and comments denoted the command types. 

### Example:

```sql
-- create_Database;
CREATE DATABASE IF NOT EXISTS PROD_LEARNER_ANALYTICS;

-- set_database; 

USE DATABASE PROD_LEARNER_ANALYTICS;

-- CREATE_SCHEMAS;

CREATE SCHEMA IF NOT EXISTS SCHEMA1;
CREATE SCHEMA IF NOT EXISTS SCHEMA2;

-- grant_Table Permissions;

GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES ON FUTURE TABLES IN SCHEMA SCHEMA1 TO ROLE1;

-- set_schema schema1;

USE SCHEMA SCHEMA1;

-- Create_TABLES schema1;

CREATE TABLE IF NOT EXISTS Table1
(
"id" BIGINT,
"name" VARCHAR
);

-- set_schema schema2;

USE SCHEMA SCHEMA2;

-- Create_TABLES schema2;

CREATE TABLE IF NOT EXISTS Table1
(
"id" BIGINT,
"name" VARCHAR
);
```
**Notes** 
- All comments and commands must end with **;**
- All comments must be unqiue even if of the same type. See example for create_tables and set_schema comments. 