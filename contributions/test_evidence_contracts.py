import unittest,tempfile,os,json,sqlite3
from pathlib import Path
from contextlib import closing
import pandas as pd
from evidence_contracts import export_data_product

class ContractTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=os.environ.get("ROOT2RAJ_TEST_TEMP",os.environ.get("TEMP",".")))
        self.out=Path(self.temp.name)
    def tearDown(self):
        self.temp.cleanup()
    def export(self,table):
        table.to_csv(self.out/"facts.csv",index=False)
        return export_data_product(self.out,{"facts":table},{"facts":["key"]},"a"*64,"verified implementation","Synthetic contract test")
    def test_valid_export_and_database_key_enforcement(self):
        checks=self.export(pd.DataFrame({"key":["A","B"],"units":[2,3]}))
        self.assertTrue(all(checks.values()))
        with closing(sqlite3.connect(self.out/"gold.sqlite")) as con:
            self.assertEqual(con.execute("SELECT SUM(units) FROM facts").fetchone()[0],5)
            with self.assertRaises(sqlite3.IntegrityError):
                con.execute("INSERT INTO facts VALUES ('C',-1)")
            with self.assertRaises(sqlite3.IntegrityError):
                con.execute("INSERT INTO facts VALUES ('C',NULL)")
            with self.assertRaises(sqlite3.IntegrityError):
                con.execute("INSERT INTO facts VALUES ('C','wrong type')")
        contracts=json.loads((self.out/"data_contracts.json").read_text())
        self.assertEqual(contracts["schema_version"],"1.0.0")
        lineage=json.loads((self.out/"lineage.json").read_text())
        self.assertEqual(len(lineage["tables"][0]["csv_sha256"]),64)
    def test_duplicate_primary_key_rejected(self):
        with self.assertRaises(ValueError): self.export(pd.DataFrame({"key":["A","A"],"units":[1,2]}))
    def test_null_measure_rejected(self):
        with self.assertRaises(ValueError): self.export(pd.DataFrame({"key":["A"],"units":[None]}))
    def test_negative_measure_rejected(self):
        with self.assertRaises(ValueError): self.export(pd.DataFrame({"key":["A"],"units":[-1]}))
    def test_nonfinite_measure_rejected(self):
        with self.assertRaises(ValueError): self.export(pd.DataFrame({"key":["A"],"units":[float("inf")]}))
