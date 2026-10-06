"""Export versioned gold data products with lineage and executable SQL contracts."""
from pathlib import Path
from contextlib import closing
import hashlib,json,sqlite3
import pandas as pd
import numpy as np

CONTRACT_VERSION="1.0.0"

def export_data_product(out,tables,primary_keys,source_hash,implementation,experiment):
    out=Path(out)
    schema={}; ddl=[]; checks={}
    assert all("CustomerID" not in t.columns and "InvoiceNo" not in t.columns for t in tables.values())
    for name,table in tables.items():
        if not name.replace("_","").isalnum(): raise ValueError("Invalid table identifier")
        keys=primary_keys[name]
        if not set(keys).issubset(table.columns): raise ValueError("Missing primary key")
        if table.empty or table.isna().any().any() or table.duplicated(keys).any():
            raise ValueError(f"{name}: empty table, null values or duplicate primary key")
        fields=[]; clauses=[]
        for col in table.columns:
            quoted='"'+str(col).replace('"','""')+'"'
            dtype=table[col].dtype
            sql_type="INTEGER" if pd.api.types.is_integer_dtype(dtype) or pd.api.types.is_bool_dtype(dtype) else "REAL" if pd.api.types.is_numeric_dtype(dtype) else "TEXT"
            if sql_type in ("INTEGER","REAL") and not np.isfinite(table[col].astype(float)).all():
                raise ValueError(f"{name}.{col}: non-finite numeric value")
            nonnegative=sql_type!="TEXT" and (col.endswith("_gbp") or "units" in col or "wape" in col or "coverage" in col or col=="window_days")
            if nonnegative and (table[col]<0).any(): raise ValueError(f"{name}.{col}: negative value")
            clause=f"{quoted} {sql_type} NOT NULL"
            if nonnegative: clause+=f" CHECK ({quoted} >= 0)"
            clauses.append(clause)
            fields.append(dict(name=str(col),sql_type=sql_type,nullable=False,nonnegative=nonnegative))
        key_sql=", ".join('"'+str(k).replace('"','""')+'"' for k in keys)
        statement=f'CREATE TABLE "{name}" (\n  '+",\n  ".join(clauses)+f",\n  PRIMARY KEY ({key_sql})\n) STRICT;"
        ddl.append(statement)
        schema[name]={"grain":keys,"row_count":len(table),"fields":fields}
    with closing(sqlite3.connect(out/"gold.sqlite")) as con:
        for name,table in tables.items():
            con.execute(f'DROP TABLE IF EXISTS "{name}"')
            con.execute(ddl[list(tables).index(name)])
            normalized=table.copy()
            for col in normalized.columns:
                if pd.api.types.is_datetime64_any_dtype(normalized[col].dtype):
                    normalized[col]=normalized[col].dt.strftime("%Y-%m-%d")
            normalized.to_sql(name,con,index=False,if_exists="append")
            count=con.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0]
            assert count==len(table)
            checks[name+"_sql_row_count"]=True
            # The primary-key rejection is tested against a real exported row.
            quoted_columns=", ".join('"'+str(c).replace('"','""')+'"' for c in table.columns)
            con.execute("SAVEPOINT contract_probe")
            try:
                con.execute(f'INSERT INTO "{name}" ({quoted_columns}) SELECT {quoted_columns} FROM "{name}" LIMIT 1')
            except sqlite3.IntegrityError:
                checks[name+"_duplicate_key_rejected"]=True
            else:
                raise AssertionError("SQL primary-key contract failed")
            finally:
                con.execute("ROLLBACK TO contract_probe")
                con.execute("RELEASE contract_probe")
        checks["sql_integrity_check"]=con.execute("PRAGMA integrity_check").fetchone()[0]=="ok"
        con.commit()
    (out/"gold_schema.sql").write_text("\n\n".join(ddl),encoding="utf-8")
    contracts={"schema_version":CONTRACT_VERSION,"layer":"gold","tables":schema,
        "freshness":"Static historical snapshot; no scheduled ingestion or live freshness claim",
        "breaking_change_rule":"Increase major version if a field type, primary key, target, or denominator changes"}
    (out/"data_contracts.json").write_text(json.dumps(contracts,indent=2),encoding="utf-8")
    lineage={"manifest_version":CONTRACT_VERSION,"experiment":experiment,
        "source":{"name":"UCI Online Retail","doi":"10.24432/C5BW33","license":"CC BY 4.0","workbook_sha256":source_hash},
        "implementation_sha256":hashlib.sha256(implementation.encode()).hexdigest(),
        "layers":[
            {"id":"bronze","grain":"Original invoice line","operation":"Unchanged workbook; source hash and schema verification"},
            {"id":"silver","grain":"Deduplicated invoice line","operation":"Exact duplicate removal and explicit sale/credit classification"},
            {"id":"experiment","grain":"Defined in notebook","operation":experiment},
            {"id":"gold","grain":"Declared primary keys","operation":"Aggregate evidence exported under executable SQLite STRICT contracts"}],
        "edges":[["bronze","silver"],["silver","experiment"],["experiment","gold"]],
        "privacy":"No invoice or customer identifiers in gold outputs; source workbook is not redistributed",
        "tables":[{"name":name,"csv_sha256":hashlib.sha256((out/(name+".csv")).read_bytes()).hexdigest(),"rows":len(t)} for name,t in tables.items()]}
    (out/"lineage.json").write_text(json.dumps(lineage,indent=2),encoding="utf-8")
    return checks
