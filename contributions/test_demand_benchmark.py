import unittest
import numpy as np
import pandas as pd
from demand_benchmark import make_features,select_products,metrics

class DemandTests(unittest.TestCase):
    def panel(self):
        return pd.DataFrame({"StockCode":["A"]*70,"date":pd.date_range("2011-01-01",periods=70),"units":np.arange(70,dtype=float)})
    def test_shifted_lags_and_mean(self):
        f,_=make_features(self.panel())
        first=f.iloc[0]
        self.assertEqual(first.lag_1,27)
        self.assertEqual(first.lag_7,21)
        self.assertEqual(first.mean_7,np.mean(np.arange(21,28)))
        self.assertEqual(first.mean_28,np.mean(np.arange(28)))
    def test_future_changes_do_not_change_past_features(self):
        a=self.panel(); b=a.copy()
        b.loc[b.date>=pd.Timestamp("2011-02-20"),"units"]=9999
        fa,columns=make_features(a); fb,_=make_features(b)
        mask=fa.date<=pd.Timestamp("2011-02-20")
        np.testing.assert_allclose(fa.loc[mask,columns],fb.loc[mask,columns])
    def test_product_selection_ignores_future(self):
        sales=pd.DataFrame({"StockCode":["A","B","B"],"InvoiceDate":pd.to_datetime(["2011-01-01","2011-01-01","2011-10-01"]),"Quantity":[10,2,100000]})
        self.assertEqual(select_products(sales,1),["A"])
    def test_product_lags_do_not_cross_boundaries(self):
        a=self.panel(); b=a.copy(); b.StockCode="B"; b.units=1000
        f,_=make_features(pd.concat([a,b]))
        self.assertTrue((f.loc[f.StockCode=="B","lag_1"]==1000).all())
    def test_wape_and_mae(self):
        self.assertEqual(metrics([0,10],[2,8]),dict(mae_units=2.,wape_pct=40.))
        with self.assertRaises(ValueError): metrics([0],[0])
