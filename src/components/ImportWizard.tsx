/**
 * Milestone 1 — Excel inventory import wizard.
 * Flow: upload .xlsx -> server-side PREVIEW (read-only, nothing committed)
 *       -> operator reviews rows/site mapping and approves new sites
 *       -> explicit confirmation -> transactional commit -> result summary.
 */
import { useRef, useState } from 'react';
import { apiService, ImportPreviewResponse } from '../services/api';
import { Upload, FileSpreadsheet, AlertTriangle, CheckCircle, XCircle, Copy, ShieldQuestion, Loader2 } from 'lucide-react';

type Step = 'upload' | 'preview' | 'confirm' | 'done' | 'error';

const statusBadge = (s: string) => {
  switch (s) {
    case 'importable': return <span className="inline-flex items-center gap-1 text-[10px] px-1.5 py-0.5 rounded bg-noc-success/10 text-noc-success"><CheckCircle className="w-3 h-3" />IMPORTABLE</span>;
    case 'invalid': return <span className="inline-flex items-center gap-1 text-[10px] px-1.5 py-0.5 rounded bg-noc-danger/10 text-noc-danger"><XCircle className="w-3 h-3" />INVALID</span>;
    case 'skip_duplicate': return <span className="inline-flex items-center gap-1 text-[10px] px-1.5 py-0.5 rounded bg-noc-warning/10 text-noc-warning"><Copy className="w-3 h-3" />DUPLICATE</span>;
    default: return <span className="inline-flex items-center gap-1 text-[10px] px-1.5 py-0.5 rounded bg-noc-info/10 text-noc-info"><ShieldQuestion className="w-3 h-3" />SITE REVIEW</span>;
  }
};

