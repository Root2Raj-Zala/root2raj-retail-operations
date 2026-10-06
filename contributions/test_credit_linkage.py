import unittest
from datetime import datetime,timedelta
from credit_linkage import match_events,prepare_groups
import pandas as pd

class CreditTests(unittest.TestCase):
    def event(self,day,kind,q,price=2,pos=0):
        return (datetime(2020,1,1)+timedelta(days=day),kind,q,price,pos)
    def test_partial_and_capacity(self):
        result=match_events([self.event(0,1,5),self.event(1,0,8),self.event(2,0,3)])
        self.assertEqual(result["matched_units"],5)
        self.assertEqual(result["unmatched_units"],6)
    def test_future_sale(self):
        self.assertEqual(match_events([self.event(0,0,3),self.event(1,1,3)])["matched_units"],0)
    def test_same_timestamp(self):
        self.assertEqual(match_events([self.event(0,1,3),self.event(0,0,3)])["matched_units"],0)
    def test_window_boundary(self):
        self.assertEqual(match_events([self.event(0,1,3),self.event(7,0,3)],7)["matched_units"],3)
        self.assertEqual(match_events([self.event(0,1,3),self.event(7.01,0,3)],7)["matched_units"],0)
    def test_fifo_lifo_lag(self):
        events=[self.event(0,1,2),self.event(5,1,2),self.event(6,0,2)]
        self.assertEqual(match_events(events,90,"FIFO")["lag_value"],24)
        self.assertEqual(match_events(events,90,"LIFO")["lag_value"],4)
    def test_key_isolation_and_missing_id(self):
        f=pd.DataFrame([
            [1,"A",2,"2020-01-01",5,"sale"],
            [1,"A",3,"2020-01-02",-1,"credit"],
            [2,"A",2,"2020-01-02",-1,"credit"],
            [1,"B",2,"2020-01-02",-1,"credit"],
            [None,"A",2,"2020-01-02",-1,"credit"]],
            columns=["CustomerID","StockCode","UnitPrice","InvoiceDate","Quantity","kind"])
        f.InvoiceDate=pd.to_datetime(f.InvoiceDate)
        self.assertEqual(sum(match_events(g)["matched_units"] for g in prepare_groups(f)),0)
        self.assertEqual(len(prepare_groups(f)),3)
    def test_invalid_inputs(self):
        with self.assertRaises(ValueError): match_events([],0)
        with self.assertRaises(ValueError): match_events([] ,90,"random")
        with self.assertRaises(ValueError): match_events([self.event(0,1,-3)])
