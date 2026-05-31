from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    with path.open('r', encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text('', encoding='utf-8')
        return
    fields: list[str] = []
    for r in rows:
        for k in r.keys():
            if k not in fields:
                fields.append(k)
    with path.open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def fnum(x: Any) -> float | None:
    try:
        if x is None or str(x).strip() == '':
            return None
        return float(x)
    except Exception:
        return None


def compact_condition(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    out = []
    for r in rows:
        out.append({
            'dataset_name': r.get('dataset_name',''),
            'model_name': r.get('model_name',''),
            'retriever': r.get('retriever',''),
            'top_k': r.get('top_k',''),
            'n': r.get('n',''),
            'answer_f1_relaxed': r.get('answer_f1_relaxed',''),
            'exact_match_relaxed': r.get('exact_match_relaxed',''),
            'evidence_f1': r.get('evidence_f1',''),
            'evidence_recall': r.get('evidence_recall',''),
            'parse_errors': r.get('parse_errors',''),
        })
    return out


def join_summaries(condition_rows: list[dict[str, Any]], oncu_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    key_to_oncu = {}
    for r in oncu_rows:
        key = (r.get('dataset_name',''), r.get('model_name',''), r.get('retriever',''), str(r.get('top_k','')))
        key_to_oncu[key] = r
    joined=[]
    for r in condition_rows:
        key=(r.get('dataset_name',''), r.get('model_name',''), r.get('retriever',''), str(r.get('top_k','')))
        o=key_to_oncu.get(key,{})
        joined.append({**r, 'valid_groups': o.get('valid_groups',''), 'total_groups': o.get('total_groups',''), 'oncu_relaxed_f1': o.get('oncu_relaxed_f1','')})
    return joined


def winners(joined: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups=defaultdict(list)
    for r in joined:
        groups[(r['dataset_name'], r['model_name'])].append(r)
    rows=[]
    for (dataset, model), items in sorted(groups.items()):
        by_oncu=max(items, key=lambda r: fnum(r.get('oncu_relaxed_f1')) if fnum(r.get('oncu_relaxed_f1')) is not None else -1)
        by_f1=max(items, key=lambda r: fnum(r.get('answer_f1_relaxed')) if fnum(r.get('answer_f1_relaxed')) is not None else -1)
        rows.append({
            'dataset_name': dataset,
            'model_name': model,
            'best_oncu_retriever': by_oncu.get('retriever',''),
            'best_oncu_top_k': by_oncu.get('top_k',''),
            'best_oncu_relaxed_f1': by_oncu.get('oncu_relaxed_f1',''),
            'best_answer_retriever': by_f1.get('retriever',''),
            'best_answer_top_k': by_f1.get('top_k',''),
            'best_answer_f1_relaxed': by_f1.get('answer_f1_relaxed',''),
        })
    return rows


def latex_table(rows: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    lines.append(r'\begin{table*}[!t]')
    lines.append(r'\renewcommand{\arraystretch}{1.10}')
    lines.append(r'\caption{Reader-facing retriever-family results. Each row reports answer and evidence performance after actually running the reader on retrieved contexts produced by lexical, dense, and hybrid retrieval. ONCU is computed using the existing no-evidence and oracle-evidence references for the same model and dataset.}')
    lines.append(r'\label{tab:reader_facing_retfam_results}')
    lines.append(r'\centering')
    lines.append(r'\scriptsize')
    lines.append(r'\setlength{\tabcolsep}{3pt}')
    lines.append(r'\begin{tabular}{llcrrrrr}')
    lines.append(r'\toprule')
    lines.append(r'Model & Dataset & Ret. & $k$ & Ans. F1 & Ev. F1 & ONCU & Parse \\')
    lines.append(r'\midrule')
    for r in rows:
        def fmt(x):
            v=fnum(x)
            return f'{v:.3f}' if v is not None else '--'
        model=str(r.get('model_name','')).replace('_','\\_')
        ds=str(r.get('dataset_name','')).replace('_','\\_')
        ret=str(r.get('retriever','')).replace('_','\\_')
        k=str(r.get('top_k',''))
        lines.append(f"{model} & {ds} & {ret} & {k} & {fmt(r.get('answer_f1_relaxed'))} & {fmt(r.get('evidence_f1'))} & {fmt(r.get('oncu_relaxed_f1'))} & {r.get('parse_errors','')} \\")
    lines.append(r'\bottomrule')
    lines.append(r'\end{tabular}')
    lines.append(r'\end{table*}')
    path.write_text('\n'.join(lines)+'\n', encoding='utf-8')


def main() -> None:
    p=argparse.ArgumentParser()
    p.add_argument('--run-dirs', nargs='+', required=True, help='Output directories from run_retriever_family_ablation.py --run-reader')
    p.add_argument('--output-dir', required=True)
    args=p.parse_args()
    run_dirs=[Path(x) for x in args.run_dirs]
    out=Path(args.output_dir)
    condition=[]
    oncu=[]
    retrieval=[]
    for d in run_dirs:
        condition += compact_condition(read_csv(d/'reader_condition_summary.csv'))
        oncu += read_csv(d/'reader_oncu_summary.csv')
        for r in read_csv(d/'retrieval_only_summary.csv'):
            r['run_dir']=str(d)
            retrieval.append(r)
    joined=join_summaries(condition,oncu)
    write_csv(out/'reader_facing_condition_summary.csv', condition)
    write_csv(out/'reader_facing_oncu_summary.csv', oncu)
    write_csv(out/'reader_facing_joined_summary.csv', joined)
    write_csv(out/'reader_facing_winners.csv', winners(joined))
    write_csv(out/'retrieval_only_family_summary.csv', retrieval)
    latex_table(joined, out/'reader_facing_retfam_results_table.tex')
    print(f'Wrote reader-facing retriever-family summaries to {out}')
    print(f'joined rows: {len(joined)}')


if __name__ == '__main__':
    main()