export default function ImportWizard({ onClose, onCommitted }: { onClose: () => void; onCommitted: () => void }) {
  const [step, setStep] = useState<Step>('upload');
  const [file, setFile] = useState<File | null>(null);
  const [pv, setPv] = useState<ImportPreviewResponse | null>(null);
  const [approved, setApproved] = useState<Set<string>>(new Set());
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const pickFile = (f: File | null) => {
    setError(null);
    if (!f) return;
    if (!f.name.toLowerCase().endsWith('.xlsx')) { setError('Only .xlsx workbooks are supported.'); return; }
    if (f.size > 5 * 1024 * 1024) { setError('Workbook exceeds the 5 MB upload limit.'); return; }
    setFile(f);
  };

  const doPreview = async () => {
    if (!file) return;
    setBusy(true); setError(null);
    try {
      const res = await apiService.previewImport(file);
      setPv(res);
      setApproved(new Set());
      setStep('preview');
    } catch (e: any) {
      setError(e?.message || 'Preview failed'); setStep('error');
    } finally { setBusy(false); }
  };

  const toggleApprove = (loc: string) => {
    setApproved((prev) => { const n = new Set(prev); if (n.has(loc)) { n.delete(loc); } else { n.add(loc); } return n; });
  };

  const doCommit = async () => {
    if (!file) return;
    setBusy(true); setError(null);
    try {
      const res = await apiService.commitImport(file, Array.from(approved));
      setResult(`${res.message} — inserted: ${res.summary.inserted}, skipped duplicates: ${res.summary.skipped}, invalid: ${res.summary.invalid}, pending site review: ${res.summary.skipped_site_review}`);
      setStep('done');
      onCommitted();
    } catch (e: any) {
      setError(e?.message || 'Import failed — the transaction was rolled back and no rows were written.');
      setStep('error');
    } finally { setBusy(false); }
  };

  const pendingSites = pv?.site_mapping.filter((m) => m.status === 'new_pending_approval') ?? [];
  const ambiguousSites = pv?.site_mapping.filter((m) => m.status === 'ambiguous') ?? [];
  const importableCount = pv ? pv.rows.filter((r) => r.status === 'importable').length : 0;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
      <div className="bg-noc-surface border border-noc-border rounded-xl w-full max-w-4xl max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between px-6 py-4 border-b border-noc-border sticky top-0 bg-noc-surface">
          <h3 className="text-lg font-semibold text-noc-text flex items-center gap-2">
            <FileSpreadsheet className="w-5 h-5 text-noc-primary" /> Excel Inventory Import
            <span className="text-[10px] px-2 py-0.5 rounded bg-noc-surface-2 text-noc-text-muted uppercase">{step}</span>
          </h3>
          <button onClick={onClose} className="text-noc-text-muted hover:text-noc-text text-xl leading-none">&times;</button>
        </div>

        <div className="p-6 space-y-4">
          {error && (
            <div className="flex items-start gap-2 p-3 rounded-lg bg-noc-danger/10 border border-noc-danger/30 text-sm text-noc-danger">
              <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" /><span>{error}</span>
            </div>
          )}

          {step === 'upload' && (
            <div className="space-y-4">
              <p className="text-sm text-noc-text-muted">
                Upload the network device workbook (<code>.xlsx</code>). The preview step validates every row and performs
                <strong> no database writes</strong>. Nothing is imported until you explicitly confirm. Credentials are never imported.
              </p>
              <div
                onClick={() => inputRef.current?.click()}
                onDragOver={(e) => e.preventDefault()}
                onDrop={(e) => { e.preventDefault(); pickFile(e.dataTransfer.files?.[0] ?? null); }}
                className="border-2 border-dashed border-noc-border rounded-xl p-10 text-center cursor-pointer hover:border-noc-primary transition-colors"
              >
                <Upload className="w-8 h-8 mx-auto text-noc-text-muted mb-3" />
                <p className="text-sm text-noc-text">{file ? file.name : 'Click or drop a .xlsx workbook here'}</p>
                <input ref={inputRef} type="file" accept=".xlsx" className="hidden" onChange={(e) => pickFile(e.target.files?.[0] ?? null)} />
              </div>
              <div className="flex justify-end gap-3">
                <button onClick={onClose} className="px-4 py-2 text-sm border border-noc-border rounded-lg text-noc-text-muted hover:text-noc-text">Cancel</button>
                <button onClick={doPreview} disabled={!file || busy} className="px-4 py-2 text-sm text-white bg-noc-primary rounded-lg disabled:opacity-50 flex items-center gap-2">
                  {busy && <Loader2 className="w-4 h-4 animate-spin" />} Preview rows
                </button>
              </div>
            </div>
          )}

          {(step === 'preview' || step === 'confirm') && pv && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 md:grid-cols-6 gap-2 text-center">
                {([
                  ['Total rows', pv.summary.total_rows, 'text-noc-text'],
                  ['Valid', pv.summary.valid, 'text-noc-success'],
                  ['Invalid', pv.summary.invalid, 'text-noc-danger'],
                  ['Dup in file', pv.summary.duplicate_in_file, 'text-noc-warning'],
                  ['Existing in DB', pv.summary.existing_in_db, 'text-noc-warning'],
                  ['Site review', pv.summary.review_needed, 'text-noc-info'],
                ] as [string, number, string][]).map(([label, v, cls]) => (
                  <div key={label} className="p-2 rounded-lg bg-noc-bg border border-noc-border">
                    <p className={`text-lg font-bold ${cls}`}>{v}</p>
                    <p className="text-[10px] text-noc-text-muted uppercase">{label}</p>
                  </div>
                ))}
              </div>

              {(pendingSites.length > 0 || ambiguousSites.length > 0) && (
                <div className="p-3 rounded-lg bg-noc-bg border border-noc-border space-y-2">
                  <p className="text-xs font-semibold text-noc-text uppercase">Site mapping (locations are never auto-created silently)</p>
                  {pendingSites.map((m) => (
                    <label key={m.location} className="flex items-center gap-2 text-sm text-noc-text">
                      <input type="checkbox" checked={approved.has(m.location)} onChange={() => toggleApprove(m.location)} className="rounded border-noc-border" />
                      Approve NEW site <span className="font-mono">&quot;{m.location}&quot;</span>
                      <span className="text-xs text-noc-text-muted">({m.row_numbers.length} row{m.row_numbers.length > 1 ? 's' : ''})</span>
                    </label>
                  ))}
                  {ambiguousSites.map((m) => (
                    <p key={m.location} className="flex items-center gap-2 text-sm text-noc-warning">
                      <AlertTriangle className="w-4 h-4" /> &quot;{m.location}&quot; matches multiple sites ({m.candidates.join(', ')}) — rows skipped for manual review.
                    </p>
                  ))}
                </div>
              )}

              <div className="max-h-72 overflow-y-auto border border-noc-border rounded-lg">
                <table className="noc-table text-xs">
                  <thead><tr><th>Row</th><th>Name</th><th>IP</th><th>Vendor</th><th>Status</th><th>Messages</th></tr></thead>
                  <tbody>
                    {pv.rows.map((r) => (
                      <tr key={r.row_no}>
                        <td className="font-mono">{r.row_no}</td>
                        <td>{r.name ?? <span className="text-noc-danger">(missing)</span>}</td>
                        <td className="font-mono">{r.ip_raw ?? r.management_ip ?? '—'}</td>
                        <td>{r.vendor ?? '—'}</td>
                        <td>{statusBadge(r.status)}</td>
                        <td className="text-noc-text-muted">
                          {[...r.errors, ...r.warnings].join('; ')}
                          {r.status === 'skip_duplicate' && !r.errors.length && (r.duplicate_of_row ? `duplicate of row ${r.duplicate_of_row}` : 'already exists in database')}
                          {r.status === 'skip_site_review' && 'site needs approval/review'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="flex justify-between gap-3 pt-2 border-t border-noc-border">
                <button onClick={() => setStep(step === 'confirm' ? 'preview' : 'upload')} className="px-4 py-2 text-sm border border-noc-border rounded-lg text-noc-text-muted hover:text-noc-text">
                  {step === 'confirm' ? 'Back to preview' : 'Choose other file'}
                </button>
                {step === 'preview' ? (
                  <button onClick={() => setStep('confirm')} disabled={busy} className="px-4 py-2 text-sm text-white bg-noc-primary rounded-lg">
                    Continue ({importableCount} importable)
                  </button>
                ) : (
                  <button onClick={doCommit} disabled={busy} className="px-4 py-2 text-sm text-white bg-noc-danger rounded-lg disabled:opacity-50 flex items-center gap-2">
                    {busy && <Loader2 className="w-4 h-4 animate-spin" />} Confirm &amp; commit import
                  </button>
                )}
              </div>

              {step === 'confirm' && (
                <div className="p-3 rounded-lg bg-noc-warning/10 border border-noc-warning/30 text-sm text-noc-warning flex items-start gap-2">
                  <AlertTriangle className="w-4 h-4 mt-0.5" />
                  <span>This will write to the database inside a single transaction. Duplicate and invalid rows are skipped (never merged or deleted). Ambiguous sites stay pending review. Approved new sites: {Array.from(approved).join(', ') || '(none)'}. Click &quot;Confirm &amp; commit import&quot; to proceed.</span>
                </div>
              )}
            </div>
          )}

          {step === 'done' && (
            <div className="space-y-4">
              <div className="flex items-start gap-2 p-3 rounded-lg bg-noc-success/10 border border-noc-success/30 text-sm text-noc-success">
                <CheckCircle className="w-4 h-4 mt-0.5" /><span>{result}</span>
              </div>
              <p className="text-xs text-noc-text-muted">Devices were registered with monitoring DISABLED and status UNKNOWN — registration does not imply reachability. Configure credentials separately, then enable monitoring per device.</p>
              <div className="flex justify-end"><button onClick={onClose} className="px-4 py-2 text-sm text-white bg-noc-primary rounded-lg">Done</button></div>
            </div>
          )}

          {step === 'error' && (
            <div className="flex justify-end gap-3">
              <button onClick={onClose} className="px-4 py-2 text-sm border border-noc-border rounded-lg text-noc-text-muted">Close</button>
              <button onClick={() => { setStep('upload'); setError(null); }} className="px-4 py-2 text-sm text-white bg-noc-primary rounded-lg">Try another file</button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
