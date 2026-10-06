"""Capacity-constrained candidate credit linkage; no claim of ground truth."""
from collections import deque, defaultdict
from datetime import timedelta
import pandas as pd

def match_events(events, window_days=90, policy="FIFO"):
    if policy not in {"FIFO","LIFO"} or window_days <= 0:
        raise ValueError("Expected FIFO/LIFO and a positive lookback")
    # kind 0 = credit, kind 1 = sale: same-time sales cannot fund credits.
    events=sorted(events,key=lambda e:(e[0],e[1],e[4]))
    lots=deque()
    matched=unmatched=lag_value=matched_value=0.0
    buckets=defaultdict(float)
    monthly=defaultdict(lambda:[0.0,0.0])
    credit_units=credit_value=0.0
    for time,kind,quantity,price,position in events:
        if quantity<=0 or price<=0 or kind not in (0,1):
            raise ValueError("Events require positive magnitudes and prices")
        while lots and lots[0][0] < time-timedelta(days=window_days):
            lots.popleft()
        if kind==1:
            lots.append([time,float(quantity)])
            continue
        remaining=float(quantity)
        credit_units+=remaining
        credit_value+=remaining*price
        month=time.strftime("%Y-%m")
        monthly[month][1]+=remaining*price
        while lots and remaining>0:
            lot=lots[0] if policy=="FIFO" else lots[-1]
            lag=(time-lot[0]).total_seconds()/86400
            assert 0 < lag <= window_days
            taken=min(remaining,lot[1])
            value=taken*price
            matched+=taken
            matched_value+=value
            lag_value+=lag*value
            monthly[month][0]+=value
            bucket="<1 day" if lag<1 else "1-7 days" if lag<=7 else "7-30 days" if lag<=30 else "30-90 days" if lag<=90 else "90-365 days"
            buckets[bucket]+=value
            remaining-=taken
            lot[1]-=taken
            if lot[1]==0:
                lots.popleft() if policy=="FIFO" else lots.pop()
        unmatched+=remaining
    assert abs(matched+unmatched-credit_units)<1e-6
    assert matched_value<=credit_value+1e-6
    return dict(matched_units=matched,unmatched_units=unmatched,matched_value=matched_value,
                credit_value=credit_value,lag_value=lag_value,buckets=dict(buckets),monthly=dict(monthly))

def prepare_groups(frame):
    required={"CustomerID","StockCode","UnitPrice","InvoiceDate","Quantity","kind"}
    if not required.issubset(frame.columns):
        raise ValueError("Missing required columns")
    eligible=frame[frame.CustomerID.notna() & frame.kind.isin(["sale","credit"])].copy()
    eligible["position"]=range(len(eligible))
    eligible["event_kind"]=(eligible.kind=="sale").astype(int)
    eligible=eligible.sort_values(["InvoiceDate","event_kind","position"],kind="stable")
    groups=[]
    for _,g in eligible.groupby(["CustomerID","StockCode","UnitPrice"],sort=False):
        if not (g.event_kind==0).any():
            continue
        groups.append([(t.to_pydatetime(),int(k),abs(float(q)),float(p),int(i))
                       for t,k,q,p,i in g[["InvoiceDate","event_kind","Quantity","UnitPrice","position"]].itertuples(index=False,name=None)])
    return groups

def run_linkage(frame,windows=(7,30,90,365)):
    groups=prepare_groups(frame)
    credits=frame[frame.kind=="credit"]
    total=float((-credits.Quantity*credits.UnitPrice).sum())
    identified=float((-credits.loc[credits.CustomerID.notna(),"Quantity"]*credits.loc[credits.CustomerID.notna(),"UnitPrice"]).sum())
    summary=[]; lag_rows=[]; monthly_rows=[]
    for window in windows:
        for policy in ("FIFO","LIFO"):
            parts=[match_events(g,window,policy) for g in groups]
            value=sum(p["matched_value"] for p in parts)
            eligible_value=sum(p["credit_value"] for p in parts)
            assert abs(eligible_value-identified)<1e-5
            buckets=defaultdict(float); months=defaultdict(lambda:[0.,0.])
            for part in parts:
                for b,v in part["buckets"].items(): buckets[b]+=v
                for m,vals in part["monthly"].items():
                    for i in (0,1): months[m][i]+=vals[i]
            summary.append(dict(window_days=window,policy=policy,matched_value_gbp=value,
                unmatched_identified_value_gbp=identified-value,missing_id_credit_value_gbp=total-identified,
                all_credit_value_gbp=total,identified_credit_value_gbp=identified,
                coverage_all_pct=100*value/total,coverage_identified_pct=100*value/identified,
                value_weighted_lag_days=sum(p["lag_value"] for p in parts)/value if value else 0))
            for b in ["<1 day","1-7 days","7-30 days","30-90 days","90-365 days"]:
                lag_rows.append(dict(window_days=window,policy=policy,lag_bucket=b,matched_value_gbp=buckets[b]))
            all_months=(-credits.Quantity*credits.UnitPrice).groupby(credits.InvoiceDate.dt.strftime("%Y-%m")).sum()
            for month,all_value in all_months.items():
                vals=months[month]
                monthly_rows.append(dict(window_days=window,policy=policy,month=month,
                    matched_value_gbp=vals[0],identified_credit_value_gbp=vals[1],all_credit_value_gbp=float(all_value),
                    coverage_all_pct=100*vals[0]/all_value if all_value else 0))
    return pd.DataFrame(summary),pd.DataFrame(lag_rows),pd.DataFrame(monthly_rows)
