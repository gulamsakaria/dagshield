import { fmt } from "./ui";

export interface LedgerRow {
  label: string;
  value: number | string | null;
  sign?: "+" | "-";
  tone?: "total" | "flag";
}

// Rules show their arithmetic like a ledger: one line per figure, a ruled total, a flagged excess.
export default function Ledger({ rows }: { rows: LedgerRow[] }) {
  return (
    <table className="ledger">
      <tbody>
        {rows.map((r, i) => (
          <tr key={i} className={r.tone ? `ledger-${r.tone}` : undefined}>
            <th scope="row">{r.label}</th>
            <td className="num">
              {r.sign ? (
                <span aria-label={r.sign === "+" ? "plus" : "minus"}>
                  {r.sign === "+" ? "+" : "−"}{" "}
                </span>
              ) : null}
              {typeof r.value === "number" || r.value === null ? fmt(r.value) : r.value}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
