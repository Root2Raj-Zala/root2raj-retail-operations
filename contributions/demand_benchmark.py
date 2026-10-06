"""One-day-ahead benchmark with shifted features and fixed chronological splits."""
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from sklearn.ensemble import HistGradientBoostingRegressor
from threadpoolctl import threadpool_limits

TRAIN_END=pd.Timestamp("2011-06-30")
VALID_END=pd.Timestamp("2011-08-31")
TEST_END=pd.Timestamp("2011-11-30")

def select_products(sales,n=12):
    # Product selection uses only the initial training period.
    training=sales[sales.InvoiceDate.dt.normalize()<=TRAIN_END]
    ranked=training.groupby("StockCode").Quantity.sum().sort_values(ascending=False,kind="stable")
    return ranked.head(n).index.astype(str).tolist()

def make_panel(sales,products):
    days=pd.date_range("2010-12-01",TEST_END,freq="D")
    data=sales[sales.StockCode.isin(products)].copy()
    data["date"]=data.InvoiceDate.dt.normalize()
    sums=data.groupby(["StockCode","date"]).Quantity.sum()
    index=pd.MultiIndex.from_product([products,days],names=["StockCode","date"])
    panel=sums.reindex(index,fill_value=0).rename("units").reset_index()
    return panel.sort_values(["StockCode","date"]).reset_index(drop=True)

def make_features(panel):
    panel=panel.sort_values(["StockCode","date"]).reset_index(drop=True).copy()
    grouped=panel.groupby("StockCode",sort=False).units
    for lag in (1,7,14,28):
        panel[f"lag_{lag}"]=grouped.shift(lag)
    for width in (7,28):
        panel[f"mean_{width}"]=grouped.transform(lambda s:s.shift(1).rolling(width,min_periods=width).mean())
    day=panel.date.dt.dayofweek
    panel["dow_sin"]=np.sin(2*np.pi*day/7)
    panel["dow_cos"]=np.cos(2*np.pi*day/7)
    panel["month_sin"]=np.sin(2*np.pi*panel.date.dt.month/12)
    panel["month_cos"]=np.cos(2*np.pi*panel.date.dt.month/12)
    dummies=pd.get_dummies(panel.StockCode,prefix="sku",dtype=float)
    panel=pd.concat([panel,dummies],axis=1)
    features=["lag_1","lag_7","lag_14","lag_28","mean_7","mean_28","dow_sin","dow_cos","month_sin","month_cos"]+dummies.columns.tolist()
    return panel.dropna(subset=features).reset_index(drop=True),features

def metrics(actual,prediction):
    actual=np.asarray(actual,dtype=float); prediction=np.asarray(prediction,dtype=float)
    if len(actual)==0 or not np.isfinite(prediction).all() or actual.sum()<=0:
        raise ValueError("Expected finite predictions and positive aggregate demand")
    error=np.abs(actual-prediction)
    return dict(mae_units=float(error.mean()),wape_pct=float(100*error.sum()/actual.sum()))

def run_benchmark(table,features):
    train=table[table.date<=TRAIN_END]
    valid=table[(table.date>TRAIN_END)&(table.date<=VALID_END)]
    test=table[(table.date>VALID_END)&(table.date<=TEST_END)]
    assert train.date.max()<valid.date.min() and valid.date.max()<test.date.min()
    candidates={
        "Ridge alpha=1":make_pipeline(StandardScaler(),Ridge(alpha=1)),
        "Ridge alpha=100":make_pipeline(StandardScaler(),Ridge(alpha=100)),
        "Gradient boosting 15 leaves":HistGradientBoostingRegressor(max_iter=120,max_leaf_nodes=15,learning_rate=.06,loss="absolute_error",early_stopping=False,random_state=42),
        "Gradient boosting 31 leaves":HistGradientBoostingRegressor(max_iter=120,max_leaf_nodes=31,learning_rate=.06,loss="absolute_error",early_stopping=False,random_state=42)}
    baselines={"Yesterday":"lag_1","Same weekday last week":"lag_7","Trailing 7-day mean":"mean_7"}
    validation=[]; valid_predictions={}
    with threadpool_limits(limits=2):
        for name,column in baselines.items():
            pred=valid[column].to_numpy()
            valid_predictions[name]=pred
            validation.append(dict(model=name,**metrics(valid.units,pred)))
        for name,model in candidates.items():
            model.fit(train[features],train.units)
            pred=np.clip(model.predict(valid[features]),0,None)
            valid_predictions[name]=pred
            validation.append(dict(model=name,**metrics(valid.units,pred)))
    validation=pd.DataFrame(validation).sort_values(["wape_pct","model"])
    winner=validation.iloc[0].model
    # Selection is completed before any test prediction or test score.
    final_train=table[table.date<=VALID_END]
    predictions=test[["StockCode","date","units"]].copy()
    scorecard=[]
    with threadpool_limits(limits=2):
        for name in validation.model:
            if name in baselines:
                pred=test[baselines[name]].to_numpy()
            else:
                fitted=clone(candidates[name]).fit(final_train[features],final_train.units)
                pred=np.clip(fitted.predict(test[features]),0,None)
            predictions[name]=pred
            val=validation.set_index("model").loc[name]
            scorecard.append(dict(model=name,selected_on_validation=name==winner,
                validation_mae_units=float(val.mae_units),validation_wape_pct=float(val.wape_pct),
                test_mae_units=metrics(test.units,pred)["mae_units"],test_wape_pct=metrics(test.units,pred)["wape_pct"]))
    per_product=[]
    for sku,g in predictions.groupby("StockCode"):
        if g.units.sum()>0:
            for name in validation.model:
                per_product.append(dict(StockCode=sku,model=name,**metrics(g.units,g[name])))
    return pd.DataFrame(scorecard),predictions,pd.DataFrame(per_product),winner
