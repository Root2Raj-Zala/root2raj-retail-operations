"""Execute the public notebooks, keeping run outputs and caches inside this project."""
from pathlib import Path
import argparse,json,os,shutil,time,sys
import nbformat
from nbclient import NotebookClient

def main():
    project=Path(__file__).resolve().parent
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-workbook",type=Path,help="Unchanged UCI Online Retail.xlsx; otherwise downloaded by each notebook")
    parser.add_argument("--output-dir",type=Path,default=project/".runs")
    parser.add_argument("--kernel",help="Optional installed kernel; defaults to this Python interpreter")
    args=parser.parse_args()
    output=args.output_dir.resolve()
    output.mkdir(parents=True,exist_ok=True)
    cache=output/".cache"
    paths={"MPLCONFIGDIR":"matplotlib","IPYTHONDIR":"ipython","JUPYTER_CONFIG_DIR":"jupyter/config","JUPYTER_DATA_DIR":"jupyter/data","JUPYTER_RUNTIME_DIR":"jupyter/runtime","TEMP":"tmp","TMP":"tmp"}
    for variable,relative in paths.items():
        folder=cache/relative
        folder.mkdir(parents=True,exist_ok=True)
        os.environ[variable]=str(folder)
    os.environ["PYTHONDONTWRITEBYTECODE"]="1"
    if not args.kernel:
        args.kernel="root2raj-reproduction"
        spec=cache/"jupyter/data/kernels"/args.kernel
        spec.mkdir(parents=True,exist_ok=True)
        (spec/"kernel.json").write_text(json.dumps({"argv":[sys.executable,"-B","-m","ipykernel_launcher","-f","{connection_file}"],"display_name":"Root2Raj reproduction","language":"python"}),encoding="utf-8")
    records=[]
    for notebook in sorted((project/"notebooks").glob("*.ipynb")):
        run=output/notebook.stem
        (run/"data").mkdir(parents=True,exist_ok=True)
        if args.source_workbook:
            shutil.copyfile(args.source_workbook,run/"data/Online Retail.xlsx")
        os.environ["ROOT2RAJ_HOME"]=str(run)
        nb=nbformat.read(notebook,as_version=4)
        start=time.time()
        print("Executing",notebook.name,flush=True)
        NotebookClient(nb,timeout=600,kernel_name=args.kernel,resources={"metadata":{"path":str(run)}}).execute()
        nbformat.write(nb,run/notebook.name)
        records.append({"notebook":notebook.name,"elapsed_seconds":round(time.time()-start,2),"results":json.loads((run/"outputs/results.json").read_text(encoding="utf-8")),"validation":json.loads((run/"outputs/validation.json").read_text(encoding="utf-8"))})
    if not records: raise RuntimeError("No notebooks found")
    (output/"verification.json").write_text(json.dumps(records,indent=2),encoding="utf-8")
    print("Verified",len(records),"notebooks; outputs:",output,flush=True)

if __name__=="__main__":
    main()
