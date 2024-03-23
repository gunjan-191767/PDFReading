##pip install tabula-py
import pandas as pd
from sqlalchemy import create_engine
import tabula

# Assuming dfs_page1 is already defined
# Assuming column_names_page1 is already defined
column_names_page1 = [
    "App ID", "Xref", "Settlement Date", "Broker", "Sub Broker", 
    "Borrower Name", "Description", "Total Loan Amount", 
    "Commission Rate", "Upfront", "Upfront Incl GST"
]

# Read PDF tables
dfs_page1 =tabula.read_pdf("Test.pdf", pages=1, multiple_tables=True)

# Initialize Excel writer
# writer = pd.ExcelWriter("output.xlsx", engine="xlsxwriter")

# Combine tables from page 1 into a single DataFrame
combined_df = pd.concat(dfs_page1, ignore_index=True)

# Process combined DataFrame
if len(combined_df.columns) > 0 and combined_df.columns[0] == "Unnamed: 0":
    # Drop the first column if it is named "Unnamed: 0"
    combined_df = combined_df.drop(columns=["Unnamed: 0"])

# Assign column names to DataFrame
combined_df.columns = column_names_page1
values = combined_df["App ID"].str.split()
combined_df["App ID"] = values.str[0]
combined_df["Xref"] = values.str[-1]

split_string = ' Upfront Commission'
combined_df[["Borrower Name", "Description"]] = combined_df['Borrower Name'].str.split(split_string, n=1, expand=True)
combined_df['Description'] = combined_df['Description'] + split_string

combined_df["Borrower Name"] = combined_df["Borrower Name"].str.strip()
combined_df["Description"] = combined_df["Description"].str.strip()

# Drop duplicates based on Xref and Total Loan Amount
deduplicated_df = combined_df.drop_duplicates(subset=["Xref", "Total Loan Amount"])

# # Write DataFrame to Excel sheet
# deduplicated_df.to_excel(writer, sheet_name="Deduplicated_Data", index=False)

# MySQL connection parameters
host = 'localhost'
user = 'root'
password = 'your_password'
database = 'tax'
table_name = 'transactions'

# Create SQLAlchemy engine
engine = create_engine(f'mysql://{user}:{password}@{host}/{database}')

# Check if table exists
if engine.has_table(table_name):
    # Append deduplicated data to existing table
    deduplicated_df.to_sql(name=table_name, con=engine, if_exists='append', index=False, chunksize=1000)
else:
    # Create table if it does not exist
    deduplicated_df.to_sql(name=table_name, con=engine, if_exists='replace', index=False)


# writer.close()

####-- 1. Calculate the total loan amount during a specific time period.
SELECT SUM("Total Loan Amount") AS "Total Loan Amount" FROM "transactions" WHERE "Settlement Date" BETWEEN 'start_date' AND 'end_date';

# ###-- 2. Calculate the highest loan amount given by a broker.
SELECT MAX("Total Loan Amount") AS "Highest Loan Amount" FROM "transactions" WHERE "Broker" = 'broker_name';

# ########-- Part 5: Reporting

# #############-- 1. Generate a report for the broker, sorting loan amounts in descending order from maximum to minimum, covering daily, weekly, and monthly periods.
SELECT "Settlement Date", "Broker", "Total Loan Amount" FROM "transactions" ORDER BY "Settlement Date" DESC, "Total Loan Amount" DESC;
# 
# #########-- 2. Generate a report of the total loan amount grouped by date.
SELECT "Settlement Date", SUM("Total Loan Amount") AS "Total Loan Amount" FROM "transactions" GROUP BY "Settlement Date";

# ###########-- 3. Define tier level of each transaction
SELECT *, CASE WHEN "Total Loan Amount" > 100000 THEN 'Tier 1' WHEN "Total Loan Amount" > 50000 THEN 'Tier 2' WHEN "Total Loan Amount" > 10000 THEN 'Tier 3' ELSE 'Tier 4' END AS "Tier" FROM "transactions";

# ######### 4. Generate a report of the number of loans under each tier group by date.
SELECT "Settlement Date", "Tier", COUNT(*) AS "Number of Loans" FROM (SELECT *, CASE WHEN "Total Loan Amount" > 100000 THEN 'Tier 1' WHEN "Total Loan Amount" > 50000 THEN 'Tier 2' WHEN "Total Loan Amount" > 10000 THEN 'Tier 3' ELSE 'Tier 4' END AS "Tier" FROM "transactions") AS tiered_data GROUP BY "Settlement Date", "Tier";
